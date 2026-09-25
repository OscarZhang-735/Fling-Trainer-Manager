"""Offline HTML fixtures exercise the real lxml parser."""

import unittest
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
            for search_type in [Spider.Search, Spider.Download, Spider.ArchivedDownload]:
                with self.subTest(response=response, search_type=search_type):
                    with patch.object(Spider, "crawler", return_value=response):
                        self.assertEqual(search_type("example").run(), [])

    def test_search_missing_cover_does_not_shift_following_image(self):
        html = '''<div class="content">
        <article><div></div><div><h2><a href="one">One</a></h2></div></article>
        <article><div><div><a><img src="two.jpg"/></a></div></div>
        <div><h2><a href="two">Two</a></h2></div></article></div>'''
        with patch.object(Spider, "crawler", return_value=html) as request:
            result = Spider.Search("A&B + game").run()
        self.assertEqual(request.call_args.args[0], "https://flingtrainer.com/?s=A%26B+%2B+game")
        self.assertEqual(result, [["One", "one", BLANK_IMG, "COMMON"],
                                  ["Two", "two", "two.jpg", "COMMON"]])

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
