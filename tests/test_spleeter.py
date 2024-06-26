from mirtoolkit import spleeter, utils
import tempfile


def test_separate():
    download_link = "https://github.com/deezer/spleeter/raw/master/audio_example.mp3"
    audio_file = tempfile.NamedTemporaryFile(suffix=".mp3")

    utils.download(download_link, audio_file.name)
    out = spleeter.separate(audio_file.name)
    stems = out["separated"]

    assert len(stems) == 5
    for name in stems:
        stem = stems[name]
        assert len(stem) > 2


if __name__ == "__main__":
    test_separate()
