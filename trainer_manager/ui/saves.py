"""ui.saves: extracted application components."""

import shutil
import subprocess
import os
import time
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QHeaderView, QTableWidgetItem, QFileDialog, QGridLayout
from qfluentwidgets import MessageBox, BodyLabel, PushButton, TableWidget, LineEdit, PrimaryPushButton, HorizontalSeparator, MessageBoxBase, SubtitleLabel, TitleLabel
from qfluentwidgets import FluentIcon as FIF
from trainer_manager import services as utils
from trainer_manager.runtime import Font


class SavingWidget(QFrame):
    class CreateNewSaveMessageBox(MessageBoxBase):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.titleLabel = SubtitleLabel('Create New Back-Up Configuration', self)
            self.nameLineEdit = LineEdit(self)
            self.nameLineEdit.setPlaceholderText('Name of this configuration')
            self.srcLineEdit = LineEdit(self)
            self.srcLineEdit.setPlaceholderText('Source of the game saves:')
            self.srcLineEdit.setClearButtonEnabled(True)
            self.srcButton = PushButton("Select", self)
            self.dstLineEdit = LineEdit(self)
            self.dstLineEdit.setPlaceholderText('Destination of the game saves:')
            self.dstLineEdit.setClearButtonEnabled(True)
            self.dstButton = PushButton("Select", self)

            self.srcLayout = QHBoxLayout(self)
            self.dstLayout = QHBoxLayout(self)

            self.srcLayout.addWidget(self.srcLineEdit, 4)
            self.srcLayout.addWidget(self.srcButton, 1)
            self.dstLayout.addWidget(self.dstLineEdit, 4)
            self.dstLayout.addWidget(self.dstButton, 1)

            # add widget to view layout
            self.viewLayout.addWidget(self.titleLabel)
            self.viewLayout.addWidget(self.nameLineEdit)
            self.viewLayout.addLayout(self.srcLayout)
            self.viewLayout.addLayout(self.dstLayout)

            # change the text of button
            self.yesButton.setText('Confirm')
            self.cancelButton.setText('Cancel')
            self.yesButton.setDisabled(True)

            self.widget.setMinimumWidth(350)
            self.nameLineEdit.textChanged.connect(self._verify_path)
            self.srcLineEdit.textChanged.connect(self._verify_path)
            self.dstLineEdit.textChanged.connect(self._verify_path)
            self.srcButton.clicked.connect(lambda: self._folder_selector("src"))
            self.dstButton.clicked.connect(lambda: self._folder_selector("dst"))
            # self.hideYesButton()

        def _verify_path(self):
            if self.nameLineEdit.text() != "" and self.srcLineEdit.text() != "" and self.dstLineEdit.text() != "":
                self.yesButton.setEnabled(True)
            else:
                self.yesButton.setDisabled(True)

        def _folder_selector(self, mode):
            if mode == "src":
                title = 'Select the source'
            else:
                title = 'Select the destination'
            dir_path = QFileDialog.getExistingDirectory(self, title, os.getcwd())
            if dir_path:
                if mode == "src":
                    self.srcLineEdit.setText(dir_path)
                elif mode == "dst":
                    self.dstLineEdit.setText(dir_path)

    class SaveDetailMessageBox(MessageBoxBase):
        def __init__(self, file_row, parent=None):
            super().__init__(parent)
            self.data = utils.Data.json_read("data/data.json")
            self.file_row = file_row
            self.edited = False
            self.saves = []
            self.name = self.data["files"]["save_file"][self.file_row][0]
            self.src = self.data["files"]["save_file"][self.file_row][1]
            self.dst = self.data["files"]["save_file"][self.file_row][2]
            self.titleLabel = SubtitleLabel("Manage the save", self)
            self.nameLineEdit = LineEdit(self)
            self.nameLineEdit.setText(self.name)
            self.nameLineEdit.setClearButtonEnabled(True)
            self.srcLineEdit = LineEdit(self)
            self.srcLineEdit.setText(self.src)
            self.srcLineEdit.setClearButtonEnabled(True)
            self.srcButton = PushButton("Select", self)
            self.dstLineEdit = LineEdit(self)
            self.dstLineEdit.setText(self.dst)
            self.dstLineEdit.setClearButtonEnabled(True)
            self.dstButton = PushButton("Select", self)
            self.applyButton = PrimaryPushButton("Apply", self)
            self.applyButton.setIcon(FIF.COMPLETED)
            self.deleteConfigButton = PushButton("Delete the Config", self)
            self.deleteConfigButton.setIcon(FIF.REMOVE_FROM)
            self.hTopSeparator = HorizontalSeparator(self)
            self.tableTitleLabel = BodyLabel(self)
            self.backupTable = TableWidget(self)
            self.backupTable.horizontalHeader().setVisible(False)
            self.backupTable.verticalHeader().setVisible(False)
            self.backupTable.setEditTriggers(TableWidget.NoEditTriggers)
            self.backupTable.setBorderVisible(True)
            self.newBackupButton = PrimaryPushButton("Back up", self)
            self.newBackupButton.setIcon(FIF.SAVE_COPY)
            self.recoveryButton = PushButton("Recovery", self)
            self.recoveryButton.setIcon(FIF.COPY)
            self.deleteBackupButton = PushButton("Delete", self)
            self.deleteBackupButton.setIcon(FIF.DELETE)
            self.viewFolderButton = PushButton("View folder", self)
            self.viewFolderButton.setIcon(FIF.FOLDER)

            self.srcLayout = QHBoxLayout(self)
            self.dstLayout = QHBoxLayout(self)
            self.funcLayout = QGridLayout(self)

            self.srcLayout.addWidget(self.srcLineEdit, 4)
            self.srcLayout.addWidget(self.srcButton, 1)
            self.dstLayout.addWidget(self.dstLineEdit, 4)
            self.dstLayout.addWidget(self.dstButton, 1)
            self.funcLayout.addWidget(self.newBackupButton, 1, 1)
            self.funcLayout.addWidget(self.recoveryButton, 1, 2)
            self.funcLayout.addWidget(self.deleteBackupButton, 2, 1)
            self.funcLayout.addWidget(self.viewFolderButton, 2, 2)

            self.viewLayout.addWidget(self.titleLabel)
            self.viewLayout.addWidget(self.nameLineEdit)
            self.viewLayout.addLayout(self.srcLayout)
            self.viewLayout.addLayout(self.dstLayout)
            self.viewLayout.addWidget(self.applyButton)
            self.viewLayout.addWidget(self.deleteConfigButton)
            self.viewLayout.addWidget(self.hTopSeparator)
            self.viewLayout.addWidget(self.tableTitleLabel)
            self.viewLayout.addWidget(self.backupTable)
            self.viewLayout.addLayout(self.funcLayout)

            self.widget.setMinimumWidth(550)
            self.cancelButton.hide()

            self.recoveryButton.setDisabled(True)
            self.deleteBackupButton.setDisabled(True)
            self.viewFolderButton.setDisabled(True)
            self.applyButton.setDisabled(True)
            self.table_default()

            self.srcButton.clicked.connect(lambda: self._folder_selector("src"))
            self.dstButton.clicked.connect(lambda: self._folder_selector("dst"))
            self.backupTable.cellClicked.connect(lambda: self.activator_funcs(True))
            self.viewFolderButton.clicked.connect(self.view_folder)
            self.deleteBackupButton.clicked.connect(self.delete_save)
            self.newBackupButton.clicked.connect(self.new_backup)
            self.recoveryButton.clicked.connect(self.recovery_backup)
            self.nameLineEdit.textChanged.connect(self.info_change_check)
            self.srcLineEdit.textChanged.connect(self.info_change_check)
            self.dstLineEdit.textChanged.connect(self.info_change_check)
            self.applyButton.clicked.connect(self.apply_change)
            self.deleteConfigButton.clicked.connect(self.delete_config)

        def table_default(self):
            save_info = self.data["files"]["save_file"][self.file_row]
            dirs = []
            if not os.path.exists(save_info[2]):
                self.backupTable.setVisible(False)
                self.tableTitleLabel.setText("This destination folder is no longer available.")
                return False
            for file in os.scandir(save_info[2]):
                if file.is_dir():
                    dirs.append(file.name)
            count = len(dirs)
            self.saves = dirs
            if count != 0:
                self.tableTitleLabel.setText(f"There are {count} backed-up saves.")
                self.backupTable.setVisible(True)
                self.backupTable.setColumnCount(1)
                self.backupTable.setRowCount(count)
            else:
                self.backupTable.setVisible(False)
                self.tableTitleLabel.setText("There is 0 backed-up saves.")
            for dir in dirs:
                item = QTableWidgetItem()
                item.setText(dir)
                item.setFont(Font.STANDARD_FONT)
                self.backupTable.setItem(dirs.index(dir), 0, item)
            self.backupTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        def activator_funcs(self, status=True):
            if status and not self.backupTable.selectedItems():
                return False
            self.recoveryButton.setEnabled(status)
            self.deleteBackupButton.setEnabled(status)
            self.viewFolderButton.setEnabled(status)

        def view_folder(self):
            path = os.path.normpath(os.path.join(self.data["files"]["save_file"][self.file_row][2],
                                                 self.backupTable.item(self.backupTable.currentRow(), 0).text()))
            print(path)
            subprocess.run(f'explorer "{path}"')

        def _folder_selector(self, mode):
            if mode == "src":
                title = 'Select the new source'
            else:
                title = 'Select the new destination'
            dir_path = QFileDialog.getExistingDirectory(self, title, os.getcwd())
            if dir_path:
                if mode == "src":
                    self.srcLineEdit.setText(dir_path)
                elif mode == "dst":
                    self.dstLineEdit.setText(dir_path)

        def delete_save(self):
            path = os.path.normpath(os.path.join(self.dst, self.saves[self.backupTable.currentRow()]))
            w = MessageBox("Warning", f"Are you sure to remove this save:\n{path}\nThis operation is irreversible.",
                           self)
            if w.exec():
                shutil.rmtree(path)
                self.table_default()

        def delete_config(self):
            w = MessageBox("Warning", "Are you sure to remove this configuration?\nThis operation is irreversible",
                           self)
            if w.exec():
                del self.data["files"]["save_file"][self.file_row]
                utils.Data.json_write("data/data.json", self.data)
                n = MessageBox("Notification", "Would you like to clear the destination folder?", self)
                if n.exec():
                    shutil.rmtree(self.dst)
                self.close()

        def new_backup(self):
            dir_name = time.strftime("%Y-%m-%d@%H-%M-%S")
            dir_path = os.path.normpath(os.path.join(self.dst, dir_name))
            print(dir_path)
            if os.path.exists(dir_path):
                utils.Help.warning("Warning", f"Destination folder <{dir_path}> already exists.")
                return False
            if not os.path.exists(self.src):
                utils.Help.warning("Warning", f"Source folder <{self.src}> already exists.")
                return False
            shutil.copytree(self.src, dir_path)
            n = MessageBox("Notification", f"New backup created.\n<{dir_path}>", self)
            n.cancelButton.hide()
            if n.exec():
                pass
            self.table_default()

        def info_change_check(self):
            if self.nameLineEdit.text() != self.name or self.srcLineEdit.text() != self.src or self.dstLineEdit.text() != self.dst:
                self.activator_funcs(False)
                self.newBackupButton.setDisabled(True)
                self.applyButton.setEnabled(True)
                self.edited = True
            else:
                self.activator_funcs(True)
                self.newBackupButton.setEnabled(True)
                self.applyButton.setDisabled(True)
                self.edited = False

        def recovery_backup(self):
            w = MessageBox("Warning",
                           f"""
                           This operation will OVERWRITE your original save folder:
                           {self.src} .\n
                           It is strongly RECOMMENDED that you back everything up in advance.
                           This operation is IRREVERSIBLE.
                           """,
                           self)
            if w.exec():
                path = os.path.normpath(os.path.join(self.dst, self.saves[self.self.backupTable.currentRow()]))
                if not os.path.exists(path) or not os.path.exists(self.src):
                    utils.Help.warning("Warning", "Destination or Source folder doesn't exist.")
                    return False
                shutil.rmtree(self.src)
                shutil.copytree(path, self.src)
                n = MessageBox("Notification",
                               f"Recovery Successful.\n{path} -> {self.src}",
                               self)
                n.cancelButton.hide()
                if n.exec():
                    pass

        def apply_change(self):
            name = self.nameLineEdit.text()
            src = self.srcLineEdit.text()
            dst = self.dstLineEdit.text()
            name_collision = False
            dst_collision = False
            for item in self.data["files"]["save_file"]:
                if self.data["files"]["save_file"].index(item) != self.file_row:
                    if name == item[0]:
                        name_collision = True
                    if dst == item[2]:
                        dst_collision = True
                if name_collision and dst_collision:
                    break

            if name_collision or dst_collision:
                content = ""
                if name_collision:
                    content = f"The name '{name}' is already occupied by another configuration"
                    self.nameLineEdit.setText(self.name)
                elif dst_collision:
                    content = f"The destination '{dst}' is already occupied by another configuration"
                    self.dstLineEdit.setText(self.dst)
                w = MessageBox("Warning", content, self)
                w.cancelButton.hide()
                if w.exec():
                    pass
                return False
            self.data["files"]["save_file"][self.file_row][0] = name
            self.data["files"]["save_file"][self.file_row][1] = src
            self.data["files"]["save_file"][self.file_row][2] = dst
            if dst != self.dst:
                n = MessageBox("Notification", "Would you like to clear the original destination folder?", self)
                if n.exec():
                    shutil.rmtree(self.dst)
            utils.Data.json_write("data/data.json", self.data)
            self.data = utils.Data.json_read("data/data.json")
            self.name = self.data["files"]["save_file"][self.file_row][0]
            self.src = self.data["files"]["save_file"][self.file_row][1]
            self.dst = self.data["files"]["save_file"][self.file_row][2]
            self.table_default()
            self.info_change_check()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.data = utils.Data.json_read("data/data.json")
        self.setObjectName("Saving")
        self.vBoxLayoutMain = QVBoxLayout(self)
        self.hBoxLayoutTop = QHBoxLayout(self)
        self.hBoxLayoutMiddle = QHBoxLayout(self)
        self.vBoxLayoutMain.setContentsMargins(30, 60, 30, 50)
        self.vBoxLayoutMain.setSpacing(30)
        self.hBoxLayoutTop.setSpacing(20)
        self.hBoxLayoutMiddle.setSpacing(20)

        self.titleLabel = TitleLabel("Saves", self)
        self.titleLabel.setFixedHeight(40)
        self.refreshButton = PushButton(self)
        self.refreshButton.setIcon(FIF.UPDATE)
        self.refreshButton.setText("Refresh")
        self.cloudSyncButton = PushButton(self)
        self.cloudSyncButton.setIcon(FIF.CLOUD_DOWNLOAD)
        self.cloudSyncButton.setText("Cloud Sync")
        self.cloudSyncButton.setDisabled(True)
        self.addNewButton = PrimaryPushButton(self)
        self.addNewButton.setIcon(FIF.ADD_TO)
        self.addNewButton.setText("Add new save")
        self.backupAllButton = PrimaryPushButton(self)
        self.backupAllButton.setIcon(FIF.SAVE_COPY)
        self.backupAllButton.setText("Back Up All")
        self.noSavesLabel = BodyLabel("Oops! No saves found.", self)
        self.noSavesLabel.setFont(Font.STANDARD_HUGE_FONT)
        self.noSavesLabel.setAlignment(Qt.AlignCenter)
        self.savesTable = TableWidget(self)
        self.savesTable.horizontalHeader().setVisible(False)
        self.savesTable.verticalHeader().setVisible(False)
        self.savesTable.setColumnCount(1)
        self.savesTable.setEditTriggers(TableWidget.NoEditTriggers)
        self.savesTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horiz_seperator_1 = HorizontalSeparator(self)

        self.savesTable.setVisible(False)

        self.hBoxLayoutTop.addWidget(self.addNewButton, 2)
        self.hBoxLayoutTop.addWidget(self.backupAllButton, 2)
        self.hBoxLayoutTop.addWidget(self.cloudSyncButton, 1)
        self.hBoxLayoutTop.addWidget(self.refreshButton, 1)
        self.hBoxLayoutMiddle.addWidget(self.noSavesLabel)
        self.hBoxLayoutMiddle.addWidget(self.savesTable)

        self.vBoxLayoutMain.addWidget(self.titleLabel)
        self.vBoxLayoutMain.addLayout(self.hBoxLayoutTop)
        self.vBoxLayoutMain.addWidget(self.horiz_seperator_1)
        self.vBoxLayoutMain.addLayout(self.hBoxLayoutMiddle)

        self.save_table_default()
        self.addNewButton.clicked.connect(self.create_backup)
        self.refreshButton.clicked.connect(self.refresh)
        self.savesTable.cellDoubleClicked.connect(self.save_detail)
        self.backupAllButton.clicked.connect(self.backup_all)

    def refresh(self):
        self.data = utils.Data.json_read("data/data.json")
        self.save_table_default()

    def save_table_default(self):
        save_list = self.data["files"]["save_file"]
        count = len(save_list)
        if count != 0:
            self.savesTable.setVisible(True)
            self.noSavesLabel.setVisible(False)
            self.savesTable.setRowCount(count)
            self.savesTable.clear()
        else:
            self.savesTable.setVisible(False)
            self.noSavesLabel.setVisible(True)
            self.savesTable.clear()
            return None
        for save in save_list:
            print(save)
            name = save[0]
            src_path = save[1]
            dst_path = save[2]
            item = QTableWidgetItem()
            item.setText(name)
            item.setFont(Font.STANDARD_FONT)
            self.savesTable.setItem(save_list.index(save), 0, item)

    def create_backup(self):
        w = self.CreateNewSaveMessageBox(self)
        if w.exec():
            name = w.nameLineEdit.text()
            src = w.srcLineEdit.text()
            dst = w.dstLineEdit.text()
            for item in self.data["files"]["save_file"]:
                if name == item[0] or dst == item[2]:
                    invalid = MessageBox("Warning",
                                         "Invalid name or destination, they may be occupied by other configuration",
                                         self)
                    invalid.cancelButton.hide()
                    if invalid.exec():
                        pass
                    return False
            self.data["files"]["save_file"].append([name, src, dst])
            utils.Data.json_write("data/data.json", self.data)
            self.refresh()

    def save_detail(self):
        w = self.SaveDetailMessageBox(self.savesTable.currentRow(), self)
        if w.exec() or w.close():
            self.refresh()

    # TODO: ALL-BACK-UP FEATURE INCOMPLETE
    def backup_all(self):
        save_list = self.data["files"]["save_file"]
        count = len(save_list)
        if count != 0:
            done_notice = "The following configurations have been backed-up successfully:"
            for i in range(count):
                item = save_list[i]
                name = item[0]
                src = item[1]
                dst = item[2]
                dst_name = time.strftime("%Y-%m-%d@%H-%M-%S")
                dst_path = os.path.normpath(os.path.join(dst, dst_name))
                print(f"{src} -> {dst_path}")
                if os.path.exists(dst_path):
                    utils.Help.warning("Warning", f"Destination folder <{dst_path}> already exists.")
                    return False
                if not os.path.exists(src):
                    utils.Help.warning("Warning", f"Source folder <{src}> doesn't exists.")
                    return False
                shutil.copytree(src, dst_path)
                done_notice += f"\n{name}"
            n = MessageBox("Notification", done_notice, self)
            n.cancelButton.hide()
            if n.exec():
                pass
