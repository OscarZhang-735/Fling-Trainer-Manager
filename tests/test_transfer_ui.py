"""Qt worker lifecycle and embedded progress, without downloads or file mutations."""

import unittest
from threading import Event
from unittest.mock import Mock

try:
    from PyQt5.QtCore import QThread
    from PyQt5.QtWidgets import QApplication, QPushButton
    from PyQt5.QtTest import QTest
    from trainer_manager.ui.transfers import DownloadSession, ButtonProgress
except ImportError:
    DownloadSession = None


@unittest.skipIf(DownloadSession is None, "PyQt5 is not installed")
class TransferUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def wait_for_finish(self, session):
        for _ in range(200):
            if not session.busy:
                return
            QTest.qWait(10)
        session.worker.wait(5000)
        self.fail("The worker did not finish")

    def test_progress_button_supports_known_and_unknown_sizes(self):
        button = QPushButton("Download")
        bar = ButtonProgress(button)
        bar.progress(25, 100)
        self.assertEqual(button.text(), "Downloading 25%")
        self.assertEqual(bar.value(), 25)
        bar.progress(2 * 1024 * 1024, 0)
        self.assertEqual(button.text(), "Downloading 2.0 MB")
        self.assertEqual(bar.maximum(), 0)
        bar.stage("Extracting…")
        self.assertEqual(button.text(), "Extracting…")
        button.close()

    def test_task_runs_off_ui_thread_and_success_returns_on_ui_thread(self):
        button = QPushButton()
        session = DownloadSession(button)
        threads, callbacks = [], []
        def task(progress, stage):
            threads.append(QThread.currentThread())
            stage("Extracting…")
            progress(25, 100)
            return "executable.exe"
        session.start(task, lambda result: callbacks.append((QThread.currentThread(), result)),
                      Mock(), lambda ok: callbacks.append(ok))
        self.wait_for_finish(session)
        self.assertNotEqual(threads[0], self.app.thread())
        self.assertEqual(callbacks, [(self.app.thread(), "executable.exe"), True])
        self.assertTrue(session.indicator.isHidden())
        button.close()

    def test_worker_failure_and_registration_failure_restore_idle_state(self):
        for fail_in_task in (True, False):
            button = QPushButton()
            session = DownloadSession(button)
            errors, finished = [], []
            def task(progress, stage):
                if fail_in_task:
                    raise RuntimeError("network failed")
                return "file.exe"
            def success(result):
                raise OSError("registration failed")
            session.start(task, success, errors.append, finished.append)
            self.wait_for_finish(session)
            self.assertEqual(finished, [False])
            self.assertEqual(errors, ["network failed" if fail_in_task else "registration failed"])
            self.assertTrue(session.indicator.isHidden())
            button.close()

    def test_busy_session_ignores_duplicate_click(self):
        button = QPushButton()
        session = DownloadSession(button)
        gate = Event()
        calls = []
        def task(progress, stage):
            calls.append(1)
            gate.wait(2)
        try:
            session.start(task, Mock(), Mock(), Mock())
            session.start(task, Mock(), Mock(), Mock())
        finally:
            gate.set()
            self.wait_for_finish(session)
        self.assertEqual(calls, [1])
        button.close()
