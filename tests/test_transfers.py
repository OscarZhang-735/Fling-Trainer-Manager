"""Transfer failures and registration, with all network and disk writes mocked."""

import stat
import io
import sys
import types
import unittest
import zipfile
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import requests

from trainer_manager.services.transfers import download_trainer, register_trainer, _extract, _download_format, _publish
from trainer_manager.services.storage import Data


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.response = MagicMock()
        self.response.__enter__.return_value = self.response
        self.response.headers = {"Content-Length": "6"}
        self.response.iter_content.return_value = [b"abc", b"def"]
        self.get = self.stack.enter_context(patch("trainer_manager.services.transfers.requests.get", return_value=self.response))
        self.mkdir = self.stack.enter_context(patch.object(Path, "mkdir"))
        self.open = self.stack.enter_context(patch.object(Path, "open"))
        self.rename = self.stack.enter_context(patch.object(Path, "rename", return_value=Path("trainer.zip")))
        self.replace = self.stack.enter_context(patch.object(Path, "replace", autospec=True,
            side_effect=lambda candidate, target: Path(target)))
        self.cleanup = self.stack.enter_context(patch("trainer_manager.services.transfers.shutil.rmtree"))
        self.is_zip = self.stack.enter_context(patch("trainer_manager.services.transfers.zipfile.is_zipfile", return_value=True))

    def test_streams_progress_and_honors_archive_only_setting(self):
        progress = Mock()
        with patch("trainer_manager.services.transfers._extract") as extract:
            result = download_trainer("https://example.com/download?id=1", "A: Game.zip", "trainers", False, progress)
        self.assertEqual(result.executable, "")
        extract.assert_not_called()
        self.assertEqual(progress.call_args.args, (6, 6))
        self.get.assert_called_once()
        self.assertTrue(self.get.call_args.kwargs["stream"])
        self.assertEqual(self.get.call_args.kwargs["timeout"], (10, 30))
        self.assertEqual(self.open.call_args.args, ("xb",))

    def test_unknown_or_encoded_length_does_not_report_false_percentage(self):
        for headers in ({}, {"Content-Length": "bad"}, {"Content-Length": "999", "Content-Encoding": "gzip"}):
            self.response.headers = headers
            progress = Mock()
            download_trainer("https://example.com/game", "Game", "trainers", False, progress)
            self.assertEqual(progress.call_args.args, (6, 0))

    def test_http_error_does_not_write_or_rename_file(self):
        self.response.raise_for_status.side_effect = requests.HTTPError("403 Forbidden")
        with self.assertRaisesRegex(RuntimeError, "403 Forbidden"):
            download_trainer("https://example.com/game", "Game", "trainers")
        self.open.assert_not_called()
        self.rename.assert_not_called()

    def test_html_empty_and_truncated_downloads_never_reach_extraction(self):
        for headers, chunks in (({"Content-Type": "text/html"}, [b"html"]),
                                ({}, []), ({"Content-Length": "10"}, [b"short"])):
            self.response.headers = headers
            self.response.iter_content.return_value = chunks
            with patch("trainer_manager.services.transfers._extract") as extract:
                with self.assertRaises(RuntimeError):
                    download_trainer("https://example.com/game", "Game", "trainers")
            extract.assert_not_called()
        self.rename.assert_not_called()

    def test_interrupted_download_cleans_staging_and_does_not_install(self):
        def broken():
            yield b"abc"
            raise requests.ConnectionError("interrupted")
        self.response.iter_content.return_value = broken()
        with self.assertRaisesRegex(RuntimeError, "interrupted"):
            download_trainer("https://example.com/game", "Game", "trainers")
        self.rename.assert_not_called()
        self.replace.assert_not_called()
        self.cleanup.assert_called_once()

    def test_unsupported_content_is_rejected_even_with_archive_extension(self):
        self.is_zip.return_value = False
        self.open.return_value.__enter__.return_value.read.return_value = b"not a zip"
        with self.assertRaisesRegex(RuntimeError, "not a supported ZIP, RAR or Windows EXE"):
            download_trainer("https://example.com/fake.zip", "Game", "trainers")
        self.rename.assert_not_called()

    def test_nested_archive_executable_is_published_directly_in_trainer_folder(self):
        with patch("trainer_manager.services.transfers._extract", return_value="trainers/Game/files/nested/Real.EXE"), \
                patch.object(Path, "is_file", return_value=True):
            result = download_trainer("https://example.com/game", "Game", "trainers")
        self.assertEqual(result.executable, str(Path("trainers/Game/Real.EXE").resolve()))
        self.assertEqual(self.replace.call_args.args[0], Path("trainers/Game/files/nested/Real.EXE"))

    def test_zip_rejects_traversal_links_and_missing_executable(self):
        for name in ("../escape.exe", "C:/escape.exe", "readme.txt", "link.exe"):
            member = zipfile.ZipInfo(name)
            if name == "link.exe":
                member.external_attr = stat.S_IFLNK << 16
            with patch("trainer_manager.services.transfers.zipfile.ZipFile") as factory:
                archive = factory.return_value.__enter__.return_value
                archive.infolist.return_value = [member]
                with self.assertRaises(ValueError):
                    _extract(Path("game.zip"), Path("trainers/files"))
                archive.extract.assert_not_called()

    def test_zip_uses_extracted_path_instead_of_matching_archive_name(self):
        with patch("trainer_manager.services.transfers.zipfile.ZipFile") as factory:
            archive = factory.return_value.__enter__.return_value
            archive.infolist.return_value = [zipfile.ZipInfo("nested/Actual.EXE")]
            archive.extract.return_value = "trainers/files/nested/Actual.EXE"
            result = _extract(Path("unrelated-name.zip"), Path("trainers/files"))
        self.assertEqual(result, str(Path("trainers/files/nested/Actual.EXE").resolve()))

    def test_registration_does_not_depend_on_cover_cache_and_updates_existing_record(self):
        data = Data.normalize_config({"config": {"cache": {"detail_image": False}},
                                      "files": {"trainers": [["Game", "old.exe", "old", "NONE", "COMMON", "url", "REGISTERED"]]}})
        with patch.object(Data, "load_config", return_value=data), \
                patch.object(Data, "json_write_atomic") as write, patch.object(Path, "is_file", return_value=True):
            register_trainer(["Game", "https://example.com/game", "", "COMMON"], "actual/Trainer.exe")
        saved = write.call_args.args[1]
        self.assertEqual(len(saved["files"]["trainers"]), 1)
        self.assertEqual(saved["files"]["trainers"][0][1], "actual/Trainer.exe")
        self.assertEqual(saved["files"]["trainers"][0][3], "NONE")

    def test_registration_persists_release_without_changing_seven_column_row_shape(self):
        data = Data.normalize_config({})
        release = {"name": "Game.v1.Trainer", "download_url": "https://example.com/v1", "date": "2025-01-01", "version": "v1"}
        with patch.object(Data, "load_config", return_value=data), \
                patch.object(Data, "json_write_atomic"), patch.object(Path, "is_file", return_value=True):
            record = register_trainer(["Game", "https://example.com/game", "", "COMMON"], "trainer.exe", release=release)
        self.assertEqual(len(record), 7)
        self.assertEqual(record[-3:], ["COMMON", "https://example.com/game", "REGISTERED"])
        self.assertEqual(data["files"]["trainer_versions"]["COMMON:https://example.com/game"], release)

    def test_repeated_downloads_publish_to_same_flat_path(self):
        with patch("trainer_manager.services.transfers._download_format", return_value=".exe"):
            first = download_trainer("https://example.com/v1", "Game Trainer", "trainers")
            second = download_trainer("https://example.com/v2", "Game Trainer", "trainers")
        self.assertEqual(first.executable, second.executable)
        self.assertEqual(Path(first.executable).parent, Path("trainers/Game Trainer").resolve())
        self.assertEqual(self.cleanup.call_count, 2)

    def test_locked_current_file_reports_failure_without_removing_it(self):
        self.replace.side_effect = PermissionError("trainer is running")
        with patch("trainer_manager.services.transfers._download_format", return_value=".exe"):
            with self.assertRaisesRegex(RuntimeError, "trainer is running"):
                download_trainer("https://example.com/v2", "Game Trainer", "trainers")
        self.cleanup.assert_called_once()

    def test_missing_executable_does_not_change_registration(self):
        with patch.object(Path, "is_file", return_value=False), patch.object(Data, "json_write_atomic") as write:
            with self.assertRaises(ValueError):
                register_trainer(["Game", "url", "", "ARCHIVED"], "missing.exe")
        write.assert_not_called()

    def test_rar_extraction_failure_closes_archive_and_reports_missing_tool(self):
        class RarCannotExec(Exception):
            pass
        member = Mock(filename="nested/Game.EXE", file_redir=None)
        member.isdir.return_value = False
        member.is_symlink.return_value = False
        factory = MagicMock()
        archive = factory.return_value.__enter__.return_value
        archive.infolist.return_value = [member]
        archive.extract.side_effect = RarCannotExec()
        module = types.SimpleNamespace(RarFile=factory, RarCannotExec=RarCannotExec)
        with patch.dict(sys.modules, {"rarfile": module}):
            with self.assertRaisesRegex(RuntimeError, "WinRAR/UnRAR"):
                _extract(Path("trainer.rar"), Path("files"))
        factory.return_value.__exit__.assert_called_once()

    def test_archive_type_comes_from_content_not_download_url(self):
        self.is_zip.return_value = False
        self.open.return_value.__enter__.return_value.read.return_value = b"Rar!\x1a\x07\x01\x00"
        self.rename.return_value = Path("trainer.rar")
        result = download_trainer("https://example.com/download?id=1", "Game", "trainers", False)
        self.assertEqual(result.archive, str(Path("trainers/Game/Game.rar").resolve()))
        self.assertEqual(self.rename.call_args.args[0].suffix, ".rar")

    def test_atomic_registration_does_not_replace_original_if_serialization_fails(self):
        with patch("trainer_manager.services.storage.json.dump", side_effect=OSError("disk full")), \
                patch("trainer_manager.services.storage.os.replace") as replace:
            with self.assertRaisesRegex(OSError, "disk full"):
                Data.json_write_atomic("data/data.json", {})
        replace.assert_not_called()

    def test_download_sends_detail_page_referrer_or_source_root(self):
        for explicit, expected in (("https://flingtrainer.com/trainer/game/", "https://flingtrainer.com/trainer/game/"),
                                   (None, "https://flingtrainer.com/")):
            download_trainer("https://flingtrainer.com/downloads/token", "Game", "trainers", False,
                             referrer=explicit)
            self.assertEqual(self.get.call_args.kwargs["headers"]["Referer"], expected)

    def test_direct_executable_is_installed_without_archive_extraction(self):
        for extract in (True, False):
            with patch("trainer_manager.services.transfers._download_format", return_value=".exe"), \
                    patch("trainer_manager.services.transfers._extract") as unpack:
                self.rename.return_value = Path("saved/trainer.exe")
                result = download_trainer("https://flingtrainer.com/downloads/token", "Game", "trainers", extract)
            self.assertEqual(result.executable, str(Path("trainers/Game/Game.exe").resolve()))
            self.assertEqual(result.archive, result.executable)
            self.assertEqual(self.rename.call_args.args[0].suffix, ".exe")
            unpack.assert_not_called()

    def test_direct_executable_preserves_header_or_final_url_filename(self):
        self.response.url = "https://example.com/archive.zip/Game%20v2%20Trainer.exe"
        cases = [("attachment; filename*=UTF-8''Game%20%E4%B8%AD%E6%96%87.exe", "Game 中文.exe"),
                 ('attachment; filename="Game Original.EXE"', "Game Original.EXE"),
                 ("", "Game v2 Trainer.exe")]
        for header, expected in cases:
            self.response.headers["Content-Disposition"] = header
            with patch("trainer_manager.services.transfers._download_format", return_value=".exe"):
                result = download_trainer("https://example.com/token", "Game", "trainers")
            self.assertEqual(Path(result.executable).name, expected)

    def test_opaque_download_uses_release_name_with_actual_extension(self):
        self.response.url = "https://example.com/token"
        with patch("trainer_manager.services.transfers._download_format", return_value=".exe"):
            result = download_trainer("https://example.com/token", "Game", "trainers",
                                      release_name="Game.v2.Trainer.zip")
        self.assertEqual(Path(result.executable).name, "Game.v2.Trainer.exe")

    def test_changed_filename_retires_only_registered_file_in_same_folder(self):
        folder = Path("trainers/Game").resolve()
        old = folder / "Game v1.exe"
        with patch.object(Path, "is_file", return_value=True), \
                patch.object(Path, "exists", return_value=False), \
                patch.object(Path, "unlink", autospec=True) as unlink:
            saved = _publish(Path("cache/Game v2.exe"), folder, previous_executable=old)
        self.assertEqual(saved, str(folder / "Game v2.exe"))
        unlink.assert_called_once_with(old)

    def test_changed_filename_locked_old_file_rolls_back_new_file(self):
        folder = Path("trainers/Game").resolve()
        old = folder / "Game v1.exe"
        with patch.object(Path, "is_file", return_value=True), \
                patch.object(Path, "exists", return_value=False), \
                patch.object(Path, "unlink", autospec=True, side_effect=[PermissionError("locked"), None]) as unlink:
            with self.assertRaisesRegex(PermissionError, "locked"):
                _publish(Path("cache/Game v2.exe"), folder, previous_executable=old)
        self.assertEqual([call.args[0] for call in unlink.call_args_list], [old, folder / "Game v2.exe"])

    def test_exe_detection_checks_pe_signature_not_only_mz_prefix(self):
        self.is_zip.return_value = False
        dos = b"MZ" + bytes(58) + (128).to_bytes(4, "little")
        for content, valid in ((dos + bytes(64) + b"PE\x00\x00", True),
                               (dos + bytes(64) + b"fake", False), (b"MZfake", False)):
            self.open.return_value = io.BytesIO(content)
            if valid:
                self.assertEqual(_download_format(Path("download.part")), ".exe")
            else:
                with self.assertRaises(ValueError):
                    _download_format(Path("download.part"))
