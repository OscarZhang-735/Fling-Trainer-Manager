"""JSON persistence, downloads and local file operations."""

import json
import os
import re
import zipfile
from copy import deepcopy
from pathlib import Path
from urllib.request import urlretrieve
from uuid import uuid4

CONFIG_PATH = "data/data.json"
_INVALID_FILENAME_CHARS = str.maketrans({char: " " for char in '\\/:*?"<>|'})


class Data:
    def __init__(self):

        self.init_json = {
            "config": {
                "download": {
                    "path": ".\\trainers\\",
                    "trainer": "./trainers/",
                    "games": "./games/",
                    "patches": "./patches/",
                    "extract": True
                },
                "cache": {
                    "detail_image": True
                },
                "resources": {
                    "detail_img": ".\\resource\\img_cache\\image.jpg",
                    "blank_img": "resource/anon.jpg",
                    "avatar_img": "resource/shoko.png",
                    "cover_folder": "resource/game_covers",
                    "trainer_cover_folder": "resource/trainer_covers"
                },
                "library": {
                    "filter": "REGISTERED_ONLY"
                },
                "save_backup": {
                    "max_number": 10,
                    "auto_clean": False
                },
                "program": {
                    "username": "Rinne",
                    "user_avatar": "resource/shoko.png",
                    "icon": "resource/logo.png",
                    "title": "TrainerManager",
                    "connection_allow": True
                }
            },
            "files": {
                "save_file": [],
                "downloaded": [],
                "trainers": [],
                "trainer_versions": {},
                "game_cats": [
                    "ALL",
                    "UNCATEGORIZED",
                ],
                "games": []
            }
        }

    @staticmethod
    def normalize_config(data):
        """Fill missing settings without changing the input or losing legacy data."""
        result = deepcopy(data)
        config = result.setdefault("config", {})
        download = config.setdefault("download", {})
        if "trainer" not in download and "path" in download:
            download["trainer"] = download["path"]
        resources = config.setdefault("resources", {})
        for key, value in config.get("runtime", {}).items():
            resources.setdefault(key, value)
        files = result.setdefault("files", {})
        if "trainers" not in files and "downloaded" in files:
            files["trainers"] = []
            for row in files["downloaded"]:
                if len(row) == 6:
                    # Legacy records have a source URL but no source type column.
                    source = "COMMON" if str(row[4]).startswith(("http://", "https://")) else "UNKNOWN"
                    status = "REGISTERED" if row[5] == "VERIFIED" else row[5]
                    files["trainers"].append(row[:4] + [source, row[4], status])
                else:
                    files["trainers"].append(deepcopy(row))
        if config.get("library", {}).get("filter") == "VERIFIED_ONLY":
            config["library"]["filter"] = "REGISTERED_ONLY"

        def fill_missing(target, defaults):
            for key, value in defaults.items():
                if key not in target:
                    target[key] = deepcopy(value)
                elif isinstance(value, dict) and isinstance(target[key], dict):
                    fill_missing(target[key], value)

        fill_missing(result, Data().init_json)
        return result

    @staticmethod
    def load_config(path=CONFIG_PATH):
        try:
            data = Data.json_read(path)
        except FileNotFoundError:
            data = {}
        return Data.normalize_config(data)

    @staticmethod
    def prepare_directories(data):
        config = data["config"]
        directories = [Path(CONFIG_PATH).parent]
        directories.extend(Path(config["download"][key]) for key in ("trainer", "games", "patches"))
        directories.extend(Path(config["resources"][key]) for key in ("cover_folder", "trainer_cover_folder"))
        directories.append(Path(config["resources"]["detail_img"]).parent)
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def json_read(path):
        with open(path, 'r') as f:
            data = json.load(f)
        return data

    @staticmethod
    def json_write(path, data):
        with open(path, "w") as f:
            json.dump(data, f)

    @staticmethod
    def json_write_atomic(path, data):
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + "." + uuid4().hex + ".tmp")
        with temporary.open("x", encoding="utf-8") as output:
            json.dump(data, output)
        os.replace(temporary, target)

    @staticmethod
    def json_convert(json_string):
        pattern = r'(?<!")(\b\w+\b)(?!")\s*:'

        def add_quotes(match):
            return f'"{match.group(1)}":'

        return re.sub(pattern, add_quotes, json_string)


class File:
    @staticmethod
    def list_files(path):
        print(os.listdir(path))
        print(Data.json_read(CONFIG_PATH)["files"]["trainers"])

    @staticmethod
    def string_valid(string):
        return string.translate(_INVALID_FILENAME_CHARS)


class Download:
    @staticmethod
    def download_file(url, file_name):
        urlretrieve(url.replace(" ", "%20"), file_name)

    @staticmethod
    def extract_file(file_name):
        """Keep ZIP's first-EXE and RAR's all-EXE extraction semantics.

        Return the extracted member name, None when none is found, or -1
        when the external RAR extraction tool is unavailable.
        """
        suffix = Path(file_name).suffix.lower()
        if suffix not in {".zip", ".rar"}:
            return None
        destination = Data.load_config(CONFIG_PATH)["config"]["download"]["trainer"]
        if suffix == ".zip":
            with zipfile.ZipFile(file_name, "r") as archive:
                for member in archive.namelist():
                    if Path(member).suffix.lower() == ".exe":
                        archive.extract(member, destination)
                        return member
            return None

        # RAR support is only needed when actually extracting a RAR archive.
        import rarfile

        extracted = None
        with rarfile.RarFile(file_name, "r") as archive:
            for member in archive.namelist():
                if Path(member).suffix.lower() == ".exe":
                    try:
                        archive.extract(member, destination)
                    except rarfile.RarCannotExec:
                        return -1
                    extracted = member
        return extracted
