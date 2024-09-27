import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from enum import Enum
from pathlib import Path

from tqdm import tqdm as _tqdm


def tqdm(*args, dynamic_ncols=True, **kwargs):
    return _tqdm(
        *args,
        dynamic_ncols=dynamic_ncols,
        **kwargs,
    )


class DOWNLOAD_RESULT(Enum):
    SUCCESS = "success"
    EXIST = "exist"
    INVALID_ID = "invalid_id"
    FAILED_OTHER = "other"
    FAILED_UNAVAILABLE = "unavailable"
    FAILED_PRIVATE = "private"
    FAILED_REMOVED = "removed"
    FAILED_COPYRIGHT = "copyright"
    FAILED_UNSUPPORTED = "unsupported"


class WeirdYtIdException(Exception):
    def __init__(self, yt_id):
        self.yt_id = yt_id
        super().__init__(f"Weird YouTube ID: {yt_id}")


def cmd_download(args):
    _check_download_dependencies()

    yt_ids = _parse_ids(args)
    failed_skip_types = set(args.failed_skip_type.split(","))

    _download_wrapper(
        yt_ids=yt_ids,
        tgt_type=args.type,
        output_dir_root=args.output_dir,
        failed_file=args.failed_file,
        failed_skip_type=failed_skip_types,
        verbose=args.verbose,
    )


def _parse_ids(args):
    if args.input == "file":
        return _parse_ids_file(args.id_file)
    elif args.input == "args":
        return _parse_ids_args(args)
    elif args.input == "stdin":
        return _parse_ids_stdin()
    else:
        raise ValueError(f"Invalid input type: {args.input}")


def _parse_ids_file(id_file):
    yt_ids = []
    if id_file.suffix == ".json":
        for entry in json.loads(id_file.read_text()):
            yt_ids.append(_input_to_id(entry))
    else:
        for line in id_file.read_text().strip().splitlines():
            for entry in line.strip().split():
                yt_ids.append(_input_to_id(entry))
    return yt_ids


def _parse_ids_args(args):
    yt_ids = []
    for entry in args.args:
        yt_ids.append(_input_to_id(entry))
    return yt_ids


def _parse_ids_stdin():
    yt_ids = []
    for line in sys.stdin:
        for entry in line.strip().split():
            yt_ids.append(_input_to_id(entry))
    return yt_ids


def _input_to_id(text):
    if "youtube.com" in text:
        return text.split("v=")[-1][:11]
    else:
        return text


def _download_wrapper(
    yt_ids,
    tgt_type,
    output_dir_root,
    failed_file,
    failed_skip_type,
    verbose=False,
):
    assert output_dir_root.exists(), f"Directory {output_dir_root} does not exist."
    failed_file.touch(exist_ok=True)
    failed_type = {}

    for line in failed_file.read_text().strip().splitlines():
        yt_id, ftype = line.split()
        failed_type[yt_id] = ftype

    # remove duplicates
    yt_ids = list(dict.fromkeys(yt_ids))

    for yt_id in tqdm(yt_ids, dynamic_ncols=True):
        if failed_type.get(yt_id) in failed_skip_type:
            continue

        r, yt_id = _download(yt_id, tgt_type, output_dir_root, verbose)

        if r == DOWNLOAD_RESULT.SUCCESS:
            pass
        elif r == DOWNLOAD_RESULT.EXIST:
            pass
        elif r == DOWNLOAD_RESULT.INVALID_ID:
            print(f"[{yt_id}] Invalid ID.")
        elif r in (
            DOWNLOAD_RESULT.FAILED_REMOVED,
            DOWNLOAD_RESULT.FAILED_UNAVAILABLE,
            DOWNLOAD_RESULT.FAILED_PRIVATE,
            DOWNLOAD_RESULT.FAILED_COPYRIGHT,
            DOWNLOAD_RESULT.FAILED_UNSUPPORTED,
            DOWNLOAD_RESULT.FAILED_OTHER,
        ):
            if yt_id not in failed_type:
                failed_type[yt_id] = r.value
                with open(failed_file, "a") as f:
                    f.write(f"{yt_id} {r.value}\n")
            else:
                if failed_type[yt_id] != r.value:
                    failed_type[yt_id] = r.value
                    buf = []
                    for k, v in failed_type.items():
                        buf.append(f"{k} {v}\n")
                    failed_file.write_text("".join(buf))


def _get_save_dir(yt_id, db_root):
    return db_root / yt_id[0] / yt_id[1] / yt_id[2] / yt_id


