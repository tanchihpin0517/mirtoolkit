import json
import logging
import subprocess
from pathlib import Path

from joblib import Parallel, delayed

from mirtoolkit import beat_transformer, sheetsage


def _get_test_audio():
    test_audio = Path.home() / ".mirtoolkit/sheetsage/rickroll.mp3"
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    # url = "https://www.youtube.com/watch?v=AbZH7XWDW_k"  # INVU
    if not test_audio.exists():
        subprocess.run(
            [
                "yt-dlp",
                "-x",
                "--audio-format",
                "mp3",
                "--audio-quality",
                "0",
                "-o",
                test_audio,
                url,
            ],
            check=True,
        )
    return test_audio


def _get_test_audio_beat(test_audio: Path):
    beat_file = Path.home() / f".mirtoolkit/sheetsage/{test_audio.stem}.json"
    if not beat_file.exists():
        result = Parallel(n_jobs=1)([delayed(beat_transformer.detect)(test_audio)])
        beats, downbeats = result[0]
        beat_file.write_text(json.dumps({"beats": beats.tolist(), "downbeats": downbeats.tolist()}))
    return json.loads(beat_file.read_text())


def test_sheetsage():
    logging.basicConfig(level=logging.INFO)
    audio_path = _get_test_audio()
    beat_info = _get_test_audio_beat(audio_path)
    sheetsage.infer(
        audio_path=audio_path,
        use_jukebox=True,
        beat_information=beat_info,
        dynamic_chunking=True,
    )


if __name__ == "__main__":
    test_sheetsage()
