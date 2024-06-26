from mirtoolkit import beat_transformer
from mirtoolkit.utils import download
import numpy as np
import librosa
import tempfile


TEST_AUDIO_URL = "https://github.com/tanchihpin0517/mirtoolkit_beat_transformer/raw/main/test_audio/%E9%99%88%E4%BD%B3%20-%20%E6%84%9B%E3%81%95%E3%82%8C%E3%82%8B%E8%8A%B1%20%E6%84%9B%E3%81%95%E3%82%8C%E3%81%AC%E8%8A%B1%20(cover%20%E4%B8%AD%E5%B3%B6%E3%81%BF%E3%82%86%E3%81%8D).mp3"


def test_detect_beat():
    test_audio = tempfile.NamedTemporaryFile(suffix=".mp3")
    download(TEST_AUDIO_URL, test_audio.name)
    beat, downbeat = beat_transformer.detect_beat(test_audio.name)
    assert isinstance(beat, np.ndarray) and isinstance(downbeat, np.ndarray)


def test_stft():
    test_audio = tempfile.NamedTemporaryFile(suffix=".mp3")
    download(TEST_AUDIO_URL, test_audio.name)
    y, _ = librosa.load(test_audio.name)
    y = y[:, None]
    spectrogram = beat_transformer.stft(y)
    assert isinstance(spectrogram, np.ndarray)
    assert len(spectrogram.shape) == 3


if __name__ == "__main__":
    test_detect_beat()
    test_stft()
