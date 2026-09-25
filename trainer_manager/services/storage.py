"""JSON persistence, downloads and local file operations."""

import json
import os
import re
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

CONFIG_PATH = "data/data.json"
_INVALID_FILENAME_CHARS = str.maketrans({char: " " for char in '\\/:*?"<>|'})


class Data:
    def __init__(self):

        self.init_json = {
            "config": {
                "download": {
                    "path": ".\\trainers\\",
                    "extract": True
                },
                "cache": {
                    "detail_image": True
                },
                "resources": {
                    "detail_img": ".\\resource\\img_cache\\image.jpg",
                    "blank_img": ".\\resource\\original\\blank.png",
                    "avatar_img": ".\\resource\\icons\\avatar.png",
                    "cover_folder": ".\\resource\\game_covers"
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
                    "user_avatar": "resource/icons/avatar.png",
                    "icon": "resource/icons/icon3.png",
                    "title": "TrainerManager",
                    "connection_allow": True
                }
            },
            "files": {
                "save_file": [],
                "downloaded": [],
                "game_cats": [
                    "ALL",
                    "UNCATEGORIZED",
                ],
                "games": []
            }
        }

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
        destination = Data.json_read(CONFIG_PATH)["config"]["download"]["trainer"]
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
