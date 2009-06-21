# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/homoludens/projekti/eric4/brePodder/mainwindow.ui'
#
# Created: Tue Jan 29 20:12:18 2008
#      by: PyQt4 UI code generator 4.3.1
#

from PyQt4 import QtCore, QtGui,  QtNetwork,  QtTest,  QtWebKit
import feedparser
from sql import *
import os
from getfavicon import getIcoUrl
#from Download import *
import Image
import opml
import re
from time import gmtime, strftime, mktime, sleep
from elixir import *
import sqlalchemy
import sys  
import sqlite3

#session = sqlalchemy.orm.scoped_session(sqlalchemy.orm.sessionmaker(autoflush=True,autocommit=True))
#session.begin()
sys.setappdefaultencoding('utf-8')  
class Download(object):
    def setup(self):
#        self.http = []
#        self.httpGetId = []
#        ui.outFile = []
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
#        self.itemsDownloading=[]
        
    def downloadFile(self, link, item):
        self.CurDir = os.getcwd()
        self.itemZaPrenos=item
        print "Download.downloadFile"
        url = QtCore.QUrl(link)
        fileInfo = QtCore.QFileInfo(url.path())
        fileName = QtCore.QString(fileInfo.fileName())
        httpIndex=ui.itemsDownloading.index(self.itemZaPrenos.text(5))
        print httpIndex
        
        # Qt 4.4+ doesn't wont to show images named favicon.ico, favicon.icon is ok
        if '.ico' in fileName:
            fileName = fileName.replace('.ico','.icon')
            
        if QtCore.QFile.exists(fileName):
            if self.locationRedirect:
                fileDelete=QtCore.QFile(fileName)
#                fileDelete.remove()
            elif not self.paused:
                print "There already exists a file called "+fileName+ " in the current directory." 
                if  not ui.outFile[httpIndex].open(QtCore.QIODevice.Append):
                    print "Unable to save file "+fileName
#                   TODO: what does this line do?
                    ui.outFile[of] = None
                    return
        
            if url.port() != -1:
                ui.http[httpIndex].setHost(url.host(), url.port())
            else:
                ui.http[httpIndex].setHost(url.host(), 80)
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
            print ui.outFile
            return
        ui.http.append(QtNetwork.QHttp())
        ui.outFile.append(QtCore.QFile(fileName))
        of=len(ui.outFile)-1
        ht=len(ui.http)-1
        
        QtCore.QObject.connect(ui.http[ht], QtCore.SIGNAL("dataReadProgress(int, int)"), self.updateDataReadProgress)
        QtCore.QObject.connect(ui.http[ht], QtCore.SIGNAL("requestFinished(int, bool)"), self.httpRequestFinished)
        QtCore.QObject.connect(ui.http[ht], QtCore.SIGNAL("done(bool)"), self.downloadDone)
        QtCore.QObject.connect(ui.actionCancel,QtCore.SIGNAL("activated()"),self.cancelDownload)
        QtCore.QObject.connect(ui.actionPause,QtCore.SIGNAL("activated()"),self.pauseDownload)
        QtCore.QObject.connect(ui.actionResume ,QtCore.SIGNAL("activated()"),self.resumeDownload)
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
#        print "****************** Http header received"
#        print header.toString()
#        print header.statusCode()
        if header.statusCode() == 200:
            print 'Link OK!'
        if header.statusCode() == 206:
            print 'Link Resuming!'
        elif header.statusCode() in [301, 302]: # Moved permanently or temporarily
            if header.hasKey('Location'):
                self.locationRedirect = str(header.value('Location'))
#                print header.value('Location')
        
        sidkey = "set-cookie"
        if header.hasKey(sidkey):
            print header.value(sidkey)
#            QRegExp rx("PHPSESSID=(.+);");
#            rx.setMinimal(true);
#            rx.setCaseSensitive(false);
#            if (rx.search(resp.value(sidkey)) >= 0)
#                cookie = "PHPSESSID=" + rx.cap(1);
#                cout << "found cookie:" << cookie << "\n";

 
    
    def httpRequestFinished(self, requestId, error):
        of=len(ui.outFile)-1
        if self.httpRequestAborted:
            if ui.outFile[of] is not None:
                print self.CurDir
                os.chdir(self.CurDir)
                ui.outFile[of].close()
                ui.outFile[of].remove()
                ui.outFile[of] = None
                os.chdir(os.path.expanduser('~')+'/.brePodder') 
            return

        if requestId != ui.httpGetId[of]:
            return
        
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
            ui.outFile[of].close()
    
        if error and not self.paused:
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
        if self.urlRedirect:
            self.urlRedirect = None
            return
        if not done:
            url =  self.itemZaPrenos.text(5).toUtf8().data()
            
            p=re.compile("\W")  
#            ChannelDir = p.sub(" ",self.itemZaPrenos.text(0).toUtf8().data().decode())
            ChannelDir = p.sub("",self.itemZaPrenos.text(0).toUtf8().data())
#            e.channel.title #ovde smeju da stignu samo ascii karakteri jer je to ime foldera
#            ChannelDir =  self.itemZaPrenos.text(0).toUtf8().data()

            #ova linija me nesto drka kada dodajem novi kanal. trebalo bi da je proverim i vidim sta ce mi
            
            url_done = QtCore.QUrl(url)
            fileInfo = QtCore.QFileInfo(url_done.path())
            file = QtCore.QString(fileInfo.fileName()).toUtf8().data()
            
#            i = url.rfind('/')
#            fileName = url[i+1:]


            os.chdir(os.path.expanduser('~')+'/.brePodder/'+ChannelDir)
            if file[-3:]=='ico':
                # this is bad and system depended, but... 
                print ChannelDir
                #TODO Remove this 'convert' command
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
                ui.itemsDownloading.remove(ui.itemZaPrekid.text(5))
    
    def pauseDownload(self):
        print "PAUSED"
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
        print "RESUMED"
