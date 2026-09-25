"""ui.library: extracted application components."""

import subprocess
import os
import time
import webbrowser
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QPixmap
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QHeaderView, QTableWidgetItem
from qfluentwidgets import MessageBox, ImageLabel, BodyLabel, PushButton, TableWidget, PrimaryPushButton, HorizontalSeparator, VerticalSeparator, TitleLabel
from qfluentwidgets import FluentIcon as FIF
from trainer_manager.services import crawler
from trainer_manager import services as utils
from trainer_manager.ui.common import Error
from trainer_manager.ui.common import WorkerThread
from trainer_manager.runtime import Font


class LibraryWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # self.resize(400, 400)
        self.file_name_list = None
        self.row = None
        self.current_exe = None
        self.data = utils.Data.load_config("data/data.json")
        self.setObjectName("Library")
        self.vBoxLayoutMain = QVBoxLayout(self)
        self.vBoxLayoutMiddle = QVBoxLayout(self)
        self.hBoxLayoutMiddle = QHBoxLayout(self)
        self.hBoxLayoutTop = QHBoxLayout(self)
        self.vBoxLayoutMain.setContentsMargins(30, 60, 30, 50)
        self.vBoxLayoutMain.setSpacing(30)
        self.hBoxLayoutTop.setSpacing(20)
        self.vBoxLayoutMiddle.setSpacing(10)

        self.titleLabel = TitleLabel("Library", self)
        self.titleLabel.setFixedHeight(40)
        """
        self.searchLine = LineEdit(self)
        self.searchLine.setAlignment(Qt.AlignCenter)
        self.searchLine.setFixedWidth(300)
        self.searchLine.setPlaceholderText("Search in Local Library")
        self.searchLine.setClearButtonEnabled(True)
        self.searchButton = PrimaryPushButton(self)
        self.searchButton.setIcon(FIF.SEARCH)
        self.searchButton.setText("Search")
        """

        self.clearButton = PushButton(self)
        self.clearButton.setIcon(FIF.UPDATE)
        self.clearButton.setText("Refresh")
        self.folderButton = PushButton(self)
        self.folderButton.setIcon(FIF.FOLDER)
        self.folderButton.setText("Browse the Folder")

        self.resultLabel = BodyLabel(self)
        self.resultLabel.setText("")
        self.resultLabel.setFont(Font.STANDARD_MIDDLE_FONT)

        self.resultTable = TableWidget(self)
        self.resultTable.setColumnCount(2)
        self.resultTable.horizontalHeader().setVisible(False)
        self.resultTable.verticalHeader().setVisible(False)
        self.resultTable.setEditTriggers(TableWidget.NoEditTriggers)
        self.resultTable.setShowGrid(False)

        self.separator_horiz_top = HorizontalSeparator(self)
        self.separator_vertical_middle = VerticalSeparator(self)

        self.waitingWidget = BodyLabel(self)
        self.waitingWidget.setText("Input a keyword to search")
        self.waitingWidget.setFont(Font.STANDARD_HUGE_FONT)
        self.waitingWidget.setAlignment(Qt.AlignCenter)
        self.noResultWidget = BodyLabel(self)
        self.noResultWidget.setText("Oops! No results found.")
        self.noResultWidget.setFont(Font.STANDARD_HUGE_FONT)
        self.noResultWidget.setAlignment(Qt.AlignCenter)
        self.detailImage = ImageLabel(self)
        self.detailLabel = BodyLabel(self)
        self.runButton = PrimaryPushButton("Launch", self)
        self.runButton.setIcon(FIF.PLAY)
        self.visitPageButton = PushButton("Visit Website", self)
        self.visitPageButton.setIcon(FIF.LINK)
        self.deleteButton = PushButton("Delete", self)
        self.deleteButton.setIcon(FIF.CLOSE)
        self.updateButton = PushButton("Update", self)
        self.updateButton.setIcon(FIF.UP)

        # self.hBoxLayoutTop.addWidget(self.searchLine, 1, Qt.AlignLeft)
        # self.hBoxLayoutTop.addWidget(self.searchButton, 1, Qt.AlignLeft)
        self.hBoxLayoutTop.addWidget(self.resultLabel, 5, Qt.AlignLeft)
        self.hBoxLayoutTop.addWidget(self.folderButton, 1, Qt.AlignRight)
        self.hBoxLayoutTop.addWidget(self.clearButton, 1, Qt.AlignRight)

        self.vBoxLayoutMiddle.addWidget(self.detailImage, 1)
        self.vBoxLayoutMiddle.addWidget(self.detailLabel, 1)
        self.vBoxLayoutMiddle.addWidget(self.runButton)
        self.vBoxLayoutMiddle.addWidget(self.visitPageButton)
        self.vBoxLayoutMiddle.addWidget(self.deleteButton)
        self.vBoxLayoutMiddle.addWidget(self.updateButton)
        self.detailImage.setVisible(False)
        self.detailLabel.setVisible(False)
        self.runButton.setVisible(False)
        self.deleteButton.setVisible(False)
        self.updateButton.setVisible(False)
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

        self.resultTable.cellClicked.connect(self.show_detail)
        self.resultTable.cellDoubleClicked.connect(self.run_trainer)
        self.folderButton.clicked.connect(self.open_folder)
        self.clearButton.clicked.connect(self.table_default)
        self.runButton.clicked.connect(self.run_trainer)
        self.deleteButton.clicked.connect(self.remove_file)
        self.visitPageButton.clicked.connect(self.open_link)
        self.updateButton.clicked.connect(self.update_file)
        # self.resultTable.setVisible(False)
        self.table_default()
        self.noResultWidget.setVisible(False)

    def run_trainer(self):
        self.trainer_thread = WorkerThread(self.current_exe)
        self.trainer_thread.finished.connect(lambda: print("Trainer quited"))
        self.trainer_thread.start()

    def open_link(self):
        link = self.data["files"]["trainers"][self.row][4]
        if link != "NONE":
            webbrowser.open(link)

    def open_folder(self):
        path = self.data["config"]["download"]["trainer"]
        path = os.path.normpath(path)
        print(path)
        subprocess.run(f'explorer "{path}"')

    def remove_file(self):
        mbox = MessageBox("Warning", "Are you sure you want to delete this file? This operation is irreversible.", self)
        if mbox.exec():
            os.remove(self.current_exe)
            if self.file_name_list[self.row][-3] == "COMMON":
                os.remove(self.file_name_list[self.row][3])
            if self.file_name_list[self.row][-1] == "REGISTERED":
                del self.file_name_list[self.row]
                self.data["files"]["trainers"] = self.file_name_list
                utils.Data.json_write("data/data.json", self.data)
            else:
                del self.file_name_list[self.row]
            self.table_default()

    def update_file(self):
        url = self.file_name_list[self.row][5]
        root_folder = self.data["config"]["download"]["trainer"]
        queryObj = crawler.Spider.Download(url)
        res = queryObj.run()
        if res:
            print("Removing: ", self.current_exe)
            os.remove(self.file_name_list[self.row][1])  # Remove previous file
            file_name = root_folder + res[0][0] + ".zip"
            print("Downloading: ", file_name)
            utils.Download.download_file(res[0][1], file_name)  # Download new file
            exe = utils.Download.extract_file(file_name)
            if exe == -1:
                Error.FileError.ExtractionError()
            os.remove(file_name)  # Remove zip file after extraction.
            self.data["files"]["trainers"][self.row][1] = root_folder + exe  # Update new exe name.
            self.data["files"]["trainers"][self.row][2] = time.strftime('%Y-%m-%d',
                                                                        time.localtime())  # Update new download time
            utils.Data.json_write("data/data.json", self.data)
            print(f"Registration of <{self.file_name_list[self.row][0]}> updated.")
            mb = MessageBox("Notification", f"{self.file_name_list[self.row][0]} is now up to date.", self)
            mb.cancelButton.hide()
            if mb.exec():
                pass

        else:
            mb = MessageBox("Error", f"Download links of {self.file_name_list[self.row][0]} are not found.", self)
            mb.yesButton.setText('Report Issue')
            mb.cancelButton.setText('Cancel')
            if mb.exec():
                utils.Help.report("Issue Report",
                                  f"Resource Unavailable: Cannot reach download resource of <{self.file_name_list[self.row][0]}>",
                                  time.asctime())

    def table_default(self):
        self.data = utils.Data.load_config("data/data.json")
        self.separator_vertical_middle.setVisible(False)
        self.detailImage.setVisible(False)
        self.detailLabel.setVisible(False)
        self.runButton.setVisible(False)
        self.visitPageButton.setVisible(False)
        self.deleteButton.setVisible(False)
        self.updateButton.setVisible(False)
        self.resultTable.setVisible(True)
        file_name_list = self.data["files"]["trainers"]
        self.file_name_list = file_name_list
        if self.data["config"]["library"]["filter"] == "REGISTERED_ONLY":
            if len(file_name_list) <= 0:
                self.resultTable.setVisible(False)
                self.waitingWidget.setVisible(True)
                self.waitingWidget.setText("No downloaded trainers found.")
                return None
        else:
            names = []
            for file_info in file_name_list:
                names.append(file_info[1].split("\\")[-1])
            for temp_file in os.listdir(self.data["config"]["download"]["trainer"]):
                if temp_file not in names:
                    file_name_list.append([
                        "[UNREGISTERED] " + temp_file,
                        self.data["config"]["download"]["trainer"] + temp_file,
                        "UNKNOWN",
                        "UNKNOWN",
                        "UNKNOWN",
                        "UNKNOWN",
                        "UNREGISTERED"
                    ])
        self.fill_table(file_name_list)

    def show_detail(self, row, col):
        self.row = row
        self.separator_vertical_middle.setVisible(True)
        self.detailLabel.setVisible(True)
        self.detailImage.setVisible(True)
        self.runButton.setVisible(True)
        self.visitPageButton.setVisible(True)
        self.visitPageButton.setDisabled(False)
        self.updateButton.setVisible(True)
        self.updateButton.setDisabled(False)
        self.deleteButton.setVisible(True)
        pic = QPixmap()
        if self.file_name_list[row][-3] == "COMMON":
            pic_file = self.file_name_list[row][3]
            pic.load(pic_file)
            content = f"Name: {self.file_name_list[row][0]}\nDownload Time: {self.file_name_list[row][2]}"
        elif self.file_name_list[row][-3] == "ARCHIVED":
            content = f"File: {self.file_name_list[row][0]}\nDownload Time: {self.file_name_list[row][2]}\n**This is an archived Trainer**"
            pic.load(self.data["config"]["resources"]["blank_img"])
            self.visitPageButton.setDisabled(True)
            self.updateButton.setDisabled(True)
        else:
            content = f"File: {self.file_name_list[row][0]} \n**This file is not registered**"
            pic.load(self.data["config"]["resources"]["blank_img"])
            self.visitPageButton.setDisabled(True)
            self.updateButton.setDisabled(True)
        self.detailLabel.setText(content)
        self.detailLabel.setFont(Font.STANDARD_FONT)
        self.detailImage.setImage(pic)
        self.detailImage.setFixedSize(250, 250)
        self.current_exe = self.file_name_list[row][1]
        self.resultTable.resizeColumnsToContents()

    def fill_table(self, table):
        count = len(table)
        self.resultLabel.setText(f"There are {count} trainer(s) in your library.")
        self.waitingWidget.setVisible(False)
        self.resultTable.setRowCount(count)
        self.resultTable.clear()
        if count == 0:
            self.noResultWidget.setVisible(True)
            return None
        for row in range(count):
            item = QTableWidgetItem()
            item.setText(table[row][0])
            item.setFont(Font.STANDARD_FONT)
            if table[row][-3] != "COMMON":
                item.setForeground(QBrush(Qt.gray))
            if table[row][-1] != "REGISTERED":
                item.setForeground(QBrush(Qt.red))
            self.resultTable.setItem(row, 0, item)
        self.resultTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
