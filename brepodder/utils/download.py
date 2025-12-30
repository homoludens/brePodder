from ui.Ui_mainwindow import *
import os
from typing import Any, Optional, IO

from PyQt5 import QtCore, QtNetwork, QtWidgets

from logger import get_logger

logger = get_logger(__name__)


class Download(QtCore.QObject):
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
        self.manager: QtNetwork.QNetworkAccessManager = QtNetwork.QNetworkAccessManager()
        self.link: QtCore.QUrl = QtCore.QUrl(link)

        self.CurrentChannel: Optional[str] = None
        self.header: Optional[QtNetwork.QNetworkRequest] = None
        self.totalBytes: int = 0
        self.bytesRead: int = 0
        self.tempBytes: int = 0
        self.resumed: bool = False
        self.paused: bool = False
        self.urlRedirect: Optional[QtCore.QUrl] = None
        self.locationRedirect: Optional[str] = None
        self.httpRequestAborted: bool = False
        self.faviconFound: bool = False
        self.i: int = 0
        self.downloadFile()

    def downloadFile(self) -> None:
        self.header = QtNetwork.QNetworkRequest(self.link)
        if self._status == "paused":
            logger.debug("Resuming download")
            resume_bytes = "bytes=" + str(self.bytesRead) + "-"
            logger.debug("Resume bytes: %s", resume_bytes)
            self.header.setRawHeader(b'Range', bytes(resume_bytes, 'utf-8'))

        self.reply = self.manager.get(self.header)
        self.reply.setParent(self)

        self.manager.finished.connect(lambda reply: self.replyFinished(reply, self.fileName))
        self.reply.error.connect(self.on_reply_error)
        self.reply.downloadProgress.connect(self.updateDataReadProgress)
        self.reply.readyRead.connect(self.on_reply_readyRead)

        self.Parent.actionCancel.triggered.connect(self.cancelDownload)
        self.Parent.actionPause.triggered.connect(self.pauseDownload)
        self.Parent.actionResume.triggered.connect(self.resumeDownload)

    def updateDataReadProgress(self, bytesRead: int, totalBytes: int) -> None:

        if self.httpRequestAborted:
            return

        if not self._status == "paused":
            if self.tempBytes == 0:
                self.totalBytes = totalBytes
            self.bytesRead = bytesRead

        if self._status == "paused":
            self._status = "downloading"
            logger.debug("Downloading")
            self.tempBytes = self.bytesRead

        self.bytesRead = self.tempBytes + bytesRead
        try:
            downloaded = str(round((float(self.bytesRead) / float(self.totalBytes)) * 100))
        except (ZeroDivisionError, ValueError, TypeError) as e:
            logger.debug("Failed to calculate download progress: %s", e)
            downloaded = '0'

        self.itemZaPrenos.setText(3, downloaded)

    def replyFinished(self, reply: QtNetwork.QNetworkReply, file: str) -> None:
        logger.debug("Reply finished for %s", file)
        status = self.reply.attribute(QtNetwork.QNetworkRequest.HttpStatusCodeAttribute)
        logger.debug("HTTP status: %s", status)

        if (status == 200):
            self.finishedDownloading = True

            if not (self.fp is None or self.fp.closed):
                self.fp.close()

            self._status = "downloaded"

        elif (status == 302):
            self.link = self.reply.attribute(QtNetwork.QNetworkRequest.RedirectionTargetAttribute)
            self.downloadFile()

        else:
            logger.error("Network error, status: %s", status)

    def on_reply_readyRead(self) -> None:
        if (self.fp is None or self.fp.closed):
            self.fp = open(self.saveFileName, "wb")
        read = self.reply.readAll()
        self.fp.write(read)
        self.fp.flush()

        if (read.length() > 0):
            self.startedSaving = True

    def pauseDownload(self) -> None:
        self.reply.abort()
        self._status = "paused"

    def resumeDownload(self) -> None:
        if (self._status == "paused"):
            self.fp = open(self.saveFileName, "ab")
            self.downloadFile()

    def cancelDownload(self) -> None:
        if self.Parent.tab_2.isVisible():
            if self.itemZaPrenos == self.Parent.itemZaPrekid:
                self.reply.abort()
                self.itemZaPrenos.setText(3, "CANCELED")
                self._status = "stoped"
                self.remove_file()

    def remove_file(self) -> None:
        if not (self.fp is None or self.fp.closed):
            self.fp.close()

        if (os.path.exists(self.saveFileName)):
            os.remove(self.saveFileName)

    def on_reply_error(self, code: int) -> None:
        logger.error("Download error (code %s): %s", code, self.reply.errorString())
        self._status = "error"
