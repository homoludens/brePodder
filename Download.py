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
#        self.itemsDownloading=[]
        
    def downloadFile(self, link, item):
        self.CurDir = os.getcwd()
        self.itemZaPrenos=item
        url = QtCore.QUrl(link)
        fileInfo = QtCore.QFileInfo(url.path())
        fileName = QtCore.QString(fileInfo.fileName())
        httpIndex=ui.itemsDownloading.index(self.itemZaPrenos.text(5))
        
        # Qt 4.4+ doesn't wont to show images named favicon.ico, favicon.icon is ok
        if '.ico' in fileName:
            fileName = fileName.replace('.ico','.icon')
            
        if QtCore.QFile.exists(fileName):
            if self.locationRedirect:
                fileDelete=QtCore.QFile(fileName)
#                fileDelete.remove()
            elif not self.paused:
                print "There already exists a file called "+fileName+ " in the current directory." 
#TODO: kada fajl vec postoji ovde izbacuje gresku "IndexError: list index out of range" jer je ui.outFile prazan
                if  not ui.outFile[httpIndex].open(QtCore.QIODevice.Append):
                    print "Unable to save file "+fileName
#                   TODO: what does this line do?
#                    ui.outFile[of] = None
                    return
        
            if url.port() != -1:
                ui.http[httpIndex].setHost(url.host(), url.port())
            else:
                ui.http[httpIndex].setHost(url.host(), 80)
# TODO: insert setting of username and password for podcast download. does anyone need this?
            if  not url.userName().isEmpty():
                ui.http[httpIndex].setUser(url.userName(), url.password())
            
#           important for some hosts (example libsyn), which have some query in url 
            if url.hasQuery():
                realUrl=url.path()+'?'+url.encodedQuery()
            else:
                realUrl=url.path()
                
            self.get=QtCore.QString().append('GET')
            self.header=QtNetwork.QHttpRequestHeader(self.get, realUrl.replace(" ", "%20"))
            self.header.setValue("Host", url.host())
            self.header.setValue("User-agent", "brePodder")
            if self.bytesRead:
                self.header.setValue("Range", "bytes="+str(self.bytesRead)+"-")
            self.q=None
            self.httpRequestAborted = False
            ui.httpGetId.append(ui.http[httpIndex].request(self.header, self.q, ui.outFile[httpIndex]))
#            print os.getcwd()
#            print ui.outFile
            return
            
        ui.http.append(QtNetwork.QHttp())
        ui.outFile.append(QtCore.QFile(fileName))
        of=len(ui.outFile)-1
        ht=len(ui.http)-1
        print "ht " + str(ht)
        
        QtCore.QObject.connect(ui.actionCancel,QtCore.SIGNAL("activated()"),self.cancelDownload)
        QtCore.QObject.connect(ui.actionPause,QtCore.SIGNAL("activated()"),self.pauseDownload)
        QtCore.QObject.connect(ui.actionResume ,QtCore.SIGNAL("activated()"),self.resumeDownload)
        
        QtCore.QObject.connect(ui.http[ht], QtCore.SIGNAL("dataReadProgress(int, int)"), self.updateDataReadProgress)
        QtCore.QObject.connect(ui.http[ht], QtCore.SIGNAL("requestFinished(int, bool)"), self.httpRequestFinished)
        QtCore.QObject.connect(ui.http[ht], QtCore.SIGNAL("done(bool)"), self.downloadDone)
        QtCore.QObject.connect(ui.http[ht], QtCore.SIGNAL('responseHeaderReceived(const QHttpResponseHeader&)'), self.responseHeaderReceived)
        
        if  not ui.outFile[of].open(QtCore.QIODevice.WriteOnly):
            print "Unable to save file "+fileName
            ui.outFile[of] = None
            return
        
        if url.port() != -1:
            ui.http[ht].setHost(url.host(), url.port())
        else:
            ui.http[ht].setHost(url.host(), 80)
        if  not url.userName().isEmpty():
            ui.http[ht].setUser(url.userName(), url.password())
            
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
        ui.httpGetId.append(ui.http[ht].request(self.header, self.q, ui.outFile[of]))
        
