from PyQt4 import QtCore, QtGui,  QtNetwork,  QtTest
import feedparser
from sql import *
import os
from getfavicon import getIcoUrl
import Image
import re
import Ui_mainwindow

class Download(object):
    def setup(self):
        self.http = []
        self.httpGetId = []
        self.outFile = []
        self.itemZaPrenos = None
        self.CurDir = None
        self.CurrentChannel = None
        self.header=None
        self.totalBytes=0
        self.bytesRead=0
        self.tempBytes=0
        self.resumed=False
        self.paused=False
        
    def downloadFile(self, link, item):
        self.CurDir = os.getcwd()
        self.itemZaPrenos=item
        print "Download.downloadFile"
        url = QtCore.QUrl(link)
#        print url
        fileInfo = QtCore.QFileInfo(url.path())
        fileName = QtCore.QString(fileInfo.fileName())
    
        if QtCore.QFile.exists(fileName):
            print "There already exists a file called "+fileName+ " in the current directory." 
            if  not self.outFile[0].open(QtCore.QIODevice.Append):
                print "Unable to save file "+fileName
                self.outFile[of] = None
                return
        
            if url.port() != -1:
                self.http[0].setHost(url.host(), url.port())
            else:
                self.http[0].setHost(url.host(), 80)
            if  not url.userName().isEmpty():
                self.http[0].setUser(url.userName(), url.password())
            self.get=QtCore.QString().append('GET')
            self.header=QtNetwork.QHttpRequestHeader(self.get, url.path().replace(" ", "%20"))
            self.header.setValue("Host", url.host())
            self.header.setValue("User-agent", "brePodder")
            if self.bytesRead:
                self.header.setValue("Range", "bytes="+str(self.bytesRead)+"-")
            self.q=None
            self.httpRequestAborted = False
            self.httpGetId.append(self.http[0].request(self.header, self.q, self.outFile[0]))
            return
        self.http.append(QtNetwork.QHttp())
        self.outFile.append(QtCore.QFile(fileName))
        of=len(self.outFile)-1
        ht=len(self.http)-1
        QtCore.QObject.connect(self.http[ht], QtCore.SIGNAL("dataReadProgress(int, int)"), self.updateDataReadProgress)
        QtCore.QObject.connect(self.http[ht], QtCore.SIGNAL("requestFinished(int, bool)"), self.httpRequestFinished)
        QtCore.QObject.connect(self.http[ht], QtCore.SIGNAL("done(bool)"), self.downloadDone)
        QtCore.QObject.connect(Ui_mainwindow.ui.actionCancel,QtCore.SIGNAL("activated()"),self.cancelDownload)
        QtCore.QObject.connect(Ui_mainwindow.ui.actionPause,QtCore.SIGNAL("activated()"),self.pauseDownload)
        QtCore.QObject.connect(Ui_mainwindow.ui.actionResume ,QtCore.SIGNAL("activated()"),self.resumeDownload)
        if  not self.outFile[of].open(QtCore.QIODevice.WriteOnly):
            print "Unable to save file "+fileName
            self.outFile[of] = None
            return
        
        if url.port() != -1:
            self.http[ht].setHost(url.host(), url.port())
        else:
            self.http[ht].setHost(url.host(), 80)
        if  not url.userName().isEmpty():
            self.http[ht].setUser(url.userName(), url.password())
            
##   ovo je kod sa kojim moze da se odradi pause/resume:
#
        self.get=QtCore.QString().append('GET')
        self.header=QtNetwork.QHttpRequestHeader(self.get, url.path().replace(" ", "%20"))
        self.header.setValue("Host", url.host())
        self.header.setValue("User-agent", "brePodder")
#        if self.bytesRead:
#            self.header.setValue("Range", "bytes "+str(self.bytesRead)+"-"+str(self.totalBytes)+"/"+str(self.totalBytes))
        self.q=None
        
        self.httpRequestAborted = False
        self.httpGetId.append(self.http[ht].request(self.header, self.q, self.outFile[of]))
        
#        self.httpRequestAborted = False
#        self.httpGetId.append(self.http[ht].get(url.path().replace(" ", "%20"), self.outFile[of]))
        
    def httpRequestFinished(self, requestId, error):
        of=len(self.outFile)-1
        if self.httpRequestAborted:
            if self.outFile[of] is not None:
                print self.CurDir
                os.chdir(self.CurDir)
                self.outFile[of].close()
                self.outFile[of].remove()
                self.outFile[of] = None
                os.chdir(os.path.expanduser('~')+'/.brePodder') 
            return

        if requestId != self.httpGetId[of]:
            return
        self.outFile[of].close()
    
        if error and not self.paused:
            os.chdir(self.CurDir)
            self.outFile[of].close()
            self.outFile[of].remove()
            self.outFile[of] = None
            os.chdir(os.path.expanduser('~')+'/.brePodder')
        elif not self.paused:
