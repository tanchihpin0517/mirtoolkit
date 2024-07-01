import torch
from piano_transcription_inference import PianoTranscription, sample_rate, load_audio_stream


_instance = None


def _get_model(device):  # singleton
    global _instance
    if _instance is None:
        _instance = PianoTranscription(device=device, checkpoint_path=None)
    return _instance


@torch.no_grad()
def transcribe(audio_file, output_midi_file=None, device=None):
    # Load audio
    audio_stream = load_audio_stream(audio_file, sr=sample_rate, mono=True)

    # Transcriptor
    if device is None:
        device = 'cuda' if torch.cuda.is_available else 'cpu'
    transcriptor = _get_model(device)  # device: 'cuda' | 'cpu'

    # Transcribe and write out to MIDI file
    transcribed_dict = transcriptor.transcribe_stream(audio_stream, output_midi_file)

    return transcribed_dict
