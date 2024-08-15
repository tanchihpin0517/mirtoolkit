import json
import logging

from mirtoolkit import config, sheetsage, utils

TEST_NAME = "sheetsage"
TEST_AUDIO_URL = "https://www.dropbox.com/scl/fi/ex0i7en6tq1fjtuwyctu4/cover.mp3?rlkey=kkptte4s0hl7r25lsaiza2yqi&st=nxkhfctv&dl=0"
TEST_BEAT_URL = "https://www.dropbox.com/scl/fi/zfjeotmbn7yerd7zb43c4/beat_info.json?rlkey=0mn18ta0qgcxx3hikiy8gvyiu&st=g7wdj0mw&dl=0"
TEST_AUDIO = config.CACHE_DIR.joinpath(f"test_input/{TEST_NAME}/input.mp3")
TEST_BEAT = config.CACHE_DIR.joinpath(f"test_input/{TEST_NAME}/beat_info.json")

TEST_AUDIO.parent.mkdir(exist_ok=True, parents=True)


def test_sheetsage():
    logging.basicConfig(level=logging.INFO)
    audio_file, beat_info_file = _get_test_inputs()
    beat_info = json.loads(beat_info_file.read_text())
    sheetsage.infer(
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
    test_sheetsage()
