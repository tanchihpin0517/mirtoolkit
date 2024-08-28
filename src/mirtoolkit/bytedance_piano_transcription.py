"""
ByteDance Piano Transcription
- reference: https://github.com/qiuqiangkong/piano_transcription_inference
"""

from pathlib import Path

import numpy as np
import torch
import torchaudio
from piano_transcription_inference import (
    PianoTranscription,
    load_audio,
    load_audio_stream,
    sample_rate,
)


class ByteDancePianoTranscription:
    def __init__(self, cuda=None):
        if cuda is None:
            cuda = torch.cuda.is_available()

        self.model = PianoTranscription(
            device="cuda" if cuda else "cpu",  # device: 'cuda' | 'cpu'
            checkpoint_path=None,
        )

    @torch.no_grad()
    def __call__(self, file_or_array, output_midi_file=None, sr=None, stream=False):
        """
        Function for transcribing piano notes from an audio file or audio array.

        Args:
            file_or_array (str or Path or numpy.ndarray): Path to the audio file or audio array.
            output_midi_file (str, optional): Path to save the transcribed MIDI file. Defaults to None.

        Returns:
            dict: A dictionary containing the transcribed piano notes.
        """
        if isinstance(file_or_array, (str, Path)):
            audio_path = file_or_array
            if stream:
                # Load audio
                audio_stream = load_audio_stream(audio_path, sr=sample_rate, mono=True)
                # Transcribe and write out to MIDI file
                transcribed_dict = self.model.transcribe_stream(audio_stream, output_midi_file)
            else:
                # Load audio
                (audio_array, _) = load_audio(audio_path, sr=sample_rate, mono=True)
                # Transcribe and write out to MIDI file
                transcribed_dict = self.model.transcribe(audio_array, output_midi_file)

        else:
            assert sr is not None, "Sample rate must be provided if audio array is given."
            audio_array = file_or_array
            if isinstance(audio_array, np.ndarray):
                audio_array = torch.from_numpy(audio_array)
            audio_array = torchaudio.transforms.Resample(sr, sample_rate)(audio_array)
            audio_array = audio_array.numpy()
            transcribed_dict = self.model.transcribe(audio_array, output_midi_file)

        return transcribed_dict
