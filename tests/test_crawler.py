"""Offline HTML fixtures exercise the real lxml parser."""

import unittest
from threading import Barrier
from unittest.mock import Mock, patch

import requests

from trainer_manager.services.crawler import BLANK_IMG, Spider


class CrawlerTests(unittest.TestCase):
    def test_archive_filters_correct_rows_and_repeated_calls_do_not_accumulate(self):
        html = '''<table class="files"><tbody>
        <tr><td><a href="wrong.zip">Other Game</a></td></tr>
        <tr><td><a href="first.zip">Wanted Game</a></td></tr>
        <tr><td><a href="https://cdn.example/second.zip">Wanted Game</a></td></tr>
        </tbody></table>'''
        with patch.object(Spider, "crawler", return_value=html):
            search = Spider.ArchivedDownload("wanted game")
        expected = [
            ["Wanted Game", "https://archive.flingtrainer.com/first.zip", BLANK_IMG, "ARCHIVED"],
            ["Wanted Game", "https://cdn.example/second.zip", BLANK_IMG, "ARCHIVED"],
        ]
        self.assertEqual(search.run(), expected)
        self.assertEqual(search.run(), expected)

    def test_failed_or_empty_responses_return_empty_results(self):
        for response in ["error", "", "<html></html>"]:
            for search_type in [Spider.Search, Spider.Download, Spider.ArchivedDownload, Spider.SearchAll]:
                with self.subTest(response=response, search_type=search_type):
                    with patch.object(Spider, "crawler", return_value=response):
                        self.assertEqual(search_type("example").run(), [])

    def test_catalog_filters_keywords_and_ignores_navigation_and_duplicate_links(self):
        html = '''<div class="entry-inner">
        <a href="#A">A</a>
        <a href="https://archive.flingtrainer.com/">My Trainers Archive</a>
        <ul><li><a href="/trainer/one/">Wanted <b>Game</b> Trainer</a></li>
        <li><a href="/trainer/other/">Other Game Trainer</a></li>
        <li><a href="/trainer/two/">Wanted Game II Trainer</a></li></ul>
        <a href="/trainer/one/#download">Wanted Game Trainer</a>
        <a href="https://other.example/trainer/one/">Wanted Game Trainer</a>
        <a href="/tag/wanted-game/">Wanted Game Trainer</a></div>'''
        with patch.object(Spider, "crawler", return_value=html) as request:
            search = Spider.Search("  GAME\t wanted  ")
        self.assertEqual(request.call_args.args[0], "https://flingtrainer.com/all-trainers/")
        expected = [["Wanted Game Trainer", "https://flingtrainer.com/trainer/one/", BLANK_IMG, "COMMON"],
                    ["Wanted Game II Trainer", "https://flingtrainer.com/trainer/two/", BLANK_IMG, "COMMON"]]
        self.assertEqual(search.run(), expected)
        search.parser()
        self.assertEqual(search.run(), expected)

    def test_searches_both_sources_concurrently_and_preserves_versions(self):
        barrier = Barrier(2)
        pages = {
            "https://flingtrainer.com/all-trainers/": '''
                <a href="/trainer/wanted/">Wanted Game Trainer</a>''',
            "https://archive.flingtrainer.com/": '''<table class="files sortable">
                <tr><td><a href="one.zip">Wanted.Game.v1.Trainer</a></td></tr>
                <tr><td><a href="one.zip">Wanted.Game.v1.Trainer</a></td></tr>
                <tr><td><a href="two.zip">Wanted.Game.v2.Trainer</a></td></tr>
                <tr><td><a href="other.zip">Other.Game.Trainer</a></td></tr></table>''',
        }

        def fetch(url):
            barrier.wait(timeout=5)
            return pages[url]

        with patch.object(Spider, "crawler", side_effect=fetch) as request:
            search = Spider.SearchAll(" Wanted-GAME ")
        self.assertCountEqual([call.args[0] for call in request.call_args_list], pages)
        self.assertEqual(search.failed_sources, [])
        self.assertEqual(search.run(), [
            ["Wanted Game Trainer", "https://flingtrainer.com/trainer/wanted/", BLANK_IMG, "COMMON"],
            ["Wanted.Game.v1.Trainer", "https://archive.flingtrainer.com/one.zip", BLANK_IMG, "ARCHIVED"],
            ["Wanted.Game.v2.Trainer", "https://archive.flingtrainer.com/two.zip", BLANK_IMG, "ARCHIVED"],
        ])
        self.assertEqual(search.run(), search.run())

    def test_one_source_failure_keeps_other_source_results(self):
        for failed_source in ("All Trainers", "Archive"):
            with self.subTest(failed_source=failed_source):
                pages = {
                    "https://flingtrainer.com/all-trainers/": 'error' if failed_source == "All Trainers" else
                    '<a href="/trainer/game/">Game Trainer</a>',
                    "https://archive.flingtrainer.com/": 'error' if failed_source == "Archive" else
                    '<table class="files"><tr><td><a href="game.zip">Game Trainer</a></td></tr></table>',
                }
                with patch.object(Spider, "crawler", side_effect=pages.__getitem__):
                    search = Spider.SearchAll("game")
                self.assertEqual(search.failed_sources, [failed_source])
                self.assertEqual(len(search.run()), 1)
                self.assertEqual(search.run()[0][-1], "ARCHIVED" if failed_source == "All Trainers" else "COMMON")

    def test_empty_keywords_do_not_fetch_or_match_entire_catalog(self):
        with patch.object(Spider, "crawler") as request:
            for keyword in ("", " \t\n ", "---"):
                for search_type in (Spider.Search, Spider.ArchivedDownload, Spider.SearchAll):
                    self.assertEqual(search_type(keyword).run(), [])
        request.assert_not_called()

    def test_both_source_failures_are_reported(self):
        with patch.object(Spider, "crawler", return_value="error"):
            search = Spider.SearchAll("game")
        self.assertEqual(search.run(), [])
        self.assertEqual(search.failed_sources, ["All Trainers", "Archive"])

    def test_details_keep_metadata_with_its_row(self):
        html = '''<table class="da-attachments-table"><tbody>
        <tr><td><a href="one.zip">One</a></td><td></td><td>1 MB</td><td>2</td></tr>
        <tr><td>No link</td><td>ignored</td></tr>
        <tr><td><a href="two.zip">Two</a></td><td>Today</td><td>3 MB</td><td>4</td></tr>
        </tbody></table>'''
        with patch.object(Spider, "crawler", return_value=html):
            result = Spider.Download("example").run()
        self.assertEqual(result, [["One", "one.zip", "1 MB", "2", ""],
                                  ["Two", "two.zip", "3 MB", "4", "Today"]])

    def test_timeout_and_http_errors_use_existing_error_sentinel(self):
        with patch("trainer_manager.services.crawler.requests.get", side_effect=requests.Timeout):
            self.assertEqual(Spider.crawler("https://example.com"), "error")
        with patch("trainer_manager.services.crawler.requests.get", return_value=Mock(status_code=503)):
            self.assertEqual(Spider.crawler("https://example.com"), "error")
