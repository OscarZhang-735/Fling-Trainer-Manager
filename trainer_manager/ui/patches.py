"""ui.patches: extracted application components."""

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QTableWidgetItem
from qfluentwidgets import TableWidget, HorizontalSeparator, TitleLabel
from trainer_manager import services as utils
from trainer_manager.runtime import Font


class PatchWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.data = utils.Data.load_config("data/data.json")
        try:
            self.patches = utils.Data.json_read("data/patch.json")
        except FileNotFoundError:
            self.patches = {"patches": {"neko_nyan_steam": [], "neko_nyan_non_steam": []}}
        self.setObjectName("Patch")
        self.vBoxLayoutMain = QVBoxLayout(self)
        self.hBoxLayoutTop = QHBoxLayout(self)
        self.hBoxLayoutMiddle = QHBoxLayout(self)
        self.vBoxLayoutMain.setContentsMargins(30, 60, 30, 50)
        self.vBoxLayoutMain.setSpacing(30)
        self.hBoxLayoutTop.setSpacing(20)
        self.hBoxLayoutMiddle.setSpacing(20)

        self.titleLabel = TitleLabel("Patch", self)
        self.titleLabel.setFixedHeight(40)
        self.patchTable = TableWidget(self)
        self.patchTable.setColumnCount(2)
        self.patchTable.horizontalHeader().setVisible(False)
        self.patchTable.verticalHeader().setVisible(False)
        self.patchTable.setEditTriggers(TableWidget.NoEditTriggers)
        self.patchTable.setShowGrid(False)
        self.hSeperator_1 = HorizontalSeparator(self)

        self.hBoxLayoutMiddle.addWidget(self.patchTable)

        self.vBoxLayoutMain.addWidget(self.titleLabel)
        self.vBoxLayoutMain.addWidget(self.titleLabel)
        self.vBoxLayoutMain.addLayout(self.hBoxLayoutTop)
        self.vBoxLayoutMain.addWidget(self.hSeperator_1)
        self.vBoxLayoutMain.addLayout(self.hBoxLayoutMiddle)

        self.list_table("nekoNyanSteam")

    def list_table(self, filter):
        patch_list = []
        if filter == "nekoNyanSteam":
            patch_list = self.patches["patches"]["neko_nyan_steam"]
        elif filter == "nekoNyanNonSteam":
            patch_list = self.patches["patches"]["neko_nyan_non_steam"]
        # print(patch_list)
        for patch in patch_list:
            item = QTableWidgetItem()
            item.setText(patch["name"])
            item.setFont(Font.STANDARD_FONT)
            self.patchTable.setItem(patch_list.index(patch), 1, item)
