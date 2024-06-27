import logging
import numpy as np
from scipy.signal.windows import hann
import librosa
import torch
from librosa.core import stft as librosa_stft
from librosa.core import istft as librosa_istft
from spleeter.audio.adapter import AudioAdapter
from spleeter.separator import Separator
from madmom.features.beats import DBNBeatTrackingProcessor
from madmom.features.downbeats import DBNDownBeatTrackingProcessor
from typing import Optional
from beat_transformer import DemixedDilatedTransformerModel

from .config import PROJ_DIR
from .utils import download

REPO_DIR = PROJ_DIR.joinpath("beat_transformer")
REPO_URL = "https://github.com/tanchihpin0517/mirtoolkit_beat_transformer/raw/main"
FOLD = 4
PARAM_PATH = {
    0: REPO_DIR / "checkpoint/fold_0_trf_param.pt",
    1: REPO_DIR / "checkpoint/fold_1_trf_param.pt",
    2: REPO_DIR / "checkpoint/fold_2_trf_param.pt",
    3: REPO_DIR / "checkpoint/fold_3_trf_param.pt",
    4: REPO_DIR / "checkpoint/fold_4_trf_param.pt",
    5: REPO_DIR / "checkpoint/fold_5_trf_param.pt",
    6: REPO_DIR / "checkpoint/fold_6_trf_param.pt",
    7: REPO_DIR / "checkpoint/fold_7_trf_param.pt"
}
SPLEETER_CONFIG = {
    "train_csv": "path/to/train.csv",
    "validation_csv": "path/to/test.csv",
    "model_dir": "5stems",
    "mix_name": "mix",
    "instrument_list": ["vocals", "piano", "drums", "bass", "other"],
    "sample_rate": 44100,
    "frame_length": 4096,
    "frame_step": 1024,
    "T": 512,
    "F": 1024,
    "n_channels": 2,
    "separation_exponent": 2,
    "mask_extension": "zeros",
    "learning_rate": 1e-4,
    "batch_size": 4,
    "training_cache": "training_cache",
    "validation_cache": "validation_cache",
    "train_max_steps": 2500000,
    "throttle_secs": 600,
    "random_seed": 8,
    "save_checkpoints_steps": 300,
    "save_summary_steps": 5,
    "model": {
        "type": "unet.softmax_unet",
        "params": {
            "conv_activation": "ELU",
            "deconv_activation": "ELU"
        }
    }
}


logging.basicConfig()
logger = logging.getLogger(__name__)
_instance_separator = None
_instance_models = None


def _download_checkpoint():
    path = PARAM_PATH[FOLD]
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    logger.warn(f"Downloading checkpoint for fold {FOLD}...")
    url = f"{REPO_URL}/checkpoint/fold_{FOLD}_trf_param.pt"
    download(url, path)


_download_checkpoint()


def _get_separator():
    global _instance_separator
    if _instance_separator is None:
        _instance_separator = Separator('spleeter:5stems')
    return _instance_separator


def _get_models():
    global _instance_models
    if _instance_models is None:
        # Initialize Beat Transformer to estimate (down-)beat activation from demixed input
        model = DemixedDilatedTransformerModel(
            attn_len=5, instr=5, ntoken=2,
            dmodel=256, nhead=8, d_hid=1024,
            nlayers=9, norm_first=True
        )
        model.load_state_dict(
            torch.load(PARAM_PATH[FOLD], map_location=torch.device('cpu'))['state_dict'])
        model.eval()

        # Initialize DBN Beat Tracker to locate beats from beat activation
        beat_tracker = DBNBeatTrackingProcessor(
            min_bpm=55.0, max_bpm=215.0, fps=44100 / 1024,
            transition_lambda=100, observation_lambda=6,
            num_tempi=None, threshold=0.2,
        )

        # Initialize DBN Downbeat Tracker to locate downbeats from downbeat activation
        downbeat_tracker = DBNDownBeatTrackingProcessor(
            beats_per_bar=[3, 4],
            min_bpm=55.0, max_bpm=215.0, fps=44100 / 1024,
            transition_lambda=100, observation_lambda=6,
            num_tempi=None, threshold=0.2,
        )

        _instance_models = (model, beat_tracker, downbeat_tracker)
    return _instance_models


