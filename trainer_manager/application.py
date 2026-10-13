"""application: extracted application components."""

import sys
import os
import atexit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from trainer_manager import services as utils
from trainer_manager.runtime import ICON
from trainer_manager.ui.window import Window


def exit_handler():
    """
    Remove image cache if there is when exiting .
    :return: None
    """
    try:
        os.remove("resources/img_cache/image.jpg")
    except FileNotFoundError:
        pass


def setup_check():
    utils.Data.prepare_directories(utils.Data.load_config())


def main():
    """Run the desktop application with the original startup sequence."""
    print(os.getcwd())
    atexit.register(exit_handler)
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(ICON))
    setup_check()
    w = Window()
    w.show()
    app.exec_()
