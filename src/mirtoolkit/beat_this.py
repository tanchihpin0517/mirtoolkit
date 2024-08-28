"""
CPJKU's beat_this
- reference: https://github.com/CPJKU/beat_this
"""

import sys
from pathlib import Path

import torch

from .utils import load_audio

if not sys.version_info < (3, 10):
    from beat_this.inference import Audio2Beats


class BeatThis:
    def __init__(self, cuda=None, dbn=True):
        if cuda is None:
            cuda = torch.cuda.is_available()

        self.audio2beats = Audio2Beats(
            device="cuda" if cuda else "cpu",
            dbn=dbn,
        )

    @torch.no_grad()
    def __call__(self, file_or_array, sr=None):
        """
        Function for extracting beat and downbeat positions (in seconds) from a file or a data array.

        Args:
            file_or_array (str or Path or ndarray): Path to the audio file or numpy array containing the audio data.
            sr (int, optional): Sample rate of the audio file. Required if `file_or_array` is a numpy array. Defaults to None.
            dbn (bool): Whether to use the madmom DBN for post-processing. Default is True.
            verbose (bool): Whether to print progress information. Default is True.

        Returns:
            beats (ndarray): Array of beat positions in seconds.
            downbeats (ndarray): Array of downbeat positions in seconds.
        """
        if sys.version_info < (3, 10):
            raise ImportError("Python 3.10 or higher is required to use this function.")

        if isinstance(file_or_array, (str, Path)):
            audio, sr = load_audio(file_or_array, dtype="float64")
        else:
            audio = file_or_array

        beats, downbeats = self.audio2beats(audio, sr)

        return beats, downbeats
