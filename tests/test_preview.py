"""Qt preview checks; run with QT_QPA_PLATFORM=offscreen for headless validation."""

import unittest
from pathlib import Path
from unittest.mock import Mock, patch

try:
    from PyQt5.QtCore import QBuffer, QIODevice
    from PyQt5.QtGui import QPixmap, QColor
    from PyQt5.QtNetwork import QNetworkReply
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtTest import QTest
    from trainer_manager.ui.preview import ImagePreview
except ImportError:
    ImagePreview = None


@unittest.skipIf(ImagePreview is None, "PyQt5 is not installed")
class PreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.preview = ImagePreview()

    def tearDown(self):
        self.preview.clear()
        self.preview.close()

    def picture(self, width=800, height=400):
        image = QPixmap(width, height)
        image.fill(QColor("#478de8"))
        return image

    def test_landscape_and_portrait_preserve_ratio_and_stay_inside_frame(self):
        for width, height in ((800, 400), (400, 800), (400, 400)):
            self.preview.setImage(self.picture(width, height))
            rect = self.preview.imageRect()
            self.assertTrue(self.preview.rect().contains(rect))
            self.assertAlmostEqual(rect.width() / rect.height(), width / height, delta=0.02)
            self.assertLessEqual(abs(rect.center().x() - self.preview.rect().center().x()), 1)

    def test_missing_file_clears_previous_image(self):
        self.preview.setImage(self.picture())
        self.preview.loadFile("this-preview-file-does-not-exist.jpg")
        self.assertTrue(self.preview.image.isNull())
        self.assertEqual(self.preview.message, "No preview available")

    def test_selecting_new_image_aborts_previous_request_and_ignores_late_reply(self):
        old = Mock()
        self.preview._reply = old
        self.preview.setImage(self.picture(400, 800))
        old.abort.assert_called_once()
        self.preview._finished(old, "https://example.com/old.jpg")
        old.readAll.assert_not_called()
        old.deleteLater.assert_called_once()
        self.assertEqual(self.preview.image.height(), 800)

    def test_failed_or_invalid_image_response_is_not_cached(self):
        for error in (QNetworkReply.ContentAccessDenied, QNetworkReply.NoError):
            reply = Mock()
            reply.error.return_value = error
            reply.readAll.return_value = b"<html>Access denied</html>"
            self.preview._reply = reply
            self.preview._finished(reply, "https://example.com/failure")
            self.assertTrue(self.preview.image.isNull())
            self.assertNotIn("https://example.com/failure", self.preview._cache)

    def test_successful_response_is_reused_without_network(self):
        buffer = QBuffer()
        buffer.open(QIODevice.WriteOnly)
        self.picture().save(buffer, "PNG")
        reply = Mock()
        reply.error.return_value = QNetworkReply.NoError
        reply.readAll.return_value = bytes(buffer.data())
        url = "https://example.com/cover.png"
        with patch.object(self.preview._network, "get", return_value=reply):
            self.preview.loadUrl(url)
        self.preview._finished(reply, url)
        self.assertFalse(self.preview.loading)
        self.assertFalse(self.preview._animation.isActive())
        with patch.object(self.preview._network, "get") as get:
            self.preview.loadUrl(url)
        get.assert_not_called()
        self.assertEqual(self.preview.image.width(), 800)
        self.assertFalse(self.preview._animation.isActive())

    def test_timeout_cancels_download_and_allows_retry(self):
        reply = Mock()
        self.preview._reply = reply
        self.preview._timeout()
        reply.abort.assert_called_once()
        self.assertIsNone(self.preview._reply)
        self.assertIn("retry", self.preview.message)

    def test_loading_animation_advances_and_stops_on_timeout(self):
        reply = Mock()
        with patch.object(self.preview._network, "get", return_value=reply):
            self.preview.loadUrl("https://example.com/cover.jpg")
        self.assertTrue(self.preview.loading)
        QTest.qWait(100)
        self.assertNotEqual(self.preview._angle, 0)
        self.preview._timeout()
        self.assertFalse(self.preview.loading)
        self.assertFalse(self.preview._animation.isActive())

    def test_archive_fallback_replaces_pending_image_without_network(self):
        reply = Mock()
        with patch.object(self.preview._network, "get", return_value=reply) as get:
            self.preview.loadUrl("https://example.com/cover.jpg")
            fallback = Path(__file__).resolve().parents[1] / "resource" / "anon.jpg"
            self.preview.loadFile(str(fallback))
        get.assert_called_once()
        reply.abort.assert_called_once()
        self.assertFalse(self.preview.image.isNull())
        self.assertFalse(self.preview.loading)
        self.assertFalse(self.preview._animation.isActive())

    def test_animation_stops_on_failure_and_when_hidden(self):
        for outcome in ("failure", "hide"):
            with self.subTest(outcome=outcome):
                self.preview.show()
                reply = Mock()
                with patch.object(self.preview._network, "get", return_value=reply):
                    self.preview.loadUrl("https://example.com/cover.jpg")
                if outcome == "failure":
                    reply.error.return_value = QNetworkReply.ContentAccessDenied
                    self.preview._finished(reply, "https://example.com/cover.jpg")
                else:
                    self.preview.hide()
                self.assertFalse(self.preview.loading)
                self.assertFalse(self.preview._animation.isActive())

    def test_enlarge_uses_original_image_in_resizable_dialog(self):
        self.preview.setImage(self.picture())
        with patch("trainer_manager.ui.preview.QDialog.exec_", return_value=0) as opened:
            self.preview.enlarge()
        opened.assert_called_once()


if __name__ == "__main__":
    unittest.main()
