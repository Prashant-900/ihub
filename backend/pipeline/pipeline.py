import numpy as np
import os
import uuid
import json
from .stt import STT
from .tts import synthesize_text
try:
    # import db manager if available
    from database import db
except Exception:
    try:
        from backend.database import db
    except Exception:
        try:
            from ..database import db
        except Exception:
            db = None

def get_animation_timeline():
    """Return animation timeline for speech end"""
    return {
        "timeline": [
            {
                "time": 0.0,
                "expressions": ["Normal.exp3"],
                "triggers": [],
                "trigger_speed": 1.0,
            },
            {
                "time": 0.5,
                "expressions": ["Smile.exp3"],
                "triggers": ["shaketrigger"],
                "trigger_speed": 1.5,
            },
            {
                "time": 1.0,
                "expressions": ["Sad.exp3"],
                "triggers": [],
                "trigger_speed": 1.0,
            }
        ]
    }

def get_text_box_data(ai_text):
    """Generate text box data for displaying AI response text.
    Splits text into sentences and assigns timing and positioning.
    """
    if not ai_text:
        return []
    
    # Simple split by sentence (period, exclamation, question mark)
    sentences = []
    current = ""
    for char in ai_text:
        current += char
        if char in '.!?':
            sentences.append(current.strip())
            current = ""
    if current.strip():
        sentences.append(current.strip())
    
    # Estimate duration per sentence (roughly 1 second per 10 words)
    text_data = []
    pos_cycle = [0, 1, 2, 3]  # Cycle through positions
    for idx, sentence in enumerate(sentences):
        word_count = len(sentence.split())
        duration = max(1.0, word_count / 10.0)
        
        text_data.append({
            "sentence": sentence,
            "duration": duration,
            "pos": pos_cycle[idx % len(pos_cycle)],
            "type": idx % 4  # Cycle through types
        })
    
    return text_data

class Pipeline:
    def __init__(self, device=None):
        self.stt = STT(device=device)

    def handle_input(self, audio_frames: list = None, user_text: str = None, response_mode: str = 'audio'):
        """
        Process either audio_frames or user_text, persist user message and AI response to DB,
        create audio file for the AI response in backend/cache (only if response_mode='audio') and return a dict:
        { 'ai_text': str, 'timeline': list, 'audio_id': str or None, 'user_row': {...}, 'ai_row': {...} }
        
        response_mode: 'audio' or 'text' - determines if TTS should be run
        """
        # get transcription / text
        if user_text is None:
            if not audio_frames:
                user_text = ''
            else:
                audio_data = np.concatenate(audio_frames) if isinstance(audio_frames, list) and audio_frames else np.array([], dtype=np.float32)
                try:
                    user_text = self.stt.transcribe(audio_data)
                except Exception:
                    user_text = ''

        # create pipeline response (timeline + text)
        response = self.process_audio(audio_frames or [])
        timeline = response.get('timeline') if response and response.get('timeline') is not None else []
        # If timeline is a dict with 'timeline' key, unwrap it
        if isinstance(timeline, dict) and 'timeline' in timeline:
            timeline = timeline['timeline']
        if not isinstance(timeline, list):
            timeline = list(timeline) if timeline is not None else []

        # persist user message (log errors if DB operations fail)
        user_row = None
        try:
            if db:
                try:
                    user_row = db.insert_message('user', user_text or '', None)
                except Exception:
                    pass
        except Exception:
            pass

        # create AI reply text (placeholder)
        ai_text = (user_text or '')

        # Synthesize audio using TTS only if response_mode is 'audio'
        cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        audio_id = None
        
        if response_mode == 'audio':
            try:
                # synthesize_text returns the filename (with extension)
                # We pass cache_dir (directory), not audio_path (file)
                filename = synthesize_text(ai_text, cache_dir)
                # Extract audio_id from filename (remove extension)
                audio_id = os.path.splitext(filename)[0]
            except Exception:
                # Fallback to dummy audio if TTS fails
                try:
                    audio_id = str(uuid.uuid4())
                    audio_path = os.path.join(cache_dir, f"{audio_id}.wav")
                    with open(audio_path, 'wb') as f:
                        f.write(b'RIFF....WAVEfmt ')
                except Exception:
                    pass

        ai_row = None
        try:
            if db:
                try:
                    ai_row = db.insert_ai_response(ai_text, timeline, audio_id)
                except Exception:
                    pass
        except Exception:
            pass

        return {
            'ai_text': ai_text,
            'timeline': timeline,
            'audio_id': audio_id,
            'text': get_text_box_data(ai_text),
            'user_row': user_row,
            'ai_row': ai_row,
            'user_text': user_text,
        }

    def process_audio(self, audio_frames: list):
        """
        audio_frames: list of np.ndarray float32 chunks [-1,1]
        Returns dict with transcription + animation timeline
        """
        if not audio_frames:
            audio_data = np.array([], dtype=np.float32)
        else:
            audio_data = np.concatenate(audio_frames)

        text = self.stt.transcribe(audio_data)

        response = {
            "text": text,
        }
        response.update(get_animation_timeline())
        return response
