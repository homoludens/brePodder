#from PyQt4 import QtCore, QtGui,  QtNetwork,  QtTest
import feedparser
from sql import *
#import os
from getfavicon import getIcoUrl
import Image
import re
from Ui_mainwindow import *

class Download(QtCore.QObject):
    def setup(self, ui):
        self.ui=ui
        self.itemZaPrenos = None
        self.CurDir = None
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
#        self.downloadId=0
       
    def downloadFile(self, link, item, downloadId):
        self.downloadId=downloadId
        self.CurDir = os.getcwd()
        self.itemZaPrenos=item
        url = QtCore.QUrl(link)
        fileInfo = QtCore.QFileInfo(url.path())
        fileName = QtCore.QString(fileInfo.fileName())
        
#        httpIndex=self.ui.itemsDownloading.index(self.itemZaPrenos.text(5))
        
        # Qt 4.4+ doesn't wont to show images named favicon.ico, favicon.icon is ok
#        if '.ico' in fileName:
#            fileName = fileName.replace('.ico','.icon')
            
        if QtCore.QFile.exists(fileName):
            if self.locationRedirect:
                fileDelete=QtCore.QFile(fileName)
#                fileDelete.remove()
            elif not self.paused:
                print "There already exists a file called "+fileName+ " in the current directory." 
#TODO: kada fajl vec postoji ovde izbacuje gresku "IndexError: list index out of range" jer je self.ui.outFile prazan
                if  not self.ui.outFile[downloadId][1].open(QtCore.QIODevice.Append):
                    print "Unable to save file "+fileName
#                   TODO: what does this line do?
#                    self.ui.outFile[of] = None
                    return
        
            if url.port() != -1:
                self.ui.http[downloadId][1].setHost(url.host(), url.port())
            else:
                self.ui.http[downloadId][1].setHost(url.host(), 80)
# TODO: insert setting of username and password for podcast download. does anyone need this?
            if  not url.userName().isEmpty():
                self.ui.http[downloadId][1].setUser(url.userName(), url.password())
            
#           important for some hosts (example libsyn), which have some query in url 
            if url.hasQuery():
                realUrl=url.path()+'?'+url.encodedQuery()
            else:
                realUrl=url.path()
   #         from PyQt4 import QtNetwork
            self.get=QtCore.QString().append('GET')
            self.header=QtNetwork.QHttpRequestHeader(self.get, realUrl.replace(" ", "%20"))
            self.header.setValue("Host", url.host())
            self.header.setValue("User-agent", "brePodder")
            if self.bytesRead:
                self.header.setValue("Range", "bytes="+str(self.bytesRead)+"-")
            self.q=None
            self.httpRequestAborted = False
            self.ui.httpGetId.append(self.ui.http[downloadId][1].request(self.header, self.q, self.ui.outFile[downloadId][1]))
            return
            
        self.ui.http.append((downloadId, QtNetwork.QHttp()))
        self.ui.outFile.append((downloadId, QtCore.QFile(fileName)))
        
        of=downloadId
        ht=downloadId
        
        QtCore.QObject.connect(self.ui.actionCancel,QtCore.SIGNAL("activated()"),self.cancelDownload)
        QtCore.QObject.connect(self.ui.actionPause,QtCore.SIGNAL("activated()"),self.pauseDownload)
        QtCore.QObject.connect(self.ui.actionResume ,QtCore.SIGNAL("activated()"),self.resumeDownload)
        
        QtCore.QObject.connect(self.ui.http[downloadId][1], QtCore.SIGNAL("dataReadProgress(int, int)"), self.updateDataReadProgress)
        QtCore.QObject.connect(self.ui.http[downloadId][1], QtCore.SIGNAL("requestFinished(int, bool)"), self.httpRequestFinished)
        QtCore.QObject.connect(self.ui.http[downloadId][1], QtCore.SIGNAL("done(bool)"), self.downloadDone)
        QtCore.QObject.connect(self.ui.http[downloadId][1], QtCore.SIGNAL('responseHeaderReceived(const QHttpResponseHeader&)'), self.responseHeaderReceived)
        
        if  not self.ui.outFile[downloadId][1].open(QtCore.QIODevice.WriteOnly):
            print "Unable to save file "+fileName
            self.ui.outFile[downloadId]= None
            return
        
        if url.port() != -1:
            self.ui.http[downloadId][1].setHost(url.host(), url.port())
        else:
            self.ui.http[downloadId][1].setHost(url.host(), 80)
        if  not url.userName().isEmpty():
            self.ui.http[downloadId][1].setUser(url.userName(), url.password())
            
