import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from tqdm import tqdm as _tqdm


def tqdm(*args, dynamic_ncols=True, **kwargs):
    return _tqdm(
        *args,
        dynamic_ncols=dynamic_ncols,
        **kwargs,
    )


class DownloadFailedOther(Exception):
    keyword = "other"

    def __init__(self, yt_id):
        self.yt_id = yt_id
        super().__init__(f"Other error: {yt_id}")


class DownloadFailedInvalidId(Exception):
    keyword = "invalid_id"

    def __init__(self, yt_id):
        self.yt_id = yt_id
        super().__init__(f"Invalid YouTube ID: {yt_id}")


class DownloadFailedUnavailable(Exception):
    keyword = "unavailable"

    def __init__(self, yt_id):
        self.yt_id = yt_id
        super().__init__(f"Unavailable: {yt_id}")


class DownloadFailedPrivate(Exception):
    keyword = "private"

    def __init__(self, yt_id):
        self.yt_id = yt_id
        super().__init__(f"Private: {yt_id}")


class DownloadFailedRemoved(Exception):
    keyword = "removed"

    def __init__(self, yt_id):
        self.yt_id = yt_id
        super().__init__(f"Removed: {yt_id}")


class DownloadFailedCopyright(Exception):
    keyword = "copyright"

    def __init__(self, yt_id):
        self.yt_id = yt_id
        super().__init__(f"Copyright: {yt_id}")


class DownloadFailedUnsupported(Exception):
    keyword = "unsupported"

    def __init__(self, yt_id):
        self.yt_id = yt_id
        super().__init__(f"Unsupported: {yt_id}")


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
        cookies_file=args.cookies_file,
        request_interval=args.request_interval,
        download_interval=args.download_interval,
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
    cookies_file=None,
    request_interval=1,
    download_interval=1,
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

        try:
            yt_id = _download(
                yt_id,
                tgt_type,
                output_dir_root,
                verbose,
                cookies_file=cookies_file,
                request_interval=request_interval,
                download_interval=download_interval,
            )
        except DownloadFailedInvalidId as e:
            print(f"[{e.yt_id}] Invalid ID.")
        except (
            DownloadFailedPrivate,
            DownloadFailedRemoved,
            DownloadFailedUnavailable,
            DownloadFailedUnsupported,
            DownloadFailedCopyright,
            DownloadFailedOther,
        ) as e:
            if yt_id not in failed_type:
                failed_type[yt_id] = e.keyword
                with open(failed_file, "a") as f:
                    f.write(f"{yt_id} {e.keyword}\n")
            else:
                if failed_type[yt_id] != e.keyword:
                    failed_type[yt_id] = e.keyword
                    buf = []
                    for k, v in failed_type.items():
                        buf.append(f"{k} {v}\n")
                    failed_file.write_text("".join(buf))


def _get_save_dir(yt_id, db_root):
    return db_root / yt_id[0] / yt_id[1] / yt_id[2] / yt_id


def _get_download_cmd(
    tgt_type, yt_id, tmp_dir, cookies_file=None, request_interval=1, download_interval=1
):
    if tgt_type == "audio":
        cmd = [
            "yt-dlp",
            f"https://www.youtube.com/watch?v={yt_id}",
            "-f",
            "bestaudio",
            "--write-info-json",
            "--output",
            f"{tmp_dir.name}/{tgt_type}.%(ext)s",
            "--sleep-requests",
            str(request_interval),
            "--sleep-interval",
            str(download_interval),
        ]
    elif tgt_type == "video":
        cmd = [
            "yt-dlp",
            f"https://www.youtube.com/watch?v={yt_id}",
            "--write-info-json",
            "--output",
            f"{tmp_dir.name}/{tgt_type}.%(ext)s",
            "--sleep-requests",
            str(request_interval),
            "--sleep-interval",
            str(download_interval),
        ]
    else:
        raise ValueError(f"Invalid target type: {tgt_type}")

    if cookies_file:
        cmd += ["--cookies", str(cookies_file)]

    return cmd


def _download(
    yt_id,
    tgt_type,
    output_root_dir,
    verbose=False,
    cookies_file=None,
    request_interval=1,
    download_interval=1,
):
    if len(yt_id) < 4:
        raise DownloadFailedInvalidId(yt_id)

    save_dir = _get_save_dir(yt_id, output_root_dir)
    tmp_dir = tempfile.TemporaryDirectory()
    manifest_file = save_dir / "manifest.json"

    manifest = {"files": {}}
    if manifest_file.exists():
        manifest = json.loads(manifest_file.read_text())

    try:
        if tgt_type in manifest["files"]:
            return yt_id

        cmd = _get_download_cmd(
            tgt_type,
            yt_id,
            tmp_dir,
            cookies_file=cookies_file,
            request_interval=request_interval,
            download_interval=download_interval,
        )

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

        return yt_id

    except subprocess.CalledProcessError as e:
        _clean_save_dir(save_dir)

        if verbose:
            print(e)

            if len(e.stderr) > 0:
                print(f"[{yt_id}] stderr:")
                print(e.stderr)

        last_line = e.stderr.strip().splitlines()[-1].lower()
        if "private" in last_line:
            raise DownloadFailedPrivate(yt_id)
        elif "unavailable" in last_line or "available" in last_line:
            raise DownloadFailedUnavailable(yt_id)
        elif "removed" in last_line:
            raise DownloadFailedRemoved(yt_id)
        elif "copyright" in last_line:
            raise DownloadFailedCopyright(yt_id)
        elif "unsupported" in last_line:
            raise DownloadFailedUnsupported(yt_id)
        else:
            raise DownloadFailedOther(yt_id)

    except BaseException as e:  # include non-typical exceptions like KeyboardInterrupt
        _clean_save_dir(save_dir)
        raise e


def _safely_write_manifest(manifest_file, manifest, indent=2):
    tmp_file = manifest_file.parent / f"{manifest_file.name}.tmp"
    tmp_file.write_text(json.dumps(manifest, indent=indent))
    if manifest_file.exists():
        manifest_file.unlink()
    shutil.move(tmp_file, manifest_file)


def _clean_save_dir(save_dir):
    manifest_file = save_dir / "manifest.json"

    if not save_dir.exists():
        return

    if not manifest_file.exists():
        shutil.rmtree(save_dir)
        return

    recorded_files = [manifest_file]
    manifest = json.loads(manifest_file.read_text())

    for _, file_name in manifest["files"].items():
        recorded_files.append(save_dir / file_name)

    for file in save_dir.iterdir():
        if file not in recorded_files:
            file.unlink()


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
        default=(  # default: "private,removed,unavailable,unsupported"
            f"{DownloadFailedPrivate.keyword},"
            f"{DownloadFailedRemoved.keyword},"
            f"{DownloadFailedUnavailable.keyword},"
            f"{DownloadFailedUnsupported.keyword}"
        ),
        help="Type of failed downloads to skip. Separated by comma(,)",
    )
    download_parser.add_argument("-v", "--verbose", action="store_true")
    download_parser.add_argument("--cookies_file", type=Path, help="Path to the cookies file")
    download_parser.add_argument(
        "--request_interval", type=int, default=1, help="Request interval in seconds"
    )
    download_parser.add_argument(
        "--download_interval", type=int, default=1, help="Download interval in seconds"
    )

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
        if args.input == "file":
            if args.id_file is None:
                download_parser.print_help()
                print("Please provide a file containing YouTube IDs")
                exit(1)
        elif args.input == "args":
            if args.args is None:
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
