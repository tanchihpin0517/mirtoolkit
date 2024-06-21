from mirtoolkit import bytedance_piano_transcription, utils
import tempfile


def test_transcribe():
    # download input audio from link
    download_link = (
        "https://raw.githubusercontent.com/"
        "qiuqiangkong/piano_transcription_inference/master/resources/cut_liszt.mp3"
    )
    audio_file = tempfile.NamedTemporaryFile(suffix=".mp3")
    output_midi_file = tempfile.NamedTemporaryFile(suffix=".mid")

    utils.download(download_link, audio_file.name)
    bytedance_piano_transcription.transcribe(audio_file.name, output_midi_file.name)
