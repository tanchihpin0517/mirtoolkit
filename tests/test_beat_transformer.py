import tempfile
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

from mirtoolkit import beat_transformer
from mirtoolkit.utils import download

TEST_AUDIO_URL = "https://github.com/tanchihpin0517/mirtoolkit_beat_transformer/raw/main/test_audio/%E9%99%88%E4%BD%B3%20-%20%E6%84%9B%E3%81%95%E3%82%8C%E3%82%8B%E8%8A%B1%20%E6%84%9B%E3%81%95%E3%82%8C%E3%81%AC%E8%8A%B1%20(cover%20%E4%B8%AD%E5%B3%B6%E3%81%BF%E3%82%86%E3%81%8D).mp3"


def _get_test_audio():
    test_audio = Path.home() / ".mirtoolkit/beat_transformer/test_audio.mp3"
    if not test_audio.exists():
        download(TEST_AUDIO_URL, test_audio.name)
    return test_audio


def test_detect_beat():
    test_audio = _get_test_audio()
    beat, downbeat = beat_transformer.detect_beat(test_audio)
    assert isinstance(beat, np.ndarray) and isinstance(downbeat, np.ndarray)


def test_stft():
    test_audio = tempfile.NamedTemporaryFile(suffix=".mp3")
    download(TEST_AUDIO_URL, test_audio.name)
    y, _ = librosa.load(test_audio.name)
    y = y[:, None]
    spectrogram = beat_transformer.stft(y)
    assert isinstance(spectrogram, np.ndarray)
    assert len(spectrogram.shape) == 3


def _write_beat_demo(audio_file, beat_info, output_file):
    audio, sr = librosa.load(audio_file)
    beat, downbeat = beat_info
    beats_click = librosa.clicks(
        times=beat, sr=sr, click_freq=1000.0, click_duration=0.1, click=None, length=len(audio)
    )
    downbeats_click = librosa.clicks(
        times=downbeat, sr=sr, click_freq=1500.0, click_duration=0.15, click=None, length=len(audio)
    )

    out = 0.6 * audio + 0.25 * beats_click
    sf.write(output_file, out, sr)


if __name__ == "__main__":
    test_audio = _get_test_audio()
    beat, downbeat = beat_transformer.detect_beat(test_audio, window_size=500)
    _write_beat_demo(test_audio, (beat, downbeat), "./tests_output/beat_demo.wav")