#        self.paused = False
        if ui.tab_2.isVisible():
            if self.itemZaPrenos == ui.itemZaPrekid:
                self.itemZaPrenos.setText(3, "RESUMED")
                p=re.compile("\W")  
                ChannelDir = p.sub("",self.itemZaPrenos.text(0).toAscii().data())
                os.chdir(os.path.expanduser('~')+'/.brePodder/'+ChannelDir)
                resumeLink=self.itemZaPrenos.text(5).toAscii().data()
                item=self.itemZaPrenos
                
#                self.http[0].abort()
                self.downloadFile(resumeLink, item)
#TODO sigrno postoji razlog da se vratim u 'home' direktorijum
#                os.chdir(os.path.expanduser('~')+'/.brePodder')
                self.httpRequestAborted = False
                self.paused = False
        
            
class Ui_MainWindow(object):
    def __init__(self, parent=None):
        self.http = []
        self.httpGetId = []
        self.outFile = []
        self.itemZaPrenos = []
        self.dd=[]
        self.itemZaPrenos = None
        self.rawstr = r"""(?:\<img.*?\c=")(.*?)(?:\")"""  #it's better with "\src" (not "\c") but that doesn't work
        self.compile_obj = re.compile(self.rawstr, re.I)
        self.fontBold = QtGui.QFont()
        self.fontBold.setWeight(75)
        self.fontBold.setBold(True)
        self.ChannelForUpdate=None
        self.TTThread=[]
        self.BufferSize = 5
#        self.freeBytes = QtCore.QSemaphore(self.BufferSize)
#        self.usedBytes = QtCore.QSemaphore()
        self.Mutex = QtCore.QMutex()
#        self.freeBytes.acquire()
        self.itemsDownloading=[]


    def setupUi(self, MainWindow):
        self.dd=[]
        
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(QtCore.QSize(QtCore.QRect(0,0,604,511).size()).expandedTo(MainWindow.minimumSizeHint()))
        MainWindow.setWindowIcon(QtGui.QIcon("images/musicstore.png"))

        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.gridlayout = QtGui.QGridLayout(self.centralwidget)
        self.gridlayout.setObjectName("gridlayout")

        self.tabWidget = QtGui.QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")

        self.tab = QtGui.QWidget()
        self.tab.setObjectName("tab")

        self.gridlayout1 = QtGui.QGridLayout(self.tab)
        self.gridlayout1.setObjectName("gridlayout1")

        self.splitter_2 = QtGui.QSplitter(self.tab)
        self.splitter_2.setOrientation(QtCore.Qt.Horizontal)
        self.splitter_2.setObjectName("splitter_2")

        self.widget = QtGui.QWidget(self.splitter_2)
        self.widget.setObjectName("widget")

        self.vboxlayout = QtGui.QVBoxLayout(self.widget)
        self.vboxlayout.setSpacing(-1)
        self.vboxlayout.setObjectName("vboxlayout")

        self.listWidget = QtGui.QTreeWidget(self.widget)
        
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred,QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.listWidget.sizePolicy().hasHeightForWidth())
        self.listWidget.setSizePolicy(sizePolicy)
        self.listWidget.setMaximumSize(QtCore.QSize(16777215,16777215))
        self.listWidget.setSizeIncrement(QtCore.QSize(0,0))
        self.listWidget.setBaseSize(QtCore.QSize(0,0))
        self.listWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
#        self.listWidget.setFrameShadow(QtGui.QFrame.Raised)
        self.listWidget.setObjectName("listWidget")
        self.listWidget.setAlternatingRowColors(True)
#        self.listWidget.setMouseTracking(True)
        self.vboxlayout.addWidget(self.listWidget)
        

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setObjectName("hboxlayout")

        self.QLineEdit1 = QtGui.QLineEdit(self.widget)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.QLineEdit1.sizePolicy().hasHeightForWidth())
        self.QLineEdit1.setSizePolicy(sizePolicy)
        self.QLineEdit1.setMinimumSize(QtCore.QSize(0,0))
        self.QLineEdit1.setMaximumSize(QtCore.QSize(16777215,16777215))
        self.QLineEdit1.setObjectName("QLineEdit1")
        self.hboxlayout.addWidget(self.QLineEdit1)

        self.QPushButton1 = QtGui.QPushButton(self.widget)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum,QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.QPushButton1.sizePolicy().hasHeightForWidth())
        self.QPushButton1.setSizePolicy(sizePolicy)
        self.QPushButton1.setMinimumSize(QtCore.QSize(20,0))
        self.QPushButton1.setMaximumSize(QtCore.QSize(50,16777215))
        self.QPushButton1.setObjectName("QPushButton1")
        self.hboxlayout.addWidget(self.QPushButton1)

#        spacerItem = QtGui.QSpacerItem(10,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
#        self.hboxlayout.addItem(spacerItem)
        self.vboxlayout.addLayout(self.hboxlayout)

        self.splitter = QtGui.QSplitter(self.splitter_2)
        
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.splitter.sizePolicy().hasHeightForWidth())
        self.splitter.setSizePolicy(sizePolicy)
        
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName("splitter")

        self.treeWidget_2 = QtGui.QTreeWidget(self.splitter)
        self.treeWidget_2.setItemsExpandable(False)
#        self.treeWidget_2.setSortingEnabled(True)
        self.treeWidget_2.setAnimated(True)
        self.treeWidget_2.setAlternatingRowColors(True)
        self.treeWidget_2.setObjectName("treeWidget_2")

#        self.QTextBrowser1 = QtWebKit.QWebView(self.splitter) #Qt4.4
        self.QTextBrowser1 = QtGui.QTextBrowser(self.splitter) # Qt4.3
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.QTextBrowser1.sizePolicy().hasHeightForWidth())
        self.QTextBrowser1.setSizePolicy(sizePolicy)
        self.QTextBrowser1.setMinimumSize(QtCore.QSize(0,0))
        self.QTextBrowser1.setSizeIncrement(QtCore.QSize(4,0))
        self.QTextBrowser1.setBaseSize(QtCore.QSize(400,0))