def _get_download_cmd(tgt_type, yt_id, tmp_dir):
    if tgt_type == "audio":
        return [
            "yt-dlp",
            "--netrc",
            f"https://www.youtube.com/watch?v={yt_id}",
            "-f",
            "bestaudio",
            "--write-info-json",
            "--output",
            f"{tmp_dir.name}/{tgt_type}.%(ext)s",
        ]
    elif tgt_type == "video":
        return [
            "yt-dlp",
            "--netrc",
            f"https://www.youtube.com/watch?v={yt_id}",
            "--write-info-json",
            "--output",
            f"{tmp_dir.name}/{tgt_type}.%(ext)s",
        ]
    else:
        raise ValueError(f"Invalid target type: {tgt_type}")


def _download(yt_id, tgt_type, output_root_dir, verbose):
    if len(yt_id) < 4:
        return DOWNLOAD_RESULT.INVALID_ID, yt_id

    save_dir = _get_save_dir(yt_id, output_root_dir)
    tmp_dir = tempfile.TemporaryDirectory()
    manifest_file = save_dir / "manifest.json"

    manifest = {"files": {}}
    if manifest_file.exists():
        manifest = json.loads(manifest_file.read_text())

    try:
        if tgt_type in manifest["files"]:
            return DOWNLOAD_RESULT.EXIST, yt_id

        cmd = _get_download_cmd(tgt_type, yt_id, tmp_dir)

        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE if not verbose else None,
            stderr=subprocess.PIPE,
            text=True,
        )

        files = list(Path(tmp_dir.name).glob("*"))
        assert len(files) == 2, str(files)
        # find file end with "info.json"
        info_file = [file for file in files if file.name.endswith("info.json")][0]
        tgt_file = [file for file in files if file != info_file][0]

        save_dir.mkdir(exist_ok=True, parents=True)
        save_tgt_file = save_dir / f"{tgt_type}{tgt_file.suffix}"
        save_info_file = save_dir / f"{tgt_type}_info.json"

        # clean existing files before moiving new files
        for existing_file in save_dir.glob(f"{tgt_type}*"):
            existing_file.unlink()
        shutil.move(tgt_file, save_tgt_file)
        shutil.move(info_file, save_info_file)

        manifest["files"][tgt_type] = save_tgt_file.name
        manifest["files"][f"{tgt_type}_info"] = save_info_file.name

        _safely_write_manifest(manifest_file, manifest)

        return DOWNLOAD_RESULT.SUCCESS, yt_id

    except subprocess.CalledProcessError as e:
        _clean_save_dir(save_dir, manifest, tgt_type)

        if verbose:
            print(e)

            if len(e.stderr) > 0:
                print(f"[{yt_id}] stderr:")
                print(e.stderr)

        last_line = e.stderr.strip().splitlines()[-1].lower()
        if "private" in last_line:
            return DOWNLOAD_RESULT.FAILED_PRIVATE, yt_id
        elif "unavailable" in last_line or "available" in last_line:
            return DOWNLOAD_RESULT.FAILED_UNAVAILABLE, yt_id
        elif "removed" in last_line:
            return DOWNLOAD_RESULT.FAILED_REMOVED, yt_id
        elif "copyright" in last_line:
            return DOWNLOAD_RESULT.FAILED_COPYRIGHT, yt_id
        elif "unsupported" in last_line:
            return DOWNLOAD_RESULT.FAILED_UNSUPPORTED, yt_id
        else:
            return DOWNLOAD_RESULT.FAILED_OTHER, yt_id

    except BaseException as e:  # include non-typical exceptions like KeyboardInterrupt
        _clean_save_dir(save_dir, manifest, tgt_type)
        raise e


def _safely_write_manifest(manifest_file, manifest, indent=2):
    tmp_file = manifest_file.parent / f"{manifest_file.name}.tmp"
    tmp_file.write_text(json.dumps(manifest, indent=indent))
    if manifest_file.exists():
        manifest_file.unlink()
    shutil.move(tmp_file, manifest_file)


def _clean_save_dir(save_dir, manifest, tgt_type):
    for file in save_dir.glob(f"{tgt_type}*"):
        file.unlink()

    if save_dir.exists():
        if len(list(save_dir.iterdir())) <= 1:  # only manifest.json left
            shutil.rmtree(save_dir)


