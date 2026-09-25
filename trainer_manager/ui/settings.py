"""ui.settings: extracted application components."""

import os
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QFileDialog, QGridLayout
from qfluentwidgets import MessageBox, BodyLabel, PushButton, LineEdit, PrimaryPushButton, HorizontalSeparator, SubtitleLabel, SwitchButton
from trainer_manager import services as utils
from trainer_manager.runtime import Font


class SettingWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # self.resize(400, 400)
        self.data = utils.Data.json_read("data/data.json")
        # self.data = utils.Data.json_read("./data/data.json")
        self.setObjectName("Setting")
        self.vBoxLayoutMain = QVBoxLayout(self)
        self.vBoxLayoutMain.setContentsMargins(30, 60, 30, 50)
        self.vBoxLayoutMain.setSpacing(15)

        self.titleLabel = SubtitleLabel("Settings", self)
        self.pathTitleLabel = BodyLabel("Download Path", self)
        self.pathTitleLabel.setFont(Font.STANDARD_MIDDLE_FONT)
        self.trainerLabel = BodyLabel("Trainer Download Path:", self)
        self.gameLabel = BodyLabel("Game Download Path:", self)
        self.patchLabel = BodyLabel("Patch Download Path:", self)

        self.trainerLineEdit = LineEdit(self)
        self.gameLineEdit = LineEdit(self)
        self.patchLineEdit = LineEdit(self)
        self.trainerButton = PushButton("Select", self)
        self.gameButton = PushButton("Select", self)
        self.patchButton = PushButton("Select", self)
        self.miscTitle = BodyLabel("Misc", self)
        self.miscTitle.setFont(Font.STANDARD_MIDDLE_FONT)
        self.detailImgSwitch = SwitchButton(self)
        self.detailImgSwitch.setOnText("Enable Detail Image Cache")
        self.detailImgSwitch.setOffText("Disable Detail Image Cache")
        self.trainerFilterSwitch = SwitchButton(self)
        self.trainerFilterSwitch.setOnText("Enable Library Filter: Registered Trainers Only")
        self.trainerFilterSwitch.setOffText("Disable Library Filter: All (Not Recommended)")
        self.connectionSwitch = SwitchButton(self)
        self.connectionSwitch.setOnText("Enable Internet Connection")
        self.connectionSwitch.setOffText("Disable Internet Connection")

        self.customTitle = BodyLabel("User", self)
        self.customTitle.setFont(Font.STANDARD_MIDDLE_FONT)
        self.usernameLabel = BodyLabel("Username:", self)
        self.usernameLineEdit = LineEdit(self)
        self.avatarLabel = BodyLabel("Avatar:", self)
        self.avatarLineEdit = LineEdit(self)
        self.avatarButton = PushButton("Select", self)

        self.applyButton = PrimaryPushButton("Apply", self)
        self.undoButton = PushButton("Undo", self)

        self.pathBox = QGridLayout(self)
        self.miscBox = QGridLayout(self)
        self.userBox = QGridLayout(self)
        self.operationBox = QHBoxLayout(self)

        self.pathBox.addWidget(self.trainerLabel, 1, 1)
        self.pathBox.addWidget(self.trainerLineEdit, 1, 2)
        self.pathBox.addWidget(self.trainerButton, 1, 3)
        self.pathBox.addWidget(self.gameLabel, 2, 1)
        self.pathBox.addWidget(self.gameLineEdit, 2, 2)
        self.pathBox.addWidget(self.gameButton, 2, 3)
        self.pathBox.addWidget(self.patchLabel, 3, 1)
        self.pathBox.addWidget(self.patchLineEdit, 3, 2)
        self.pathBox.addWidget(self.patchButton, 3, 3)

        self.miscBox.addWidget(self.detailImgSwitch, 1, 1)
        self.miscBox.addWidget(self.trainerFilterSwitch, 1, 2)
        self.miscBox.addWidget(self.connectionSwitch, 2, 1)

        self.userBox.addWidget(self.usernameLabel, 1, 1)
        self.userBox.addWidget(self.usernameLineEdit, 1, 2, 1, 2)
        self.userBox.addWidget(self.avatarLabel, 2, 1)
        self.userBox.addWidget(self.avatarLineEdit, 2, 2)
        self.userBox.addWidget(self.avatarButton, 2, 3)

        self.operationBox.addWidget(self.undoButton)
        self.operationBox.addWidget(self.applyButton)

        self.hSeperator_1 = HorizontalSeparator(self)
        self.hSeperator_2 = HorizontalSeparator(self)
        self.hSeperator_3 = HorizontalSeparator(self)
        self.hSeperator_4 = HorizontalSeparator(self)
        self.hSeperator_5 = HorizontalSeparator(self)

        self.vBoxLayoutMain.addWidget(self.titleLabel)
        self.vBoxLayoutMain.addWidget(self.hSeperator_1)
        self.vBoxLayoutMain.addWidget(self.pathTitleLabel)
        self.vBoxLayoutMain.addLayout(self.pathBox)
        self.vBoxLayoutMain.addWidget(self.hSeperator_2)
        self.vBoxLayoutMain.addWidget(self.miscTitle)
        self.vBoxLayoutMain.addLayout(self.miscBox)
        self.vBoxLayoutMain.addWidget(self.hSeperator_4)
        self.vBoxLayoutMain.addWidget(self.customTitle)
        self.vBoxLayoutMain.addLayout(self.userBox)
        self.vBoxLayoutMain.addWidget(self.hSeperator_5)
        self.vBoxLayoutMain.addLayout(self.operationBox)

        self.trainerButton.clicked.connect(lambda: self._select_folder("trainer"))
        self.gameButton.clicked.connect(lambda: self._select_folder("game"))
        self.patchButton.clicked.connect(lambda: self._select_folder("patch"))
        self.avatarButton.clicked.connect(self._select_file)
        self.applyButton.clicked.connect(self.save_change)
        self.undoButton.clicked.connect(self.data_init)

        self.data_init()

    def data_init(self):
        self.data = utils.Data.json_read("data/data.json")
        trainer_path = self.data["config"]["download"]["trainer"]
        game_path = self.data["config"]["download"]["games"]
        patch_path = self.data["config"]["download"]["patches"]
        username = self.data["config"]["program"]["username"]
        avatar = self.data["config"]["program"]["user_avatar"]
        bool_img_cache = self.data["config"]["cache"]["detail_image"]
        if self.data["config"]["library"]["filter"]:
            bool_library_filter = True
        else:
            bool_library_filter = False
        bool_connection = self.data["config"]["program"]["connection_allow"]

        self.trainerLineEdit.setText(trainer_path)
        self.gameLineEdit.setText(game_path)
        self.patchLineEdit.setText(patch_path)
        self.detailImgSwitch.setChecked(bool_img_cache)
        self.trainerFilterSwitch.setChecked(bool_library_filter)
        self.connectionSwitch.setChecked(bool_connection)
        self.usernameLineEdit.setText(username)
        self.avatarLineEdit.setText(avatar)

    def _select_folder(self, mode):
        dir_path = QFileDialog.getExistingDirectory(self, f'Select the {mode} download path', os.getcwd())
        if dir_path:
            if mode == "trainer":
                self.trainerLineEdit.setText(dir_path)
            elif mode == "patch":
                self.patchLineEdit.setText(dir_path)
            elif mode == "games":
                self.gameLineEdit.setText(dir_path)

    def _select_file(self):
        w = QFileDialog(self)
        w.setWindowTitle(f"Select a avatar file")
        w.setFileMode(QFileDialog.AnyFile)
        w.setDirectory(os.getcwd())
        w.setNameFilter("Image File (*.png, *.jpg)")
        file_path = w.exec()
        if file_path and w.selectedFiles():
            path = w.selectedFiles()[0]
            self.avatarLineEdit.setText(path)

    def input_validating(self):
        os.chdir(".")
        path_list = []
        invalid_list = []
        path_list.append(self.trainerLineEdit.text())
        path_list.append(self.gameLineEdit.text())
        path_list.append(self.patchLineEdit.text())
        path_list.append(self.avatarLineEdit.text())
        for path in path_list:
            if not os.path.exists(path):
                invalid_list.append(path)
        if len(invalid_list) > 0:
            w = MessageBox("Warning", f"The following paths you input are invalid:\n{invalid_list}", self)
            w.cancelButton.hide()
            if w.exec():
                self.data_init()
                return False
        if self.usernameLineEdit == "":
            w = MessageBox("Warning", "Username cannot be empty.", self)
            w.cancelButton.hide()
            if w.exec():
                self.data_init()
                return False
        return True

    def save_change(self):
        if not self.input_validating():
            return False
        self.data["config"]["download"]["trainer"] = self.trainerLineEdit.text()
        self.data["config"]["download"]["games"] = self.gameLineEdit.text()
        self.data["config"]["download"]["patches"] = self.patchLineEdit.text()
        self.data["config"]["cache"]["detail_image"] = self.detailImgSwitch.isChecked()
        if self.trainerFilterSwitch.isChecked():
            self.data["config"]["library"]["filter"] = "REGISTERED_ONLY"
        else:
            self.data["config"]["library"]["filter"] = "ALL"
        self.data["config"]["program"]["connection_allow"] = self.connectionSwitch.isChecked()
        self.data["config"]["program"]["username"] = self.usernameLineEdit.text()
        self.data["config"]["program"]["user_avatar"] = self.avatarLineEdit.text()

        print(self.data["config"])

        utils.Data.json_write("data/data.json", self.data)
