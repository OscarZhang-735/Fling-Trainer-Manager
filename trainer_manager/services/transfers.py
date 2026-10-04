"""Select releases and atomically replace a trainer in its stable, flat directory."""

import re
import stat
import shutil
import time
import zipfile
from dataclasses import dataclass, field
from email.message import Message
from pathlib import Path, PurePosixPath, PureWindowsPath
from urllib.parse import unquote, urlsplit
from uuid import uuid4

import requests

from .storage import Data, File, CONFIG_PATH
from .releases import release_info, source_key, installed_release, same_release

_RESERVED_NAME = re.compile(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)", re.I)


@dataclass
class TransferResult:
    # The saved download may be an archive or a directly served executable.
    archive: str
    executable: str = ""
    release: dict = field(default_factory=dict)
    up_to_date: bool = False


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
        raise RuntimeError("RAR extraction requires WinRAR/UnRAR on PATH.") from error


def _response_filename(response, suffix, fallback):
    header = Message()
    header["Content-Disposition"] = response.headers.get("Content-Disposition", "")
    remote_url = response.url if isinstance(response.url, str) else ""
    names = [header.get_filename(), unquote(urlsplit(remote_url).path.rsplit("/", 1)[-1])]
    for name in names:
        if not name:
            continue
        name = PureWindowsPath(name).name
        if Path(name).suffix.lower() != suffix:
            continue
        try:
            _validate_member(name)
        except ValueError:
            continue
        return name
    fallback = re.sub(r"\.(exe|zip|rar)$", "", fallback, flags=re.I)
    return _safe_name(fallback) + suffix


def _publish(candidate, folder, filename=None, previous_executable=None):
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / (filename or candidate.name)
    previous = Path(previous_executable).resolve() if previous_executable else None
    # Only retire the registered executable in this game's flat directory.
    retire = (previous is not None and previous.parent == folder.resolve()
              and previous != target.resolve() and previous.is_file())
    if retire and target.exists():
        raise FileExistsError("A different file already exists with the new trainer's name.")
    saved = candidate.replace(target)
    if retire:
        try:
            previous.unlink()
        except OSError:
            target.unlink()  # Keep the registered old version when it is locked/in use.
            raise
    return str(saved)


def _cleanup_attempt(attempt, cache):
    if attempt.parent != cache or not re.fullmatch(r"[a-f0-9]{12}", attempt.name):
        raise ValueError("Invalid temporary download directory.")
    shutil.rmtree(attempt, ignore_errors=True)


def download_trainer(url, name, destination, extract=True, progress=lambda done, total: None,
                     stage=lambda text: None, referrer=None, release_name=None,
                     previous_executable=None):
    if urlsplit(url).scheme not in ("http", "https"):
        raise ValueError("Invalid download URL.")
    folder = Path(destination).resolve() / _safe_name(name)
    cache = Path(destination).resolve() / ".download-cache"
    # Staging is outside the trainer folder; only the validated current EXE is published.
    attempt = cache / uuid4().hex[:12]
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
        filename = _response_filename(response, suffix, release_name or name)
        archive = partial.rename(attempt / ("trainer" + suffix))
        if suffix == ".exe":
            # New main-site links can redirect straight to an EXE inside a former ZIP URL.
            # It is already runnable, so the archive extraction setting does not apply.
            executable = _publish(archive, folder, filename, previous_executable)
            return TransferResult(executable, executable)
        if not extract:
            return TransferResult(_publish(archive, folder, filename))
        stage("Extracting…")
        executable = _extract(archive, attempt / "files")
        if not Path(executable).is_file():
            raise ValueError("Extraction did not produce a trainer executable.")
        executable = _publish(Path(executable), folder, previous_executable=previous_executable)
        return TransferResult(executable, executable)
    except Exception as error:
        raise RuntimeError(str(error)) from error
    finally:
        _cleanup_attempt(attempt, cache)


def install_latest(source, destination, extract=True, progress=lambda done, total: None,
                   stage=lambda text: None):
    from .crawler import Spider
    if source[-1] == "COMMON":
        stage("Checking standalone version…")
        selected = Spider.Download(source[1]).latest_standalone()
        if selected is None:
            raise ValueError("No standalone trainer is available. No file was downloaded.")
        referrer = source[1]
    else:
        selected = [source[0], source[1], "", "", ""]
        referrer = None
    result = download_trainer(selected[1], source[0], destination, extract, progress, stage, referrer,
                              release_name=selected[0])
    result.release = release_info(selected)
    return result


def update_trainer(record, destination, progress=lambda done, total: None, stage=lambda text: None):
    from .crawler import Spider
    stage("Checking standalone version…")
    detail = Spider.Download(record[5])
    selected = detail.latest_standalone()
    if selected is None:
        raise ValueError("No standalone trainer is available. No file was downloaded.")
    available = release_info(selected)
    installed = installed_release(Data.load_config(), record, detail.standalone_rows)
    if Path(record[1]).is_file() and same_release(installed, available):
        return TransferResult("", record[1], available, True)
    result = download_trainer(selected[1], record[0], destination, progress=progress,
                              stage=stage, referrer=record[5], release_name=selected[0],
                              previous_executable=record[1])
    result.release = available
    return result


def register_trainer(source, executable, cover="NONE", release=None):
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
    if release:
        data["files"].setdefault("trainer_versions", {})[source_key(source)] = dict(release)
    Data.json_write_atomic(CONFIG_PATH, data)
    return record


def remember_release(source, release):
    """Backfill a recognized legacy version without changing the installation record/date."""
    data = Data.load_config()
    versions = data["files"].setdefault("trainer_versions", {})
    if versions.get(source_key(source)) != release:
        versions[source_key(source)] = dict(release)
        Data.json_write_atomic(CONFIG_PATH, data)
