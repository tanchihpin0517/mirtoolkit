import json
import logging
import sys

import pytest

from mirtoolkit import config, utils

if sys.version_info < (3, 12):
    from mirtoolkit.sheetsage import SheetSage

TEST_NAME = "sheetsage"
TEST_AUDIO_URL = "https://www.dropbox.com/scl/fi/zj68yghtn0cwtwnqj7vrx/pop.00000.wav?rlkey=bejuh89wehbc8psl9ujmqa73u&st=im68h2jp&dl=0"
TEST_BEAT_URL = "https://www.dropbox.com/scl/fi/zfjeotmbn7yerd7zb43c4/beat_info.json?rlkey=0mn18ta0qgcxx3hikiy8gvyiu&st=f70p421a&dl=0"
TEST_AUDIO = config.CACHE_DIR.joinpath(f"test_input/{TEST_NAME}/input.mp3")
TEST_BEAT = config.CACHE_DIR.joinpath(f"test_input/{TEST_NAME}/beat_info.json")

TEST_AUDIO.parent.mkdir(exist_ok=True, parents=True)


@pytest.mark.skipif(sys.version_info >= (3, 12), reason="Skip due to compatibility issues")
def test_sheetsage():
    logging.basicConfig(level=logging.INFO)
    audio_file, beat_info_file = _get_test_inputs()
    beat_info = json.loads(beat_info_file.read_text())
    sheetsage = SheetSage()
    sheetsage(
        audio_path=audio_file,
        use_jukebox=True,
        beat_information=beat_info,
        dynamic_chunking=True,
    )


def _get_test_inputs():
    if not TEST_AUDIO.exists():
        utils.download(TEST_AUDIO_URL, TEST_AUDIO)
    if not TEST_BEAT.exists():
        utils.download(TEST_BEAT_URL, TEST_BEAT)
    return TEST_AUDIO, TEST_BEAT


if __name__ == "__main__":
    test_functions = [obj for name, obj in locals().items() if name.startswith("test_")]
    for test_func in test_functions:
        test_func()
