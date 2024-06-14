from mirtoolkit import demucs, utils
import tempfile


def test_separate():
    # download input audio from link
    download_link = "https://github.com/facebookresearch/demucs/raw/main/test.mp3"
    audio_file = tempfile.NamedTemporaryFile(suffix=".mp3")

    utils.download(download_link, audio_file)
    demucs.separate(audio_file.name)
