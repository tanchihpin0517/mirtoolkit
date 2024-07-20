import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Union

import sheetsage
from tqdm import tqdm as tqdm_fn


def infer(
    audio_path: Union[str, Path] = None,
    audio_url: str = None,
    segment_start_hint=None,
    segment_end_hint=None,
    use_jukebox=True,
    measures_per_chunk=8,
    dynamic_chunking=True,
    segment_hints_are_downbeats=False,
    beat_information=None,
    beats_per_measure_hint=None,
    beats_per_minute_hint=None,
    detect_melody=True,
    detect_harmony=True,
    melody_threshold=None,
    harmony_threshold=None,
    beat_detection_padding=15.0,
    avoid_chunking_if_possible=True,
    legacy_behavior=False,
    status_change_callback=lambda s: logging.info(s.name),
    return_intermediaries=False,
    tqdm=tqdm_fn,
    return_dict=True,
):
    # assert audio_path or audio_url should be provided but not both
    assert (audio_path and not audio_url) or (
        audio_url and not audio_path
    ), f"One of audio_path or audio_url should be provided but not both: {audio_path}, {audio_url}"

    if audio_path:  # if audio_path is provided
        audio_path = Path(audio_path)
        assert audio_path.exists(), f"File not found: {audio_path}"
    else:  # if audio_url is provided
        ext = "mp3"
        tmp_dir = tempfile.TemporaryDirectory()
        tmp_audio_file = tmp_dir.name + f"/audio.{ext}"
        subprocess.run(
            [
                "yt-dlp",
                "-x",
                "--audio-format",
                ext,
                "--audio-quality",
                "0",
                "-o",
                tmp_dir.name + "/audio.%(ext)s",
                audio_url,
            ],
            check=True,
        )
        audio_path = Path(tmp_audio_file)

    sheetsage_output = sheetsage.infer(
        audio_path_bytes_or_url=audio_path,
        segment_start_hint=segment_start_hint,
        segment_end_hint=segment_end_hint,
        use_jukebox=use_jukebox,
        measures_per_chunk=measures_per_chunk,
        dynamic_chunking=dynamic_chunking,
        segment_hints_are_downbeats=segment_hints_are_downbeats,
        beat_information=beat_information,
        beats_per_measure_hint=beats_per_measure_hint,
        beats_per_minute_hint=beats_per_minute_hint,
        detect_melody=detect_melody,
        detect_harmony=detect_harmony,
        melody_threshold=melody_threshold,
        harmony_threshold=harmony_threshold,
        beat_detection_padding=beat_detection_padding,
        avoid_chunking_if_possible=avoid_chunking_if_possible,
        legacy_behavior=legacy_behavior,
        status_change_callback=status_change_callback,
        return_intermediaries=return_intermediaries,
        tqdm=tqdm,
    )

    if return_dict:
        return sheetsage_output
    else:
        return (
            sheetsage_output["lead_sheet"],
            sheetsage_output["segment_beats"],
            sheetsage_output["segment_beats_times"],
            sheetsage_output["chunks_tertiaries"],
            sheetsage_output["melody_logits"],
            sheetsage_output["harmony_logits"],
            sheetsage_output["melody_last_hidden_state"],
            sheetsage_output["harmony_last_hidden_state"],
        )
