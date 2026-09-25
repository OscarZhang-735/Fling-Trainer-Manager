"""ui.games: extracted application components."""

import shutil
import subprocess
import os
import time
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QHeaderView, QTableWidgetItem, QTableWidget, QFileDialog
from qfluentwidgets import MessageBox, ImageLabel, BodyLabel, PushButton, TableWidget, LineEdit, PrimaryPushButton, HorizontalSeparator, VerticalSeparator, MessageBoxBase, SubtitleLabel, TitleLabel, ComboBox
from qfluentwidgets import FluentIcon as FIF
from trainer_manager import services as utils
from trainer_manager.ui.common import WorkerThread
from trainer_manager.runtime import Font


class GameWidget(QFrame):
    class CreateNewGameMessageBox(MessageBoxBase):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.titleLabel = SubtitleLabel('Create New Local-Game Configuration', self)
            self.nameLineEdit = LineEdit(self)
            self.nameLineEdit.setPlaceholderText('Name')
            self.nameLineEdit.setClearButtonEnabled(True)
            self.gameLocationLineEdit = LineEdit(self)
            self.gameLocationLineEdit.setPlaceholderText('Game Location')
            self.gameLocationLineEdit.setClearButtonEnabled(True)
            self.gameLocationButton = PushButton(self)
            self.gameLocationButton.setText("Select")
            self.coverLocationLineEdit = LineEdit(self)
            self.coverLocationLineEdit.setPlaceholderText('Cover Location [optional]')
            self.coverLocationLineEdit.setClearButtonEnabled(True)
            self.coverLocationButton = PushButton(self)
            self.coverLocationButton.setText("Select")
            self.categoryCombo = ComboBox(self)
            cats = utils.Data.load_config("data/data.json")["files"]["game_cats"]
            self.categoryCombo.addItems(cats)
            self.categoryCombo.removeItem(cats.index("ALL"))
            self.infoLineEdit = LineEdit(self)
            self.infoLineEdit.setPlaceholderText('Introduction [optional]')
            self.infoLineEdit.setClearButtonEnabled(True)

            self.gameLocationLayout = QHBoxLayout(self)
            self.gameLocationLayout.addWidget(self.gameLocationLineEdit, 3)
            self.gameLocationLayout.addWidget(self.gameLocationButton, 1)
            self.coverLocationLayout = QHBoxLayout(self)
            self.coverLocationLayout.addWidget(self.coverLocationLineEdit, 3)
            self.coverLocationLayout.addWidget(self.coverLocationButton, 1)

            # add widget to view layout
            self.viewLayout.addWidget(self.titleLabel)
            self.viewLayout.addWidget(self.nameLineEdit)
            self.viewLayout.addLayout(self.gameLocationLayout)
            self.viewLayout.addLayout(self.coverLocationLayout)
            self.viewLayout.addWidget(self.infoLineEdit)
            self.viewLayout.addWidget(self.categoryCombo)

            self.yesButton.setText('Confirm')
            self.cancelButton.setText('Cancel')
            self.yesButton.setDisabled(True)
            self.widget.setMinimumWidth(350)

            self.nameLineEdit.textChanged.connect(self.check_input)
            self.gameLocationLineEdit.textChanged.connect(self.check_input)
            self.gameLocationButton.clicked.connect(self._select_game_path)
            self.coverLocationButton.clicked.connect(self._select_cover_path)

        def check_input(self):
            if self.nameLineEdit.text() != "" and self.gameLocationLineEdit.text() != "":
                self.yesButton.setEnabled(True)
            else:
                self.yesButton.setDisabled(True)

        def _select_game_path(self):
            w = QFileDialog(self)
            w.setWindowTitle("Select a file")
            w.setFileMode(QFileDialog.AnyFile)
            w.setDirectory(os.getcwd())
            w.setNameFilter("Executable File (*.exe)")
            file_path = w.exec()
            if file_path and w.selectedFiles():
                path = w.selectedFiles()[0]
                print("File:", path)
                self.gameLocationLineEdit.setText(str(path))
                self.nameLineEdit.setText(str(path).split("/")[-1].removesuffix(".exe"))

        def _select_cover_path(self):
            w = QFileDialog(self)
            w.setWindowTitle("Select a file")
            w.setFileMode(QFileDialog.AnyFile)
            w.setDirectory(os.getcwd())
            w.setNameFilter("Image File (*.*)")
            file_path = w.exec()
            if file_path and w.selectedFiles():
                path = w.selectedFiles()[0]
                print("File:", path)
                self.coverLocationLineEdit.setText(str(path))

    class ManageCategoriesMessageBox(MessageBoxBase):
        class NamingBox(MessageBoxBase):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.titleLabel = SubtitleLabel(self)
                self.titleLabel.setText("New Category")
                self.nameLineEdit = LineEdit(self)
                self.nameLineEdit.setPlaceholderText("Name of the category")
                self.viewLayout.addWidget(self.titleLabel)
                self.viewLayout.addWidget(self.nameLineEdit)
                self.widget.setMinimumWidth(300)

        def __init__(self, parent=None):
            super().__init__(parent)
            self.cats = []
            self.data = utils.Data.load_config("data/data.json")
            self.titleLabel = SubtitleLabel('Manage Your Categories', self)
            self.categoryTable = TableWidget(self)
            self.categoryTable.horizontalHeader().setVisible(False)
            self.categoryTable.verticalHeader().setVisible(False)
            self.categoryTable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            self.addNewCategoryButton = PrimaryPushButton("Add a Category")
            self.addNewCategoryButton.setIcon(FIF.FOLDER_ADD)
            self.deleteCategoryButton = PushButton("Delete a Category")
            self.deleteCategoryButton.setIcon(FIF.DELETE)
            self.yesButton.setText('OK')
            self.cancelButton.hide()

            # add widget to view layout
            self.viewLayout.addWidget(self.titleLabel)
            self.viewLayout.addWidget(self.categoryTable)
            self.viewLayout.addWidget(self.addNewCategoryButton)
            self.viewLayout.addWidget(self.deleteCategoryButton)
            self.categoryTable.cellClicked.connect(lambda: self.deleteCategoryButton.setEnabled(True))
            self.deleteCategoryButton.clicked.connect(self.delete_category)
            self.addNewCategoryButton.clicked.connect(self.add_new_category)
            self.widget.setMinimumWidth(500)
            self.deleteCategoryButton.setDisabled(True)
            self.category_default()

        def category_default(self):
            self.cats = utils.Data.load_config("data/data.json")["files"]["game_cats"]
            self.cats.remove("ALL")
            self.cats.remove("UNCATEGORIZED")
            count = len(self.cats)
            self.categoryTable.setRowCount(count)
            self.categoryTable.setColumnCount(1)
            self.categoryTable.clear()
            for row in range(count):
                item = QTableWidgetItem()
                item.setText(self.cats[row])
                item.setFont(Font.STANDARD_FONT)
                self.categoryTable.setItem(row, 0, item)
            self.categoryTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        def delete_category(self):
            w = MessageBox("Confirmation", "Are you sure you want to delete the category?", self)
            if w.exec():
                games = self.data["files"]["games"]
                count = 0
                cat = self.categoryTable.currentItem().text()
                for game in games:
                    if game[-1] == cat:
                        self.data["files"]["games"][count][-1] = "UNCATEGORIZED"
                    count += 1
                self.data["files"]["game_cats"].remove(cat)
                utils.Data.json_write("data/data.json", self.data)
                self.category_default()

        def add_new_category(self):
            w = self.NamingBox(self)
            if w.exec():
                name = w.nameLineEdit.text()
            else:
                return None
            self.categoryTable.insertRow(self.categoryTable.rowCount())
            item = QTableWidgetItem()
            item.setText(name)
            self.categoryTable.setItem(self.categoryTable.rowCount(), 0, item)
            self.data["files"]["game_cats"].append(name)
            utils.Data.json_write("data/data.json", self.data)
            self.category_default()

    class EditGameMessageBox(MessageBoxBase):
        def __init__(self, row, parent=None):
            super().__init__(parent)
            self.data = utils.Data.load_config("data/data.json")
            self.titleLabel = SubtitleLabel('Edit Game Configuration', self)
            self.nameLineEdit = LineEdit(self)
            self.nameLineEdit.setText(self.data["files"]["games"][row][0])
            self.nameLineEdit.setClearButtonEnabled(True)
            self.gameLocationLineEdit = LineEdit(self)
            self.gameLocationLineEdit.setText(self.data["files"]["games"][row][1])
            self.gameLocationLineEdit.setClearButtonEnabled(True)
            self.gameLocationButton = PushButton(self)
            self.gameLocationButton.setText("Select")
            self.coverLocationLineEdit = LineEdit(self)
            self.coverLocationLineEdit.setPlaceholderText('New Cover Location')
            self.coverLocationLineEdit.setClearButtonEnabled(True)
            self.coverLocationButton = PushButton(self)
            self.coverLocationButton.setText("Select")
            self.coverClearButton = PushButton(self)
            self.coverClearButton.setText("Clear")
            self.categoryCombo = ComboBox(self)
            cats = utils.Data.load_config("data/data.json")["files"]["game_cats"]
            self.categoryCombo.addItems(cats)
            self.categoryCombo.removeItem(cats.index("ALL"))
            self.categoryCombo.setCurrentText(self.data["files"]["games"][row][-1])
            self.infoLineEdit = LineEdit(self)
            if self.data["files"]["games"][row][3]:
                self.infoLineEdit.setText(self.data["files"]["games"][row][3])
            else:
                self.infoLineEdit.setPlaceholderText("Introduction [optional]")
            self.infoLineEdit.setClearButtonEnabled(True)

            self.gameLocationLayout = QHBoxLayout(self)
            self.gameLocationLayout.addWidget(self.gameLocationLineEdit, 3)
            self.gameLocationLayout.addWidget(self.gameLocationButton, 1)
            self.coverLocationLayout = QHBoxLayout(self)
            self.coverLocationLayout.addWidget(self.coverLocationLineEdit, 4)
            self.coverLocationLayout.addWidget(self.coverLocationButton, 1)
            self.coverLocationLayout.addWidget(self.coverClearButton, 1)

            # add widget to view layout
            self.viewLayout.addWidget(self.titleLabel)
            self.viewLayout.addWidget(self.nameLineEdit)
            self.viewLayout.addLayout(self.gameLocationLayout)
            self.viewLayout.addLayout(self.coverLocationLayout)
            self.viewLayout.addWidget(self.infoLineEdit)
            self.viewLayout.addWidget(self.categoryCombo)

            self.yesButton.setText('Confirm')
            self.cancelButton.setText('Cancel')
            self.widget.setMinimumWidth(450)

            self.nameLineEdit.textChanged.connect(self.check_input)
            self.gameLocationLineEdit.textChanged.connect(self.check_input)
            self.gameLocationButton.clicked.connect(self._select_game_path)
            self.coverLocationButton.clicked.connect(self._select_cover_path)
            self.coverClearButton.clicked.connect(lambda: self.coverLocationLineEdit.setText("CLEAR"))

        def check_input(self, text):
            if self.nameLineEdit.text() != "" and self.gameLocationLineEdit.text() != "":
                self.yesButton.setEnabled(True)
            else:
                self.yesButton.setDisabled(True)

        def _select_game_path(self):
            w = QFileDialog(self)
            w.setWindowTitle("Select a file")
            w.setFileMode(QFileDialog.AnyFile)
            w.setDirectory(os.getcwd())
            w.setNameFilter("Executable File (*.exe)")
            file_path = w.exec()
            if file_path and w.selectedFiles():
                path = w.selectedFiles()[0]
                print("File:", path)
                self.gameLocationLineEdit.setText(str(path))
                self.nameLineEdit.setText(str(path).split("/")[-1].removesuffix(".exe"))

        def _select_cover_path(self):
            w = QFileDialog(self)
            w.setWindowTitle("Select a file")
            w.setFileMode(QFileDialog.AnyFile)
            w.setDirectory(os.getcwd())
            w.setNameFilter("Image File (*.*)")
            file_path = w.exec()
            if file_path and w.selectedFiles():
                path = w.selectedFiles()[0]
                print("File:", path)
                self.coverLocationLineEdit.setText(str(path))

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.game_list = []
        self.row = None
        self.current_exe = None
        self.data = utils.Data.load_config("data/data.json")
        self.setObjectName("Game")
        self.vBoxLayoutMain = QVBoxLayout(self)
        self.vBoxLayoutMiddle = QVBoxLayout(self)
        self.hBoxLayoutMiddle = QHBoxLayout(self)
        self.hBoxLayoutTop = QHBoxLayout(self)
        self.vBoxLayoutMain.setContentsMargins(30, 60, 30, 50)
        self.vBoxLayoutMain.setSpacing(30)
        self.hBoxLayoutTop.setSpacing(20)
        self.vBoxLayoutMiddle.setSpacing(10)

        self.titleLabel = TitleLabel("Local Games", self)
        self.titleLabel.setFixedHeight(40)
        self.filter = ComboBox(self)
        self.filter.setPlaceholderText("Filter")
        self.manageCategoryButton = PrimaryPushButton(self)
        self.manageCategoryButton.setIcon(FIF.FOLDER_ADD)
        self.manageCategoryButton.setText("Manage Categories")
        self.addNewButton = PrimaryPushButton(self)
        self.addNewButton.setIcon(FIF.ADD_TO)
        self.addNewButton.setText("Add new Game")
        self.refreshButton = PushButton(self)
        self.refreshButton.setIcon(FIF.UPDATE)
        self.refreshButton.setText("Refresh")

        self.resultTable = TableWidget(self)
        self.resultTable.setColumnCount(2)
        self.resultTable.horizontalHeader().setVisible(False)
        self.resultTable.verticalHeader().setVisible(False)
        self.resultTable.setEditTriggers(TableWidget.NoEditTriggers)
        self.resultTable.setShowGrid(False)

        self.separator_horiz_top = HorizontalSeparator(self)
        self.separator_vertical_middle = VerticalSeparator(self)

        self.noResultWidget = BodyLabel(self)
        self.noResultWidget.setText("No results found.")
        self.noResultWidget.setFont(Font.STANDARD_HUGE_FONT)
        self.noResultWidget.setAlignment(Qt.AlignCenter)

        self.detailImage = ImageLabel(self)
        self.detailLabel = BodyLabel(self)
        self.runButton = PrimaryPushButton("Launch", self)
        self.runButton.setIcon(FIF.PLAY)
        self.editButton = PushButton("Edit", self)
        self.editButton.setIcon(FIF.EDIT)
        # self.deleteButton = PushButton("Delete", self)
        # self.deleteButton.setIcon(FIF.DELETE)
        self.removeButton = PushButton("Remove", self)
        self.removeButton.setIcon(FIF.CLOSE)
        self.folderButton = PushButton("Browse File", self)
        self.folderButton.setIcon(FIF.FOLDER)

        self.hBoxLayoutTop.addWidget(self.filter, 1)
        self.hBoxLayoutTop.addWidget(self.manageCategoryButton, 1)
        self.hBoxLayoutTop.addWidget(self.addNewButton, 1, )
        self.hBoxLayoutTop.addWidget(self.refreshButton, 1)

        self.vBoxLayoutMiddle.addWidget(self.detailImage, 1)
        self.vBoxLayoutMiddle.addWidget(self.detailLabel, 1)
        self.vBoxLayoutMiddle.addWidget(self.runButton)
        self.vBoxLayoutMiddle.addWidget(self.editButton)
        self.vBoxLayoutMiddle.addWidget(self.removeButton)
        self.vBoxLayoutMiddle.addWidget(self.folderButton)
        self.detail_widget_visibility(False)
        self.detailLabel.setFixedWidth(250)
        self.detailLabel.setWordWrap(True)

        self.hBoxLayoutMiddle.addWidget(self.resultTable)
        self.hBoxLayoutMiddle.addWidget(self.separator_vertical_middle)
        self.hBoxLayoutMiddle.addLayout(self.vBoxLayoutMiddle)
        self.separator_vertical_middle.setVisible(False)

        self.vBoxLayoutMain.addWidget(self.titleLabel, 1)
        self.vBoxLayoutMain.addLayout(self.hBoxLayoutTop, 1)
        self.vBoxLayoutMain.addWidget(self.separator_horiz_top)
        self.vBoxLayoutMain.addWidget(self.noResultWidget, 1)
        self.vBoxLayoutMain.addWidget(self.noResultWidget, 1)
        self.vBoxLayoutMain.addLayout(self.hBoxLayoutMiddle, 1)

        self.filter.currentTextChanged.connect(lambda: self.table_default(self.filter.text()))
        self.resultTable.cellClicked.connect(self.show_detail)
        self.addNewButton.clicked.connect(self.add_new_game)
        self.manageCategoryButton.clicked.connect(self.manage_category)
        self.editButton.clicked.connect(self.edit_game)
        self.refreshButton.clicked.connect(self.refresh)
        self.removeButton.clicked.connect(lambda: self.delete_game("lib"))
        self.folderButton.clicked.connect(self.open_folder)
        self.runButton.clicked.connect(self.run_application)
        self.resultTable.cellDoubleClicked.connect(self.run_application)
        self.noResultWidget.setVisible(False)

        self.table_default("ALL")
        self.combobox_default()

    def run_application(self):
        self.current_exe = self.game_list[self.row][1]
        self.application_thread = WorkerThread(self.current_exe)
        self.application_thread.finished.connect(lambda: "Game quited")
        self.application_thread.start()

    def open_folder(self):
        path = os.path.dirname(self.game_list[self.row][1])
        path = os.path.normpath(path)
        print(path)
        subprocess.run(f'explorer "{path}"')

    def add_new_game(self):
        w = self.CreateNewGameMessageBox(self)
        if w.exec_():
            name = w.nameLineEdit.text()
            location = w.gameLocationLineEdit.text()
            cover = w.coverLocationLineEdit.text()
            if cover != "":
                shutil.copyfile(cover, os.path.normpath(
                    os.path.join(self.data["config"]["resources"]["cover_folder"], f"{name}.jpg")))
            introduction = w.infoLineEdit.text()
            category = w.categoryCombo.currentText()
            game = [name, location, time.strftime('%Y-%m-%d', time.localtime()), introduction, category]
            self.data["files"]["games"].append(game)
            utils.Data.json_write("data/data.json", self.data)
            self.refresh()

    def manage_category(self):
        w = self.ManageCategoriesMessageBox(self)
        if w.exec():
            self.refresh()

    def edit_game(self):
        w = self.EditGameMessageBox(self.resultTable.currentRow(), self)
        if w.exec():
            name = w.nameLineEdit.text()
            location = w.gameLocationLineEdit.text()
            introduction = w.infoLineEdit.text()
            category = w.categoryCombo.currentText()
            cover = w.coverLocationLineEdit.text()
            if cover != "":
                try:
                    if cover == "CLEAR":
                        os.remove(os.path.normpath(
                            os.path.join(self.data["config"]["resources"]["cover_folder"], f"{name}.jpg")))
                    else:
                        shutil.copyfile(cover,
                                        os.path.normpath(os.path.join(self.data["config"]["resources"]["cover_folder"],
                                                                      f"{name}.jpg")))
                except FileNotFoundError:
                    pass
            self.data["files"]["games"][self.resultTable.currentRow()] = [name, location,
                                                                          time.strftime('%Y-%m-%d', time.localtime()),
                                                                          introduction, category]
            utils.Data.json_write("data/data.json", self.data)
            self.refresh()

    def refresh(self):
        self.data = utils.Data.load_config("data/data.json")
        self.detail_widget_visibility(False)
        self.table_default()
        self.combobox_default()

    def delete_game(self, mode="lib"):
        if mode == "lib":
            w = MessageBox("Warning",
                           "This will permanently REMOVE the game from your library, but it will be still on your hard drive",
                           self)
        else:
            w = MessageBox("Warning",
                           "This will permanently REMOVE the game from your library, it will be also DELETED from your hard drive",
                           self)
        if w.exec():
            game = self.data["files"]["games"][self.resultTable.currentRow()]
            self.data["files"]["games"].remove(game)
            utils.Data.json_write("data/data.json", self.data)
            self.refresh()
            if mode == "all":
                try:
                    os.remove(game[1])
                except FileNotFoundError:
                    pass

    def combobox_default(self):
        cats = self.data["files"]["game_cats"]
        self.filter.clear()
        self.filter.addItems(cats)
        self.filter.setCurrentIndex(0)

    def table_default(self, key="ALL"):
        self.game_list = []
        self.resultTable.setVisible(True)
        for game in self.data["files"]["games"]:
            if game[-1] == key or key == "ALL":
                self.game_list.append(game)
        count = len(self.game_list)
        self.noResultWidget.setVisible(False)
        if count == 0:
            self.detail_widget_visibility(False)
            self.resultTable.setVisible(False)
            self.noResultWidget.setVisible(True)
            return None
        else:
            self.resultTable.setRowCount(count)
            self.resultTable.clear()
            for row in range(count):
                if self.game_list[row][-1] == key or key == "ALL":
                    item = QTableWidgetItem()
                    item.setText(self.game_list[row][0])
                    item.setFont(Font.STANDARD_FONT)
                    self.resultTable.setItem(row, 0, item)
            self.resultTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def detail_widget_visibility(self, visibility):
        self.separator_vertical_middle.setVisible(visibility)
        self.detailLabel.setVisible(visibility)
        self.detailImage.setVisible(visibility)
        self.runButton.setVisible(visibility)
        self.editButton.setVisible(visibility)
        self.folderButton.setVisible(visibility)
        self.removeButton.setVisible(visibility)

    def show_detail(self, row, col):
        self.row = row
        self.detail_widget_visibility(True)
        self.editButton.setDisabled(False)
        pic_name = self.game_list[self.row][0] + ".jpg"
        pic_name = os.path.normpath(os.path.join(self.data["config"]["resources"]["cover_folder"], pic_name))
        pic = QPixmap()
        if os.path.exists(pic_name):
            pic.load(pic_name)
        else:
            pic.load(self.data["config"]["resources"]["blank_img"])
        content = f"Name: {self.game_list[self.row][0]}\nCategory: {self.game_list[self.row][-1]}\nAdd/Edit Time: {self.game_list[self.row][2]}\nIntroduction: {self.game_list[self.row][3]}"

        self.detailLabel.setText(content)
        self.detailLabel.setFont(Font.STANDARD_FONT)
        self.detailImage.setImage(pic)
        self.detailImage.setFixedSize(250, 250)
        self.current_exe = self.game_list[row][1]
        self.resultTable.resizeColumnsToContents()
