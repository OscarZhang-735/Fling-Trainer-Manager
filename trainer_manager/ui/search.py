"""ui.search: extracted application components."""

import os
from functools import partial
from pathlib import Path
import webbrowser
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QStandardItemModel
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QHeaderView, QTableWidgetItem
from qfluentwidgets import isDarkTheme, BodyLabel, PushButton, TableWidget, LineEdit, PrimaryPushButton, HorizontalSeparator, VerticalSeparator, TitleLabel
from qfluentwidgets import FluentIcon as FIF
from trainer_manager.services import crawler
from trainer_manager import services as utils
from trainer_manager.runtime import Font
from trainer_manager.ui.preview import ImagePreview
from trainer_manager.ui.transfers import DownloadSession
from trainer_manager.services.transfers import install_latest, register_trainer


class SearchWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # self.resize(400, 400)
        self.name = None
        self.row = None
        self.config = utils.Data.load_config("data/data.json")["config"]
        self.data = utils.Data.load_config("data/data.json")
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
        self.searchLine.setPlaceholderText("Search FLiNG and Archive")
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
        self.detailImage = ImagePreview(self, dark=isDarkTheme())
        self.detailLabel = BodyLabel(self)
        self.downloadButton = PrimaryPushButton("Download", self)
        self.downloadButton.setIcon(FIF.DOWNLOAD)
        self._transfer = DownloadSession(self.downloadButton, self)
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
        if not self.searchLine.text().strip():
            self.searchButton.setDisabled(True)
            print("Invalid input")
            return
        else:
            self.searchButton.setEnabled(True)

    def show_detail(self, row, col):
        if self._transfer.busy:
            return
        self.row = row
        self.separator_vertical_middle.setVisible(True)
        self.detailLabel.setVisible(True)
        self.detailImage.setVisible(True)
        self.downloadButton.setVisible(True)
        self.visitPageButton.setVisible(True)
        self.visitPageButton.setDisabled(False)
        name = self.resultTable.item(row, 0).text()
        self.detailImage.clear()
        if self.query_result[row][-1] == "COMMON":
            detailObj = crawler.Spider.Download(self.query_result[row][1])
            image_url = detailObj.image_url
            self.query_result[row][2] = image_url
            if image_url != crawler.BLANK_IMG:
                self.detailImage.loadUrl(image_url)
            latest = detailObj.latest_standalone()
            if latest is None:
                self.detail_result = None
                self.downloadButton.setDisabled(True)
                self.detailLabel.setText("No standalone download available. Please retry or visit the website.")
                return
            self.detail_result = latest
        else:
            self.detail_result = [name, self.query_result[row][1], "No Info",
                                  "No Info\n**This is an archived Trainer**", "Before 2019-05"]
            self.detailImage.loadFile(self.config["resources"]["blank_img"])
            self.visitPageButton.setDisabled(True)
        content = f"Name: {name}\nLatest File: {self.detail_result[0]}\nSize: {self.detail_result[2]}\nDate: {self.detail_result[4]}\nDownloads: {self.detail_result[3]}"
        self.detailLabel.setText(content)
        self.detailLabel.setFont(Font.STANDARD_FONT)
        self.check_download(name)
        self.resultTable.resizeColumnsToContents()

    def download_file(self):
        if self._transfer.busy or not self.detail_result or self.row is None:
            return
        self.config = utils.Data.load_config()["config"]
        self._download_source = self.query_result[self.row][:]
        self._set_download_busy(True)
        task = partial(install_latest, self._download_source, self.config["download"]["trainer"],
                       self.config["download"]["extract"])
        self._transfer.start(task, self._download_success, self._download_error, self._download_finished)

    def _set_download_busy(self, busy):
        for widget in (self.resultTable, self.clearButton, self.searchLine, self.searchButton):
            widget.setEnabled(not busy)
        self.downloadButton.setEnabled(not busy)
        if not busy:
            self.check_input()

    def _download_success(self, result):
        if result.executable:
            self.register_download(result.executable, result.release)
            self.downloadButton.setText("Downloaded")
            self.status("Download completed and added to library.")
        else:
            self.downloadButton.setText("Archive saved")
            self.status("Archive saved. Automatic extraction is disabled.")
            self.detailLabel.setText("Archive saved to:\n" + result.archive)
        self.downloadButton.setToolTip(result.executable or result.archive)
        self.downloadButton.setIcon(FIF.COMPLETED)

    def _download_error(self, error):
        self.downloadButton.setText("Retry download")
        self.downloadButton.setIcon(FIF.DOWNLOAD)
        self.detailLabel.setText("Download failed:\n" + error)
        self.status("Download failed. You can retry.")

    def _download_finished(self, succeeded):
        self._set_download_busy(False)
        self.downloadButton.setEnabled(not succeeded)

    def search(self):
        if self._transfer.busy:
            return
        if not self.searchLine.text().strip():
            return None
        if not utils.Data.load_config()["config"]["program"]["connection_allow"]:
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
        self.detail_result = None
        self.row = None
        self.status("Searching All Trainers and Archive.")
        queryObj = crawler.Spider.SearchAll(self.searchLine.text())
        search_result = queryObj.run()
        self.status("Data received.")
        self.query_result = search_result
        count = len(search_result)
        self.resultTable.setRowCount(count)
        self.resultTable.clear()
        self.status("Loading Data.")
        result_status = f"{count} result(s) found."
        if queryObj.failed_sources:
            result_status += " Unavailable: " + ", ".join(queryObj.failed_sources) + ". Please retry."
        self.status(result_status)
        if count == 0:
            self.noResultWidget.setText("Search incomplete. Please retry." if queryObj.failed_sources
                                        else "Oops! No results found.")
            self.noResultWidget.setVisible(True)
            return None
        for row in range(count):
            item = QTableWidgetItem()
            item.setText(search_result[row][0])
            item.setFont(Font.STANDARD_FONT)
            if search_result[row][-1] == "ARCHIVED":
                item.setForeground(QBrush(Qt.gray))
            self.resultTable.setItem(row, 0, item)
        self.resultTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def status(self, text):
        self.resultLabel.setText(text)
        print(text)

    def clear(self):
        if self._transfer.busy:
            return
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

    def register_download(self, executable, release):
        cover = "NONE"
        if (self._download_source[-1] == "COMMON" and self.config["cache"]["detail_image"]
                and not self.detailImage.image.isNull()):
            cover_path = str(Path(executable).parent / "preview.jpg")
            if self.detailImage.image.save(cover_path, "JPG"):
                cover = cover_path
        register_trainer(self._download_source, executable, cover, release)
        self.data = utils.Data.load_config()

    def check_download(self, name):
        self.data = utils.Data.load_config("data/data.json")
        for downloaded in self.data["files"]["trainers"]:
            if name == downloaded[0] and os.path.isfile(downloaded[1]):
                self.downloadButton.setIcon(FIF.COMPLETED)
                self.downloadButton.setText("Downloaded")
                self.downloadButton.setDisabled(True)
                return True
        self.downloadButton.setIcon(FIF.DOWNLOAD)
        self.downloadButton.setText("Download")
        self.downloadButton.setDisabled(False)
        return False

    def refresh_repository_state(self):
        self.data = utils.Data.load_config()
        self.config = self.data["config"]
        if self.row is not None and self.query_result and self.detail_result:
            self.check_download(self.query_result[self.row][0])
