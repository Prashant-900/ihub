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
        Processes either audio or text input, persists messages, and returns AI response data.
        """
        # Step 1: Transcribe if user_text not provided
        if user_text is None:
            if not audio_frames:
                user_text = ''
            else:
                audio_data = np.concatenate(audio_frames) if isinstance(audio_frames, list) else np.array([], dtype=np.float32)
                try:
                    user_text = self.stt.transcribe(audio_data)
                except Exception:
                    user_text = ''

        # Step 2: Generate timeline (from animation function directly)
        timeline = get_animation_timeline()["timeline"]

        # Step 3: Generate AI text box data
        ai_text = get_text_box_data(user_text)  # You may replace user_text with your actual AI response later

        # Step 4: Persist user message
        user_row, ai_row = None, None
        try:
            if db:
                user_row = db.insert_message('user', user_text or '', None)
        except Exception:
            pass

        # Step 5: Synthesize TTS audio only if needed
        cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        audio_id = None

        if response_mode == 'audio':
            try:
                sentences = ' '.join([s['sentence'] for s in ai_text])
                filename = synthesize_text(sentences, cache_dir)
                audio_id = os.path.splitext(filename)[0]
            except Exception:
                # fallback dummy audio only in audio mode
                try:
                    audio_id = str(uuid.uuid4())
                    audio_path = os.path.join(cache_dir, f"{audio_id}.wav")
                    with open(audio_path, 'wb') as f:
                        f.write(b'RIFF....WAVEfmt ')
                except Exception:
                    pass

        # Step 6: Save AI response in DB
        try:
            if db:
                text = ' '.join(s['sentence'] for s in ai_text)
                ai_row = db.insert_ai_response(text, timeline, audio_id)
        except Exception:
            pass

        # Step 7: Return final structured data
        return {
            'ai_text': ai_text,
            'timeline': timeline,
            'audio_id': audio_id,
            'user_row': user_row,
            'ai_row': ai_row,
            'user_text': user_text,
        }
