"""Aspect-preserving previews with cancellable, in-memory image loading."""

from collections import OrderedDict

from PyQt5.QtCore import Qt, QRect, QSize, QTimer, QUrl
from PyQt5.QtGui import QColor, QPainter, QPen, QPixmap, QPalette
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PyQt5.QtWidgets import QWidget, QDialog, QVBoxLayout, QLabel, QDialogButtonBox


class ImageCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = QPixmap()
        self.message = "No preview available"
        self.loading = False
        self._angle = 0
        self.setMinimumSize(120, 100)

    def sizeHint(self):
        return QSize(250, 190)

    def imageRect(self):
        if self.image.isNull():
            return QRect()
        area = self.rect().adjusted(10, 10, -10, -10)
        size = self.image.size().scaled(area.size(), Qt.KeepAspectRatio)
        rect = QRect(0, 0, size.width(), size.height())
        rect.moveCenter(area.center())
        return rect

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        painter.setPen(self.palette().color(QPalette.Mid))
        painter.setBrush(self.palette().color(QPalette.Base))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 8, 8)
        if self.image.isNull():
            text_rect = self.rect().adjusted(16, 16, -16, -16)
            if self.loading:
                ring = QRect(0, 0, 32, 32)
                ring.moveCenter(self.rect().center())
                ring.translate(0, -14)
                painter.setBrush(Qt.NoBrush)
                painter.setPen(QPen(self.palette().color(QPalette.Mid), 3))
                painter.drawEllipse(ring)
                painter.setPen(QPen(self.palette().color(QPalette.Highlight), 3,
                                    Qt.SolidLine, Qt.RoundCap))
                painter.drawArc(ring, -self._angle * 16, 100 * 16)
                text_rect.setTop(ring.bottom() + 10)
                text_rect.setHeight(30)
            painter.setPen(self.palette().color(QPalette.Text))
            painter.drawText(text_rect, Qt.AlignCenter | Qt.TextWordWrap, self.message)
        else:
            painter.drawPixmap(self.imageRect(), self.image)


class ImagePreview(ImageCanvas):
    MAX_IMAGE_BYTES = 12 * 1024 * 1024
    MAX_CACHED_IMAGES = 8

    def __init__(self, parent=None, dark=False):
        super().__init__(parent)
        palette = self.palette()
        palette.setColor(QPalette.Base, QColor("#24272c" if dark else "#f5f6f8"))
        palette.setColor(QPalette.Window, QColor("#202328" if dark else "#ffffff"))
        palette.setColor(QPalette.Text, QColor("#cbd2dc" if dark else "#586273"))
        palette.setColor(QPalette.WindowText, palette.color(QPalette.Text))
        palette.setColor(QPalette.Mid, QColor("#3d424a" if dark else "#dce0e6"))
        palette.setColor(QPalette.Highlight, QColor("#78b9ff" if dark else "#1675ce"))
        self.setPalette(palette)
        self.setFixedSize(250, 190)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAccessibleName("Image preview")
        self._network = QNetworkAccessManager(self)
        self._reply = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._timeout)
        self._animation = QTimer(self)
        self._animation.setInterval(30)
        self._animation.timeout.connect(self._animate)
        self._cache = OrderedDict()

    def _animate(self):
        self._angle = (self._angle + 12) % 360
        self.update()

    def _cancel(self):
        self._timer.stop()
        self._animation.stop()
        self.loading = False
        reply, self._reply = self._reply, None
        if reply is not None:
            reply.abort()

    def setImage(self, image):
        self._cancel()
        self.image = QPixmap(image)
        self.message = "No preview available"
        self.setCursor(Qt.PointingHandCursor if not self.image.isNull() else Qt.ArrowCursor)
        self.setToolTip("Click to enlarge" if not self.image.isNull() else self.message)
        self.update()

    def clear(self, message="No preview available"):
        self.setImage(QPixmap())
        self.message = message
        self.setToolTip(message)
        self.update()

    def loadFile(self, path):
        self.setImage(QPixmap(path))

    def loadUrl(self, url):
        self.clear("Loading preview…")
        if url in self._cache:
            self._cache.move_to_end(url)
            self.setImage(self._cache[url])
            return
        if QUrl(url).scheme() not in ("https", "http"):
            self.clear()
            return
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b"User-Agent", b"Mozilla/5.0")
        request.setAttribute(QNetworkRequest.RedirectPolicyAttribute,
                             QNetworkRequest.NoLessSafeRedirectPolicy)
        reply = self._network.get(request)
        self._reply = reply
        reply.downloadProgress.connect(lambda received, total: self._progress(reply, received, total))
        reply.finished.connect(lambda: self._finished(reply, url))
        self.loading = True
        self._angle = 0
        self._animation.start()
        self.update()
        self._timer.start(10000)

    def _progress(self, reply, received, total):
        if reply is self._reply and max(received, total) > self.MAX_IMAGE_BYTES:
            self.clear("Preview image is too large")

    def _timeout(self):
        self.clear("Preview timed out. Select the item to retry.")

    def _finished(self, reply, url):
        try:
            if reply is not self._reply:
                return
            self._reply = None
            self._timer.stop()
            image = QPixmap()
            if reply.error() != QNetworkReply.NoError:
                self.clear("Preview unavailable. Select the item to retry.")
                return
            content = bytes(reply.readAll())
            if len(content) > self.MAX_IMAGE_BYTES or not image.loadFromData(content):
                self.clear("Preview unavailable")
                return
            # Bound decoded memory while retaining enough detail for the enlarged view.
            if max(image.width(), image.height()) > 2400:
                image = image.scaled(2400, 2400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._cache[url] = image
            while len(self._cache) > self.MAX_CACHED_IMAGES:
                self._cache.popitem(last=False)
            self.setImage(image)
        finally:
            reply.deleteLater()

    def hideEvent(self, event):
        if self._reply is not None:
            self.clear("Select the item to load its preview.")
        super().hideEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.enlarge()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.enlarge()
        else:
            super().keyPressEvent(event)

    def enlarge(self):
        if self.image.isNull():
            return
        dialog = QDialog(self.window())
        dialog.setPalette(self.palette())
        dialog.setWindowTitle("Image preview")
        layout = QVBoxLayout(dialog)
        canvas = ImageCanvas(dialog)
        canvas.image = QPixmap(self.image)
        layout.addWidget(canvas, 1)
        layout.addWidget(QLabel(f"{self.image.width()} × {self.image.height()}", dialog))
        buttons = QDialogButtonBox(QDialogButtonBox.Close, parent=dialog)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        available = self.screen().availableGeometry().size()
        dialog.resize(min(960, int(available.width() * 0.85)),
                      min(720, int(available.height() * 0.85)))
        dialog.exec_()
        dialog.deleteLater()
