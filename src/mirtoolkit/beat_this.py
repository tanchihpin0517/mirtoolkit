import sys

import torch

if not sys.version_info < (3, 10):
    from beat_this.inference import File2Beats


@torch.no_grad()
def detect(audio_file, dbn=True, cuda=None, verbose=True):
    if sys.version_info < (3, 10):
        raise ImportError("Python 3.10 or higher is required to use this function.")

    if cuda is None:
        cuda = torch.cuda.is_available()

    file2beats = File2Beats(
        checkpoint_path="final0",
        device="cuda" if cuda else "cpu",
        dbn=dbn,
    )
    beats, downbeats = file2beats(audio_file)

    return beats, downbeats
