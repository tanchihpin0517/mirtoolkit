import shutil
import subprocess
import tempfile
from pathlib import Path

import torch
import torchaudio


def download(url, file):
    assert isinstance(url, str)
    assert isinstance(file, (str, Path))
    if isinstance(file, str):
        file = Path(file)

    if shutil.which("wget") is None:
        raise FileNotFoundError("wget not found. Please install wget.")
    # Download the file using wget
    tmp_dir = tempfile.TemporaryDirectory()
    tmp_file = tmp_dir.name + "/" + file.name
    subprocess.run(["wget", "-O", tmp_file, url], check=True)
    shutil.move(tmp_file, file)

    # try:
    #     # Send a GET request to the URL
    #     response = requests.get(url, stream=True)
    #     response.raise_for_status()  # Raise an error for bad status codes

    #     tmp_dir = tempfile.TemporaryDirectory()
    #     tmp_file = tmp_dir.name + "/" + file.name
    #     with open(tmp_file, "wb") as f:
    #         for chunk in response.iter_content(chunk_size=8192):
    #             f.write(chunk)
    #     shutil.move(tmp_file, file)
    # except requests.RequestException as e:
    #     print(f"An error occurred: {e}")


def load_audio(
    path, dtype="float32", return_tensor=False, channels_first=False, mono=False, sr=None
):
    """
    Load an audio file from the given path.
    Args:
        path (str): The path to the audio file.
        dtype (str, optional): The desired data type of the audio waveform. Defaults to "float64".
        return_tensor (bool, optional): Whether to return the audio waveform as a tensor. Defaults to False.
        channels_first (bool, optional): Whether to return the audio waveform with channels as the first dimension. Defaults to False.
    Returns:
        tuple or ndarray: If `return_tensor` is False, returns a tuple containing the audio waveform as a numpy ndarray and the sample rate as an integer. If `return_tensor` is True, returns a tuple containing the audio waveform as a PyTorch tensor and the sample rate as an integer.
    """
    assert dtype in ["float32", "float64"]

    try:
        waveform, sample_rate = torchaudio.load(path, channels_first=channels_first)
        if mono and waveform.shape[0] > 1:
            if channels_first:
                waveform = waveform.mean(0)
            else:
                waveform = waveform.mean(-1)

        if dtype == "float64":
            waveform = waveform.to(dtype=torch.float64)

    except Exception:
        # in case torchaudio fails, try soundfile
        import soundfile as sf

        waveform, sample_rate = sf.read(path, dtype=dtype)
        waveform = torch.from_numpy(waveform)

    if sr is not None:
        # resample the audio to the given sample rate
        waveform = torchaudio.transforms.Resample(sample_rate, sr)(waveform)
        sample_rate = sr

    if not return_tensor:
        waveform = waveform.squeeze().numpy()

    return waveform, sample_rate
