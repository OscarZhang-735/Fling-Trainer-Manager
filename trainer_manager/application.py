"""application: extracted application components."""

import sys
import os
import atexit
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from trainer_manager import services as utils
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
    requirements = ["./data", "./resources/game_covers", "./resources/img_cache"]
    missing = []
    for r in requirements:
        if not os.path.exists(r):
            missing.append(r)
    if len(missing) > 0:
        utils.Help.warning("Warning", f"Key files/directories are missing: {missing}.")
        exit()


def main():
    """Run the desktop application with the original startup sequence."""
    print(os.getcwd())
    atexit.register(exit_handler)
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    setup_check()
    app.exec_()
