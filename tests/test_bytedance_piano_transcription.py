from mirtoolkit import config, utils
from mirtoolkit.bytedance_piano_transcription import ByteDancePianoTranscription

TEST_NAME = "bytedance_piano_transcription"
TEST_AUDIO_URL = "https://www.dropbox.com/scl/fi/hc38zoizq5515cczxv9l4/cut_liszt.mp3?rlkey=mzoknr0ma6sa0nen5zlseruch&st=o1vggmes&dl=0"
TEST_AUDIO = config.CACHE_DIR.joinpath(f"test_input/{TEST_NAME}/cut_liszt.mp3")
TEST_OUTPUT_MIDI = config.CACHE_DIR.joinpath(f"test_output/{TEST_NAME}/output.mid")

TEST_AUDIO.parent.mkdir(exist_ok=True, parents=True)
TEST_OUTPUT_MIDI.parent.mkdir(exist_ok=True, parents=True)


def test_file():
    if not TEST_AUDIO.exists():
        utils.download(TEST_AUDIO_URL, TEST_AUDIO)
    transcriptor = ByteDancePianoTranscription()
    _ = transcriptor(TEST_AUDIO, TEST_OUTPUT_MIDI)


def test_file_stream():
    if not TEST_AUDIO.exists():
        utils.download(TEST_AUDIO_URL, TEST_AUDIO)
    transcriptor = ByteDancePianoTranscription()
    _ = transcriptor(TEST_AUDIO, TEST_OUTPUT_MIDI, stream=True)


def test_array():
    audio, sr = utils.load_audio(TEST_AUDIO)
    transcriptor = ByteDancePianoTranscription()
    _ = transcriptor(audio, TEST_OUTPUT_MIDI, sr=sr)


if __name__ == "__main__":
    test_functions = [obj for name, obj in locals().items() if name.startswith("test_")]
    for test_func in test_functions:
        test_func()
