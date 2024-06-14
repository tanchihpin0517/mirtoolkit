import torch
from piano_transcription_inference import PianoTranscription, sample_rate, load_audio


_instance = None


def _get_model(device):  # singleton
    global _instance
    if _instance is None:
        _instance = PianoTranscription(device=device, checkpoint_path=None)
    return _instance


@torch.no_grad()
def transcribe(audio_file, output_midi_file=None):
    # Load audio
    (audio, _) = load_audio(audio_file, sr=sample_rate, mono=True)

    # Transcriptor
    device = 'cuda' if torch.cuda.is_available else 'cpu'
    transcriptor = _get_model(device)  # device: 'cuda' | 'cpu'

    # Transcribe and write out to MIDI file
    if output_midi_file is None:
        output_midi_file = "/dev/null"
    transcribed_dict = transcriptor.transcribe(audio, output_midi_file)

    return transcribed_dict
