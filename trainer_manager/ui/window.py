"""ui.window: extracted application components."""

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtWidgets import QApplication, QStackedWidget, QHBoxLayout
from qfluentwidgets import NavigationInterface, NavigationItemPosition, MessageBox, isDarkTheme, setTheme, Theme, qrouter
from qfluentwidgets import FluentIcon as FIF
from qframelesswindow import FramelessWindow
from trainer_manager.ui.search import SearchWidget
from trainer_manager.ui.library import LibraryWidget
from trainer_manager.ui.settings import SettingWidget
from trainer_manager.ui.navigation import AvatarWidget
from trainer_manager.ui.navigation import CustomTitleBar
from trainer_manager.runtime import ICON, TITLE


class Window(FramelessWindow):
    def __init__(self):
        super().__init__()
        self.setTitleBar(CustomTitleBar(self))
        # use dark theme mode
        setTheme(Theme.DARK)

        self.hBoxLayout = QHBoxLayout(self)
        self.navigationInterface = NavigationInterface(
            self, showMenuButton=True, showReturnButton=True)
        self.stackWidget = QStackedWidget(self)

        # create sub interface
        self.searchInterface = SearchWidget(self)
        self.libraryInterface = LibraryWidget(self)
        self.searchInterface._transfer.finished.connect(
            lambda ok: self.libraryInterface.table_default() if ok else None)
        self.settingInterface = SettingWidget(self)
        self.settingInterface.can_apply_settings = lambda: not (
            self.searchInterface._transfer.busy or self.libraryInterface._transfer.busy)
        self.settingInterface.settingsSaved.connect(self.libraryInterface.table_default)
        self.settingInterface.settingsSaved.connect(self.searchInterface.refresh_repository_state)
        # self.settingInterface = Widget("Settings", self)
        # initialize layout
        self.initLayout()

        # add items to navigation interface
        self.initNavigation()

        self.initWindow()

    def initLayout(self):
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.navigationInterface)
        self.hBoxLayout.addWidget(self.stackWidget)
        self.hBoxLayout.setStretchFactor(self.stackWidget, 1)

        self.titleBar.raise_()
        self.navigationInterface.displayModeChanged.connect(self.titleBar.raise_)

    def initNavigation(self):
        # enable acrylic effect
        # self.navigationInterface.setAcrylicEnabled(True)
        self.addSubInterface(self.searchInterface, FIF.SEARCH, 'Search')
        self.addSubInterface(self.libraryInterface, FIF.APPLICATION, 'Trainers')
        # add custom widget to bottom

        self.navigationInterface.addWidget(
            routeKey='avatar',
            widget=AvatarWidget(),
            onClick=self.showMessageBox,
            position=NavigationItemPosition.BOTTOM
        )

        self.addSubInterface(self.settingInterface, FIF.SETTING, 'Settings', NavigationItemPosition.BOTTOM)

        # !IMPORTANT: don't forget to set the default route key
        qrouter.setDefaultRouteKey(self.stackWidget, self.libraryInterface.objectName())

        # set the maximum width
        # self.navigationInterface.setExpandWidth(300)

        self.stackWidget.currentChanged.connect(self.onCurrentInterfaceChanged)
        self.stackWidget.setCurrentIndex(1)

    def initWindow(self):
        self.resize(900, 700)
        self.setWindowIcon(QIcon(ICON))
        self.setWindowTitle(TITLE)
        self.titleBar.setAttribute(Qt.WA_StyledBackground)
        desktop = QApplication.desktop().availableGeometry()
        width, height = desktop.width(), desktop.height()
        self.move(width // 2 - self.width() // 2, height // 2 - self.height() // 2)
        self.setQss()

    def addSubInterface(self, interface, icon, text: str, position=NavigationItemPosition.TOP):
        """ add sub interface """
        self.stackWidget.addWidget(interface)
        self.navigationInterface.addItem(
            routeKey=interface.objectName(),
            icon=icon,
            text=text,
            onClick=lambda: self.switchTo(interface),
            position=position,
            tooltip=text
        )

    def setQss(self):
        color = 'dark' if isDarkTheme() else 'light'
        with open(f'resource/{color}/demo.qss', encoding='utf-8') as f:
            self.setStyleSheet(f.read())

    def switchTo(self, widget):
        self.stackWidget.setCurrentWidget(widget)

    def onCurrentInterfaceChanged(self, index):
        widget = self.stackWidget.widget(index)
        self.navigationInterface.setCurrentItem(widget.objectName())
        qrouter.push(self.stackWidget, widget.objectName())

    def showMessageBox(self):
        w = MessageBox("Version Info", "ver. NAN", self)
        w.yesButton.setText('Yes')
        w.cancelButton.setText('No')

        if w.exec():
            QDesktopServices.openUrl(QUrl())

    def resizeEvent(self, e):
        self.titleBar.move(46, 0)
        self.titleBar.resize(self.width() - 46, self.titleBar.height())

    def closeEvent(self, event):
        if self.searchInterface._transfer.busy or self.libraryInterface._transfer.busy:
            event.ignore()
            dialog = MessageBox("Download in progress", "Please wait for the download or update to finish before closing.", self)
            dialog.cancelButton.hide()
            dialog.exec()
            return
        super().closeEvent(event)
