import torch
import numpy as np
from typing import Tuple, Optional

"""
Speech-to-Text recognition module using Silero STT model.

Provides efficient, on-device speech recognition using the Silero VAD model
with automatic model caching for performance optimization.
"""

_cached = {}


def load_stt_model(device: Optional[torch.device] = None) -> Tuple:
    """Load and cache Silero STT model.
    
    Loads the Silero STT model from PyTorch Hub with caching to avoid
    redundant downloads and initialization.
    
    Args:
        device: Torch device to load model on. Defaults to CPU
        
    Returns:
        Tuple of (model, decoder, utils) from Silero STT
        
    Raises:
        RuntimeError: If model loading fails
    """
    global _cached
    key = 'silero_stt'
    if key in _cached:
        return _cached[key]

    if device is None:
        device = torch.device('cpu')
    elif isinstance(device, str):
        device = torch.device(device)

    try:
        # Load from official upstream PyTorch Hub
        model, decoder, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-models',
            model='silero_stt',
            language='en',
            device=device
        )
        _cached[key] = (model, decoder, utils)
        return _cached[key]
    except Exception as e:
        raise RuntimeError(f'Failed to load Silero STT model: {e}')


class STT:
    """Speech-to-Text transcription service using Silero model."""

    def __init__(self, device: Optional[torch.device] = None):
        """Initialize STT service.
        
        Args:
            device: Torch device to use. Defaults to CPU
            
        Raises:
            RuntimeError: If model loading fails
        """
        self.device = device or torch.device("cpu")
        try:
            self.model, self.decoder, self.utils = load_stt_model(device=self.device)
        except Exception as e:
            raise RuntimeError(f'STT initialization failed: {e}')

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio to text.
        
        Args:
            audio: 1D float32 numpy array with audio samples normalized to [-1, 1]
            
        Returns:
            Transcribed text string, empty string if transcription fails
        """
        if audio.size == 0:
            return ""

        try:
            x = torch.from_numpy(audio).float().view(1, -1).to(self.device)
            with torch.no_grad():
                z = self.model(x)

            if self.decoder:
                return self.decoder(z[0])
            return ""
        except Exception:
            return ""
