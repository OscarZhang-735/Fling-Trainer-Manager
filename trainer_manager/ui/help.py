"""ui.help: extracted application components."""

import webbrowser
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout
from qfluentwidgets import PushButton, PrimaryPushButton, HorizontalSeparator, SubtitleLabel, TitleLabel
from qfluentwidgets import FluentIcon as FIF
from trainer_manager import services as utils
from trainer_manager.runtime import Font


class HelpingWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # self.resize(400, 400)
        self.config = utils.Data.load_config("data/data.json")["config"]
        # self.data = utils.Data.json_read("./data/data.json")
        self.setObjectName("Help")
        self.vBoxLayoutMain = QVBoxLayout(self)
        self.hBoxLayoutTop = QHBoxLayout(self)
        self.hBoxLayoutTrainer = QHBoxLayout(self)
        self.hBoxLayoutPatches = QHBoxLayout(self)
        self.hBoxLayoutDev = QHBoxLayout(self)
        self.vBoxLayoutMain.setContentsMargins(30, 60, 30, 50)
        self.vBoxLayoutMain.setSpacing(30)
        self.hBoxLayoutTop.setSpacing(20)
        self.hBoxLayoutPatches.setSpacing(20)
        self.hBoxLayoutDev.setSpacing(20)

        self.title_label = TitleLabel("Help", self)
        self.title_label.setFixedHeight(40)
        """self.docTitleLabel = BodyLabel(self)
        self.docTitleLabel.setFont(STANDARD_FONT)
        self.docTitleLabel.setText("Helping Document")"""
        self.docButton = PrimaryPushButton(self)
        self.docButton.setText("Read Document")
        self.docButton.setFont(Font.STANDARD_FONT)
        self.docButton.setIcon(FIF.LINK)

        self.trainerTitleLabel = SubtitleLabel("FLiNG Trainer Website", self)
        self.trainerButton = PushButton(self)
        self.trainerButton.setText("Visit Homepage")
        self.trainerButton.setFont(Font.STANDARD_FONT)
        self.trainerButton.setIcon(FIF.LINK)
        self.trainerArchivedButton = PushButton(self)
        self.trainerArchivedButton.setText("View Archived Trainers")
        self.trainerArchivedButton.setFont(Font.STANDARD_FONT)
        self.trainerArchivedButton.setIcon(FIF.LINK)

        self.patchTitleLabel = SubtitleLabel("Patch", self)
        self.nekoNyanButton = PushButton(self)
        self.nekoNyanButton.setText("NekoNyan Game Patches")
        self.nekoNyanButton.setFont(Font.STANDARD_FONT)
        self.nekoNyanButton.setIcon(FIF.LINK)
        self.kaguraButton = PushButton(self)
        self.kaguraButton.setText("Kagura Game Patches")
        self.kaguraButton.setFont(Font.STANDARD_FONT)
        self.kaguraButton.setIcon(FIF.LINK)

        self.devTitleLabel = SubtitleLabel("Developer", self)
        self.repoButton = PushButton(self)
        self.repoButton.setText("View the repository on GitHub")
        self.repoButton.setFont(Font.STANDARD_FONT)
        self.repoButton.setIcon(FIF.GITHUB)
        self.steamButton = PushButton(self)
        self.steamButton.setText("Steam Profile")
        self.steamButton.setFont(Font.STANDARD_FONT)
        self.steamButton.setIcon(FIF.LINK)

        self.hSeperator_1 = HorizontalSeparator(self)
        self.hSeperator_2 = HorizontalSeparator(self)
        self.hSeperator_3 = HorizontalSeparator(self)
        self.hSeperator_4 = HorizontalSeparator(self)
        self.hSeperator_5 = HorizontalSeparator(self)

        self.hBoxLayoutTrainer.addWidget(self.trainerTitleLabel)
        self.hBoxLayoutTrainer.addWidget(self.trainerButton)
        self.hBoxLayoutTrainer.addWidget(self.trainerArchivedButton)
        self.hBoxLayoutPatches.addWidget(self.patchTitleLabel)
        self.hBoxLayoutPatches.addWidget(self.nekoNyanButton)
        self.hBoxLayoutPatches.addWidget(self.kaguraButton)
        self.hBoxLayoutDev.addWidget(self.devTitleLabel)
        self.hBoxLayoutDev.addWidget(self.repoButton)
        self.hBoxLayoutDev.addWidget(self.steamButton)

        self.vBoxLayoutMain.addWidget(self.title_label, 1)
        self.vBoxLayoutMain.addWidget(self.hSeperator_1)
        self.vBoxLayoutMain.addWidget(self.docButton, 1)
        self.vBoxLayoutMain.addWidget(self.hSeperator_2)
        self.vBoxLayoutMain.addLayout(self.hBoxLayoutTrainer, 1)
        self.vBoxLayoutMain.addWidget(self.hSeperator_3)
        self.vBoxLayoutMain.addLayout(self.hBoxLayoutPatches, 1)
        self.vBoxLayoutMain.addWidget(self.hSeperator_4)
        self.vBoxLayoutMain.addLayout(self.hBoxLayoutDev, 1)

        self.docButton.clicked.connect(
            lambda: webbrowser.open("https://github.com/OscarZhang-735/Trainer-Manager/blob/master/README.md"))
        self.trainerButton.clicked.connect(lambda: webbrowser.open("https://flingtrainer.com/"))
        self.trainerArchivedButton.clicked.connect(lambda: webbrowser.open("https://archive.flingtrainer.com/"))
        self.nekoNyanButton.clicked.connect(lambda: webbrowser.open("https://patches.nekonyansoft.com/"))
        self.kaguraButton.clicked.connect(lambda: webbrowser.open("https://www.kaguragames.com/product-tag/patch/"))
        self.repoButton.clicked.connect(lambda: webbrowser.open("https://github.com/OscarZhang-735/Trainer-Manager"))
        self.steamButton.clicked.connect(
            lambda: webbrowser.open("https://steamcommunity.com/profiles/76561199209380880/"))

    def write_report(self):
        pass

    def donate(self):
        pass
