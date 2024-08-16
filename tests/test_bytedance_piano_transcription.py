from mirtoolkit import bytedance_piano_transcription, config, utils

TEST_NAME = "bytedance_piano_transcription"
TEST_AUDIO_URL = "https://www.dropbox.com/scl/fi/hc38zoizq5515cczxv9l4/cut_liszt.mp3?rlkey=mzoknr0ma6sa0nen5zlseruch&st=o1vggmes&dl=0"
TEST_AUDIO = config.CACHE_DIR.joinpath(f"test_input/{TEST_NAME}/cut_liszt.mp3")
TEST_OUTPUT_MIDI = config.CACHE_DIR.joinpath(f"test_output/{TEST_NAME}/output.mid")

TEST_AUDIO.parent.mkdir(exist_ok=True, parents=True)
TEST_OUTPUT_MIDI.parent.mkdir(exist_ok=True, parents=True)


def test_transcribe():
    if not TEST_AUDIO.exists():
        utils.download(TEST_AUDIO_URL, TEST_AUDIO)
    bytedance_piano_transcription.transcribe(TEST_AUDIO, TEST_OUTPUT_MIDI)


if __name__ == "__main__":
    test_transcribe()
