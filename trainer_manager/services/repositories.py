"""Rebuild the active library from files in the selected trainer repository."""

import os
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from .releases import installed_release, source_key
from .storage import Data, CONFIG_PATH


def repository_files(root):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError("The trainer repository must be an existing directory.")

    def fail(error):
        raise error  # Do not silently replace a library with a partial scan.

    for directory, folders, names in os.walk(root, followlinks=False, onerror=fail):
        folders[:] = [name for name in folders if name != ".download-cache"
                      and not Path(directory, name).is_symlink()]
        for name in sorted(names, key=str.casefold):
            path = Path(directory, name)
            if path.suffix.lower() != ".exe" or path.is_symlink():
                continue
            resolved = path.resolve()
            if root in resolved.parents and resolved.is_file():
                yield resolved


def rebuild_repository(data, destination):
    """Preserve known source metadata, but include only files present in this root."""
    result = deepcopy(data)
    root = Path(destination).resolve()
    paths = sorted(repository_files(root), key=lambda path: str(path).casefold())
    files = result["files"]
    catalog = files.setdefault("trainer_catalog", {})
    for record in files["trainers"]:
        if len(record) < 7:
            continue
        catalog[str(Path(record[1]).resolve())] = {
            "record": deepcopy(record), "release": installed_release(data, record)}

    records, versions = [], {}
    for path in paths:
        known = catalog.get(str(path))
        if known:
            record = deepcopy(known["record"])
            record[1] = str(path)
            release = known.get("release")
        else:
            name = path.stem if path.parent == root else path.parent.name
            cover = path.parent / "preview.jpg"
            record = [name, str(path), datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d"),
                      str(cover) if cover.is_file() else "NONE", "UNKNOWN", "NONE", "REGISTERED"]
            release = None
        records.append(record)
        if release:
            versions[source_key([record[0], record[5], "", record[-3]])] = deepcopy(release)
        catalog[str(path)] = {"record": deepcopy(record), "release": deepcopy(release)}
    files["trainers"] = records
    files["trainer_versions"] = versions
    # Retired legacy list must not leak records from another repository.
    files["downloaded"] = []
    result["config"]["download"]["trainer"] = str(root)
    result["config"]["download"]["path"] = str(root)
    return result


def refresh_repository():
    current = Data.load_config()
    rebuilt = rebuild_repository(current, current["config"]["download"]["trainer"])
    if rebuilt != current:
        Data.json_write_atomic(CONFIG_PATH, rebuilt)
    return rebuilt


def save_settings(changes):
    """Merge edited settings into fresh data, never a widget's stale file snapshot."""
    current = Data.load_config()
    destination = changes.get("download", {}).get("trainer", current["config"]["download"]["trainer"])
    result = rebuild_repository(current, destination)
    for section, values in changes.items():
        result["config"].setdefault(section, {}).update(values)
    result["config"]["download"]["trainer"] = str(Path(destination).resolve())
    result["config"]["download"]["path"] = str(Path(destination).resolve())
    Data.json_write_atomic(CONFIG_PATH, result)
    return result