#        self.httpRequestAborted = False
#        ui.httpGetId.append(self.http[ht].get(url.path().replace(" ", "%20"), ui.outFile[of]))
    
    def responseHeaderReceived(self, header):
        if header.statusCode() == 200:
            print 'Link OK!'
        if header.statusCode() == 206:
            print 'Link Resuming!'
        elif header.statusCode() in [301, 302]: # Moved permanently or temporarily
            if header.hasKey('Location'):
                self.locationRedirect = str(header.value('Location'))
        else:
            print header.statusCode()

        
        sidkey = "set-cookie"
        if header.hasKey(sidkey):
            print header.value(sidkey)
            
# ko zna kakva me je muka naterala na ovo
#            QRegExp rx("PHPSESSID=(.+);");
#            rx.setMinimal(true);
#            rx.setCaseSensitive(false);
#            if (rx.search(resp.value(sidkey)) >= 0)
#                cookie = "PHPSESSID=" + rx.cap(1);
#                cout << "found cookie:" << cookie << "\n";

 
    
    def httpRequestFinished(self, requestId, error):
        print "httpRequestFinished"
        print requestId
        print error
        if ui.tab_2.isVisible() and error:
#TODO kada se download zavrsi ovo pravi probleme, jer nista nije izabrano
            of=ui.itemsDownloading.index(ui.itemZaPrekid.text(5))
        else:
            of=len(ui.outFile)-1
            
        if self.httpRequestAborted:
            if ui.outFile[of] is not None:
                os.chdir(self.CurDir)
                ui.outFile[of].close()
                ui.outFile[of].remove()
                ui.outFile[of] = None
                del ui.outFile[of]
                os.chdir(os.path.expanduser('~')+'/.brePodder') 
            return
#ovo mi je trebalo kako bi odredio koji fajl salje request, ali mi samo smeta i mislim da mi vise ne treba.
#        if requestId != ui.httpGetId[of]:
#            return
        
        if self.locationRedirect:
            os.chdir(self.CurDir)
            self.downloadFile(self.locationRedirect, self.itemZaPrenos)
            self.urlRedirect='M'
            self.locationRedirect=None
#            os.chdir(os.path.expanduser('~')+'/.brePodder')

#            self.header=QtNetwork.QHttpRequestHeader(self.get, self.urlRedirect.path().replace(" ", "%20"))
#            self.header.setValue("Host", self.urlRedirect.host()) 
#            ui.httpGetId.append(self.http[ht].request(self.header, self.q, ui.outFile[of]))
        else:
# Never, ever close a file if you plan to write to it latter... or maybe you can re-open it.
#            ui.outFile[of].close()
            print ui.outFile[of]
            
        if error and not self.paused and ui.outFile[of] is not None:
            os.chdir(self.CurDir)
            ui.outFile[of].close()
            ui.outFile[of].remove()
            ui.outFile[of] = None
            os.chdir(os.path.expanduser('~')+'/.brePodder')
        elif not self.paused:
#            fileName = QtCore.QFileInfo(QtCore.QUrl(self.QLineEdit1.text()).path()).fileName()
            print ui.outFile[of]
#            ui.outFile[of] = None
    
    def updateDataReadProgress(self, bytesRead, totalBytes):
#        print "updateDataReadProgress"
        if self.httpRequestAborted:
            return
        if not self.resumed:
            if self.tempBytes==0:
                self.totalBytes=totalBytes
#            self.resumed=True
#            self.tempBytes=self.bytesRead
            
        if self.resumed:
            self.resumed=False
            self.tempBytes=self.bytesRead
            
        self.bytesRead=self.tempBytes+bytesRead
        self.itemZaPrenos.setText(3, str(self.bytesRead/1048576)+" MB")
