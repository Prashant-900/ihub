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
                "expressions": ["Blushing.exp3"],
                "triggers": [],
                "trigger_speed": 1.0,
            },
            {
                "time": 1.0,
                "expressions": [],
                "triggers": [],
                "trigger_speed": 0.8,
            }
        ]
    }

class Pipeline:
    def __init__(self, device=None):
        self.stt = STT(device=device)

    def handle_input(self, audio_frames: list = None, user_text: str = None):
        """
        Process either audio_frames or user_text, persist user message and AI response to DB,
        create a dummy audio file for the AI response in backend/cache and return a dict:
        { 'ai_text': str, 'timeline': list, 'audio_id': str, 'user_row': {...}, 'ai_row': {...} }
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
                    user_row = None
        except Exception:
            user_row = None

        # create AI reply text (placeholder)
        ai_text = (user_text or '')

        # Attempt to synthesize real audio using remote TTS and save to cache
        cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        audio_id = None
        try:
            audio_id = synthesize_text(ai_text, cache_dir=cache_dir)
        except Exception:
            # fallback dummy file
            audio_id = str(uuid.uuid4())
            audio_path = os.path.join(cache_dir, f"{audio_id}.wav")
            try:
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
                    ai_row = None
        except Exception:
            ai_row = None

        return {
            'ai_text': ai_text,
            'timeline': timeline,
            'audio_id': audio_id,
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
