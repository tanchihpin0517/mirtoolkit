import json
import sys

import librosa
import numpy as np
import pytest
import soundfile as sf

from mirtoolkit import beat_this, config
from mirtoolkit.utils import download

TEST_NAME = "beat_this"
TEST_AUDIO_URL = "https://www.dropbox.com/scl/fi/zj68yghtn0cwtwnqj7vrx/pop.00000.wav?rlkey=bejuh89wehbc8psl9ujmqa73u&st=im68h2jp&dl=0"
TEST_AUDIO = config.CACHE_DIR.joinpath(f"test_input/{TEST_NAME}/input.mp3")
TEST_OUTPUT_AUDIO = config.CACHE_DIR.joinpath(f"test_output/{TEST_NAME}/output.wav")
TEST_OUTPUT_BEAT = config.CACHE_DIR.joinpath(f"test_output/{TEST_NAME}/beat_info.json")

TEST_AUDIO.parent.mkdir(exist_ok=True, parents=True)
TEST_OUTPUT_AUDIO.parent.mkdir(exist_ok=True, parents=True)


@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires python3.10 or higher")
def test_detect_beat():
    test_audio = _get_test_audio()
    beats, downbeats = beat_this.detect(test_audio)
    assert isinstance(beats, np.ndarray) and isinstance(downbeats, np.ndarray)
    beat_info = {"beats": beats.tolist(), "downbeats": downbeats.tolist()}
    TEST_OUTPUT_BEAT.parent.mkdir(exist_ok=True, parents=True)
    TEST_OUTPUT_BEAT.write_text(json.dumps(beat_info, indent=4))
    _write_beat_demo(test_audio, (beats, downbeats), TEST_OUTPUT_AUDIO)


def _get_test_audio():
    TEST_AUDIO.parent.mkdir(exist_ok=True, parents=True)
    if not TEST_AUDIO.exists():
        download(TEST_AUDIO_URL, TEST_AUDIO)
    return TEST_AUDIO


def _write_beat_demo(audio_file, beat_info, output_file):
    audio, sr = librosa.load(audio_file)
    beats, downbeats = beat_info
    beats_click = librosa.clicks(
        times=beats, sr=sr, click_freq=1000.0, click_duration=0.1, click=None, length=len(audio)
    )
    downbeats_click = librosa.clicks(
        times=downbeats,
        sr=sr,
        click_freq=1500.0,
        click_duration=0.15,
        click=None,
        length=len(audio),
    )

    out = 0.6 * audio + 0.25 * beats_click + 0.25 * downbeats_click
    sf.write(output_file, out, sr)


if __name__ == "__main__":
    test_detect_beat()