#        self.QTextBrowser1.setOpenExternalLinks(True)
        self.QTextBrowser1.setObjectName("QTextBrowser1")
        self.gridlayout1.addWidget(self.splitter_2,0,0,1,1)
        self.tabWidget.addTab(self.tab,"")

        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName("tab_2")

        self.gridlayout2 = QtGui.QGridLayout(self.tab_2)
        self.gridlayout2.setObjectName("gridlayout2")

        self.treeWidget = QtGui.QTreeWidget(self.tab_2)
        self.treeWidget.setAlternatingRowColors(True)
        self.treeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeWidget.setObjectName("treeWidget")
        self.gridlayout2.addWidget(self.treeWidget,0,0,1,1)
        self.tabWidget.addTab(self.tab_2,"")

        self.tab_3 = QtGui.QWidget()
        self.tab_3.setObjectName("tab_3")
        
        
        self.treeWidget_4 = QtGui.QTreeWidget(self.tab_3)
        self.treeWidget_4.setWindowModality(QtCore.Qt.NonModal)
        self.treeWidget_4.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeWidget_4.setItemsExpandable(False)
        self.treeWidget_4.setSortingEnabled(True)
        self.treeWidget_4.setAnimated(True)
        self.treeWidget_4.setObjectName("treeWidget_4")
        
        
        self.gridlayout3 = QtGui.QGridLayout(self.tab_3)
        self.gridlayout3.setObjectName("gridlayout3")
        self.gridlayout3.addWidget(self.treeWidget_4,0,0,1,1)
        self.tabWidget.addTab(self.tab_3,"")
        self.gridlayout.addWidget(self.tabWidget,0,0,1,1)
        MainWindow.setCentralWidget(self.centralwidget)

