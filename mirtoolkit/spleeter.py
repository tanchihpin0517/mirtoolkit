import torch
from spleeter.audio.adapter import AudioAdapter
from spleeter.separator import Separator


_instance = None


def _get_model(model_card="spleeter:5stems"):  # singleton
    global _instance
    if _instance is None:
        print("Loading model...")
        _instance = Separator(model_card)
    return _instance


@torch.no_grad()
def separate(audio_file, sample_rate=44100):
    model = _get_model()
    audio_loader = AudioAdapter.default()

    origin, _ = audio_loader.load(audio_file, sample_rate=sample_rate)
    separated = model.separate(origin)

    return {
        "origin": origin,
        "separated": separated,
        "sr": sample_rate,
    }
