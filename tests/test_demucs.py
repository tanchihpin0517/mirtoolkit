from mirtoolkit import config, demucs, utils

TEST_NAME = "demucs"
TEST_AUDIO_URL = "https://github.com/facebookresearch/demucs/raw/main/test.mp3"
TEST_AUDIO = config.CACHE_DIR.joinpath(f"test_input/{TEST_NAME}/test.mp3")
TEST_OUTPUT_DIR = config.CACHE_DIR.joinpath(f"test_output/{TEST_NAME}")

TEST_AUDIO.parent.mkdir(exist_ok=True, parents=True)
TEST_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


def test_separate():
    if not TEST_AUDIO.exists():
        utils.download(TEST_AUDIO_URL, TEST_AUDIO)

    out = demucs.separate(TEST_AUDIO)  # origin, separated, sr
    assert len(out["separated"]) == 4
    for name in out["separated"]:
        stem = out["separated"][name]
        assert len(stem) == 2
        demucs.save_audio(stem, TEST_OUTPUT_DIR.joinpath(f"{name}.wav"), out["sr"])


if __name__ == "__main__":
    test_separate()
