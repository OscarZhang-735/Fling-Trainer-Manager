"""ui.search: extracted application components."""

import shutil
import os
import time
import webbrowser
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QStandardItemModel, QPixmap
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QHeaderView, QTableWidgetItem
from qfluentwidgets import MessageBox, ImageLabel, BodyLabel, PushButton, TableWidget, LineEdit, PrimaryPushButton, HorizontalSeparator, VerticalSeparator, TitleLabel
from qfluentwidgets import FluentIcon as FIF
from trainer_manager.services import crawler
from trainer_manager import services as utils
from trainer_manager.runtime import Font, NET


class SearchWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # self.resize(400, 400)
        self.name = None
        self.row = None
        self.config = utils.Data.json_read("data/data.json")["config"]
        self.data = utils.Data.json_read("data/data.json")
        self.setObjectName("Search")
        self.vBoxLayoutMain = QVBoxLayout(self)
        self.vBoxLayoutMiddle = QVBoxLayout(self)
        self.hBoxLayoutMiddle = QHBoxLayout(self)
        self.hBoxLayoutTop = QHBoxLayout(self)
        self.vBoxLayoutMain.setContentsMargins(30, 60, 30, 50)
        self.vBoxLayoutMain.setSpacing(30)
        self.hBoxLayoutTop.setSpacing(20)
        self.vBoxLayoutMiddle.setSpacing(10)

        self.titleLabel = TitleLabel("Search", self)
        self.titleLabel.setFixedHeight(40)
        self.searchLine = LineEdit(self)
        self.searchLine.setAlignment(Qt.AlignCenter)
        self.searchLine.setFixedWidth(300)
        self.searchLine.setPlaceholderText("Search on FLiNG Website")
        self.searchLine.setClearButtonEnabled(True)
        self.searchButton = PrimaryPushButton(self)
        self.searchButton.setIcon(FIF.SEARCH)
        self.searchButton.setText("Search")

        self.clearButton = PushButton(self)
        self.clearButton.setIcon(FIF.CLOSE)
        self.clearButton.setText("Clear")
        self.homepageButton = PushButton(self)
        self.homepageButton.setIcon(FIF.LINK)
        self.homepageButton.setText("Visit FLiNG Website")

        self.resultLabel = BodyLabel(self)
        self.resultLabel.setText("")

        self.exampleModel = QStandardItemModel(18, 3)
        self.resultTable = TableWidget(self)
        self.resultTable.setColumnCount(2)
        self.resultTable.horizontalHeader().setVisible(False)
        self.resultTable.verticalHeader().setVisible(False)
        self.resultTable.setEditTriggers(TableWidget.NoEditTriggers)
        self.resultTable.setShowGrid(False)

        self.separator_horiz_top = HorizontalSeparator(self)
        self.separator_vertical_middle = VerticalSeparator(self)

        self.waitingWidget = BodyLabel(self)
        self.waitingWidget.setText("Input keywords to search trainers online.")
        self.waitingWidget.setFont(Font.STANDARD_HUGE_FONT)
        self.waitingWidget.setAlignment(Qt.AlignCenter)
        self.noResultWidget = BodyLabel(self)
        self.noResultWidget.setText("Oops! No results found.")
        self.noResultWidget.setFont(Font.STANDARD_HUGE_FONT)
        self.noResultWidget.setAlignment(Qt.AlignCenter)
        self.detailImage = ImageLabel(self)
        self.detailLabel = BodyLabel(self)
        self.downloadButton = PrimaryPushButton("Download", self)
        self.downloadButton.setIcon(FIF.DOWNLOAD)
        self.visitPageButton = PushButton("Visit Website", self)
        self.visitPageButton.setIcon(FIF.LINK)

        self.hBoxLayoutTop.addWidget(self.searchLine, 1, Qt.AlignLeft)
        self.hBoxLayoutTop.addWidget(self.searchButton, 1, Qt.AlignLeft)
        self.hBoxLayoutTop.addWidget(self.resultLabel, 1, Qt.AlignLeft)
        self.hBoxLayoutTop.addWidget(self.homepageButton, 1, Qt.AlignRight)
        self.hBoxLayoutTop.addWidget(self.clearButton, 1, Qt.AlignRight)

        self.vBoxLayoutMiddle.addWidget(self.detailImage, 1)
        self.vBoxLayoutMiddle.addWidget(self.detailLabel, 1)
        self.vBoxLayoutMiddle.addWidget(self.downloadButton)
        self.vBoxLayoutMiddle.addWidget(self.visitPageButton)
        self.detailImage.setVisible(False)
        self.detailLabel.setVisible(False)
        self.downloadButton.setVisible(False)
        self.visitPageButton.setVisible(False)
        self.detailLabel.setFixedWidth(250)
        self.detailLabel.setWordWrap(True)

        self.hBoxLayoutMiddle.addWidget(self.resultTable)
        self.hBoxLayoutMiddle.addWidget(self.separator_vertical_middle)
        self.hBoxLayoutMiddle.addLayout(self.vBoxLayoutMiddle)
        self.separator_vertical_middle.setVisible(False)

        self.vBoxLayoutMain.addWidget(self.titleLabel, 1)
        self.vBoxLayoutMain.addLayout(self.hBoxLayoutTop, 1)
        self.vBoxLayoutMain.addWidget(self.separator_horiz_top)
        self.vBoxLayoutMain.addWidget(self.waitingWidget, 1)
        self.vBoxLayoutMain.addWidget(self.noResultWidget, 1)
        self.vBoxLayoutMain.addLayout(self.hBoxLayoutMiddle, 1)

        self.resultTable.setVisible(False)
        self.noResultWidget.setVisible(False)

        # keyboard.add_hotkey("enter", self.search)
        self.query_result = None
        self.detail_result = None
        self.searchButton.clicked.connect(self.search)
        self.homepageButton.clicked.connect(lambda: webbrowser.open("https://flingtrainer.com/"))
        self.clearButton.clicked.connect(self.clear)
        self.resultTable.cellClicked.connect(self.show_detail)
        self.downloadButton.clicked.connect(self.download_file)
        self.visitPageButton.clicked.connect(self.open_link)

        self.searchButton.setDisabled(True)
        self.searchLine.textChanged.connect(self.check_input)

    def check_input(self):
        if self.searchLine.text() == "" or type(self.searchLine.text()) is None:
            self.searchButton.setDisabled(True)
            print("Invalid input")
            return
        else:
            self.searchButton.setEnabled(True)

    def show_detail(self, row, col):
        self.row = row
        self.separator_vertical_middle.setVisible(True)
        self.detailLabel.setVisible(True)
        self.detailImage.setVisible(True)
        self.downloadButton.setVisible(True)
        self.visitPageButton.setVisible(True)
        self.visitPageButton.setDisabled(False)
        name = self.resultTable.item(row, 0).text()
        pic = QPixmap()
        if self.query_result[row][-1] == "COMMON":
            detailObj = crawler.Spider.Download(self.query_result[row][1])
            download_result = detailObj.run()
            if not download_result:
                self.detail_result = None
                self.downloadButton.setDisabled(True)
                self.detailLabel.setText("No download links available. Please retry or visit the website.")
                self.detailImage.setVisible(False)
                return
            self.detail_result = download_result[0]
            image_url = self.query_result[row][2]
            if image_url == crawler.BLANK_IMG:
                pic.load(self.config["resources"]["blank_img"])
            else:
                filename = self.config["resources"]["detail_img"]
                utils.Download.download_file(image_url, filename)
                pic.load(filename)
        else:
            self.detail_result = [name, self.query_result[row][1], "No Info",
                                  "No Info\n**This is an archived Trainer**", "Before 2019-05"]
            pic.load(self.config["resources"]["blank_img"])
            self.visitPageButton.setDisabled(True)
        content = f"Name: {name}\nLatest File: {self.detail_result[0]}\nSize: {self.detail_result[2]}\nDate: {self.detail_result[4]}\nDownloads: {self.detail_result[3]}"
        self.detailLabel.setText(content)
        self.detailLabel.setFont(Font.STANDARD_FONT)
        self.detailImage.setImage(pic)
        self.detailImage.setFixedSize(250, 250)
        self.check_download(name)
        self.resultTable.resizeColumnsToContents()

    def download_file(self):
        print("Downloading", self.detail_result[1])
        if ".rar" in self.detail_result[1]:
            file_name = self.config["download"]["trainer"] + self.detail_result[0] + ".rar"
        else:
            file_name = self.config["download"]["trainer"] + self.detail_result[0] + ".zip"
        print(file_name)
        utils.Download.download_file(self.detail_result[1], file_name)
        print("Download Completed.")
        # if self.config["download"]["extract"]:
        # Extract downloaded trainer
        flag = utils.Download.extract_file(file_name)
        if flag == -1:
            print("WinRAR is probably not installed or added to PATH, cannot proceed extraction.")
            os.remove(file_name)
            mb = MessageBox("Error",
                            "WinRAR is probably not installed or added to PATH, cannot proceed extraction.", self)
            mb.yesButton.setText("Download WinRAR")
            mb.cancelButton.setText("Cancel")
            if mb.exec():
                webbrowser.open("https://www.win-rar.com/download.html")
            return None
        else:
            print("Extraction Completed.")
            os.remove(file_name)

        self.register_download()

    def search(self):
        if not self.searchLine.text():
            return None
        if not NET:
            utils.Help.info("Info", "You have disabled connection for the program.")
            return None
        self.noResultWidget.setVisible(False)
        self.waitingWidget.setVisible(False)
        self.resultTable.setVisible(True)
        self.detailLabel.setVisible(False)
        self.detailImage.setVisible(False)
        self.downloadButton.setVisible(False)
        self.visitPageButton.setVisible(False)
        self.separator_vertical_middle.setVisible(False)
        self.status("Establishing connection.")
        queryObj = crawler.Spider.Search(self.searchLine.text())
        archivedQueryObj = crawler.Spider.ArchivedDownload(self.searchLine.text())
        search_result = queryObj.run()
        archived_search_result = archivedQueryObj.run()
        self.status("Data received.")
        self.query_result = search_result
        for sub_archived_result in archived_search_result:
            self.query_result.append(sub_archived_result)
        count = len(search_result)
        self.resultTable.setRowCount(count)
        self.resultTable.clear()
        self.status("Loading Data.")
        if count == 0:
            self.noResultWidget.setVisible(True)
            return None
        for row in range(count):
            item = QTableWidgetItem()
            item.setText(search_result[row][0])
            item.setFont(Font.STANDARD_FONT)
            if search_result[row][-1] == "ARCHIVED":
                item.setForeground(QBrush(Qt.gray))
            self.resultTable.setItem(row, 0, item)
        self.status(f"{count} result(s) found.")
        self.resultTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def status(self, text):
        self.resultLabel.setText(text)
        print(text)

    def clear(self):
        self.noResultWidget.setVisible(False)
        self.waitingWidget.setVisible(True)
        self.resultTable.setVisible(False)
        self.detailImage.setVisible(False)
        self.detailLabel.setVisible(False)
        self.downloadButton.setVisible(False)
        self.visitPageButton.setVisible(False)
        self.separator_vertical_middle.setVisible(False)
        self.resultTable.clear()
        self.resultTable.setRowCount(0)
        self.searchLine.setText("")
        self.resultLabel.setText("")
        self.resultLabel.setText("")
        self.query_result = None
        self.detail_result = None

    def open_link(self):
        link = self.query_result[self.row][1]
        webbrowser.open(link)

    def register_download(self):
        data = self.data
        name = self.detail_result[0]
        print("VRF: NAME:", name)
        for original_file in os.listdir(self.config["download"]["trainer"]):
            name = name.replace(".", "").replace("-FLiNG", "").replace(" ", "")
            file = original_file.replace(" ", "").replace(".", "")
            if name in file:
                self.downloadButton.setIcon(FIF.COMPLETED)
                self.downloadButton.setText("Downloaded")
                self.downloadButton.setDisabled(True)
                if self.config["cache"]["detail_image"]:
                    pic_name = self.data["config"]["resources"][
                                   "trainer_cover_folder"] + "\\" + utils.File.string_valid(
                        self.resultTable.item(self.row, 0).text()) + "-image.jpg"
                    if self.query_result[self.row][-1] == "COMMON":
                        register = [self.resultTable.item(self.row, 0).text(),
                                    data["config"]["download"]["trainer"] + original_file,
                                    time.strftime('%Y-%m-%d', time.localtime()), pic_name, "COMMON",
                                    self.query_result[self.row][1],
                                    "REGISTERED"]
                        try:
                            image_key = ("blank_img" if self.query_result[self.row][2] == crawler.BLANK_IMG
                                         else "detail_img")
                            shutil.copyfile(self.data["config"]["resources"][image_key], pic_name)
                        except FileExistsError:
                            pass
                    else:
                        register = [self.resultTable.item(self.row, 0).text(),
                                    data["config"]["download"]["trainer"] + original_file,
                                    time.strftime('%Y-%m-%d', time.localtime()), "NONE",
                                    "ARCHIVED", "NONE",
                                    "REGISTERED"]
                    data["files"]["trainers"].append(register)
                    print("Registered:", register)
                    utils.Data.json_write("data/data.json", data)
                return None
        self.downloadButton.setIcon(FIF.DOWNLOAD)
        self.downloadButton.setText("Download")
        self.downloadButton.setDisabled(False)

    def check_download(self, name):
        self.data = utils.Data.json_read("data/data.json")
        for downloaded in self.data["files"]["trainers"]:
            if name == downloaded[0]:
                self.downloadButton.setIcon(FIF.COMPLETED)
                self.downloadButton.setText("Downloaded")
                self.downloadButton.setDisabled(True)
                return True
        self.downloadButton.setIcon(FIF.DOWNLOAD)
        self.downloadButton.setText("Download")
        self.downloadButton.setDisabled(False)
        return False
