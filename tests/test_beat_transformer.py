from mirtoolkit import beat_transformer
import numpy as np


def test_detect_beat():
    test_audio = beat_transformer.REPO_DIR.joinpath(
        "test_audio/陈佳 - 愛される花 愛されぬ花 (cover 中島みゆき).mp3")
    beat, downbeat = beat_transformer.detect_beat(test_audio)
    assert isinstance(beat, np.ndarray) and isinstance(downbeat, np.ndarray)
