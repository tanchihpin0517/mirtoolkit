import torch
import demucs.api


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