#            fileName = QtCore.QFileInfo(QtCore.QUrl(self.QLineEdit1.text()).path()).fileName()
            self.outFile[of] = None
    
    def updateDataReadProgress(self, bytesRead, totalBytes):
        if self.httpRequestAborted:
            return
        if not self.resumed:
            if self.tempBytes==0:
                self.totalBytes=totalBytes
            self.resumed=True
            self.tempBytes=self.bytesRead
            
        self.bytesRead=self.tempBytes+bytesRead
        self.itemZaPrenos.setText(3, str(self.bytesRead))
#        self.bytesRead=self.bytesRead+bytesRead
        
    
    def downloadDone(self, done):
        if not done:
            url =  self.itemZaPrenos.text(5).toUtf8().data()
            
            p=re.compile("\W")  
#            ChannelDir = p.sub(" ",self.itemZaPrenos.text(0).toUtf8().data().decode())
            ChannelDir = p.sub("",self.itemZaPrenos.text(0).toUtf8().data())
            #ovde smeju da stignu samo ascii karakteri jer je to ime foldera
#            ChannelDir =  self.itemZaPrenos.text(0).toUtf8().data()

            #ova linija me nesto drka kada dodajem novi kanal. trebalo bi da je proverim i vidim sta ce mi
            
            url_done = QtCore.QUrl(url)
            fileInfo = QtCore.QFileInfo(url_done.path())
            file = QtCore.QString(fileInfo.fileName()).toUtf8().data()
            
#            i = url.rfind('/')
#            fileName = url[i+1:]
            os.chdir(ChannelDir)
            if file[-3:]=='ico':
                # this is bad and system depended, but... 
                print ChannelDir
                if os.system('convert '+file.replace(" ","\ ")+'[0] png:'+file.replace(" ","\ "))!=0:
                    os.system('cp ../images/musicstore.png '+file)
                    
#                try:
##                    os.system('convert '+file.replace(" ","\ ")+'[0] png:'+file.replace(" ","\ "))
#                    os.Image.open(file).save('favicon.png', 'PNG')
#                except IOError:
#                    print IOError
#                    Image.open('../images/musicstore.png').save('favicon.png', 'PNG')
                 
            elif file[-3:]=='png' or file[-3:]=='PNG' or file[-3:]=='jpg' or file[-3:]=='JPG':
                print 'logoBig:' +file
                size = 128, 128
                try:
                    im = Image.open(file)
                    im.thumbnail(size, Image.ANTIALIAS) #ovo ne daje bas dobar kvalitet
                    im.save('128'+file)
                except IOError:
                    print IOError
                    Image.open('../images/musicstore.png').save(file, 'PNG')
            
            else:
                try:
                    e=Episode.query.filter_by(enclosure=self.itemZaPrenos.text(5).toUtf8().data()).one()
                    e.localfile=ChannelDir+'/'+ file
                except:
                    print 'InvalidRequestError'
                    print file
                    
#                i = e.enclosure.rfind('/')
#                file = e.enclosure[i+1:]
                
                session.flush()
            os.chdir(os.path.expanduser('~')+'/.brePodder')
            self.itemZaPrenos.setText(3, "DONE")
        else:
            print "Download Error!"
        return
        
    def cancelDownload(self):
        if ui.tab_2.isVisible():
            if self.itemZaPrenos == ui.itemZaPrekid:
                self.itemZaPrenos.setText(3, "CANCELED")
                self.httpRequestAborted = True
                self.http[0].abort()
    
    def pauseDownload(self):
        print "PAUSED"
        self.paused = True
        self.resumed=False
        if ui.tab_2.isVisible():
            if self.itemZaPrenos == ui.itemZaPrekid:
                self.itemZaPrenos.setText(3, "PAUSED")
                self.outFile[0].close()
#                self.httpRequestAborted = True
                self.http[0].abort()
                
    def resumeDownload(self):
        print "RESUMED"
        self.paused = False
        if ui.tab_2.isVisible():
            if self.itemZaPrenos == ui.itemZaPrekid:
                self.itemZaPrenos.setText(3, "RESUMED")
                p=re.compile("\W")  
                ChannelDir = p.sub(" ",self.itemZaPrenos.text(0).toAscii().data())
                os.chdir(ChannelDir)
                resumeLink=self.itemZaPrenos.text(5).toAscii().data()
                item=self.itemZaPrenos
#                self.httpRequestAborted = True
#                self.http[0].abort()
                self.downloadFile(resumeLink, item)
                os.chdir(os.path.expanduser('~')+'/.brePodder')
        
            