##   ovo je kod sa kojim moze da se odradi pause/resume:
        self.get=QtCore.QString().append('GET')
        self.header=QtNetwork.QHttpRequestHeader(self.get, url.path().replace(" ", "%20"))
        self.header.setValue("Host", url.host())
        self.header.setValue("User-agent", "brePodder")
        
## next 2 lines are important for resume of download
        if self.bytesRead:
            self.header.setValue("Range", "bytes "+str(self.bytesRead)+"-"+str(self.totalBytes)+"/"+str(self.totalBytes))
        self.q=None
        
        self.httpRequestAborted = False
        self.ui.httpGetId.append(self.ui.http[downloadId][1].request(self.header, self.q, self.ui.outFile[downloadId][1]))
    
    def responseHeaderReceived(self, header):
        if header.statusCode() in [301, 302]: # Moved permanently or temporarily
            if header.hasKey('Location'):
                self.locationRedirect = str(header.value('Location'))
        elif header.statusCode() not in [200, 206]:
            print header.statusCode()       
        sidkey = "set-cookie"
        if header.hasKey(sidkey):
            print header.value(sidkey)
            
    def httpRequestFinished(self, requestId, error):
        self.i=self.i+1
        print "httpRequestFinished"
        print self.i
        print error
#        if self.ui.tab_2.isVisible() and error:
#TODO kada se download zavrsi ovo pravi probleme, jer nista nije izabrano
#            of=self.ui.itemsDownloading.index(self.ui.itemZaPrekid.text(5))
#        else:
#            of=len(self.ui.outFile)-1
            
        if self.httpRequestAborted:
            if self.ui.outFile[self.downloadId][1] is not None:
                os.chdir(self.CurDir)
                self.ui.outFile[self.downloadId][1].close()
                self.ui.outFile[self.downloadId][1].remove()
                self.ui.outFile[self.downloadId] = None
#                del self.ui.outFile[self.downloadId][1]
                os.chdir(os.path.expanduser('~')+'/.brePodder') 
            return
#ovo mi je trebalo kako bi odredio koji fajl salje request, ali mi samo smeta i mislim da mi vise ne treba.
#        if requestId != self.ui.httpGetId[of]:
#            return
        
        if self.locationRedirect:
            os.chdir(self.CurDir)
            self.downloadFile(self.locationRedirect, self.itemZaPrenos,  self.downloadId)
            self.urlRedirect='M'
            self.locationRedirect=None
#            os.chdir(os.path.expanduser('~')+'/.brePodder')

#            self.header=QtNetwork.QHttpRequestHeader(self.get, self.urlRedirect.path().replace(" ", "%20"))
#            self.header.setValue("Host", self.urlRedirect.host()) 
#            self.ui.httpGetId.append(self.http[ht].request(self.header, self.q, self.ui.outFile[of]))
        elif self.i==2:
# Never, ever close a file if you plan to write to it latter... or maybe you can re-open it.
#            self.ui.outFile[of].close()
            print "self.ui.outFile"
            print self.ui.outFile
#            self.ui.outFile[self.downloadId][1].close()

            
        if error and not self.paused and self.ui.outFile[self.downloadId] is not None:
            os.chdir(self.CurDir)
            self.ui.outFile[self.downloadId][1].close()
            self.ui.outFile[self.downloadId][1].remove()
            self.ui.outFile[self.downloadId] = None
            os.chdir(os.path.expanduser('~')+'/.brePodder')
#        elif not self.paused:
#            fileName = QtCore.QFileInfo(QtCore.QUrl(self.QLineEdit1.text()).path()).fileName()
#            print self.ui.outFile[of]
#            self.ui.outFile[of] = None
    
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
        self.itemZaPrenos.setText(3,self.ui.getReadableSize(self.bytesRead)) 
    
    def downloadDone(self, error):
#        print "downloadDone"
        if self.urlRedirect:
            self.urlRedirect = None
