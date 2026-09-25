"""Archive behavior is checked without extracting or deleting actual files."""

import sys
import types
import unittest
from unittest.mock import MagicMock, patch

import utils
from trainer_manager.services import Data, Download, File
from trainer_manager.services.data import Data as LegacyData
from trainer_manager.services.downloads import Download as LegacyDownload
from trainer_manager.services.files import File as LegacyFile


class StorageTests(unittest.TestCase):
    def test_compatibility_imports_share_class_objects(self):
        self.assertIs(utils.Data, Data)
        self.assertIs(LegacyData, Data)
        self.assertIs(LegacyDownload, Download)
        self.assertIs(LegacyFile, File)

    def test_zip_extracts_first_executable_and_reads_config_once(self):
        archive = MagicMock()
        archive.namelist.return_value = ["readme.exe.txt", "First.EXE", "Second.exe"]
        with patch("trainer_manager.services.storage.zipfile.ZipFile") as factory:
            factory.return_value.__enter__.return_value = archive
            with patch.object(Data, "json_read", return_value={
                "config": {"download": {"trainer": "trainers"}}
            }) as read:
                self.assertEqual(Download.extract_file("test.ZIP"), "First.EXE")
            read.assert_called_once()
            archive.extract.assert_called_once_with("First.EXE", "trainers")
            factory.return_value.__exit__.assert_called_once()

    def test_zip_closes_when_extraction_raises(self):
        archive = MagicMock()
        archive.namelist.return_value = ["game.exe"]
        archive.extract.side_effect = OSError("write failed")
        with patch("trainer_manager.services.storage.zipfile.ZipFile") as factory:
            factory.return_value.__enter__.return_value = archive
            with patch.object(Data, "json_read", return_value={
                "config": {"download": {"trainer": "trainers"}}
            }):
                with self.assertRaises(OSError):
                    Download.extract_file("test.zip")
            factory.return_value.__exit__.assert_called_once()

    def test_rar_closes_when_external_tool_is_missing(self):
        class RarCannotExec(Exception):
            pass

        archive = MagicMock()
        archive.namelist.return_value = ["game.exe"]
        archive.extract.side_effect = RarCannotExec()
        factory = MagicMock()
        factory.return_value.__enter__.return_value = archive
        module = types.SimpleNamespace(RarFile=factory, RarCannotExec=RarCannotExec)
        with patch.dict(sys.modules, {"rarfile": module}):
            with patch.object(Data, "json_read", return_value={
                "config": {"download": {"trainer": "trainers"}}
            }):
                self.assertEqual(Download.extract_file("test.rar"), -1)
        factory.return_value.__exit__.assert_called_once()

    def test_unknown_archive_does_not_read_config(self):
        with patch.object(Data, "json_read") as read:
            self.assertIsNone(Download.extract_file("test.zip.backup"))
        read.assert_not_called()