#        self.gridlayout3 = QtGui.QGridLayout(self.tab_3)
#        self.gridlayout3.setObjectName("gridlayout3")
#        self.tabWidget.addTab(self.tab_3,"")
#        self.gridlayout.addWidget(self.tabWidget,0,0,1,1)
#        MainWindow.setCentralWidget(self.centralwidget)

        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0,0,604,28))
        self.menubar.setObjectName("menubar")

        self.menuPodcasts = QtGui.QMenu(self.menubar)
        self.menuPodcasts.setObjectName("menuPodcasts")
        
        self.menuChannels = QtGui.QMenu(self.menubar)
        self.menuChannels.setObjectName("menuChannels")
        
        self.menuDownloads = QtGui.QMenu(self.menubar)
        self.menuDownloads.setObjectName("menuDownloads")
        
        self.actionNew = QtGui.QAction(MainWindow)
        self.actionNew.setIcon(QtGui.QIcon("images/add.png"))
        self.actionNew.setObjectName("actionNew")

        self.actionUpdateAllChannels = QtGui.QAction(MainWindow)
        self.actionUpdateAllChannels.setIcon(QtGui.QIcon("images/reload.png"))
        self.actionUpdateAllChannels.setObjectName("actionUpdate")
        
        self.actionImport = QtGui.QAction(MainWindow)
        self.actionImport.setIcon(QtGui.QIcon("images/fileimport.png"))
        self.actionImport.setObjectName("actionImport")

        self.actionExport = QtGui.QAction(MainWindow)
        self.actionExport.setIcon(QtGui.QIcon("images/fileexport.png"))
        self.actionExport.setObjectName("actionExport")
        
        self.actionQuit = QtGui.QAction(MainWindow)
        self.actionQuit.setIcon(QtGui.QIcon("images/exit.png"))
        self.actionQuit.setObjectName("actionQuit")
        
        self.menuPodcasts.addAction(self.actionNew)
        self.menuPodcasts.addAction(self.actionUpdateAllChannels)
        self.menuPodcasts.addAction(self.actionImport)
        self.menuPodcasts.addAction(self.actionExport)
        self.menuPodcasts.addSeparator()
        self.menuPodcasts.addAction(self.actionQuit)
        
        
        
        
        MainWindow.setMenuBar(self.menubar)

        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.toolBar = QtGui.QToolBar(MainWindow)
        self.toolBar.setBaseSize(QtCore.QSize(100,0))
        self.toolBar.setMouseTracking(True)
        self.toolBar.setObjectName("toolBar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea,self.toolBar)


        self.menubar.addAction(self.menuPodcasts.menuAction())
        
        self.actionUpdateFeeds = QtGui.QAction(MainWindow)
        self.actionUpdateFeeds.setIcon(QtGui.QIcon("images/reload.png"))
        self.actionUpdateFeeds.setObjectName("actionUpdateFeeds")
        
        
        self.actionCancel = QtGui.QAction(MainWindow)
        self.actionCancel.setIcon(QtGui.QIcon("images/cancel.png"))
        self.actionCancel.setObjectName("actionCancel")
        
        self.actionPause = QtGui.QAction(MainWindow)
        self.actionPause.setIcon(QtGui.QIcon("images/pause.png"))
        self.actionPause.setObjectName("actionPause")
        
        self.actionResume = QtGui.QAction(MainWindow)
        self.actionResume.setIcon(QtGui.QIcon("images/resume.png"))
        self.actionResume.setObjectName("actionResume")
        
        self.menubar.addAction(self.menuPodcasts.menuAction())
        self.toolBar.addAction(self.actionUpdateFeeds)
        self.toolBar.addAction(self.actionCancel)
        self.toolBar.addAction(self.actionPause)
        self.toolBar.addAction(self.actionResume)
        
        self.menuChannels.addAction(self.actionUpdateFeeds)
        self.menuChannels.addAction(self.actionCancel)
        self.menuChannels.addAction(self.actionImport)
        self.menuChannels.addAction(self.actionExport)
        
        self.menuDownloads.addAction(self.actionUpdateFeeds)
        self.menuDownloads.addAction(self.actionCancel)
        
        self.trayIcon = QtGui.QSystemTrayIcon(QtGui.QIcon("images/musicstore.png"),MainWindow)
        self.trayIcon.setContextMenu(self.menuPodcasts)
        self.trayIcon.show()
        
        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QObject.connect(self.listWidget,QtCore.SIGNAL("itemPressed(QTreeWidgetItem*,int)"),self.ChannelActivated)
        QtCore.QObject.connect(self.QPushButton1,QtCore.SIGNAL("clicked()"),self.AddChannel)
        QtCore.QObject.connect(self.QPushButton1,QtCore.SIGNAL("clicked()"),self.QLineEdit1.clear)
        QtCore.QObject.connect(self.treeWidget_2,QtCore.SIGNAL("itemClicked(QTreeWidgetItem*,int)"),self.EpisodeActivated)
        QtCore.QObject.connect(self.treeWidget_2,QtCore.SIGNAL("itemDoubleClicked(QTreeWidgetItem*,int)"),self.EpisodeDoubleClicked)
        QtCore.QObject.connect(self.treeWidget,QtCore.SIGNAL("itemClicked(QTreeWidgetItem*,int)"),self.DownloadActivated)
        QtCore.QObject.connect(self.trayIcon,QtCore.SIGNAL("activated(QSystemTrayIcon::ActivationReason)"),self.trayIconActivated)
        QtCore.QObject.connect(self.actionUpdateFeeds,QtCore.SIGNAL("activated()"),self.update_channel)
        QtCore.QObject.connect(self.actionQuit,QtCore.SIGNAL("activated()"),self.app_quit)
        QtCore.QObject.connect(self.actionCancel,QtCore.SIGNAL("activated()"),self.delete_channel)
        QtCore.QObject.connect(self.actionUpdateAllChannels,QtCore.SIGNAL("activated()"),self.update_all_channels)
        QtCore.QObject.connect(self.actionNew,QtCore.SIGNAL("activated()"),self.dialog_add)
        QtCore.QObject.connect(self.actionExport,QtCore.SIGNAL("activated()"),self.export_opml)
        QtCore.QObject.connect(self.actionImport,QtCore.SIGNAL("activated()"),self.import_opml)

#        QtCore.QObject.connect(self.actionImport,QtCore.SIGNAL("activated()"),self.update_channel_list)

        
        QtCore.QObject.connect(self.listWidget,QtCore.SIGNAL("customContextMenuRequested (QPoint)"),self.activeMenuChannels)
        QtCore.QObject.connect(self.treeWidget,QtCore.SIGNAL("customContextMenuRequested (QPoint)"),self.activeMenuDownloads)
        
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        
        MainWindow.setTabOrder(self.QLineEdit1,self.QPushButton1)
        MainWindow.setTabOrder(self.QPushButton1,self.QTextBrowser1)
        MainWindow.setTabOrder(self.QTextBrowser1,self.tabWidget)
        
        
    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "brePodder", None, QtGui.QApplication.UnicodeUTF8))
        self.listWidget.setStatusTip(QtGui.QApplication.translate("MainWindow", "kanali", None, QtGui.QApplication.UnicodeUTF8))
        self.listWidget.clear()

        item = QtGui.QTreeWidgetItem(self.listWidget)
        item.setText(0, QtGui.QApplication.translate("MainWindow", "naziv podkasta", None, QtGui.QApplication.UnicodeUTF8))
        item.setIcon(0, QtGui.QIcon("images/musicstore.png"))
        self.listWidget.headerItem().setText(0,QtGui.QApplication.translate("MainWindow", "Channels", None, QtGui.QApplication.UnicodeUTF8))
        item1 = QtGui.QTreeWidgetItem(self.listWidget)
        item1.setText(0, QtGui.QApplication.translate("MainWindow", "New Item", None, QtGui.QApplication.UnicodeUTF8))
       
        self.QLineEdit1.setText(QtGui.QApplication.translate("MainWindow", "addNewChannel", None, QtGui.QApplication.UnicodeUTF8))
        self.QPushButton1.setText(QtGui.QApplication.translate("MainWindow", "Add", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_2.setStatusTip(QtGui.QApplication.translate("MainWindow", "epizode", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_2.headerItem().setText(0,QtGui.QApplication.translate("MainWindow", "episode", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_2.headerItem().setText(1,QtGui.QApplication.translate("MainWindow", "size", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_2.headerItem().setText(2,QtGui.QApplication.translate("MainWindow", "date", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_2.clear()

        item2 = QtGui.QTreeWidgetItem(self.treeWidget_2)
        item2.setIcon(0,QtGui.QIcon("images/build.png"))
        item2.setText(0,QtGui.QApplication.translate("MainWindow", "naziv", None, QtGui.QApplication.UnicodeUTF8))
        item2.setText(1,QtGui.QApplication.translate("MainWindow", "33 MB", None, QtGui.QApplication.UnicodeUTF8))
        self.QTextBrowser1.setStatusTip(QtGui.QApplication.translate("MainWindow", "opis", None, QtGui.QApplication.UnicodeUTF8))
        self.QTextBrowser1.setHtml(QtGui.QApplication.translate("MainWindow", "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
        "p, li { white-space: pre-wrap; }\n"
        "</style></head><body style=\" font-family:\'Sans Serif\'; font-size:8pt; font-weight:400; font-style:normal;\">\n"
        "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">tekst u tekst browseru</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QtGui.QApplication.translate("MainWindow", "Channels", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(0,QtGui.QApplication.translate("MainWindow", "Channel", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(1,QtGui.QApplication.translate("MainWindow", "Episode", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(2,QtGui.QApplication.translate("MainWindow", "Size", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(3,QtGui.QApplication.translate("MainWindow", "%", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(4,QtGui.QApplication.translate("MainWindow", "Speed", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(5,QtGui.QApplication.translate("MainWindow", "Link", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.clear()

        item3 = QtGui.QTreeWidgetItem(self.treeWidget)
        item3.setText(0,QtGui.QApplication.translate("MainWindow", "dl-ch", None, QtGui.QApplication.UnicodeUTF8))
        item3.setText(1,QtGui.QApplication.translate("MainWindow", "dl-ep", None, QtGui.QApplication.UnicodeUTF8))
        item3.setText(2,QtGui.QApplication.translate("MainWindow", "dl-size", None, QtGui.QApplication.UnicodeUTF8))
        item3.setText(3,QtGui.QApplication.translate("MainWindow", "dl-proc", None, QtGui.QApplication.UnicodeUTF8))
        item3.setText(4,QtGui.QApplication.translate("MainWindow", "dl-speed", None, QtGui.QApplication.UnicodeUTF8))
        item3.setText(5,QtGui.QApplication.translate("MainWindow", "dl-link", None, QtGui.QApplication.UnicodeUTF8))
        
        
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QtGui.QApplication.translate("MainWindow", "Downloads", None, QtGui.QApplication.UnicodeUTF8))
        
        
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QtGui.QApplication.translate("MainWindow", "Downloads", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_4.setToolTip(QtGui.QApplication.translate("MainWindow", "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
        "p, li { white-space: pre-wrap; }\n"
        "</style></head><body style=\" font-family:\'Sans Serif\'; font-size:8pt; font-weight:400; font-style:normal;\">\n"
        "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">jn</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_4.headerItem().setText(0,QtGui.QApplication.translate("MainWindow", "Channel", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_4.headerItem().setText(1,QtGui.QApplication.translate("MainWindow", "Episode", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_4.headerItem().setText(2,QtGui.QApplication.translate("MainWindow", "Size", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_4.headerItem().setText(3,QtGui.QApplication.translate("MainWindow", "Local Link", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_4.clear()

        item6 = QtGui.QTreeWidgetItem(self.treeWidget_4)
        item6.setText(0,QtGui.QApplication.translate("MainWindow", "ch", None, QtGui.QApplication.UnicodeUTF8))
        item6.setText(1,QtGui.QApplication.translate("MainWindow", "ep", None, QtGui.QApplication.UnicodeUTF8))
        item6.setText(2,QtGui.QApplication.translate("MainWindow", "size", None, QtGui.QApplication.UnicodeUTF8))
        item6.setText(3,QtGui.QApplication.translate("MainWindow", "local file", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QtGui.QApplication.translate("MainWindow", "Lastest downlods", None, QtGui.QApplication.UnicodeUTF8))
        
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QtGui.QApplication.translate("MainWindow", "Lastest Downloads", None, QtGui.QApplication.UnicodeUTF8))
        
        self.menuPodcasts.setTitle(QtGui.QApplication.translate("MainWindow", "Podcasts", None, QtGui.QApplication.UnicodeUTF8))
        self.toolBar.setWindowTitle(QtGui.QApplication.translate("MainWindow", "toolBar", None, QtGui.QApplication.UnicodeUTF8))
        self.actionCancel.setText(QtGui.QApplication.translate("MainWindow", "Delete feed", None, QtGui.QApplication.UnicodeUTF8))
        self.actionImport.setText(QtGui.QApplication.translate("MainWindow", "Import", None, QtGui.QApplication.UnicodeUTF8))
        self.actionExport.setText(QtGui.QApplication.translate("MainWindow", "Export", None, QtGui.QApplication.UnicodeUTF8))
        self.actionNew.setText(QtGui.QApplication.translate("MainWindow", "Add New", None, QtGui.QApplication.UnicodeUTF8))
        self.actionUpdateAllChannels.setText(QtGui.QApplication.translate("MainWindow", "Update All", None, QtGui.QApplication.UnicodeUTF8))
        self.actionQuit.setText(QtGui.QApplication.translate("MainWindow", "Quit", None, QtGui.QApplication.UnicodeUTF8))
        self.actionUpdateFeeds.setText(QtGui.QApplication.translate("MainWindow", "Fetch feed", None, QtGui.QApplication.UnicodeUTF8))
    
    
    def trayIconActivated(self, reason):
        if reason==3  or reason ==2:
            if MainWindow.isHidden():
                MainWindow.show()
            else:
                MainWindow.hide()
                
                
# TODO: download images from episode description so i can show them in QTextBrowser
# this is beta... :)
    def getImageFromDesc(self, desc,  channel):
        p=re.compile("\W")  
        ChannelDir = p.sub("",channel.title)
        os.chdir(os.path.expanduser('~')+'/.brePodder/'+ChannelDir)
        
        match_obj = self.compile_obj.findall(desc)
        
        for image in match_obj:
            p = re.compile(image)
            i=image.rfind('/')
            desc = p.sub( os.getcwd()+image[i:], desc)
            self.dd.append(Download())
            self.dd[len(self.http)-1].setup()
            item = QtGui.QTreeWidgetItem(self.treeWidget)
            item.setText(0,channel.title)
            item.setText(5,image)
            self.dd[len(self.http)-1].downloadFile( image.replace(" ", "%20"), item)
            
        os.chdir(os.path.expanduser('~')+'/.brePodder')            
        return desc
        
    def EpisodeActivated(self, a, i):
#        print "EpisodeActivated"
        try:
            e=Episode.query.filter_by(title=a.text(0).toUtf8().data().decode()).one()
            if e.enclosure:
                enc=e.enclosure
            else:
                enc='None'
            if e.description:
                desc=e.description
            else:
                desc='None'
            if e.localfile:
                localFile=e.localfile
            else:
                localFile='None'
# TODO: download images from episode description so i can show them in QTextBrowser
#            desc_localimg = self.getImageFromDesc(desc, e.channel)
#            print desc_localimg

            self.QTextBrowser1.setHtml("<p>"+desc+"</br>\n\r</p><p><b>FILE: </b><a href="+enc+">"+enc+"</a></p><p><b>LOCALFILE: </b><a href="+localFile+">"+localFile+"</a></p>")
        except:
            print "EpisodeActivated exception"
    
    def DownloadActivated(self, a, i):
#        print "DownloadActivated"
        self.itemZaPrekid=a
        self.actionCancel.setToolTip("Remove Selected Download")
        self.actionPause.setToolTip("Pause Selected Download")
        self.actionResume.setToolTip("Resume Selected Download")
    
    def EpisodeDoubleClicked(self, a):
#        print "EpisodeDoubleClicked"
        a.setFont(0, self.fontBold)    #ovde cemo da probmenimo backgroundColor ali me mrzi da se sada drkam sa QBrushom
        e=Episode.query.filter_by(title=a.text(0).toUtf8().data()).one()
        
        p=re.compile("\W")  
        ChannelDir = p.sub("",e.channel.title)
        
        os.chdir(os.path.expanduser('~')+'/.brePodder/'+ChannelDir)
        item = QtGui.QTreeWidgetItem(self.treeWidget)
        item.setText(0,e.channel.title)
        item.setText(1,e.title)
        item.setText(2,str(e.size))
        item.setText(3,'0')
        item.setText(4,'0')

        try:
            item.setText(5,e.enclosure)
        except TypeError:
            print TypeError
            item.setText(5,"No link")
        
#        i = e.enclosure.rfind('/')
#        file = e.enclosure[i+1:]
        
#        e.localfile=e.channel.title+'/'+file
        session.commit()
        self.itemsDownloading.append(e.enclosure.replace(" ", "%20"))
        print self.itemsDownloading
        self.dd.append(Download())
        self.dd[len(self.http)-1].setup()
        self.dd[len(self.http)-1].downloadFile( e.enclosure.replace(" ", "%20"), item)
        
        os.chdir(os.path.expanduser('~')+'/.brePodder') 

    def AddChannel(self, newUrl = None):
        if newUrl == None:
            feedLink = self.QLineEdit1.text().toUtf8().data()
        else:
            feedLink = newUrl
        w = feedparser.parse(feedLink)
        item = QtGui.QTreeWidgetItem(self.treeWidget)
        if w.feed.has_key('title'):
            ChannelTitle=w.feed.title
        elif w.feed.has_key('link'):
            ChannelTitle=w.feed.link
        else:
            ChannelTitle=feedLink
            
        p=re.compile("\W")  
        ChannelDir = p.sub("",ChannelTitle)
        os.makedirs(ChannelDir)
        os.chdir(ChannelDir)
#        os.makedirs(ChannelTitle.decode())
#        os.chdir(ChannelTitle)

#        logo_file=ChannelTitle + '/favicon.png' 
        item.setText(0,ChannelTitle)
# download Channel logo
        if w.feed.has_key('image'):
#            item = QtGui.QTreeWidgetItem(self.treeWidget)
#            item.setText(0,w.feed.title)
            item.setText(1,w.feed.image.href)
            item.setText(5,w.feed.image.href)
            self.dd.append(Download())
            self.dd[len(self.http)-1].setup()
            self.dd[len(self.http)-1].downloadFile( w.feed.image.href, item)

            url_done = QtCore.QUrl(w.feed.image.href)
            fileInfo = QtCore.QFileInfo(url_done.path())
            fileName = QtCore.QString(fileInfo.fileName())
            
#            i = w.feed.image.href.rfind('/')
#            logo_fileBig = ChannelTitle+"/"+w.feed.image.href[i+1:]

# should we put original or 128px version of logo
            logo_fileBig = ChannelDir+"/128"+fileName.toUtf8().data()
        else: logo_fileBig=u"images/musicstore2.png"
#  download favicon
        favicon_url=getIcoUrl("http://"+QtCore.QUrl(w.feed.link).host().toUtf8().data())
        if favicon_url:
            url = favicon_url
        else:
            url = "http://"+QtCore.QUrl(w.feed.link).host().toUtf8().data()+"/favicon.ico"
        
        
        url_favicon = QtCore.QUrl(url)
        faviconInfo = QtCore.QFileInfo(url_favicon.path())
        favicon = QtCore.QString(faviconInfo.fileName()).toUtf8().data()
        
#        ifavicon=url.rfind('/')
#        favicon=url[ifavicon+1:]
        logo_file=ChannelDir +'/'+favicon
        if '.ico' in logo_file :
            logo_file = logo_file.replace('.ico','.icon')
        item2 = QtGui.QTreeWidgetItem(self.treeWidget)
        item2.setText(0,w.feed.title)
        item2.setText(1,url)
        item2.setText(5,url)
        self.dd.append(Download())
        self.dd[len(self.http)-1].setup()
        self.dd[len(self.http)-1].downloadFile( url, item2)
        
        if w.feed.has_key('subtitle'):
            ChannelSubtitle=w.feed.subtitle
        else:
            ChannelSubtitle=u'Nema opisa'
#        convert logo_file png:logo_file
#        p = QPixmap(logo_file)
#        im=p.convertToImage()
##            im=im.smoothScale(50,50,QImage.ScaleMin)
#        p.convertFromImage(im)
#        p.save(logo_file,'PNG')
#        os.makedirs(w.feed.title)

        if w.feed.has_key('links'): 
            ChannelHomepage = w.feed.links[0].href
        else:
            ChannelHomepage='http://google.com'

#        newChannel = Channel(title=ChannelTitle,link=feedLink,description=ChannelSubtitle,logo=logo_file, logobig=logo_fileBig)
        newChannel = Channel(title=ChannelTitle,link=feedLink,description=ChannelSubtitle,logo=logo_file, logobig=logo_fileBig,homepage=ChannelHomepage)
        for i in w.entries:
            if i.has_key('title'):
                newEpisode = Episode(title=i.title)
            else:
                newEpisode = Episode(title=u'pajseri nisu stavili naziv epizode')
            if i.has_key('enclosures'):
                newEpisode.enclosure = i.enclosures[0].href
                try:
                    newEpisode.size = i.enclosures[0].length
                except:
                    newEpisode.size = 1
            if i.has_key('summary_detail'):
                newEpisode.description = i.summary_detail.value
            if i.has_key('updated'):
#                epDate=strftime("%x", i.updated_parsed)
                if i.updated_parsed:
                    epDate=mktime(i.updated_parsed)
                    newEpisode.date = epDate
                else:
                    epDate=mktime(gmtime())

            newChannel.episode.append(newEpisode)
        session.commit()
        self.update_channel_list()
        os.chdir(os.path.expanduser('~')+'/.brePodder') 
        

    def ChannelActivated(self, a, i):
#        print "ChannelActivated"
        self.update_episode_list(a.text(i).toUtf8().data().decode('UTF8'))
#        self.update_episode_list(a.text(i))
#        self.update_episode_list(a.text(i).toUtf8().data().decode())
#        self.CurrentChannel=a.text(0).toUtf8().data().decode()
        self.CurrentChannel=a.text(0).toUtf8().data().decode('UTF8')
        self.actionCancel.setToolTip("Delete Selected Channel")
        self.actionUpdateFeeds.setToolTip("Update Selected Channel")
    
    def delete_channel(self):
        if self.tab.isVisible():
#            print "delete_channel"
            c=self.CurrentChannel
            ch=Channel.query.filter_by(title=self.CurrentChannel).one()
#            print ch
            j=0
            for i in ch.episode:
                ch.episode[j].delete()
                j=j+1
            ch.delete()
            #ovde treba da se rekurzivno obrise i direktorijum
            session.commit()
            self.update_channel_list()

#last 20 downloadowed episodes
    def update_lastest_episodes_list(self):
        episodes=Episode.query().filter_by(status=u'downloaded').limit(20).all()
        self.treeWidget_4.clear()
        for e in episodes:
            item = QtGui.QTreeWidgetItem(self.treeWidget_4)
            item.setText(0,e.channel.title)
            item.setText(1,e.title)
            item.setText(2,str(e.size/1024/1024)+' MB')
            item.setText(3,str(e.localfile))
            
    def update_episode_list(self,channel_Title):
#        cc = Channel.query.filter_by(title=channel_Title.toUtf8().data()).one()
        cc = Channel.query.filter_by(title=channel_Title).one()
        self.QTextBrowser1.setHtml("<p><img src="+"'"+cc.logobig+"'"+"><br>\n\n</p><p>"+cc.description+"</p><p><b>Homepage: </b><a href="+cc.homepage+">"+cc.homepage+"</a><p>")
        tt = Episode.query.filter(Episode.channel.has(title=channel_Title)).order_by(Episode.date.desc()).all() 
        self.treeWidget_2.clear()
        for t in tt:
            item2 = QtGui.QTreeWidgetItem(self.treeWidget_2)
            if not t.localfile:
                item2.setIcon(0,QtGui.QIcon("images/build.png"))
            else:
                item2.setIcon(0,QtGui.QIcon("images/mp3.png"))
            item2.setText(0,t.title)
            
            if t.size:
                if (t.size) > 1024*1024:
                    item2.setText(1,str(t.size/1024/1024)+' MB')
                else:   
                    item2.setText(1,str(t.size)+' B')
            else:
                item2.setText(1, 'None')
            try:
                b=gmtime(float(t.date))
                epDate=strftime("%x", b)
            except:
                epdate=gmtime()
                print "date exception"
            item2.setText(2,epDate)
            if t.status=='new':
                item2.setFont(0, self.fontBold)
         
    def update_channel_list(self):
        channels = Channel.query.all()
        self.listWidget.clear()
        for title in channels:
            item = QtGui.QTreeWidgetItem(self.listWidget)
            if title.episode[-1].status == u'new':
                item.setFont(0, self.fontBold)
            item.setText(0, title.title)
#        print self.freeBytes.available()
#        self.freeBytes.release()
#        print self.freeBytes.available()
#            item.setIcon(0, QtGui.QIcon(os.path.expanduser('~')+'/.brePodder/'+title.logo))
            item.setIcon(0, QtGui.QIcon(QtGui.QPixmap(os.path.expanduser('~')+'/.brePodder/'+title.logo)))

#            print os.path.expanduser('~')+'/.brePodder/'+title.logo
            item.setToolTip(0,"<p><img src="+"'"+title.logobig+"'"+"></p><p style='font-size:20pt'><b>"+title.title+"</b></p><a href="+title.link+">"+title.link+"</a>")
 
# dodati bold za channel koji ima novu epizodu. mislim da je to najefikasnije preko novog polja u bazi. 



    
    def update_channel(self):
        ch=Channel.query.filter_by(title=self.CurrentChannel).one()
        self.ChannelForUpdate=ch
        updtChTr=updateChannelThread(ch)
        QtCore.QObject.connect(updtChTr,QtCore.SIGNAL("updatesignal"),self.update_channel_list,QtCore.Qt.QueuedConnection)
        QtCore.QObject.connect(updtChTr,QtCore.SIGNAL("updatesignal_episodelist(PyQt_PyObject)"),self.update_episode_list,QtCore.Qt.QueuedConnection)
        
        self.ttthread=updtChTr
        updtChTr.start()
        
    def update_all_channels(self):
        updtChTr=[]
        ch=Channel.query.all()
        j=0
        for i in ch:
#            updtChTr=updateChannelThread(i)
#            QtCore.QObject.connect(updtChTr,QtCore.SIGNAL("updatesignal2"),self.update_channel_list,QtCore.Qt.QueuedConnection)
#            self.TTThread.append(updtChTr)
#            updtChTr.start()
            
            updtChTr.append(updateChannelThread(i))
#            QtCore.QObject.connect(updtChTr[j],QtCore.SIGNAL("updatesignal2"),self.update_channel_list,QtCore.Qt.BlockingQueuedConnection)
            self.TTThread.append(updtChTr[j])
            updtChTr[j].start()
            j=j+1
#        self.update_channel_list()
#        print 'update Channel List'
        QtCore.QObject.connect(updtChTr[j-1],QtCore.SIGNAL("updatesignal2"),self.update_channel_list,QtCore.Qt.QueuedConnection)

        
    
    def dialog_add(self):
        filename = QtGui.QFileDialog.getOpenFileName(MainWindow, 'Open file','/home')
#        file=open(filename)
#        cd = OpenFile()
#        cd.showDialog()
        print "dialog_add"
        print filename
    
    
    def app_quit(self):
#        print 'app_quit'
        app.exit()
    
    def export_opml(self):
        ch=Channel.query.all()
        o=opml.Exporter('brePodder.opml')
        o.write(ch)
        
    def import_opml(self):
#        ch=Channel.query.all()
        filename = QtGui.QFileDialog.getOpenFileName(MainWindow, 'Open file','/home')
#        i=opml.Importer('brePodderImport.opml')
        i=opml.Importer(filename.toAscii().data())
        i.get_model()
#        print "Import Done"
        for ch in i.items:
            self.AddChannel(ch['url'])
            
    def activeMenuChannels(self, pos):
        self.actionCancel.setText(QtGui.QApplication.translate("MainWindow", "Delete feed", None, QtGui.QApplication.UnicodeUTF8))
        globalPos = self.listWidget.mapToGlobal(pos);
        t=self.listWidget.indexAt(pos)
        self.menuChannels.popup(globalPos)
        
    def activeMenuDownloads(self, pos):
        self.actionCancel.setText(QtGui.QApplication.translate("MainWindow", "Cancel downlaod", None, QtGui.QApplication.UnicodeUTF8))
        globalPos = self.treeWidget.mapToGlobal(pos);
#        print pos.x(),  pos.y()
        t=self.treeWidget.indexAt(pos)
        self.menuDownloads.popup(globalPos)

        

class updateChannelThread(QtCore.QThread):
    def __init__(self,test):
        QtCore.QThread.__init__(self)
#        self.test = ui.ChannelForUpdate
        self.test = test
        self.newEpisodeExists=0
#        ui.freeBytes.acquire()

#        print test
        
    def run(self):
        ui.Mutex.lock()
        con = sqlite3.connect("/home/homoludens/.brePodder/podcasts.sqlite")
        con.isolation_level = None
        cur = con.cursor()
        self.updateChannel(self.test,cur)
        
        con.commit()
        cur.close()
        if self.newEpisodeExists:
            print self.newEpisodeExists
            print "self.newEpisodeExists"
#            self.emit(QtCore.SIGNAL("updatesignal"))
            self.emit(QtCore.SIGNAL("updatesignal2"))
#            self.emit(QtCore.SIGNAL("updatesignal_episodelist(PyQt_PyObject)"),self.test.title)
        ui.Mutex.unlock()
#        self.emit(QtCore.SIGNAL("updatesignal2"))
#        ui.usedBytes.acquire()
#        ui.freeBytes.release()
    

    def updateChannel(self, ch = None, cursor=None):
        newEpisode={}
        cur=cursor
        print "thread update channel"
        oldEpisodes=[]
        if ch == None:
            cc = cur.execute('select id,title from sql_channel where title =?', (self.CurrentChannel,))
            a = cc.fetchone()
            tt = cur.execute('select id,title,status from sql_episode where channel_id = ?', (a[0]))
        else:
            cc = cur.execute('select id,title,link from sql_channel where title =?', (ch.title,))
            a = cc.fetchone()
            tt = cur.execute('select id,title,status from sql_episode where channel_id = ?', (a[0],))
        newEpisode['channel_id'] = a[0]    
        epcount=0
        for j in tt:
            oldEpisodes.append(j[1])
            epcount=epcount+1
        feedLink = a[2].decode()
        w = feedparser.parse(feedLink)
        for i in w.entries:
            try:
                aa=oldEpisodes.index(i.title)
            except ValueError:
#                print "not in index"
                aa=None
            
            if i.has_key('title') and aa==None:
                print 'epizoda NE postoji'
                self.newEpisodeExists=1
                if i.title:
#                    newEpisode = Episode(title=i.title)
                    newEpisode['title']=i.title
                else:
#                    newEpisode = Episode(title=u'No Title')
                    newEpisode['title']=u'No Title'
                if i.has_key('enclosures'):
                    newEpisode['enclosure'] = i.enclosures[0].href
                    try:
                        newEpisode['size'] = int(i.enclosures[0].length)
                    except:
                        newEpisode['size']='1'
                    newEpisode['status'] = u"new"
                else:
                    newEpisode['enclosure'] = u'no file'
                    newEpisode['size'] = '0'
                    newEpisode['status'] = u"none"
                if i.has_key('summary_detail'):
                    newEpisode['description'] = i.summary_detail.value
                else:
                    newEpisode['description'] = u'No description'
                if i.has_key('updated'):
#                    print i.updated_parsed
#                    epDate=strftime("%x", i.updated_parsed)
                    if i.updated_parsed:
                        epDate=mktime(i.updated_parsed)
                    else:
                        epDate=mktime(gmtime())
                    newEpisode['date'] = epDate
#                    newEpisode.date = "12345"
                else:
                    epDate=mktime(gmtime())
                nEpisode=(newEpisode['title'], newEpisode['enclosure'], newEpisode['size'], newEpisode['date'], newEpisode['description'], newEpisode['status'], newEpisode['channel_id'])
                cur.execute('insert into sql_episode(title, enclosure, size, date, description, status, channel_id) values (?,?,?,?,?,?,?) ', nEpisode)
                
                #                cc.episode.append(newEpisode)
            elif not i.has_key('title'):
                print "NEMA NASLOVA EPIZODE"
                
            else:
                if j[2]!=u"old":
                    cur.execute('update  sql_episode set status= "old" where sql_episode.id = ?',(j[0],) )
#                   tt[aa].status=u"old"
#                print 'epizoda posoji'
#                newEpisode = Episode(title='pajseri nisu stavili naziv epizode')
#        session.commit()
#        session.close()
#        ui.update_channel_list()
#        ui.update_episode_list(cc.title)

    
if __name__ == "__main__":
    import sys
    os.chdir(os.path.expanduser('~'))
#    os.makedirs('.brePodder')
    os.chdir('.brePodder')
#    os.makedirs('images')
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    ui.update_channel_list()
    ui.update_lastest_episodes_list()
    sys.exit(app.exec_())
