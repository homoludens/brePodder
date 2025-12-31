from PyQt5.QtCore import QObject, pyqtSignal, QUrl
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

class NetworkFetcher(QObject):
    finished = pyqtSignal(bytes)  # Emits the downloaded data
    error = pyqtSignal(str)       # Emits error message
    progress = pyqtSignal(int, int)  # Downloaded, total bytes

    def __init__(self):
        super().__init__()
        self.manager = QNetworkAccessManager()
        self.reply = None

    def fetch(self, url):
        """Start downloading from URL"""
        request = QNetworkRequest(QUrl(url))

        # Optional: Add headers (note the different enum access in PyQt5)
        request.setHeader(QNetworkRequest.UserAgentHeader, "MyApp/1.0")

        self.reply = self.manager.get(request)
        self.reply.finished.connect(self._on_finished)
        self.reply.downloadProgress.connect(self._on_progress)
        self.reply.error.connect(self._on_error)

    def _on_finished(self):
        if self.reply.error() == QNetworkReply.NoError:
            data = self.reply.readAll().data()  # bytes
            self.finished.emit(data)
        self.reply.deleteLater()

    def _on_progress(self, received, total):
        self.progress.emit(received, total)

    def _on_error(self, error_code):
        error_msg = self.reply.errorString()
        self.error.emit(f"Network error: {error_msg}")
        self.reply.deleteLater()

    def cancel(self):
        """Cancel the current download"""
        if self.reply and self.reply.isRunning():
            self.reply.abort()
