import torch
from beat_this.inference import File2Beats


@torch.no_grad()
def detect(audio_file, dbn=True, cuda=None, verbose=True):
    if cuda is None:
        cuda = torch.cuda.is_available()

    file2beats = File2Beats(
        checkpoint_path="final0",
        device="cuda" if cuda else "cpu",
        dbn=dbn,
    )
    beats, downbeats = file2beats(audio_file)

    return beats, downbeats
