"""Shared dialogs and fonts; Qt is loaded only when used."""

import requests


class Help:
    @staticmethod
    def anonymous_report(title, content, time):
        # Temporally abandoned
        api_url = "https://api.guerrillamail.com/ajax.php"
        receiver = "2778940377@qq.com"
        params = {
            "f": "send",
            "body": f"Report Time: {time}\nIssue Description:\n{content}",
            "to": receiver,
            "subject": title,
            "from": "noreply@guerrillamail.com"
        }
        response = requests.get(api_url, params=params)
        if response.status_code == 200:
            print("Report successfully")
        else:
            print(f"Failed to report. Status code: {response.status_code}")

    @staticmethod
    def report(title, content, time):
        # Temporally abandoned
        pass

    @staticmethod
    def warning(title, content, terminate=False):
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.warning(None, title, content, QMessageBox.Yes)
        if terminate:
            exit(1)

    @staticmethod
    def info(title, content):
        from PyQt5.QtWidgets import QMessageBox

        QMessageBox.about(None, title, content)


class Font:
    def __init__(self):
        from PyQt5.QtGui import QFont

        self.STANDARD_FONT = QFont()
        self.STANDARD_FONT.setFamily("Segoe UI")
        self.STANDARD_FONT.setPointSize(10)
        self.STANDARD_MIDDLE_FONT = QFont()
        self.STANDARD_MIDDLE_FONT.setFamily("Segoe UI")
        self.STANDARD_MIDDLE_FONT.setPointSize(12)
        self.STANDARD_HUGE_FONT = QFont()
        self.STANDARD_HUGE_FONT.setFamily("Segoe UI")
        self.STANDARD_HUGE_FONT.setPointSize(18)