#            return
        if not error:
            self.ui.outFile[self.downloadId][1].close()
            self.itemZaPrenos.setText(3,"DONE")
            url =  self.itemZaPrenos.text(5).toUtf8().data()
            ChannelDir = self.ui.p.sub("",self.itemZaPrenos.text(0).toUtf8().data())
            #ova linija me nesto drka kada dodajem novi kanal. trebalo bi da je proverim i vidim sta ce mi
            url_done = QtCore.QUrl(url)
            fileInfo = QtCore.QFileInfo(url_done.path())
            file = QtCore.QString(fileInfo.fileName()).toUtf8().data()
            os.chdir(os.path.expanduser('~')+'/.brePodder/'+ChannelDir)
            if file[-3:]=='ico' and self.faviconFound:
                self.faviconFound = False
                #TODO: this is bad and system depended, but... 
                #TODO: Remove this 'convert' command - maybe i don't even need it
#                if os.system('convert '+file.replace(" ","\ ")+'[0] png:'+file.replace(" ","\ "))!=0:
#                    print "convert fail"
#                    os.system('cp ../images/musicstore.png '+file)
#                    os.system('cp ../images/musicstore.png '+file+'n')
            elif self.faviconFound:
                print "favicon: "+file
            elif (file[-3:]=='png' or file[-3:]=='PNG' or file[-3:]=='jpg' or file[-3:]=='JPG'):
#                print 'logoBig:' +file
                size = 128, 128
                try:
                    #TODO: convert image to 128x182
#                    print "convert image to 128x182"
                    import Image
                    im = Image.open(file)
                    im.thumbnail(size, Image.ANTIALIAS) #ovo ne daje bas dobar kvalitet
                    im.save('128'+file)
                except IOError:
                    print IOError
#                    Image.open('../images/musicstore.png').save(file, 'PNG')
            else:
                try:
                    e = Episode.query.filter_by(title=self.itemZaPrenos.text(1).toUtf8().data().decode('UTF8')).one()
                    e.localfile=ChannelDir.decode('utf8')+'/'+ file.decode('utf8')
                    e.status=u'downloaded'
                except:
                    print 'InvalidRequestError'
                session.commit()
            os.chdir(os.path.expanduser('~')+'/.brePodder')
#            self.itemZaPrenos.setText(3, "DONE")
            self.ui.update_lastest_episodes_list()
        else:
            print "Download Error!"
        return
        
    def cancelDownload(self):
        if self.ui.tab_2.isVisible():
            if self.itemZaPrenos == self.ui.itemZaPrekid:
                self.itemZaPrenos.setText(3, "CANCELED")
                self.httpRequestAborted = True
#                httpIndex=self.ui.itemsDownloading.index(self.ui.itemZaPrekid.text(5))
                self.ui.http[self.downloadId][1].abort()
#                del self.ui.http[self.downloadId][1]
#                self.ui.itemsDownloading.remove((self.downloadId, self.ui.itemZaPrekid.text(5)))
    
    def pauseDownload(self):
        self.paused = True
        self.resumed = False
        if self.ui.tab_2.isVisible():
            if self.itemZaPrenos == self.ui.itemZaPrekid:
                self.itemZaPrenos.setText(3, "PAUSED")
                fileLink = self.ui.itemZaPrekid.text(5)
#TODO: do i need next line?
                self.httpRequestAborted = False
#                httpIndex=self.ui.itemsDownloading.index(self.ui.itemZaPrekid.text(5))
                self.ui.http[self.downloadId][1].abort()

    def resumeDownload(self):
        if self.ui.tab_2.isVisible():
            if self.itemZaPrenos == self.ui.itemZaPrekid:
                self.itemZaPrenos.setText(3, "RESUMED")
#                p=re.compile("\W")  
                ChannelDir = self.ui.p.sub("",self.itemZaPrenos.text(0).toAscii().data())
                os.chdir(os.path.expanduser('~')+'/.brePodder/'+ChannelDir)
                resumeLink=self.itemZaPrenos.text(5).toAscii().data()
                item=self.itemZaPrenos

                self.httpRequestAborted = False
                self.resumed = True
                
                self.downloadFile(resumeLink, item, self.downloadId)
                
                self.paused = False
