# coding:utf-8
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor

import requests
from lxml import etree
from bs4 import BeautifulSoup as bs

from urllib.parse import urljoin, urlsplit, urldefrag
from .releases import is_standalone, latest_release

BLANK_IMG = "BLANK_IMG"


def _search_text(text):
    return re.sub(r"[\W_]+", " ", unicodedata.normalize("NFKC", text).casefold()).strip()


def _matches(name, keywords):
    return bool(keywords) and all(word in _search_text(name) for word in keywords)


def _html(text):
    """Do not parse failed or empty responses."""
    if not text or text == "error":
        return None
    return etree.HTML(text)


class Spider:
    @staticmethod
    def crawler(url):
        headers = {"User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1.6) ",
                   "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                   "Accept-Language": "en-us",
                   "Connection": "keep-alive",
                   "Accept-Charset": "GB2312,utf-8;q=0.7,*;q=0.7"}

        try:
            r = requests.get(url, headers=headers, timeout=5)
        except requests.exceptions.RequestException as error:
            print(f"Connection failed: {error}")
            return "error"
        print(f"Request Generated! (GET: {url})")

        if r.status_code == 200:
            print("Server Response: 200-OK")
            return r.text
        else:
            print(f"Server Response: {r.status_code}")
            return "error"

    @staticmethod
    def error():
        pass

    class NekoNyanPatchSearch:
        # Temporally abandoned
        def __init__(self):
            self.url = "https://patches.nekonyansoft.com/"
            self.text = Spider.crawler(self.url)
            if self.text != "error":
                self.parser()
            else:
                Spider.error()

        def parser(self):
            soup = bs(self.text, 'html.parser')
            print(self.text)
            buttons = soup.find_all('button', onClick=True)
            download_links = []
            print("Links")
            for button in buttons:
                onClick_value = button['onClick']
                if 'window.open' in onClick_value:
                    link = onClick_value.split("'")[1]
                    download_links.append(link)
            for link in download_links:
                print("link:", link)

    class Search:
        def __init__(self, keyword):
            self.keyword = _search_text(keyword).split()
            self.search_url = "https://flingtrainer.com/all-trainers/"
            self.sub_names = []
            self.sub_links = []
            self.sub_images = []
            self.text = Spider.crawler(self.search_url) if self.keyword else ""
            if self.text != "error":
                self.parser()
            else:
                Spider.error()

        def run(self):
            return [[name, link, image, "COMMON"]
                    for name, link, image in zip(self.sub_names, self.sub_links, self.sub_images)
                    if _matches(name, self.keyword)]

        def parser(self):
            self.sub_names, self.sub_links, self.sub_images = [], [], []
            html = _html(self.text)
            if html is None:
                return
            seen = set()
            for anchor in html.xpath("//a[@href]"):
                name = " ".join("".join(anchor.itertext()).split())
                link = urldefrag(urljoin(self.search_url, anchor.get("href")))[0]
                parsed = urlsplit(link)
                if (parsed.scheme not in ("http", "https")
                        or parsed.hostname != "flingtrainer.com"
                        or not parsed.path.startswith("/trainer/")
                        or not name.casefold().endswith(" trainer")
                        or link in seen):
                    continue
                seen.add(link)
                self.sub_names.append(name)
                self.sub_links.append(link)
                self.sub_images.append(BLANK_IMG)

    class SearchAll:
        """Search both catalogs concurrently, keeping their download types intact."""

        def __init__(self, keyword):
            self.results = []
            self.failed_sources = []
            if not _search_text(keyword):
                return
            with ThreadPoolExecutor(max_workers=2) as executor:
                searches = [
                    ("All Trainers", executor.submit(Spider.Search, keyword)),
                    ("Archive", executor.submit(Spider.ArchivedDownload, keyword)),
                ]
                seen = set()
                for source, future in searches:
                    search = future.result()
                    if not search.text or search.text == "error":
                        self.failed_sources.append(source)
                    for row in search.run():
                        if row[1] not in seen:
                            seen.add(row[1])
                            self.results.append(row)

        def run(self):
            return [row[:] for row in self.results]

    class Download:
        def __init__(self, detail_url):
            self.detail_url = detail_url
            self.image_url = BLANK_IMG
            self.standalone_rows = []
            self.download_name = []
            self.download_link = []
            self.download_size = []
            self.download_count = []
            self.download_date = []
            self.text = Spider.crawler(self.detail_url)
            if self.text != "error":
                self.parser()
            else:
                Spider.error()

        def run(self):
            re_list = []
            for i in range(len(self.download_name)):
                print(
                    f"Name: {self.download_name[i]} | Link: {self.download_link[i]} | Size: {self.download_size[i]} | Count: {self.download_count[i]} | Date: {self.download_date[i]}")
                re_list.append(
                    [self.download_name[i], self.download_link[i], self.download_size[i], self.download_count[i],
                     self.download_date[i]])

            return re_list

        def parser(self):
            self.download_name, self.download_link = [], []
            self.download_date, self.download_size, self.download_count = [], [], []
            self.image_url = BLANK_IMG
            self.standalone_rows = []
            html = _html(self.text)
            if html is None:
                return
            images = html.xpath("//meta[@property='og:image']/@content")
            images += html.xpath("//meta[@name='twitter:image']/@content")
            # Restrict fallback images to the article, excluding sidebar and comment avatars.
            images += html.xpath(
                "//div[contains(concat(' ', normalize-space(@class), ' '), ' entry-inner ')]"
                "//img/@data-src | "
                "//div[contains(concat(' ', normalize-space(@class), ' '), ' entry-inner ')]//img/@src")
            for image in images:
                image_url = urljoin(self.detail_url, image.strip())
                if image.strip() and urlsplit(image_url).scheme in ("http", "https"):
                    self.image_url = image_url
                    break
            for row in html.xpath("//table[contains(concat(' ', normalize-space(@class), ' '), ' da-attachments-table ')]//tr[td]"):
                names = row.xpath("./td[1]/a//text()")
                links = row.xpath("./td[1]/a/@href")
                if not names or not links:
                    continue
                name = " ".join(" ".join(names).split())
                self.download_name.append(name)
                self.download_link.append(urljoin(self.detail_url, links[0]))
                for column, values in [(2, self.download_date), (3, self.download_size),
                                       (4, self.download_count)]:
                    values.append(row.xpath(f"string(./td[{column}])"))

                heading = row.xpath("ancestor::table[1]/preceding::*[self::h2 or self::h3 or self::h4][1]")
                context = " ".join(heading[0].itertext()) if heading else ""
                if is_standalone(name, self.download_link[-1], context):
                    self.standalone_rows.append([name, self.download_link[-1], self.download_size[-1],
                                                 self.download_count[-1], self.download_date[-1]])

        def latest_standalone(self):
            return latest_release(self.standalone_rows)

    class ArchivedDownload:
        def __init__(self, keyword):
            self.name_list = []
            self.link_list = []
            self.url = "https://archive.flingtrainer.com/"
            self.keyword = _search_text(keyword).split()
            self.text = Spider.crawler(self.url) if self.keyword else ""
            self.result_name = []
            self.result_link = []
            self.parser()

        def parser(self):
            self.name_list, self.link_list = [], []
            html = _html(self.text)
            if html is None:
                return
            for link in html.xpath("//table[contains(concat(' ', normalize-space(@class), ' '), ' files ')]//tr/td/a[@href]"):
                self.name_list.append("".join(link.itertext()))
                self.link_list.append(link.get("href"))

        def run(self):
            matches = [(name, link) for name, link in zip(self.name_list, self.link_list)
                       if _matches(name, self.keyword)]
            self.result_name = [name for name, _ in matches]
            self.result_link = [link for _, link in matches]
            return [[name, urljoin(self.url, link), BLANK_IMG, "ARCHIVED"]
                    for name, link in matches]