def _check_download_dependencies():
    # check yt-dlp is installed
    try:
        print("Checking yt-dlp version ... ", end="")
        subprocess.run("yt-dlp --version", shell=True, check=True, stdout=subprocess.PIPE)
        print("Done.")
    except subprocess.CalledProcessError:
        print("yt-dlp is not installed. Please install it first.")
        exit(1)

    # check ffmpeg is installed
    try:
        print("Checking ffmpeg version ... ", end="")
        subprocess.run("ffmpeg -version", shell=True, check=True, stdout=subprocess.PIPE)
        print("Done.")
    except subprocess.CalledProcessError:
        print("ffmpeg is not installed. Please install it first.")
        exit(1)


def cmd_sanity_check(args):
    _sanity_check(args.root_dir)


def _sanity_check(root_dir):
    weird_yt_ids = []
    item_dirs = []

    for l1_dir in root_dir.iterdir():
        for l2_dir in l1_dir.iterdir():
            for l3_dir in l2_dir.iterdir():
                for item_dir in l3_dir.iterdir():
                    item_dirs.append(item_dir)

    for item_dir in tqdm(item_dirs):
        manifest_file = item_dir / "manifest.json"
        yt_id = item_dir.name

        try:
            # 1. Check if manifest.json exists
            if not manifest_file.exists():
                raise WeirdYtIdException(yt_id)

            manifest = json.loads(manifest_file.read_text())

            # 2. Check if files exist
            for file in manifest["files"]:
                if not (item_dir / manifest["files"][file]).exists():
                    raise WeirdYtIdException(yt_id)

            # 3. Check all files are in manifest.json
            for file in item_dir.iterdir():
                if file == manifest_file:
                    continue
                if file.name not in manifest["files"].values():
                    raise WeirdYtIdException(yt_id)

        except WeirdYtIdException as e:
            weird_yt_ids.append(e.yt_id)

    if len(weird_yt_ids) > 0:
        Path("weird_yt_ids.txt").write_text("\n".join(weird_yt_ids))
    print(f"Found {len(weird_yt_ids)} weird yt_ids.")


def main():
    parser = argparse.ArgumentParser(
        description="YouTube Database Utility",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Download subcommand
    download_parser = subparsers.add_parser(
        "download", help="Download", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    download_parser.set_defaults(func=cmd_download)
    download_parser.add_argument(
        "-i", "--input", choices=["file", "args", "stdin"], default="args", help="Input type"
    )
    download_parser.add_argument(
        "-f", "--id_file", type=Path, help="File containing youtube IDs. Required if input is file"
    )
    download_parser.add_argument("args", nargs="*", help="IDs or urls. Required if input is args")
    download_parser.add_argument(
        "-o", "--output_dir", type=Path, required=True, help="Output directory"
    )
    download_parser.add_argument(
        "-t", "--type", choices=["audio", "video"], default="audio", help="Type of the download"
    )

    download_parser.add_argument(
        "--failed_file",
        type=Path,
        default=Path("download_failed.txt"),
        help="File to store failed downloads",
    )
    download_parser.add_argument(
        "--failed_skip_type",
        type=str,
        default=(  # default: "removed,unavailable,unsupported"
            f"{DOWNLOAD_RESULT.FAILED_REMOVED.value},"
            f"{DOWNLOAD_RESULT.FAILED_UNAVAILABLE.value},"
            f"{DOWNLOAD_RESULT.FAILED_UNSUPPORTED.value}"
        ),
        help="Type of failed downloads to skip. Separated by comma(,)",
    )
    download_parser.add_argument("-v", "--verbose", action="store_true")

    # Sanity check subcommand
    sanity_check_parser = subparsers.add_parser(
        "sanity_check",
        help="Perform a sanity check on a saved directory",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    sanity_check_parser.set_defaults(func=cmd_sanity_check)
    sanity_check_parser.add_argument("root_dir", type=Path, help="Path to the directory to check")

    args = parser.parse_args()

    if args.command == "download":
        if args.input == "file" and args.id_file is None:
            download_parser.print_help()
            print("Please provide a file containing YouTube IDs")
            exit(1)
        elif args.input == "args" and not args.args:
            download_parser.print_help()
            print("Please provide YouTube IDs or URLs")
            exit(1)
        elif args.input == "stdin":
            pass
        else:
            print(download_parser.print_help())
            print("Invalid input type")
            exit(1)
        args.func(args)
    else:
        print("Invalid command")
        print(parser.print_help())
        exit(1)


if __name__ == "__main__":
    main()
