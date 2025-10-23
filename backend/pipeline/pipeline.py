import numpy as np
from .stt import STT

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
