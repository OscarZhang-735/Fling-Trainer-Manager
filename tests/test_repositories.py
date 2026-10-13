"""Repository changes rebuild records without downloading, moving or deleting files."""

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from trainer_manager.services.storage import Data
from trainer_manager.services.releases import source_key
from trainer_manager.services.repositories import rebuild_repository, refresh_repository, save_settings, repository_files


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.old = Path("old-repository").resolve()
        self.new = Path("new-repository").resolve()
        self.source = ["Game Trainer", "https://example.com/game/", "", "COMMON"]
        self.record = [self.source[0], str(self.old / "Game Trainer" / "Game v1.exe"),
                       "2026-01-01", "NONE", "COMMON", self.source[1], "REGISTERED"]
        self.release = {"version": "v1", "name": "Game v1", "download_url": "https://example.com/v1"}
        self.data = Data.normalize_config({"config": {"download": {"trainer": str(self.old)}},
            "files": {"trainers": [self.record], "trainer_versions": {source_key(self.source): self.release}}})

    def scan(self, data, root, paths):
        with patch("trainer_manager.services.repositories.repository_files", return_value=paths), \
                patch.object(Path, "stat", return_value=SimpleNamespace(st_mtime=1700000000)), \
                patch.object(Path, "is_file", return_value=False):
            return rebuild_repository(data, root)

    def test_empty_repository_clears_active_records_and_versions_but_preserves_other_data(self):
        self.data["files"]["games"] = [["My Game"]]
        result = self.scan(self.data, self.new, [])
        self.assertEqual(result["files"]["trainers"], [])
        self.assertEqual(result["files"]["trainer_versions"], {})
        self.assertEqual(result["files"]["games"], [["My Game"]])
        self.assertEqual(result["config"]["download"]["trainer"], str(self.new))
        self.assertEqual(self.data["files"]["trainers"], [self.record])

    def test_switching_back_restores_only_existing_records_and_version_metadata(self):
        switched = self.scan(self.data, self.new, [])
        restored = self.scan(switched, self.old, [Path(self.record[1])])
        self.assertEqual(restored["files"]["trainers"], [self.record])
        self.assertEqual(restored["files"]["trainer_versions"][source_key(self.source)], self.release)
        absent = self.scan(switched, self.old, [])
        self.assertEqual(absent["files"]["trainers"], [])

    def test_new_repository_imports_files_without_old_repository_version(self):
        path = self.new / "Game Trainer" / "Game v2.exe"
        result = self.scan(self.data, self.new, [path])
        row = result["files"]["trainers"][0]
        self.assertEqual(row[0:2], ["Game Trainer", str(path)])
        self.assertEqual(row[-3:], ["UNKNOWN", "NONE", "REGISTERED"])
        self.assertEqual(result["files"]["trainer_versions"], {})

    def test_same_repository_rescan_removes_missing_records(self):
        result = self.scan(self.data, self.old, [])
        self.assertEqual(result["files"]["trainers"], [])

    def test_save_settings_reads_latest_records_and_preserves_unedited_settings(self):
        self.data["config"]["download"]["extract"] = False
        with patch.object(Data, "load_config", return_value=self.data), \
                patch.object(Data, "json_write_atomic") as write, \
                patch("trainer_manager.services.repositories.repository_files", return_value=[Path(self.record[1])]):
            result = save_settings({"program": {"username": "New name"}})
        self.assertEqual(result["files"]["trainers"], [self.record])
        self.assertFalse(result["config"]["download"]["extract"])
        self.assertEqual(result["config"]["program"]["username"], "New name")
        write.assert_called_once()

    def test_scan_failure_does_not_write_settings(self):
        with patch.object(Data, "load_config", return_value=self.data), \
                patch.object(Data, "json_write_atomic") as write, \
                patch("trainer_manager.services.repositories.repository_files", side_effect=PermissionError("denied")):
            with self.assertRaises(PermissionError):
                save_settings({"download": {"trainer": str(self.new)}})
        write.assert_not_called()

    def test_unchanged_refresh_does_not_rewrite_configuration(self):
        normalized = self.scan(self.data, self.old, [Path(self.record[1])])
        with patch.object(Data, "load_config", return_value=normalized), \
                patch.object(Data, "json_write_atomic") as write, \
                patch("trainer_manager.services.repositories.repository_files", return_value=[Path(self.record[1])]):
            refresh_repository()
        write.assert_not_called()

    def test_recursive_scan_excludes_staging_links_and_non_executables(self):
        folders = [".download-cache", "Game Trainer", "linked"]
        tree = [(str(self.new), folders, ["readme.txt", "Root.EXE"]),
                (str(self.new / "Game Trainer"), [], ["Game.exe", "preview.jpg"])]
        with patch("trainer_manager.services.repositories.os.walk", return_value=tree), \
                patch.object(Path, "is_dir", return_value=True), \
                patch.object(Path, "is_file", return_value=True), \
                patch.object(Path, "is_symlink", autospec=True, side_effect=lambda path: path.name == "linked"):
            paths = list(repository_files(self.new))
        self.assertEqual(folders, ["Game Trainer"])
        self.assertEqual(paths, [self.new / "Root.EXE", self.new / "Game Trainer" / "Game.exe"])


if __name__ == "__main__":
    unittest.main()
