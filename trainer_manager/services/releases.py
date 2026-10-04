"""Standalone release selection and version identities without changing trainer row layouts."""

import re
from datetime import datetime
from pathlib import PureWindowsPath


def is_standalone(name, url, context=""):
    text = name + " " + url + " " + context
    return not re.search(r"wemod|plitch|auto[\W_]*updat|installer|\bsetup\b", text, re.I)


def latest_release(rows):
    candidates = [row for row in rows if is_standalone(row[0], row[1])]
    if not candidates:
        return None

    def order(row):
        try:
            published = datetime.fromisoformat(row[4].strip()).replace(tzinfo=None)
        except ValueError:
            published = datetime.min
        # Numeric version order is only a tie-breaker when dates are equal/missing.
        numbers = tuple(int(part) for part in re.findall(r"\d+", row[0]))
        return published, numbers

    return max(candidates, key=order)


def release_info(row):
    version = re.search(r"\bv\d.*?(?=[. _-]+(?:Plus|Trainer)\b|$)", row[0], re.I)
    return {"download_url": row[1], "name": row[0], "date": row[4].strip(),
            "version": version.group().rstrip(". -_") if version else row[0]}


def source_key(source):
    return source[-1] + ":" + (source[1].rstrip("/") if source[-1] == "COMMON" else source[0])


def installed_release(data, record, candidates=()):
    source = [record[0], record[5], "", record[-3]]
    stored = data["files"].get("trainer_versions", {}).get(source_key(source))
    if stored:
        return stored
    # Old versions used the release filename as an ancestor directory or EXE name.
    def normalize(text):
        text = re.sub(r"\.(exe|zip|rar)$", "", text, flags=re.I)
        text = re.sub(r"[- ._]*FLiNG$", "", text, flags=re.I)
        return re.sub(r"\W|_", "", text).casefold()
    parts = {normalize(part) for part in PureWindowsPath(record[1]).parts}
    for row in candidates:
        if normalize(row[0]) in parts:
            return release_info(row)
    return None


def same_release(installed, available):
    if not installed:
        return False
    # A rotated download token alone is not a new release; a reused URL with a new
    # filename/date still is. Older metadata with only a link remains readable.
    if installed.get("name") and installed.get("date"):
        return all(installed.get(key) == available.get(key) for key in ("name", "date"))
    return bool(installed.get("download_url")) and installed["download_url"] == available["download_url"]
