"""
Download manager for brePodder.

Handles downloading podcast episodes with pause/resume support.
"""
import os
import threading
from typing import Any, Optional, IO

import requests
from PyQt6 import QtCore, QtWidgets

from brepodder.logger import get_logger

logger = get_logger(__name__)


class Download(QtCore.QObject):
    """
    Download manager for a single file.

    Supports pause, resume, and cancel operations.
    Uses threading to avoid blocking the UI.
    """
    # Qt signals for thread-safe communication
    progress_updated = QtCore.pyqtSignal(int, int)
    download_finished = QtCore.pyqtSignal(str, str, int)  # fileName, saveFilePath, downloadId
    download_error = QtCore.pyqtSignal(str)

    fp: Optional[IO[bytes]] = None

    def __init__(self, link: str, item: QtWidgets.QTreeWidgetItem, download_id: int, parent: Any = None) -> None:

        QtCore.QObject.__init__(self)

        url_done = QtCore.QUrl(link)
        file_info = QtCore.QFileInfo(url_done.path())
        self.file_name: str = file_info.fileName()

        self._status: str = "downloading"
        self.download_id: int = download_id
        self.current_dir: str = os.getcwd()
        self.save_file_name: str = self.current_dir + '/' + self.file_name
        self.item_for_transfer: QtWidgets.QTreeWidgetItem = item

        self.parent: Any = parent
        self.link: str = link

        self.current_channel: Optional[str] = None
        self.total_bytes: int = 0
        self.bytes_read: int = 0
        self.temp_bytes: int = 0
        self.resumed: bool = False
        self.paused: bool = False
        self.http_request_aborted: bool = False
        self.favicon_found: bool = False
        self.i: int = 0
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._download_thread: Optional[threading.Thread] = None

        # Connect signals
        self.progress_updated.connect(self._update_progress_ui)
        self.download_finished.connect(self._on_finished)
        self.download_error.connect(self._on_error)

        self.download_file()

    def download_file(self) -> None:
        """Start the download in a background thread."""
        self._download_thread = threading.Thread(target=self._download_worker, daemon=True)
        self._download_thread.start()

        self.parent.actionCancel.triggered.connect(self.cancel_download)
        self.parent.actionPause.triggered.connect(self.pause_download)
        self.parent.actionResume.triggered.connect(self.resume_download)

    def _download_worker(self) -> None:
        """Background worker that performs the actual download."""
        try:
            headers = {}
            if self._status == "paused" and self.bytes_read > 0:
                logger.debug("Resuming download from byte %d", self.bytes_read)
                headers['Range'] = f'bytes={self.bytes_read}-'
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
                self.total_bytes = int(response.headers.get('content-length', 0))
                self.bytes_read = 0
                self.temp_bytes = 0
            elif response.status_code == 206:  # Partial content (resume)
                content_range = response.headers.get('content-range', '')
                if '/' in content_range:
                    self.total_bytes = int(content_range.split('/')[-1])
                self.temp_bytes = self.bytes_read

            # Open file for writing
            self.fp = open(self.save_file_name, mode)

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
                    self.bytes_read += bytes_downloaded
                    self.progress_updated.emit(self.temp_bytes + self.bytes_read, self.total_bytes)

            if not (self.fp is None or self.fp.closed):
                self.fp.close()

            # Check if download completed successfully
            if not self._stop_event.is_set() and not self._pause_event.is_set():
                self.download_finished.emit(self.file_name, self.save_file_name, self.download_id)
            elif self._pause_event.is_set():
                logger.debug("Download paused at %d bytes", self.bytes_read)

        except requests.exceptions.SSLError as e:
            logger.error("SSL error during download: %s", e)
            self.download_error.emit(f"SSL error: {e}")
        except requests.exceptions.RequestException as e:
            logger.error("Network error during download: %s", e)
            self.download_error.emit(f"Network error: {e}")
        except Exception as e:
            logger.error("Unexpected error during download: %s", e)
            self.download_error.emit(f"Error: {e}")

    def _update_progress_ui(self, bytes_read: int, total_bytes: int) -> None:
        """Update the UI with download progress."""
        if self.http_request_aborted:
            return

        try:
            if total_bytes > 0:
                downloaded = str(round((float(bytes_read) / float(total_bytes)) * 100))
            else:
                downloaded = '0'
        except (ZeroDivisionError, ValueError, TypeError) as e:
            logger.debug("Failed to calculate download progress: %s", e)
            downloaded = '0'

        self.item_for_transfer.setText(3, downloaded)

    def _on_finished(self, file: str, save_path: str, download_id: int) -> None:
        """Handle download completion."""
        logger.debug("Download finished for %s at %s", file, save_path)
        self._status = "downloaded"

    def _on_error(self, error: str) -> None:
        """Handle download error."""
        logger.error("Download failed: %s", error)
        self._status = "error"

    def pause_download(self) -> None:
        """Pause the current download."""
        logger.debug("Pausing download")
        self._pause_event.set()
        self._status = "paused"

    def resume_download(self) -> None:
        """Resume a paused download."""
        if self._status == "paused":
            logger.debug("Resuming download")
            self._pause_event.clear()
            self.download_file()

    def cancel_download(self) -> None:
        """Cancel the current download."""
        if self.parent.tab_2.isVisible():
            if self.item_for_transfer == self.parent.item_for_cancel:
                logger.debug("Cancelling download")
                self._stop_event.set()
                if self._download_thread and self._download_thread.is_alive():
                    self._download_thread.join(timeout=2.0)
                self.item_for_transfer.setText(3, "CANCELED")
                self._status = "stopped"
                self.remove_file()

    def remove_file(self) -> None:
        """Remove the partially downloaded file."""
        if not (self.fp is None or self.fp.closed):
            self.fp.close()

        if os.path.exists(self.save_file_name):
            os.remove(self.save_file_name)
