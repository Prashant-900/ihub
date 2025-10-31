# pipeline.py
import numpy as np
import os
import uuid
from .stt import STT
from .tts import synthesize_text
from .llm import LLM

try:
    from database import db
except Exception:
    try:
        from backend.database import db
    except Exception:
        try:
            from ..database import db
        except Exception:
            db = None


class Pipeline:
    def __init__(self, device=None):
        self.stt = STT(device=device)
        self.llm = LLM()

    def handle_input(self, audio_frames=None, user_text=None, response_mode='audio', user_expression=None):
        # Step 1: Transcribe audio if needed
        if user_text is None:
            if not audio_frames:
                user_text = ''
            else:
                try:
                    audio_data = np.concatenate(audio_frames) if isinstance(audio_frames, list) else np.array([], dtype=np.float32)
                    user_text = self.stt.transcribe(audio_data)
                except Exception:
                    user_text = ''

        # Step 2: Get structured response from LLM with optional user expression context
        llm_response = self.llm.generate(user_text, user_expression=user_expression)
        ai_text = llm_response["ai_text"]
        timeline = llm_response["timeline"]
        text = llm_response["text"]

        # Step 3: Persist user message with expression
        user_row, ai_row = None, None
        try:
            if db:
                user_row = db.insert_message('user', user_text or '', expression=user_expression)
        except Exception:
            pass

        # Step 4: Generate TTS if needed
        cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        audio_id = None

        if response_mode == 'audio':
            try:
                texts = ' '.join([s['text'] for s in ai_text])
                filename = synthesize_text(texts, cache_dir)
                audio_id = os.path.splitext(filename)[0]
            except Exception:
                audio_id = str(uuid.uuid4())
                audio_path = os.path.join(cache_dir, f"{audio_id}.wav")
                with open(audio_path, 'wb') as f:
                    f.write(b'RIFF....WAVEfmt ')

        # Step 5: Save AI response
        try:
            if db:
                ai_row = db.insert_ai_response(text, timeline, audio_id)
        except Exception:
            pass

        # Step 6: Return everything
        return {
            'ai_text': ai_text,
            'timeline': timeline,
            'audio_id': audio_id,
            'user_row': user_row,
            'ai_row': ai_row,
            'user_text': user_text,
            'user_expression': user_expression,
        }
