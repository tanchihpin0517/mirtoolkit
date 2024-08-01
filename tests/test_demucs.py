from mirtoolkit import demucs, utils
import tempfile


def test_separate():
    download_link = "https://github.com/facebookresearch/demucs/raw/main/test.mp3"
    audio_file = tempfile.NamedTemporaryFile(suffix=".mp3")

    utils.download(download_link, audio_file.name)
    out = demucs.separate(audio_file.name)
    assert len(out["separated"]) == 4
    for name in out["separated"]:
        stem = out["separated"][name]
        assert len(stem) == 2


if __name__ == "__main__":
    test_separate()
