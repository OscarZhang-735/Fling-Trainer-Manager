# coding:utf-8
import requests
from lxml import etree
from bs4 import BeautifulSoup as bs

from urllib.parse import urlencode, urljoin

BLANK_IMG = "BLANK_IMG"


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
            self.keyword = keyword.split(" ")
            self.search_url = "https://flingtrainer.com/?" + urlencode({"s": keyword})
            self.sub_names = []
            self.sub_links = []
            self.sub_images = []
            self.text = Spider.crawler(self.search_url)
            if self.text != "error":
                self.parser()
            else:
                Spider.error()

        def run(self):
            re_list = []
            for i in range(len(self.sub_links)):
                if "My Trainers Archive" in self.sub_names[i]:
                    break
                print(f"Name: {self.sub_names[i]} | Link: {self.sub_links[i]} | Image: {self.sub_images[i]}")
                re_list.append([self.sub_names[i], self.sub_links[i], self.sub_images[i], "COMMON"])
            return re_list

        def parser(self):
            self.sub_names, self.sub_links, self.sub_images = [], [], []
            html = _html(self.text)
            if html is None:
                return
            for article in html.xpath("//div[@class='content']/article"):
                names = article.xpath("./div[2]/h2/a/text()")
                links = article.xpath("./div[2]/h2/a/@href")
                images = article.xpath("./div[1]/div/a/img/@src")
                if names and links:
                    self.sub_names.append(names[0])
                    self.sub_links.append(links[0])
                    self.sub_images.append(images[0] if images else BLANK_IMG)

    class Download:
        def __init__(self, detail_url):
            self.detail_url = detail_url
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
            html = _html(self.text)
            if html is None:
                return
            for row in html.xpath("//table[@class='da-attachments-table']/tbody/tr"):
                names = row.xpath("./td[1]/a/text()")
                links = row.xpath("./td[1]/a/@href")
                if not names or not links:
                    continue
                self.download_name.append(names[0])
                self.download_link.append(links[0])
                for column, values in [(2, self.download_date), (3, self.download_size),
                                       (4, self.download_count)]:
                    values.append(row.xpath(f"string(./td[{column}])"))

    class ArchivedDownload:
        def __init__(self, keyword):
            self.name_list = []
            self.link_list = []
            self.url = "https://archive.flingtrainer.com/"
            self.text = Spider.crawler(self.url)
            self.keyword = keyword.split(" ")
            self.result_name = []
            self.result_link = []
            self.parser()

        def parser(self):
            self.name_list, self.link_list = [], []
            html = _html(self.text)
            if html is None:
                return
            for link in html.xpath("//table[@class='files']//tr/td/a[@href]"):
                self.name_list.append("".join(link.itertext()))
                self.link_list.append(link.get("href"))

        def run(self):
            keywords = [keyword.lower() for keyword in self.keyword]
            matches = [(name, link) for name, link in zip(self.name_list, self.link_list)
                       if all(keyword in name.lower() for keyword in keywords)]
            self.result_name = [name for name, _ in matches]
            self.result_link = [link for _, link in matches]
            return [[name, urljoin(self.url, link), BLANK_IMG, "ARCHIVED"]
                    for name, link in matches]
