import urllib, sys, os

import feedparser
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
        self.link = QtCore.QUrl(QtCore.QString(link))

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
	     print "resuming"
	     #self.reply.setRawHeader("Accept-Ranges", "bytes " + str(self.bytesRead) + "-" + str(self.totalBytes) + "/" + str(self.totalBytes) )
	     self._status == "downlaod"
	     print self.reply

	#print self.header.rawHeaderList()
        self.reply = self.manager.get(self.header)
	self.reply.setParent(self)

	self.manager.finished.connect( lambda reply: self.replyFinished( reply, self.fileName ))
	self.reply.downloadProgress.connect(self.updateDataReadProgress)
	self.reply.readyRead.connect(self.on_reply_readyRead)
	#self.connect(self.reply, QtCore.SIGNAL("readyRead()"), self.on_reply_readyRead)



        QtCore.QObject.connect( self.Parent.actionCancel, QtCore.SIGNAL("activated()"), self.cancelDownload )
        QtCore.QObject.connect( self.Parent.actionPause,  QtCore.SIGNAL("activated()"), self.pauseDownload )
        QtCore.QObject.connect( self.Parent.actionResume, QtCore.SIGNAL("activated()"), self.resumeDownload )

 



    def updateDataReadProgress(self, bytesRead, totalBytes):
        if self.httpRequestAborted:
            return

        if not self._status == "paused":
            if self.tempBytes == 0:
                self.totalBytes = totalBytes
            
        if self._status == "paused":
            #self._status = "downloading"
            self.tempBytes = self.bytesRead

        self.bytesRead = self.tempBytes + bytesRead     
	self.itemZaPrenos.setText(3, str(round(( float(self.bytesRead) / float(self.totalBytes) ) * 100)))

    def replyFinished(self, reply, file):
	#self.reply = reply
	#os.chdir(self.CurDir)
        #output = open(file,'wb')
        #alltext = self.reply.readAll()
        #output.write(alltext)
        #self.fp.close()
	print "replyFinished"
        self.finishedDownloading = True;

        if not(self.startedSaving):
            return;

        if not(self.fp == None or self.fp.closed):
            self.fp.close()

        self._status = "download"
        self.emit(QtCore.SIGNAL("statusChanged()"))
        self.emit(QtCore.SIGNAL("finished()"))



    def on_reply_readyRead(self):
	#print dir(self.reply)
	#print self.reply.rawHeader("Accept-Ranges")
#PyQt4.QtCore.QByteArray('Server'), PyQt4.QtCore.QByteArray('Date'), PyQt4.QtCore.QByteArray('Content-Type'), PyQt4.QtCore.QByteArray('Content-Length'), PyQt4.QtCore.QByteArray('Last-Modified'), PyQt4.QtCore.QByteArray('Connection'), PyQt4.QtCore.QByteArray('Keep-Alive'), PyQt4.QtCore.QByteArray('Expires'), PyQt4.QtCore.QByteArray('Cache-Control'), PyQt4.QtCore.QByteArray('Accept-Ranges')

        if (self.fp == None or self.fp.closed):
            #dir = os.path.dirname(self.CurDir)
            #if not(os.path.exists(dir)):
            #    os.mkdir(dir)
            self.fp = open( self.saveFileName, "w")
        read = self.reply.readAll()
        self.fp.write(read)
        self.fp.flush()

        if (read.length() > 0): 
            self.startedSaving  = True


    def pauseDownload(self):
        self.reply.abort()

        self._status = "paused"
        self.emit(QtCore.SIGNAL("statusChanged()"))

    def resumeDownload(self):
	if (self._status == "paused"):
		self.fp = open( self.saveFileName, "a")
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
        self._status = "error"
        self.emit(QtCore.SIGNAL("statusChanged()"))
        logging.error("Download(%s): %s" % (code, self.reply.errorString()))
        self.emit(QtCore.SIGNAL("error(int, QString)"), code, self.reply.errorString())
 
