import torch
import numpy as np

_cached = {}

def load_stt_model(device=None):
    """Load and cache Silero STT model.

    Returns tuple (model, decoder, utils). Caller may pass a torch.device or
    a string (e.g. 'cpu').
    """
    global _cached
    key = 'silero_stt'
    if key in _cached:
        return _cached[key]

    if device is None:
        device = torch.device('cpu')
    elif isinstance(device, str):
        device = torch.device(device)

    # repo name follows the upstream hub repo
    model, decoder, utils = torch.hub.load(
        repo_or_dir='snakers4/silero-models',
        model='silero_stt',
        language='en',
        device=device
    )

    _cached[key] = (model, decoder, utils)
    return _cached[key]


class STT:
    def __init__(self, device=None):
        self.device = device or torch.device("cpu")
        self.model, self.decoder, self.utils = load_stt_model(device=self.device)

    def transcribe(self, audio: np.ndarray) -> str:
        """
        audio: 1D float32 numpy array normalized [-1,1]
        Returns the transcribed text
        """
        if audio.size == 0:
            return ""

        x = torch.from_numpy(audio).float().view(1, -1).to(self.device)
        with torch.no_grad():
            z = self.model(x)

        if self.decoder:
            return self.decoder(z[0])
        return ""
