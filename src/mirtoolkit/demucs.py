import demucs.api
import torch

_instance = None


def _get_model():  # singleton
    global _instance
    if _instance is None:
        _instance = demucs.api.Separator()
    return _instance


@torch.no_grad()
def separate(audio_file):
    separator = _get_model()
    origin, separated = separator.separate_audio_file(audio_file)
    return {
        "origin": origin,
        "separated": separated,
        "sr": separator.samplerate,
    }


def save_audio(audio, file, samplerate=None):
    separator = _get_model()
    if samplerate is None:
        samplerate = separator.samplerate
    demucs.api.save_audio(audio, file, samplerate=samplerate)
