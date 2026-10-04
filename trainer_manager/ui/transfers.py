"""Background transfer lifecycle and a progress strip embedded in an existing button."""

from PyQt5.QtCore import QObject, QThread, QEvent, pyqtSignal
from PyQt5.QtWidgets import QProgressBar


class TransferWorker(QThread):
    progress = pyqtSignal(object, object)
    stage = pyqtSignal(str)
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task

    def run(self):
        try:
            self.succeeded.emit(self.task(progress=self.progress.emit, stage=self.stage.emit))
        except Exception as error:
            self.failed.emit(str(error))


class ButtonProgress(QProgressBar):
    def __init__(self, button):
        super().__init__(button)
        self.button = button
        self.setTextVisible(False)
        self.setStyleSheet("QProgressBar { border: none; border-radius: 2px; background: #45515e; }"
                           "QProgressBar::chunk { background: #78b9ff; border-radius: 2px; }")
        button.installEventFilter(self)
        self._place()
        self.hide()

    def _place(self):
        self.setGeometry(6, self.button.height() - 6, max(1, self.button.width() - 12), 3)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Resize:
            self._place()
        return super().eventFilter(watched, event)

    def stage(self, text):
        self.button.setText(text)
        self.setRange(0, 0)
        self.show()

    def progress(self, done, total):
        if total > 0:
            percent = min(100, int(done * 100 / total))
            self.setRange(0, 100)
            self.setValue(percent)
            self.button.setText(f"Downloading {percent}%")
        else:
            self.setRange(0, 0)
            self.button.setText(f"Downloading {done / (1024 * 1024):.1f} MB")
        self.show()


class DownloadSession(QObject):
    finished = pyqtSignal(bool)

    def __init__(self, button, parent=None):
        super().__init__(parent)
        self.indicator = ButtonProgress(button)
        self.worker = None

    @property
    def busy(self):
        return self.worker is not None

    def start(self, task, success, failure, finished):
        if self.busy:
            return
        self._success, self._failure, self._finished = success, failure, finished
        self.ok = False
        self.indicator.stage("Connecting…")
        self.worker = TransferWorker(task, self)
        self.worker.progress.connect(self.indicator.progress)
        self.worker.stage.connect(self.indicator.stage)
        self.worker.succeeded.connect(self._complete)
        self.worker.failed.connect(self._error)
        self.worker.finished.connect(self._finish)
        self.worker.start()

    def _complete(self, result):
        self.indicator.hide()
        try:
            self._success(result)
            self.ok = True
        except Exception as error:
            self._error(str(error))

    def _error(self, error):
        self.indicator.hide()
        self._failure(error)

    def _finish(self):
        self.indicator.hide()
        self.worker.deleteLater()
        self.worker = None
        self._finished(self.ok)
        self.finished.emit(self.ok)
