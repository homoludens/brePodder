import urllib, sys, os

#import feedparser
from sql import *
from getfavicon import getIcoUrl
import re
from Ui_mainwindow import *
import pprint

#import vimpdb; vimpdb.set_trace()

class Download(QtCore.QObject):
    fp = None

    def __init__(self, link, item, downloadId, parent = None):

        QtCore.QObject.__init__(self)
        self.fileName = link.split('/')[-1]
        self._status = "downloading"
        self.downloadId = downloadId
        self.CurDir = os.getcwd()
        self.saveFileName = self.CurDir + '/' +  self.fileName
        self.itemZaPrenos = item

        self.Parent = parent
        self.manager =  QtNetwork.QNetworkAccessManager()
        self.link = QtCore.QUrl(link)

        self.CurrentChannel = None
        self.header=None
        self.totalBytes=0
        self.bytesRead=0
        self.tempBytes=0
        self.resumed=False
        self.paused=False
        self.urlRedirect=None
        self.locationRedirect = None
        self.httpRequestAborted = False
        self.faviconFound=False
        self.i = 0
        self.downloadFile()


    def downloadFile(self):

        self.header =  QtNetwork.QNetworkRequest(self.link)
        if (self._status == "paused"):
            print("resuming")
            resume_bytes = "bytes=" + str(self.bytesRead) + "-"
            print(resume_bytes)
            self.header.setRawHeader(b'Range', bytes(resume_bytes, 'utf-8'))

        self.reply = self.manager.get(self.header)
        self.reply.setParent(self)

        self.manager.finished.connect( lambda reply: self.replyFinished( reply, self.fileName ))
        self.reply.error.connect( self.on_reply_error )
        self.reply.downloadProgress.connect(self.updateDataReadProgress)
        self.reply.readyRead.connect(self.on_reply_readyRead)
        #self.connect(self.reply, QtCore.SIGNAL("readyRead()"), self.on_reply_readyRead)

        #QtCore.QObject.connect( self.Parent.actionCancel, QtCore.SIGNAL("activated()"), self.cancelDownload )
        self.Parent.actionCancel.triggered.connect(self.cancelDownload )
        #QtCore.QObject.connect( self.Parent.actionPause,  QtCore.SIGNAL("activated()"), self.pauseDownload )
        self.Parent.actionPause.triggered.connect(self.pauseDownload)
        #QtCore.QObject.connect( self.Parent.actionResume, QtCore.SIGNAL("activated()"), self.resumeDownload )
        self.Parent.actionResume.triggered.connect(self.resumeDownload )


    def updateDataReadProgress(self, bytesRead, totalBytes):

        if self.httpRequestAborted:
            return

        if not self._status == "paused":
            if self.tempBytes == 0:
                self.totalBytes = totalBytes
            self.bytesRead = bytesRead

        if self._status == "paused":
            self._status = "downloading"
            print("downloading")
            self.tempBytes = self.bytesRead
            #self.bytesRead = self.bytesRead + bytesRead

        self.bytesRead = self.tempBytes + bytesRead
        #print "bytesRead: " + str(bytesRead)  + "	self.totalBytes: " + str(self.totalBytes)
        try:
            downloaded = str(round(( float(self.bytesRead) / float(self.totalBytes) ) * 100))
        except:
            downloaded = '0'

        self.itemZaPrenos.setText(3, downloaded)


    def replyFinished(self, reply, file):
        print("replyFinished")
        status = self.reply.attribute(QtNetwork.QNetworkRequest.HttpStatusCodeAttribute)
        print(status)

        if (status == 200):
            self.finishedDownloading = True

            if not(self.fp == None or self.fp.closed):
                self.fp.close()

            self._status = "downloaded"
            #self.trigger.emit(QtCore.SIGNAL("statusChanged()"))
            #self.trigger.emit(QtCore.SIGNAL("finished()"))

        elif (status == 302):
            self.link = self.reply.attribute(QtNetwork.QNetworkRequest.RedirectionTargetAttribute)
            #print self.link
            self.downloadFile()

        else:
            print("Network Error")
            print(status)



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
        #self.trigger.emit(QtCore.SIGNAL("statusChanged()"))


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
        print("on_reply_error")
        print(code)
        self._status = "error"
        #self.trigger.emit(QtCore.SIGNAL("statusChanged()"))
        #logging.error("Download(%s): %s" % (code, self.reply.errorString()))
        #self.trigger.emit(QtCore.SIGNAL("error(int, QString)"), code, self.reply.errorString())