def stft(
    data: np.ndarray, inverse: bool = False, length: Optional[int] = None
) -> np.ndarray:
    """
    Single entrypoint for both stft and istft. This computes stft and
    istft with librosa on stereo data. The two channels are processed
    separately and are concatenated together in the result. The
    expected input formats are: (n_samples, 2) for stft and (T, F, 2)
    for istft.

    Parameters:
        data (numpy.array):
            Array with either the waveform or the complex spectrogram
            depending on the parameter inverse
        inverse (bool):
            (Optional) Should a stft or an istft be computed.
        length (Optional[int]):

    Returns:
        numpy.ndarray:
            Stereo data as numpy array for the transform. The channels
            are stored in the last dimension.
    """
    assert not (inverse and length is None)
    data = np.asfortranarray(data)
    N = SPLEETER_CONFIG["frame_length"]
    H = SPLEETER_CONFIG["frame_step"]
    win = hann(N, sym=False)
    fstft = librosa_istft if inverse else librosa_stft
    win_len_arg = {"win_length": None, "length": None} if inverse else {"n_fft": N}
    n_channels = data.shape[-1]
    out = []
    for c in range(n_channels):
        d = (
            np.concatenate((np.zeros((N,)), data[:, c], np.zeros((N,))))
            if not inverse
            else data[:, :, c].T
        )
        s = fstft(d, hop_length=H, window=win, center=False, **win_len_arg)
        if inverse:
            s = s[N: N + length]
        s = np.expand_dims(s.T, 2 - inverse)
        out.append(s)
    if len(out) == 1:
        return out[0]
    return np.concatenate(out, axis=2 - inverse)


@torch.no_grad()
def detect_beat(audio_file, window_size=8000):
    # Initialize Spleeter for pre-processing (demixing)
    separator = _get_separator()
    mel_f = librosa.filters.mel(sr=44100, n_fft=4096, n_mels=128, fmin=30, fmax=11000).T
    audio_loader = AudioAdapter.default()

    model, beat_tracker, downbeat_tracker = _get_models()
    if torch.cuda.is_available():
        model.cuda()

    waveform, _ = audio_loader.load(audio_file, sample_rate=44100)
    x = separator.separate(waveform)
    x = np.stack([np.dot(np.abs(np.mean(stft(x[key]), axis=-1))**2, mel_f) for key in x])
    x = np.transpose(x, (0, 2, 1))
    x = np.stack([librosa.power_to_db(x[i], ref=np.max) for i in range(len(x))])
    x = np.transpose(x, (0, 2, 1))
    del waveform

    # step with 8000 (paper's training setting)
    num_frames = x.shape[1]
    activation = []
    for i in range(0, num_frames, window_size):
        start, end = i, min(i + window_size, num_frames)
        model_input = torch.from_numpy(x[:, start:end, :]).unsqueeze(0).float().cuda()
        activation_frame, _ = model(model_input)
        activation.append(activation_frame.detach().cpu())
    activation = torch.cat(activation, dim=1)

    beat_activation = torch.sigmoid(activation[0, :, 0]).detach().cpu().numpy()
    downbeat_activation = torch.sigmoid(activation[0, :, 1]).detach().cpu().numpy()
    dbn_beat_pred = beat_tracker(beat_activation)

    combined_act = np.concatenate((
        np.maximum(beat_activation - downbeat_activation,
                   np.zeros(beat_activation.shape)
                   )[:, np.newaxis],
        downbeat_activation[:, np.newaxis]
    ), axis=-1)   # (T, 2)
    dbn_downbeat_pred = downbeat_tracker(combined_act)
    dbn_downbeat_pred = dbn_downbeat_pred[dbn_downbeat_pred[:, 1] == 1][:, 0]

    return dbn_beat_pred, dbn_downbeat_pred
