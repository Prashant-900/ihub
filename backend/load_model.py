import torch

model, decoder, utils = torch.hub.load(
    repo_or_dir='snakers4/silero-models',
    model='silero_stt',
    language='en', # or 'ru', 'de', etc.
    device='cpu'   # or 'cuda'
)
