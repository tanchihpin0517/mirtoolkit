"""
Demus: Demixing model from Meta
- reference: https://github.com/facebookresearch/demucs/tree/main
"""

from pathlib import Path

import demucs.api
import torch


class Demucs:
    def __init__(self, cuda=None):
        if cuda is None:
            cuda = torch.cuda.is_available()

        self.separator = demucs.api.Separator(
            device="cuda" if cuda else "cpu",
        )

    @torch.no_grad()
    def __call__(self, file_or_array):
        if not isinstance(file_or_array, (str, Path)):
            raise NotImplementedError("Array input is not supported yet.")
        else:
            audio_path = file_or_array
        origin, separated = self.separator.separate_audio_file(audio_path)
        return {
            "origin": origin,
            "separated": separated,
            "sr": self.separator.samplerate,
        }

    def save_audio(self, audio, file, samplerate=None):
        if samplerate is None:
            samplerate = self.separator.samplerate
        demucs.api.save_audio(audio, file, samplerate=samplerate)
