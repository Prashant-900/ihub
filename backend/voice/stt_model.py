import torch

# Minimal model loader that can be extended if more models are added later.
# Exposes load_stt_model() which returns (model, decoder, utils)

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

