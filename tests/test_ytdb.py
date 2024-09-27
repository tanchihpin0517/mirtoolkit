import argparse
import json
import shutil

from mirtoolkit import config, ytdb

TEST_NAME = "ytdb"
TEST_INPUT_FILE = config.CACHE_DIR.joinpath(f"test_input/{TEST_NAME}/id_file.txt")
TEST_OUTPUT_DIR = config.CACHE_DIR.joinpath(f"test_output/{TEST_NAME}/downloaded")
TEST_FAILED_FILE = config.CACHE_DIR.joinpath(f"test_output/{TEST_NAME}/download_failed.txt")
TEST_ID = "bnu2L29c0nM"

TEST_INPUT_FILE.parent.mkdir(exist_ok=True, parents=True)
TEST_OUTPUT_DIR.parent.mkdir(exist_ok=True, parents=True)


def test_download():
    args = argparse.Namespace(
        command="download",
        input="file",
        id_file=TEST_INPUT_FILE,
        output_dir=TEST_OUTPUT_DIR,
        type="audio",
        failed_file=TEST_FAILED_FILE,
        failed_skip_type="removed,unavailable,unsupported",
        verbose=True,
    )

    if TEST_OUTPUT_DIR.exists():
        shutil.rmtree(TEST_OUTPUT_DIR)
    if TEST_FAILED_FILE.exists():
        TEST_FAILED_FILE.unlink()

    TEST_INPUT_FILE.write_text(f"https://www.youtube.com/watch?v={TEST_ID}\n")
    TEST_OUTPUT_DIR.mkdir(exist_ok=True)

    _test_download_file(args)


def _test_download_file(args):
    ytdb.cmd_download(args)

    output_dir = TEST_OUTPUT_DIR / TEST_ID[0] / TEST_ID[1] / TEST_ID[2] / TEST_ID
    manifest_file = output_dir / "manifest.json"
    assert manifest_file.exists()
    manifest = json.loads(manifest_file.read_text())
    audio_file = output_dir / manifest["files"]["audio"]
    audio_info_file = output_dir / manifest["files"]["audio_info"]
    assert audio_file.exists()
    assert audio_info_file.exists()


if __name__ == "__main__":
    test_functions = [obj for name, obj in locals().items() if name.startswith("test_")]
    for test_func in test_functions:
        test_func()
