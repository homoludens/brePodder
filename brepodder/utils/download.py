from ui.Ui_mainwindow import *
import os
from PyQt5 import QtCore, QtNetwork
from logger import get_logger

logger = get_logger(__name__)


class Download(QtCore.QObject):
    fp = None

    def __init__(self, link, item, downloadId, parent=None):

        QtCore.QObject.__init__(self)

        url_done = QtCore.QUrl(link)
        fileInfo = QtCore.QFileInfo(url_done.path())
        self.fileName = fileInfo.fileName()

        self._status = "downloading"
        self.downloadId = downloadId
        self.CurDir = os.getcwd()
        self.saveFileName = self.CurDir + '/' + self.fileName
        self.itemZaPrenos = item

        self.Parent = parent
        self.manager = QtNetwork.QNetworkAccessManager()
        self.link = QtCore.QUrl(link)

        self.CurrentChannel = None
        self.header = None
        self.totalBytes = 0
        self.bytesRead = 0
        self.tempBytes = 0
        self.resumed = False
        self.paused = False
        self.urlRedirect = None
        self.locationRedirect = None
        self.httpRequestAborted = False
        self.faviconFound = False
        self.i = 0
        self.downloadFile()

    def downloadFile(self):
        self.header = QtNetwork.QNetworkRequest(self.link)
        if self._status == "paused":
            logger.debug("Resuming download")
            resume_bytes = "bytes=" + str(self.bytesRead) + "-"
            logger.debug("Resume bytes: %s", resume_bytes)
            self.header.setRawHeader(b'Range', bytes(resume_bytes, 'utf-8'))

        self.reply = self.manager.get(self.header)
        self.reply.setParent(self)

        self.manager.finished.connect(lambda reply: self.replyFinished( reply, self.fileName))
        self.reply.error.connect(self.on_reply_error)
        self.reply.downloadProgress.connect(self.updateDataReadProgress)
        self.reply.readyRead.connect(self.on_reply_readyRead)

        self.Parent.actionCancel.triggered.connect(self.cancelDownload)
        self.Parent.actionPause.triggered.connect(self.pauseDownload)
        self.Parent.actionResume.triggered.connect(self.resumeDownload)

    def updateDataReadProgress(self, bytesRead, totalBytes):

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


    def replyFinished(self, reply, file):
        logger.debug("Reply finished for %s", file)
        status = self.reply.attribute(QtNetwork.QNetworkRequest.HttpStatusCodeAttribute)
        logger.debug("HTTP status: %s", status)

        if (status == 200):
            self.finishedDownloading = True

            if not(self.fp == None or self.fp.closed):
                self.fp.close()

            self._status = "downloaded"

        elif (status == 302):
            self.link = self.reply.attribute(QtNetwork.QNetworkRequest.RedirectionTargetAttribute)
            self.downloadFile()

        else:
            logger.error("Network error, status: %s", status)

    def on_reply_readyRead(self):
        if (self.fp == None or self.fp.closed):
           self.fp = open( self.saveFileName, "wb")
        read = self.reply.readAll()
        self.fp.write(read)
        self.fp.flush()

        if (read.length() > 0):
            self.startedSaving  = True

    def pauseDownload(self):
        self.reply.abort()
        self._status = "paused"


    def resumeDownload(self):
        if (self._status == "paused"):
            self.fp = open( self.saveFileName, "ab")
            self.downloadFile()


    def cancelDownload(self):
        if self.Parent.tab_2.isVisible():
            if self.itemZaPrenos == self.Parent.itemZaPrekid:
                self.reply.abort()
                self.itemZaPrenos.setText(3, "CANCELED")
                self._status = "stoped"
                self.remove_file()

    def remove_file(self):
        if not(self.fp == None or self.fp.closed):
            self.fp.close()

        if (os.path.exists(self.saveFileName)):
            os.remove(self.saveFileName)

    def on_reply_error(self, code):
        logger.error("Download error (code %s): %s", code, self.reply.errorString())
        self._status = "error"

