"""Standalone selection and no-op updates; no files are created or removed."""

import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from trainer_manager.services.crawler import Spider
from trainer_manager.services.storage import Data
from trainer_manager.services.releases import latest_release, release_info, source_key, installed_release, same_release
from trainer_manager.services.transfers import update_trainer, install_latest, TransferResult, remember_release


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.old = ["Game.v1.2.Plus.10.Trainer-FLiNG", "https://flingtrainer.com/downloads/old", "", "", "2024-01-01 10:00"]
        self.latest = ["Game.v1.10.Plus.12.Trainer-FLiNG", "https://flingtrainer.com/downloads/new", "", "", "2025-01-01 10:00"]
        self.source = ["Game Trainer", "https://flingtrainer.com/trainer/game/", "", "COMMON"]
        self.record = [self.source[0], "trainers/Game Trainer/trainer.exe", "2024-01-01", "NONE", "COMMON", self.source[1], "REGISTERED"]
        self.data = Data.normalize_config({"files": {"trainers": [self.record]}})
        self.detail = Mock(standalone_rows=[self.old, self.latest])
        self.detail.latest_standalone.return_value = self.latest

    def test_selects_latest_date_and_excludes_newer_auto_updater(self):
        updater = ["Game Auto-Updating Trainer Setup", "https://wemod.com/game", "", "", "2026-01-01 10:00"]
        self.assertEqual(latest_release([self.old, updater, self.latest]), self.latest)
        self.assertEqual(release_info(self.latest)["version"], "v1.10")

    def test_date_beats_version_number_and_numeric_tie_breaker(self):
        newer = self.old[:]
        newer[4] = "2026-01-01 10:00"
        self.assertEqual(latest_release([self.latest, newer]), newer)
        newer[4] = self.latest[4]
        self.assertEqual(latest_release([newer, self.latest]), self.latest)

    def test_parser_filters_auto_updating_section_even_without_setup_in_filename(self):
        html = '''<h3>Auto-Updating</h3><table class="da-attachments-table">
        <tr><td><a href="/auto">Game Trainer</a></td><td>2026-01-01</td></tr></table>
        <h3>Standalone</h3><table class="da-attachments-table other">
        <tr><td><a href="/old">Game.v1.Trainer-FLiNG</a></td><td>2024-01-01</td></tr>
        <tr><td><a href="/new"><b>Game.v2.Trainer-FLiNG</b></a></td><td>2025-01-01</td></tr></table>'''
        with patch.object(Spider, "crawler", return_value=html):
            detail = Spider.Download(self.source[1])
        self.assertEqual(detail.latest_standalone()[1], "https://flingtrainer.com/new")

    def test_same_version_does_not_request_a_file_or_create_any_directory(self):
        self.data["files"]["trainer_versions"][source_key(self.source)] = release_info(self.latest)
        with patch.object(Spider, "Download", return_value=self.detail), \
                patch.object(Data, "load_config", return_value=self.data), \
                patch.object(Path, "is_file", return_value=True), \
                patch.object(Path, "mkdir") as mkdir, \
                patch("trainer_manager.services.transfers.download_trainer") as download:
            result = update_trainer(self.record, "trainers")
        self.assertTrue(result.up_to_date)
        mkdir.assert_not_called()
        download.assert_not_called()

    def test_legacy_directory_name_can_identify_installed_version_without_download(self):
        self.record[1] = "E:/Trainer/" + self.latest[0] + "/abc123/trainer.exe"
        with patch.object(Spider, "Download", return_value=self.detail), \
                patch.object(Data, "load_config", return_value=self.data), \
                patch.object(Path, "is_file", return_value=True), \
                patch("trainer_manager.services.transfers.download_trainer") as download:
            result = update_trainer(self.record, "trainers")
        self.assertTrue(result.up_to_date)
        download.assert_not_called()

    def test_new_release_or_missing_file_downloads_using_game_name_not_version_name(self):
        for exists in (True, False):
            stored = self.old if exists else self.latest
            self.data["files"]["trainer_versions"][source_key(self.source)] = release_info(stored)
            with patch.object(Spider, "Download", return_value=self.detail), \
                    patch.object(Data, "load_config", return_value=self.data), \
                    patch.object(Path, "is_file", return_value=exists), \
                    patch("trainer_manager.services.transfers.download_trainer", return_value=TransferResult("", "trainer.exe")) as download:
                result = update_trainer(self.record, "trainers")
            self.assertEqual(download.call_args.args, (self.latest[1], self.source[0], "trainers"))
            self.assertEqual(result.release, release_info(self.latest))

    def test_reused_link_with_new_release_name_or_date_triggers_update(self):
        stored = release_info(self.latest)
        stored["date"] = "2024-01-01 10:00"
        self.data["files"]["trainer_versions"][source_key(self.source)] = stored
        with patch.object(Spider, "Download", return_value=self.detail), \
                patch.object(Data, "load_config", return_value=self.data), \
                patch.object(Path, "is_file", return_value=True), \
                patch("trainer_manager.services.transfers.download_trainer", return_value=TransferResult("", "trainer.exe")) as download:
            update_trainer(self.record, "trainers")
        download.assert_called_once()

    def test_rotated_link_for_same_named_and_dated_release_does_not_require_download(self):
        stored = release_info(self.latest)
        stored["download_url"] = "https://flingtrainer.com/downloads/old-token"
        self.assertTrue(same_release(stored, release_info(self.latest)))

    def test_install_rechecks_latest_standalone_and_records_selected_release(self):
        with patch.object(Spider, "Download", return_value=self.detail), \
                patch("trainer_manager.services.transfers.download_trainer", return_value=TransferResult("", "trainer.exe")) as download:
            result = install_latest(self.source, "trainers")
        self.assertEqual(download.call_args.args[:3], (self.latest[1], self.source[0], "trainers"))
        self.assertEqual(result.release, release_info(self.latest))

    def test_no_standalone_does_not_fall_back_to_an_installer(self):
        self.detail.latest_standalone.return_value = None
        with patch.object(Spider, "Download", return_value=self.detail), \
                patch("trainer_manager.services.transfers.download_trainer") as download:
            with self.assertRaises(ValueError):
                install_latest(self.source, "trainers")
        download.assert_not_called()

    def test_backfill_keeps_install_date_and_avoids_rewriting_unchanged_data(self):
        with patch.object(Data, "load_config", return_value=self.data), \
                patch.object(Data, "json_write_atomic") as write:
            remember_release(self.source, release_info(self.latest))
            remember_release(self.source, release_info(self.latest))
        write.assert_called_once()
        self.assertEqual(self.record[2], "2024-01-01")
        self.assertEqual(installed_release(self.data, self.record), release_info(self.latest))
