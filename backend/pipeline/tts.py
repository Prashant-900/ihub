import requests
import json
import os
import time
import uuid
from typing import Optional

"""
Text-to-Speech synthesis module using remote IndexTTS service.

This module provides functions to synthesize text into speech using a remote TTS API,
with support for voice reference files and local caching of generated audio.
"""

# Configuration for the IndexTTS demo service
BASE = "https://indexteam-indextts-2-demo.hf.space"
UPLOAD_URL = f"{BASE}/gradio_api/upload?upload_id=python_upload"
QUEUE_URL = f"{BASE}/gradio_api/queue/join?__theme=system"
DATA_URL_TEMPLATE = f"{BASE}/gradio_api/queue/data?session_hash={{session_hash}}"

# Default voice reference file path
DEFAULT_VOICE_REF = os.path.join(os.path.dirname(__file__), '..', 'sample', 'sample_1.mp3')


def synthesize_text(
    text: str,
    cache_dir: Optional[str] = None,
    voice_ref: Optional[str] = None,
    timeout: int = 60
) -> str:
    """Synthesize text into speech using remote TTS service.
    
    Converts text to speech using the IndexTTS service and caches the resulting
    audio file locally for efficient retrieval.
    
    Args:
        text: Text to synthesize
        cache_dir: Directory to cache audio files. Defaults to backend/cache
        voice_ref: Path to voice reference audio file. Uses default if not provided
        timeout: Maximum seconds to wait for synthesis. Defaults to 60
        
    Returns:
        Filename (with extension) of the generated audio file in cache_dir
        
    Raises:
        RuntimeError: If synthesis, polling, or download fails
    """
    if cache_dir is None:
        # default to backend/cache relative to repo
        cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'cache'))
    os.makedirs(cache_dir, exist_ok=True)

    voice_ref = voice_ref or DEFAULT_VOICE_REF

    session_hash = f"python_session_{uuid.uuid4().hex[:8]}"
    headers = {"Content-Type": "application/json", "Origin": BASE}

    # Upload voice reference if available
    upload_path = None
    if voice_ref and os.path.exists(voice_ref):
        try:
            with open(voice_ref, 'rb') as vf:
                files = {"files": (os.path.basename(voice_ref), vf, 'audio/mpeg')}
                resp = requests.post(UPLOAD_URL, files=files, timeout=20)
                resp.raise_for_status()
                upload_data = resp.json()
                if isinstance(upload_data, list) and upload_data:
                    upload_path = upload_data[0]
        except Exception:
            upload_path = None

    # Build file_info only if we have an upload_path
    file_info = None
    if upload_path:
        try:
            file_info = {
                "path": upload_path,
                "url": f"{BASE}/gradio_api/file={upload_path}",
                "orig_name": os.path.basename(voice_ref),
                "size": os.path.getsize(voice_ref),
                "mime_type": "audio/mpeg",
                "meta": {"_type": "gradio.FileData"}
            }
        except Exception:
            file_info = None

    # Build payload (closely following the original script's shape)
    data_array = [
        "Same as the voice reference",
        file_info,
        text,
        None,
        0.8, 0, 0, 0, 0, 0, 0, 0, 0, "",
        False, 120, True, 0.8, 30, 0.8, 0, 3, 10, 1500
    ]

    payload = {"data": data_array, "event_data": None, "fn_index": 6, "trigger_id": 7, "session_hash": session_hash}

    # Send synthesis request
    try:
        queue_response = requests.post(QUEUE_URL, headers=headers, data=json.dumps(payload), timeout=20)
        queue_response.raise_for_status()
        queue_data = queue_response.json()
        event_id = queue_data.get('event_id')
        if not event_id:
            raise RuntimeError('No event_id from TTS queue response')
    except Exception as e:
        raise RuntimeError(f'TTS queue request failed: {e}')

    # Poll for result
    data_url = DATA_URL_TEMPLATE.format(session_hash=session_hash)
    attempts = 0
    max_attempts = max(5, timeout)
    result_data = None
    while attempts < max_attempts:
        attempts += 1
        try:
            r = requests.get(data_url, headers=headers, stream=True, timeout=10)
            if r.status_code != 200:
                time.sleep(1)
                continue
            for line in r.iter_lines():
                if not line:
                    continue
                try:
                    s = line.decode('utf-8')
                except Exception:
                    continue
                if not s.startswith('data: '):
                    continue
                try:
                    ev = json.loads(s[6:])
                except Exception:
                    continue
                msg = ev.get('msg')
                if msg == 'process_completed':
                    result_data = ev.get('output', {}).get('data')
                    break
            if result_data:
                break
        except Exception:
            time.sleep(1)

    if not result_data:
        raise RuntimeError('TTS polling timed out')

    # Download first file from result_data
    audio_url = None
    if isinstance(result_data, list) and len(result_data) > 0:
        first = result_data[0]
        file_data = first.get('value') if isinstance(first, dict) and first.get('value') else first
        if isinstance(file_data, dict) and file_data.get('url'):
            audio_url = file_data.get('url')

    if not audio_url:
        raise RuntimeError('No audio URL in TTS result')

    # Fetch audio and save to cache_dir with uuid
    try:
        r = requests.get(audio_url, timeout=20)
        r.raise_for_status()
        content_type = r.headers.get('content-type', '')
        ext = '.wav' if 'wav' in content_type or audio_url.lower().endswith('.wav') else os.path.splitext(audio_url)[1] or '.wav'
        audio_id = uuid.uuid4().hex
        filename = f"{audio_id}{ext}"
        out_path = os.path.join(cache_dir, filename)
        with open(out_path, 'wb') as f:
            f.write(r.content)
        # return the saved filename (includes extension) so callers can fetch /cache/<filename>
        return filename
    except Exception as e:
        raise RuntimeError(f'Failed to download TTS audio: {e}')