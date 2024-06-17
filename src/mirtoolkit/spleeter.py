import torch
from spleeter.audio.adapter import AudioAdapter
from spleeter.separator import Separator


_instance = None


def _get_model(model_card='spleeter:5stems'):  # singleton
    global _instance
    if _instance is None:
        _instance = Separator(model_card)
    return _instance


@torch.no_grad()
def separate(audio_file):
    model = _get_model()
    audio_loader = AudioAdapter.default()

    waveform, _ = audio_loader.load(audio_file, sample_rate=44100)
    r = model.separate(waveform)

    return r
