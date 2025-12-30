from ui.Ui_mainwindow import *
import os
import threading
from typing import Any, Optional, IO

import requests
from PyQt5 import QtCore, QtWidgets

from logger import get_logger

logger = get_logger(__name__)


class Download(QtCore.QObject):
    # Qt signals for thread-safe communication
    progress_updated = QtCore.pyqtSignal(int, int)
    download_finished = QtCore.pyqtSignal(str, int)
    download_error = QtCore.pyqtSignal(str)

    fp: Optional[IO[bytes]] = None

    def __init__(self, link: str, item: QtWidgets.QTreeWidgetItem, downloadId: int, parent: Any = None) -> None:

        QtCore.QObject.__init__(self)

        url_done = QtCore.QUrl(link)
        fileInfo = QtCore.QFileInfo(url_done.path())
        self.fileName: str = fileInfo.fileName()

        self._status: str = "downloading"
        self.downloadId: int = downloadId
        self.CurDir: str = os.getcwd()
        self.saveFileName: str = self.CurDir + '/' + self.fileName
        self.itemZaPrenos: QtWidgets.QTreeWidgetItem = item

        self.Parent: Any = parent
        self.link: str = link

        self.CurrentChannel: Optional[str] = None
        self.totalBytes: int = 0
        self.bytesRead: int = 0
        self.tempBytes: int = 0
        self.resumed: bool = False
        self.paused: bool = False
        self.httpRequestAborted: bool = False
        self.faviconFound: bool = False
        self.i: int = 0
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._download_thread: Optional[threading.Thread] = None

        # Connect signals
        self.progress_updated.connect(self._update_progress_ui)
        self.download_finished.connect(self._on_finished)
        self.download_error.connect(self._on_error)

        self.downloadFile()

    def downloadFile(self) -> None:
        self._download_thread = threading.Thread(target=self._download_worker, daemon=True)
        self._download_thread.start()

        self.Parent.actionCancel.triggered.connect(self.cancelDownload)
        self.Parent.actionPause.triggered.connect(self.pauseDownload)
        self.Parent.actionResume.triggered.connect(self.resumeDownload)

    def _download_worker(self) -> None:
        try:
            headers = {}
            if self._status == "paused" and self.bytesRead > 0:
                logger.debug("Resuming download from byte %d", self.bytesRead)
                headers['Range'] = f'bytes={self.bytesRead}-'
                mode = 'ab'
            else:
                mode = 'wb'

            response = requests.get(self.link, headers=headers, stream=True, timeout=30)
            
            # Handle redirects
            if response.status_code == 302:
                self.link = response.headers.get('Location', response.url)
                logger.debug("Redirected to: %s", self.link)
                self._download_worker()  # Retry with new URL
                return
            
            if response.status_code not in (200, 206):
                self.download_error.emit(f"HTTP {response.status_code}")
                return

            # Get total file size
            if response.status_code == 200:
                self.totalBytes = int(response.headers.get('content-length', 0))
                self.bytesRead = 0
                self.tempBytes = 0
            elif response.status_code == 206:  # Partial content (resume)
                content_range = response.headers.get('content-range', '')
                if '/' in content_range:
                    self.totalBytes = int(content_range.split('/')[-1])
                self.tempBytes = self.bytesRead

            # Open file for writing
            self.fp = open(self.saveFileName, mode)

            # Download in chunks
            chunk_size = 8192
            for chunk in response.iter_content(chunk_size=chunk_size):
                # Check if paused
                if self._pause_event.is_set():
                    logger.debug("Download paused")
                    break
                
                # Check if cancelled
                if self._stop_event.is_set():
                    logger.debug("Download cancelled")
                    break

                if chunk:
                    self.fp.write(chunk)
                    self.fp.flush()
                    bytes_downloaded = len(chunk)
                    self.bytesRead += bytes_downloaded
                    self.progress_updated.emit(self.tempBytes + self.bytesRead, self.totalBytes)

            if not (self.fp is None or self.fp.closed):
                self.fp.close()

            # Check if download completed successfully
            if not self._stop_event.is_set() and not self._pause_event.is_set():
                self.download_finished.emit(self.fileName, 200)
            elif self._pause_event.is_set():
                logger.debug("Download paused at %d bytes", self.bytesRead)

        except requests.exceptions.SSLError as e:
            logger.error("SSL error during download: %s", e)
            self.download_error.emit(f"SSL error: {e}")
        except requests.exceptions.RequestException as e:
            logger.error("Network error during download: %s", e)
            self.download_error.emit(f"Network error: {e}")
        except Exception as e:
            logger.error("Unexpected error during download: %s", e)
            self.download_error.emit(f"Error: {e}")

    def _update_progress_ui(self, bytesRead: int, totalBytes: int) -> None:
        if self.httpRequestAborted:
            return

        try:
            if totalBytes > 0:
                downloaded = str(round((float(bytesRead) / float(totalBytes)) * 100))
            else:
                downloaded = '0'
        except (ZeroDivisionError, ValueError, TypeError) as e:
            logger.debug("Failed to calculate download progress: %s", e)
            downloaded = '0'

        self.itemZaPrenos.setText(3, downloaded)

    def _on_finished(self, file: str, status: int) -> None:
        logger.debug("Download finished for %s", file)
        self._status = "downloaded"

    def _on_error(self, error: str) -> None:
        logger.error("Download failed: %s", error)
        self._status = "error"

    def pauseDownload(self) -> None:
        logger.debug("Pausing download")
        self._pause_event.set()
        self._status = "paused"

    def resumeDownload(self) -> None:
        if self._status == "paused":
            logger.debug("Resuming download")
            self._pause_event.clear()
            self.downloadFile()

    def cancelDownload(self) -> None:
        if self.Parent.tab_2.isVisible():
            if self.itemZaPrenos == self.Parent.itemZaPrekid:
                logger.debug("Cancelling download")
                self._stop_event.set()
                if self._download_thread and self._download_thread.is_alive():
                    self._download_thread.join(timeout=2.0)
                self.itemZaPrenos.setText(3, "CANCELED")
                self._status = "stoped"
                self.remove_file()

    def remove_file(self) -> None:
        if not (self.fp is None or self.fp.closed):
            self.fp.close()

        if os.path.exists(self.saveFileName):
            os.remove(self.saveFileName)
