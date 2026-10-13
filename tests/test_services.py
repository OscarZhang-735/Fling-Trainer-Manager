"""Offline regression checks; no GUI, network, or real file writes."""

import io
import json
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import mock_open, patch

from trainer_manager.services.data import Data
from trainer_manager.services.files import File


class DataTests(unittest.TestCase):
    def test_legacy_config_is_completed_without_mutating_or_writing_original(self):
        legacy = {
            "config": {"download": {"path": "D:/My Trainers/"},
                       "runtime": {"blank_img": "custom.jpg"},
                       "library": {"filter": "VERIFIED_ONLY"}},
            "files": {"downloaded": [["Game", "game.exe", "2024", "cover.jpg", "NONE", "VERIFIED"]]},
        }
        original = deepcopy(legacy)
        with patch.object(Data, "json_read", return_value=legacy), patch.object(Data, "json_write") as write:
            result = Data.load_config()
        self.assertEqual(legacy, original)
        write.assert_not_called()
        self.assertEqual(result["config"]["download"]["trainer"], "D:/My Trainers/")
        self.assertEqual(result["config"]["resources"]["blank_img"], "custom.jpg")
        self.assertEqual(result["files"]["downloaded"], legacy["files"]["downloaded"])
        self.assertEqual(result["files"]["trainers"][0],
                         ["Game", "game.exe", "2024", "cover.jpg", "UNKNOWN", "NONE", "REGISTERED"])
        self.assertEqual(result["config"]["library"]["filter"], "REGISTERED_ONLY")
        self.assertIn("username", result["config"]["program"])
        self.assertNotIn("games", result["files"])
        self.assertNotIn("save_file", result["files"])
        self.assertNotIn("patches", result["config"]["download"])
        self.assertEqual(Data.normalize_config(result), result)

    def test_current_settings_and_records_take_precedence_over_legacy_values(self):
        payload = {"config": {"program": {"username": "Custom", "connection_allow": False},
                              "download": {"trainer": "new/", "path": "old/"},
                              "resources": {"blank_img": "new.jpg"},
                              "runtime": {"blank_img": "old.jpg"}},
                   "files": {"trainers": [], "downloaded": [["legacy"]]}, "extra": 123}
        result = Data.normalize_config(payload)
        self.assertEqual(result["config"]["program"]["username"], "Custom")
        self.assertFalse(result["config"]["program"]["connection_allow"])
        self.assertEqual(result["config"]["download"]["trainer"], "new/")
        self.assertEqual(result["config"]["resources"]["blank_img"], "new.jpg")
        self.assertEqual(result["files"]["trainers"], [])
        self.assertEqual(result["extra"], 123)

    def test_missing_config_uses_defaults_but_invalid_json_is_not_hidden(self):
        with patch.object(Data, "json_read", side_effect=FileNotFoundError):
            self.assertEqual(Data.load_config(), Data().init_json)
        with patch("builtins.open", mock_open(read_data="not json")):
            with self.assertRaises(json.JSONDecodeError):
                Data.load_config()

    def test_prepares_configured_directories_before_pages_need_them(self):
        data = Data.normalize_config({"config": {"download": {"trainer": "custom/trainers",
                                                            "games": "legacy/games", "patches": "legacy/patches"},
                                                "resources": {"detail_img": "custom/cache/image.jpg",
                                                              "cover_folder": "legacy/game_covers"}}})
        with patch.object(Path, "mkdir", autospec=True) as mkdir:
            Data.prepare_directories(data)
        created = [call.args[0] for call in mkdir.call_args_list]
        self.assertIn(Path("custom/trainers"), created)
        self.assertIn(Path("custom/cache"), created)
        self.assertIn(Path("resource/trainer_covers"), created)
        self.assertNotIn(Path("legacy/games"), created)
        self.assertNotIn(Path("legacy/patches"), created)
        self.assertNotIn(Path("legacy/game_covers"), created)
        self.assertTrue(all(call.kwargs == {"parents": True, "exist_ok": True}
                            for call in mkdir.call_args_list))

    def test_reads_existing_trainer_records_without_conversion(self):
        payload = {"files": {"trainers": [["Game", "game.exe", "REGISTERED"]]}}
        with patch("builtins.open", mock_open(read_data=json.dumps(payload))):
            self.assertEqual(Data.json_read("data/data.json"), payload)

    def test_writes_unicode_and_nested_records(self):
        payload = {"trainers": [["游戏修改器", "D:\\Trainers\\trainer.exe"]], "enabled": True}
        output = io.StringIO()
        with patch("builtins.open") as opened:
            opened.return_value.__enter__.return_value = output
            Data.json_write("data/data.json", payload)
        self.assertEqual(json.loads(output.getvalue()), payload)

    def test_invalid_json_still_raises(self):
        with patch("builtins.open", mock_open(read_data="not json")):
            with self.assertRaises(json.JSONDecodeError):
                Data.json_read("data/data.json")

    def test_legacy_unquoted_keys(self):
        self.assertEqual(json.loads(Data.json_convert('{name: "Game", count: 2}')),
                         {"name": "Game", "count": 2})


class FileTests(unittest.TestCase):
    def test_reserved_filename_characters_become_spaces(self):
        self.assertEqual(File.string_valid('a\\/:*?"<>|b'), "a         b")

    def test_valid_unicode_filename_is_unchanged(self):
        self.assertEqual(File.string_valid("游戏 - Game (2024).exe"),
                         "游戏 - Game (2024).exe")


if __name__ == "__main__":
    unittest.main()
