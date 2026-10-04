"""Stream and install trainers into separate attempts, preserving existing versions."""

import re
import stat
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from urllib.parse import urlsplit
from uuid import uuid4

import requests

from .storage import Data, File, CONFIG_PATH

_RESERVED_NAME = re.compile(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)", re.I)


@dataclass
class TransferResult:
    # The saved download may be an archive or a directly served executable.
    archive: str
    executable: str = ""


def _safe_name(name):
    name = File.string_valid(name).strip(" .")[:100] or "trainer"
    if _RESERVED_NAME.match(name):
        name = "_" + name
    return name


def _validate_member(name):
    path = PurePosixPath(name.replace("\\", "/"))
    if (path.is_absolute() or PureWindowsPath(name).drive
            or any(part in ("..", ".") or File.string_valid(part) != part
                   or part.rstrip(" .") != part or _RESERVED_NAME.match(part) for part in path.parts)):
        raise ValueError("The archive contains an unsafe file path.")


def _download_format(path):
    if zipfile.is_zipfile(path):
        return ".zip"
    with path.open("rb") as source:
        header = source.read(64)
        if header.startswith((b"Rar!\x1a\x07\x00", b"Rar!\x1a\x07\x01\x00")):
            return ".rar"
        if len(header) == 64 and header.startswith(b"MZ"):
            pe_offset = int.from_bytes(header[60:64], "little")
            if pe_offset >= 64:
                source.seek(pe_offset)
                if source.read(4) == b"PE\x00\x00":
                    return ".exe"
    raise ValueError("The downloaded file is not a supported ZIP, RAR or Windows EXE.")


def _extract(archive_path, destination):
    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path) as archive:
            members = [item for item in archive.infolist()
                       if not item.is_dir() and item.filename.lower().endswith(".exe")]
            if not members:
                raise ValueError("No trainer executable was found in the ZIP archive.")
            member = members[0]
            _validate_member(member.filename)
            if stat.S_ISLNK(member.external_attr >> 16):
                raise ValueError("Archive links cannot be installed as trainers.")
            return str(Path(archive.extract(member, destination)).resolve())
    try:
        import rarfile
    except ImportError as error:
        raise RuntimeError("RAR support is missing. Install rarfile and WinRAR/UnRAR.") from error
    try:
        with rarfile.RarFile(archive_path) as archive:
            members = [item for item in archive.infolist()
                       if not item.isdir() and item.filename.lower().endswith(".exe")]
            if not members:
                raise ValueError("No trainer executable was found in the RAR archive.")
            for member in members:
                _validate_member(member.filename)
                if member.is_symlink() or getattr(member, "file_redir", None):
                    raise ValueError("Archive links cannot be installed as trainers.")
            for member in members:
                executable = archive.extract(member, destination)
            return str(Path(executable).resolve())
    except rarfile.RarCannotExec as error:
        raise RuntimeError("RAR extraction requires WinRAR/UnRAR on PATH. The archive has been kept.") from error


def download_trainer(url, name, destination, extract=True, progress=lambda done, total: None,
                     stage=lambda text: None, referrer=None):
    if urlsplit(url).scheme not in ("http", "https"):
        raise ValueError("Invalid download URL.")
    # A new directory per attempt avoids overwriting a working trainer or a partial download.
    attempt = Path(destination).resolve() / _safe_name(name) / uuid4().hex[:12]
    attempt.mkdir(parents=True, exist_ok=False)
    partial = attempt / "download.part"
    stage("Connecting…")
    parsed_url = urlsplit(url)
    headers = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity",
               "Referer": referrer or f"{parsed_url.scheme}://{parsed_url.netloc}/"}
    try:
        with requests.get(url, stream=True, timeout=(10, 30),
                          headers=headers) as response:
            response.raise_for_status()
            if "text/html" in response.headers.get("Content-Type", "").lower():
                raise ValueError("The server returned a web page instead of a trainer file.")
            length = response.headers.get("Content-Length", "")
            total = int(length) if length.isdigit() else 0
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                total = 0  # iter_content decodes the body; encoded Content-Length is not comparable.
            done, last_report = 0, 0
            progress(done, total)
            with partial.open("xb") as output:
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    if not chunk:
                        continue
                    output.write(chunk)
                    done += len(chunk)
                    now = time.monotonic()
                    if now - last_report >= 0.1:
                        progress(done, total)
                        last_report = now
            if not done or (total and done != total):
                raise ValueError("The download is empty or incomplete. Please retry.")
            progress(done, total)
        stage("Checking file…")
        suffix = _download_format(partial)
        archive = partial.rename(attempt / ("trainer" + suffix))
        if suffix == ".exe":
            # New main-site links can redirect straight to an EXE inside a former ZIP URL.
            # It is already runnable, so the archive extraction setting does not apply.
            return TransferResult(str(archive), str(archive))
        if not extract:
            return TransferResult(str(archive))
        stage("Extracting…")
        executable = _extract(archive, attempt / "files")
        if not Path(executable).is_file():
            raise ValueError("Extraction did not produce a trainer executable.")
        return TransferResult(str(archive), executable)
    except Exception as error:
        raise RuntimeError(f"{error}\nDownload files kept in: {attempt}") from error


def register_trainer(source, executable, cover="NONE"):
    """Read the latest data and use the exact extracted path, independently of cover caching."""
    if not Path(executable).is_file():
        raise ValueError("The extracted trainer file is missing.")
    data = Data.load_config()
    record = [source[0], executable, time.strftime("%Y-%m-%d"), cover, source[-1],
              source[1] if source[-1] == "COMMON" else "NONE", "REGISTERED"]
    rows = data["files"]["trainers"]
    for index, previous in enumerate(rows):
        if previous[0] == record[0] and previous[-3] == record[-3]:
            rows[index] = record
            break
    else:
        rows.append(record)
    Data.json_write_atomic(CONFIG_PATH, data)
    return record
