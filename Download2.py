import urllib, sys, os

import feedparser
from sql import *
from getfavicon import getIcoUrl
import re
from Ui_mainwindow import *
import pprint

#import vimpdb; vimpdb.set_trace()

class Download(QtCore.QObject):

    def __init__(self, link, item, downloadId, parent = None):

        QtCore.QObject.__init__(self)
        self.fileName = link.split('/')[-1]

        self.downloadId = downloadId
        self.CurDir = os.getcwd()
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
	
    def downloadFile(self):
        self.reply = self.manager.get(QtNetwork.QNetworkRequest(self.link))
	self.reply.setParent(self)

	self.manager.finished.connect( lambda reply: self.replyFinished( reply, self.fileName ))
	self.reply.downloadProgress.connect(self.updateDataReadProgress)


    def updateDataReadProgress(self, bytesRead, totalBytes):
        if self.httpRequestAborted:
            return
        if not self.resumed:
            if self.tempBytes==0:
                self.totalBytes=totalBytes
            
        if self.resumed:
            self.resumed=False
            self.tempBytes=self.bytesRead

        self.bytesRead=self.tempBytes+bytesRead     
	self.itemZaPrenos.setText(3, str(round(( float(bytesRead) / float(totalBytes) ) * 100)))

    def replyFinished(self, reply, file):
	self.reply = reply
	os.chdir(self.CurDir)
        output = open(file,'wb')
        alltext = self.reply.readAll()
        output.write(alltext)
        output.close()