#        self.bytesRead=self.bytesRead+bytesRead
        
    
    def downloadDone(self, done):
        print "downloadDone"
        if self.urlRedirect:
            self.urlRedirect = None
#            return
        if not done:
            url =  self.itemZaPrenos.text(5).toUtf8().data()
            
            p=re.compile("\W")  
            ChannelDir = p.sub("",self.itemZaPrenos.text(0).toUtf8().data())
#            e.channel.title #ovde smeju da stignu samo ascii karakteri jer je to ime foldera

            #ova linija me nesto drka kada dodajem novi kanal. trebalo bi da je proverim i vidim sta ce mi
            
            url_done = QtCore.QUrl(url)
            fileInfo = QtCore.QFileInfo(url_done.path())
            file = QtCore.QString(fileInfo.fileName()).toUtf8().data()
            
#            i = url.rfind('/')
#            fileName = url[i+1:]

            os.chdir(os.path.expanduser('~')+'/.brePodder/'+ChannelDir)
            if file[-3:]=='ico':
                #TODO: this is bad and system depended, but... 
                #TODO: Remove this 'convert' command - maybe i don't even need it
                if os.system('convert '+file.replace(" ","\ ")+'[0] png:'+file.replace(" ","\ "))!=0:
                    os.system('cp ../images/musicstore.png '+file+'n')
                                     
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
                    e=Episode.query.filter_by(enclosure=self.itemZaPrenos.text(5).toUtf8().data().decode('UTF8')).one()
                    e.localfile=ChannelDir.decode('utf8')+'/'+ file.decode('utf8')
                    e.status=u'downloaded'
                except:
                    print 'InvalidRequestError'
                    print file
#                i = e.enclosure.rfind('/')
#                file = e.enclosure[i+1:]
                session.commit()
            os.chdir(os.path.expanduser('~')+'/.brePodder')
            self.itemZaPrenos.setText(3, "DONE")
            ui.update_lastest_episodes_list()
        else:
            print "Download Error!"
        return
        
    def cancelDownload(self):
        if ui.tab_2.isVisible():
            if self.itemZaPrenos == ui.itemZaPrekid:
                self.itemZaPrenos.setText(3, "CANCELED")
                self.httpRequestAborted = True
                httpIndex=ui.itemsDownloading.index(ui.itemZaPrekid.text(5))
                ui.http[httpIndex].abort()
                del ui.http[httpIndex]
                ui.itemsDownloading.remove(ui.itemZaPrekid.text(5))
    
    def pauseDownload(self):
#        print "PAUSED"
        self.paused = True
        self.resumed = False
        if ui.tab_2.isVisible():
            if self.itemZaPrenos == ui.itemZaPrekid:
                self.itemZaPrenos.setText(3, "PAUSED")
                fileLink = ui.itemZaPrekid.text(5)
#                ui.outFile[0].close()
#TODO: do i need next line?
                self.httpRequestAborted = False
                httpIndex=ui.itemsDownloading.index(ui.itemZaPrekid.text(5))
                ui.http[httpIndex].abort()

    def resumeDownload(self):
#        print "RESUMED"
        if ui.tab_2.isVisible():
            if self.itemZaPrenos == ui.itemZaPrekid:
                self.itemZaPrenos.setText(3, "RESUMED")
                p=re.compile("\W")  
                ChannelDir = p.sub("",self.itemZaPrenos.text(0).toAscii().data())
                os.chdir(os.path.expanduser('~')+'/.brePodder/'+ChannelDir)
                resumeLink=self.itemZaPrenos.text(5).toAscii().data()
                item=self.itemZaPrenos

                self.httpRequestAborted = False
                self.resumed = True
                
                self.downloadFile(resumeLink, item)
                
                self.paused = False

                
# TODO: sigrno postoji razlog da se vratim u 'home' direktorijum
#                os.chdir(os.path.expanduser('~')+'/.brePodder')
