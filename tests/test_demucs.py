from mirtoolkit import config, utils
from mirtoolkit.demucs import Demucs

TEST_NAME = "demucs"
TEST_AUDIO_URL = "https://www.dropbox.com/scl/fi/zj68yghtn0cwtwnqj7vrx/pop.00000.wav?rlkey=bejuh89wehbc8psl9ujmqa73u&st=im68h2jp&dl=0"
TEST_AUDIO = config.CACHE_DIR.joinpath(f"test_input/{TEST_NAME}/test.mp3")
TEST_OUTPUT_DIR = config.CACHE_DIR.joinpath(f"test_output/{TEST_NAME}")

TEST_AUDIO.parent.mkdir(exist_ok=True, parents=True)
TEST_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


def test_separate():
    if not TEST_AUDIO.exists():
        utils.download(TEST_AUDIO_URL, TEST_AUDIO)

    demucs = Demucs()
    out = demucs(TEST_AUDIO)  # origin, separated, sr
    assert len(out["separated"]) == 4
    for name in out["separated"]:
        stem = out["separated"][name]
        assert len(stem) == 2
        demucs.save_audio(stem, TEST_OUTPUT_DIR.joinpath(f"{name}.wav"), out["sr"])


if __name__ == "__main__":
    test_functions = [obj for name, obj in locals().items() if name.startswith("test_")]
    for test_func in test_functions:
        test_func()
