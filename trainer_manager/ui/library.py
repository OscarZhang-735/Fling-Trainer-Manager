"""ui.library: extracted application components."""

import subprocess
from functools import partial
from pathlib import Path
import shutil
import os
import webbrowser
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QHeaderView, QTableWidgetItem
from qfluentwidgets import isDarkTheme, MessageBox, BodyLabel, PushButton, TableWidget, PrimaryPushButton, HorizontalSeparator, VerticalSeparator, TitleLabel
from qfluentwidgets import FluentIcon as FIF
from trainer_manager import services as utils
from trainer_manager.ui.common import WorkerThread
from trainer_manager.runtime import Font
from trainer_manager.ui.preview import ImagePreview
from trainer_manager.ui.transfers import DownloadSession
from trainer_manager.services.transfers import update_trainer, register_trainer, remember_release
from trainer_manager.services.releases import installed_release
from trainer_manager.services.repositories import refresh_repository


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
        self.detailImage = ImagePreview(self, dark=isDarkTheme())
        self.detailLabel = BodyLabel(self)
        self.runButton = PrimaryPushButton("Launch", self)
        self.runButton.setIcon(FIF.PLAY)
        self.visitPageButton = PushButton("Visit Website", self)
        self.visitPageButton.setIcon(FIF.LINK)
        self.deleteButton = PushButton("Delete", self)
        self.deleteButton.setIcon(FIF.CLOSE)
        self.updateButton = PushButton("Update", self)
        self.updateButton.setIcon(FIF.UP)
        self._transfer = DownloadSession(self.updateButton, self)

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
        link = self.file_name_list[self.row][5]
        if link != "NONE":
            webbrowser.open(link)

    def open_folder(self):
        path = utils.Data.load_config()["config"]["download"]["trainer"]
        path = os.path.normpath(path)
        print(path)
        subprocess.run(f'explorer "{path}"')

    def remove_file(self):
        mbox = MessageBox("Warning", "Are you sure you want to delete this file? This operation is irreversible.", self)
        if mbox.exec():
            os.remove(self.current_exe)
            if (self.file_name_list[self.row][-3] == "COMMON"
                    and os.path.isfile(self.file_name_list[self.row][3])):
                os.remove(self.file_name_list[self.row][3])
            if self.file_name_list[self.row][-1] == "REGISTERED":
                del self.file_name_list[self.row]
                self.data["files"]["trainers"] = self.file_name_list
                utils.Data.json_write("data/data.json", self.data)
            else:
                del self.file_name_list[self.row]
            self.table_default()

    def update_file(self):
        if self._transfer.busy or self.row is None:
            return
        current = self.file_name_list[self.row][:]
        destination = utils.Data.load_config()["config"]["download"]["trainer"]
        self._update_source = [current[0], current[5], "", current[-3]]
        self._update_cover = current[3]
        for widget in (self.resultTable, self.clearButton, self.deleteButton, self.runButton, self.updateButton):
            widget.setEnabled(False)

        task = partial(update_trainer, current, destination)

        self._transfer.start(task, self._update_success, self._update_error, self._update_finished)

    def _update_success(self, result):
        if result.up_to_date:
            remember_release(self._update_source, result.release)
        else:
            cover = "NONE"
            old_cover = Path(self._update_cover)
            if old_cover.is_file():
                target = Path(result.executable).parent / "preview.jpg"
                try:
                    if old_cover.resolve() != target.resolve():
                        shutil.copyfile(old_cover, target)
                    cover = str(target)
                except OSError:
                    pass  # A missing cover must not prevent registering the new trainer.
            register_trainer(self._update_source, result.executable, cover, result.release)
        self._was_up_to_date = result.up_to_date
        self.current_exe = result.executable
        self.updateButton.setText("Up to date" if self._was_up_to_date else "Updated")
        self.updateButton.setToolTip(result.executable)
        self.detailLabel.setText("Already up to date." if result.up_to_date else "Update completed.\n" + result.executable)

    def _update_error(self, error):
        self.updateButton.setText("Retry update")
        self.detailLabel.setText("Update failed:\n" + error)

    def _update_finished(self, succeeded):
        for widget in (self.resultTable, self.clearButton, self.deleteButton, self.runButton, self.updateButton):
            widget.setEnabled(True)
        if succeeded:
            self.table_default()
            for row, record in enumerate(self.file_name_list):
                if record[0] == self._update_source[0] and record[-3] == self._update_source[-1]:
                    self.resultTable.selectRow(row)
                    self.show_detail(row, 0)
                    self.updateButton.setText("Up to date" if self._was_up_to_date else "Updated")
                    self.updateButton.setEnabled(False)
                    self.resultLabel.setText("Already up to date. No download needed." if self._was_up_to_date
                                             else "Update completed.")
                    break

    def table_default(self):
        if self._transfer.busy:
            return
        try:
            self.data = refresh_repository()
        except (OSError, ValueError) as error:
            self.resultLabel.setText("Unable to read trainer repository: " + str(error))
            return
        self.row = None
        self.current_exe = None
        self.separator_vertical_middle.setVisible(False)
        self.detailImage.setVisible(False)
        self.detailLabel.setVisible(False)
        self.runButton.setVisible(False)
        self.visitPageButton.setVisible(False)
        self.deleteButton.setVisible(False)
        self.updateButton.setVisible(False)
        self.resultTable.setVisible(True)
        file_name_list = [row[:] for row in self.data["files"]["trainers"]]
        if self.data["config"]["library"]["filter"] == "REGISTERED_ONLY":
            file_name_list = [row for row in file_name_list if row[-1] == "REGISTERED"]
        self.file_name_list = file_name_list
        self.noResultWidget.setVisible(False)
        self.fill_table(file_name_list)

    def show_detail(self, row, col):
        if self._transfer.busy:
            return
        self.row = row
        self.separator_vertical_middle.setVisible(True)
        self.detailLabel.setVisible(True)
        self.detailImage.setVisible(True)
        self.runButton.setVisible(True)
        self.visitPageButton.setVisible(True)
        self.visitPageButton.setDisabled(False)
        self.updateButton.setVisible(True)
        self.updateButton.setText("Update")
        self.updateButton.setDisabled(False)
        self.deleteButton.setVisible(True)
        self.detailImage.clear()
        if self.file_name_list[row][-3] == "COMMON":
            pic_file = self.file_name_list[row][3]
            self.detailImage.loadFile(pic_file)
            content = f"Name: {self.file_name_list[row][0]}\nDownload Time: {self.file_name_list[row][2]}"
        elif self.file_name_list[row][-3] == "ARCHIVED":
            content = f"File: {self.file_name_list[row][0]}\nDownload Time: {self.file_name_list[row][2]}\n**This is an archived Trainer**"
            self.detailImage.loadFile(self.data["config"]["resources"]["blank_img"])
            self.visitPageButton.setDisabled(True)
            self.updateButton.setDisabled(True)
        else:
            content = f"File: {self.file_name_list[row][0]} \n**No online source is known for this local file**"
            self.visitPageButton.setDisabled(True)
            self.updateButton.setDisabled(True)
        version = installed_release(self.data, self.file_name_list[row])
        if version:
            content += "\nVersion: " + version.get("version", version.get("name", "Unknown"))
            content += "\nRelease date: " + version.get("date", "")
        self.detailLabel.setText(content)
        self.detailLabel.setFont(Font.STANDARD_FONT)
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
