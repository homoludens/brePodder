from PyQt4 import QtCore, QtGui, QtNetwork, QtWebKit
#, QtNetwork,  QtTest,  QtWebKit
#import feedparser
import os
#from getfavicon import getIcoUrl
from Download import *
#import Image
#import opml
import re
from time import gmtime, strftime, mktime, sleep
#from elixir import *
#import sqlalchemy
import sys
import sqlite3
from sql import *
#from Ui_add_folder import *
import feedparser
from audioplayer import AudioPlayer
#setup_all()

#sys.setappdefaultencoding('utf-8')
# constants

draggable = QtCore.Qt.ItemIsDragEnabled
droppable = QtCore.Qt.ItemIsDropEnabled
editable  = QtCore.Qt.ItemIsEditable
enabled   = QtCore.Qt.ItemIsEnabled
selectable = QtCore.Qt.ItemIsSelectable 
noflags = QtCore.Qt.NoItemFlags


#override QTreeViewWidget for handling Drag & Drop events 
class treeViewWidget( QtGui.QTreeWidget ):
    def __init__(self, parent=None):
      super(treeViewWidget, self).__init__(parent)
      self.setAcceptDrops(True)
      self.setDragEnabled(True)
      self.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
      self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
      self.sortByColumn(0, 0)

    def dropEvent(self, event):
        if self.itemAt( event.pos() ).flags() & droppable:         
#            what = self.selectedItems()[0].text(0)
#            where = self.itemAt(event.pos()).text(0)
#            ch=Channel.query.filter_by(title=self.selectedItems()[0].text(0)).one()
#            tx=Taxonomy.query.filter_by(title=self.itemAt(event.pos()).text(0)).one()  

            #TODO: SQL-- this on is out of scope and can not get to db object
            con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
            con.isolation_level = None
            cur = con.cursor()
            cur.execute('select id from sql_channel where title = ?', [self.selectedItems()[0].text(0).toUtf8().data(),]) 
            ch_id = cur.fetchone()[0]
            cur.execute('select id from sql_taxonomy where title = ?', ( self.itemAt(event.pos()).text(0).toUtf8().data(), ) )
            tx_id = cur.fetchone()[0]   
            cur.execute('update sql_channel set folder_id = :tx_id  where id = :ch_id', {"tx_id": tx_id, "ch_id": ch_id})
            con.commit()
            cur.close()
#            channelTitle = self.selectedItems()[0].text(0).toUtf8().data()
#            folderTitle = self.itemAt(event.pos()).text(0).toUtf8().data()
#            self.parent.db.addChannelToFolder(self,  channelTitle,  folderTitle)
            
#            ui.update_channel_list()
        else:
            print 'not folder'
            con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
            con.isolation_level = None
            cur = con.cursor()
            cur.execute('select id from sql_channel where title = ?', [self.selectedItems()[0].text(0).toUtf8().data(),])
	    ch_id = cur.fetchone()[0]  	    
	    cur.execute('update sql_channel set folder_id = NULL  where id = :ch_id', {"ch_id": ch_id})
	    con.commit()
 	    cur.close()

#      print dir(event)
#      event.setDropAction(QtCore.Qt.MoveAction)
#      event.accept() 

    def dropMimeData(self, parent, row, data, action):
        if action == QtCore.Qt.MoveAction:
            return self.moveSelection(parent, row)
        return False

    def dragEnterEvent(self, event):
            event.accept()
            print 'drag'


#Main application interface
class MainUi(object):
    def __init__(self, parent=None):
        self.http = []
        self.httpGetId = []
        self.outFile = []
#        self.itemZaPrenos = []
        self.downloadList=[]
#        self.itemZaPrenos = None
        self.rawstr = r"""(?:\<img.*?\c=")(.*?)(?:\")"""  #it's better with "\src" (not "\c") but that doesn't work
        self.compile_obj = re.compile(self.rawstr, re.I)
        self.fontBold = QtGui.QFont()
        self.fontBold.setWeight(75)
        self.fontBold.setBold(True)
        self.ChannelForUpdate=None
        self.TTThread=[]
#        self.BufferSize = 5
#        self.Mutex = QtCore.QMutex()
        
#        self.freeBytes.acquire()
        self.itemsDownloading=[]
        self.p=re.compile("\W")
        
        self.db = DBOperation()
        self.Sem = QtCore.QSemaphore(5)
        
    def setupUi(self, MainWindow):     
        self.MW =  MainWindow
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(QtCore.QSize(QtCore.QRect(0,0,600,400).size()).expandedTo(MainWindow.minimumSizeHint()))
        MainWindow.setWindowIcon(QtGui.QIcon("images/musicstore.png"))

        self.centralwidget = QtGui.QWidget(MainWindow)
        #self.centralwidget.setObjectName("centralwidget")

        self.gridlayout = QtGui.QGridLayout(self.centralwidget)
        #self.gridlayout.setObjectName("gridlayout")

        self.tabWidget = QtGui.QTabWidget(self.centralwidget)
        #self.tabWidget.setObjectName("tabWidget")

        self.tab = QtGui.QWidget()
        #self.tab.setObjectName("tab")

        self.gridlayout1 = QtGui.QGridLayout(self.tab)
        #self.gridlayout1.setObjectName("gridlayout1")

        self.splitter_2 = QtGui.QSplitter(self.tab)
        self.splitter_2.setOrientation(QtCore.Qt.Horizontal)
        #self.splitter_2.setObjectName("splitter_2")
	#self.splitter_2.setSizes( ( 200, 500) )

	self.splitter_22 = QtGui.QSplitter(self.splitter_2)
	self.splitter_22.setOrientation(QtCore.Qt.Vertical)


	#self.splitter_222 = QtGui.QSplitter(self.splitter_22)
	#self.splitter_222.setOrientation(QtCore.Qt.Horizontal)


        #self.widget = QtGui.QWidget(self.splitter_2)
        #self.widget.setObjectName("widget")

        #self.vboxlayout = QtGui.QVBoxLayout(self.widget)
        #self.vboxlayout.setSpacing(-1)
        #self.vboxlayout.setObjectName("vboxlayout")

        self.listWidget = treeViewWidget( self.splitter_22 )
        
        #sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred,QtGui.QSizePolicy.Expanding)
        #sizePolicy.setHorizontalStretch(0)
        #sizePolicy.setVerticalStretch(0)
        #sizePolicy.setHeightForWidth(self.listWidget.sizePolicy().hasHeightForWidth())
        
	#self.listWidget.setSizePolicy(sizePolicy)
        #self.listWidget.setMaximumSize(QtCore.QSize(16777215,16777215))
        #self.listWidget.setSizeIncrement(QtCore.QSize(0,0))
        #self.listWidget.setBaseSize(QtCore.QSize(0,0))
        self.listWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        #self.listWidget.setObjectName("listWidget")
        self.listWidget.setAlternatingRowColors(True)
        #self.listWidget.setLineWidth(5)
        #self.listWidget.setMidLineWidth(8)
        self.listWidget.setDragEnabled(True)
        self.listWidget.setDragDropOverwriteMode(True)
        self.listWidget.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        #self.listWidget.setAlternatingRowColors(True)
        #self.listWidget.setIconSize(QtCore.QSize(18,-1))
        #self.listWidget.setIndentation(23)
        #self.listWidget.setRootIsDecorated(True)
        #self.listWidget.setUniformRowHeights(True)
        #self.listWidget.setSortingEnabled(True)
        #self.listWidget.setAnimated(True)

        #self.vboxlayout.addWidget( self.listWidget )
        

        #self.hboxlayout = QtGui.QHBoxLayout()
        #self.hboxlayout.setObjectName("hboxlayout")

        self.splitter_222 = QtGui.QSplitter(self.splitter_22)
        self.splitter_222.setOrientation(QtCore.Qt.Horizontal)


        self.QLineEdit1 = QtGui.QLineEdit( self.splitter_222 )

        #sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.Fixed)
        #sizePolicy.setHorizontalStretch(0)
        #sizePolicy.setVerticalStretch(0)
        #sizePolicy.setHeightForWidth(self.QLineEdit1.sizePolicy().hasHeightForWidth())
        
	#self.QLineEdit1.setSizePolicy(sizePolicy)
        #self.QLineEdit1.setMinimumSize(QtCore.QSize(0,0))
        #self.QLineEdit1.setMaximumSize(QtCore.QSize(16777215,16777215))
        #self.QLineEdit1.setObjectName("QLineEdit1")

        #self.splitter_222.addWidget( self.widget )
        
        self.updateProgressBar = QtGui.QProgressBar(self.splitter_222)
        self.updateProgressBar.setValue(42);
        #self.updateProgressBar.setSizePolicy(sizePolicy)
        #self.updateProgressBar.setMinimumSize(QtCore.QSize(0,0))
        #self.updateProgressBar.setMaximumSize(QtCore.QSize(16777215,16777215))
        self.updateProgressBar.hide();
        self.splitter_222.addWidget( self.updateProgressBar )
        
        self.QPushButton1 = QtGui.QPushButton(self.splitter_222)

        #sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum,QtGui.QSizePolicy.Fixed)
        #sizePolicy.setHorizontalStretch(0)
        #sizePolicy.setVerticalStretch(0)
        #sizePolicy.setHeightForWidth(self.QPushButton1.sizePolicy().hasHeightForWidth())

        #self.QPushButton1.setSizePolicy(sizePolicy)
        self.QPushButton1.setMinimumSize(QtCore.QSize(20,20))
        self.QPushButton1.setMaximumSize(QtCore.QSize(50,25))
        #self.QPushButton1.setObjectName("QPushButton1")
        self.splitter_222.addWidget(self.QPushButton1)

	self.splitter_2.setSizes( ( 100, 50) )

        #self.vboxlayout.addLayout(self.hboxlayout)

        self.splitter = QtGui.QSplitter(self.splitter_2)
        
        #sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        #sizePolicy.setHorizontalStretch(0)
        #sizePolicy.setVerticalStretch(0)
        #sizePolicy.setHeightForWidth(self.splitter.sizePolicy().hasHeightForWidth())
        #self.splitter.setSizePolicy(sizePolicy)
        
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        #self.splitter.setObjectName("splitter")

        self.treeWidget_2 = QtGui.QTreeWidget( self.splitter )
        #self.treeWidget_2.setItemsExpandable(False)
        #self.treeWidget_2.setAnimated(True)
        self.treeWidget_2.setAlternatingRowColors(True)
        self.treeWidget_2.setObjectName("treeWidget_2")
        
	#TODO: make settings fot choosing WebKit insted of QTextBrowser
        #self.QTextBrowser1 = QtWebKit.QWebView(self.splitter) #Qt4.4
        self.QTextBrowser1 = QtGui.QTextBrowser(self.splitter) # Qt4.3
#        self.QTextBrowser1.setOpenExternalLinks(1)
#        self.QTextBrowser1.setOpenLinks(1)

        #sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.Expanding)
        #sizePolicy.setHorizontalStretch(0)
        #sizePolicy.setVerticalStretch(0)
        #sizePolicy.setHeightForWidth(self.QTextBrowser1.sizePolicy().hasHeightForWidth())
        #self.QTextBrowser1.setSizePolicy(sizePolicy)
        #self.QTextBrowser1.setMinimumSize(QtCore.QSize(0,0))
        #self.QTextBrowser1.setSizeIncrement(QtCore.QSize(4,0))
        #self.QTextBrowser1.setBaseSize(QtCore.QSize(400,0))
        self.QTextBrowser1.setObjectName("QTextBrowser1")

	self.AudioPlayer = AudioPlayer( "", self.splitter)

        self.gridlayout1.addWidget( self.splitter_2, 0, 0, 1, 1 )

        self.tabWidget.addTab( self.tab,"" )


        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName("tab_2")

        self.gridlayout2 = QtGui.QGridLayout(self.tab_2)
        self.gridlayout2.setObjectName("gridlayout2")

        self.treeWidget = QtGui.QTreeWidget(self.tab_2)
        self.treeWidget.setAlternatingRowColors(True)
        #self.treeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeWidget.setObjectName("treeWidget")
        self.gridlayout2.addWidget(self.treeWidget,0,0,1,1)
        self.tabWidget.addTab(self.tab_2,"")

        self.tab_3 = QtGui.QWidget()
        self.tab_3.setObjectName("tab_3")
        
        
        self.treeWidget_4 = QtGui.QTreeWidget(self.tab_3)
        #self.treeWidget_4.setWindowModality(QtCore.Qt.NonModal)
        #self.treeWidget_4.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        #self.treeWidget_4.setItemsExpandable(False)
        #self.treeWidget_4.setSortingEnabled(True)
        #self.treeWidget_4.setAnimated(True)
        self.treeWidget_4.setObjectName("treeWidget_4")
        
        
        self.gridlayout3 = QtGui.QGridLayout(self.tab_3)
        self.gridlayout3.setObjectName("gridlayout3")
        self.gridlayout3.addWidget(self.treeWidget_4,0,0,1,1)
        self.tabWidget.addTab(self.tab_3,"")
        self.gridlayout.addWidget(self.tabWidget,0,0,1,1)

        self.splitter_3 = QtGui.QSplitter(self.tab_3)
        #self.splitter_3.setOrientation(QtCore.Qt.Horizontal)
	self.gridlayout3.addWidget(self.splitter_3)
	self.AudioPlayer_latestDownloads = AudioPlayer( "", self.splitter_3 )         
	
	MainWindow.setCentralWidget(self.centralwidget)

        #Tab with newest episodes
        self.tab_4 = QtGui.QWidget()
        self.tab_4.setObjectName("tab_4")    
        
        self.treeWidget_5 = QtGui.QTreeWidget( self.tab_4 )
        #self.treeWidget_5.setWindowModality(QtCore.Qt.NonModal)
        #self.treeWidget_5.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        #self.treeWidget_5.setItemsExpandable(False)
        #self.treeWidget_5.setSortingEnabled(True)
        #self.treeWidget_5.setAnimated(True)
        #self.treeWidget_5.setObjectName("treeWidget_4")




        self.gridlayout4 = QtGui.QGridLayout( self.tab_4 )
        self.gridlayout4.setObjectName( "gridlayout4" )
        self.gridlayout4.addWidget( self.treeWidget_5,0,0,1,1 )
        self.tabWidget.addTab( self.tab_4,"" )
        self.gridlayout.addWidget( self.tabWidget,0,0,1,1 )


        self.splitter_4 = QtGui.QSplitter(self.tab_4)
        #self.splitter_4.setOrientation(QtCore.Qt.Horizontal)
	self.gridlayout4.addWidget(self.splitter_4)
	self.AudioPlayer_newestEpisodes = AudioPlayer( "", self.splitter_4 )

        MainWindow.setCentralWidget(self.centralwidget)




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
        
        self.actionNewFolder = QtGui.QAction(MainWindow)
        self.actionNewFolder.setIcon(QtGui.QIcon("images/reload.png"))
        self.actionNewFolder.setObjectName("actionNewFolder")
        
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
        self.menuChannels.addAction(self.actionNewFolder)
        self.menuChannels.addAction(self.actionImport)
        self.menuChannels.addAction(self.actionExport)
        self.menuPodcasts.addSeparator()
        self.menuChannels.addAction(self.actionCancel)
        
        self.menuDownloads.addAction(self.actionUpdateFeeds)
        self.menuDownloads.addAction(self.actionCancel)
        
        self.trayIcon = QtGui.QSystemTrayIcon(QtGui.QIcon("images/musicstore.png"),MainWindow)
        self.trayIcon.setContextMenu(self.menuPodcasts)
        self.trayIcon.show()
        
        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QObject.connect(self.listWidget,QtCore.SIGNAL("itemSelectionChanged()"),self.channel_activated)
        
        QtCore.QObject.connect(self.QPushButton1,QtCore.SIGNAL("clicked()"),self.AddChannel)
        QtCore.QObject.connect(self.QPushButton1,QtCore.SIGNAL("clicked()"),self.QLineEdit1.clear)
        QtCore.QObject.connect(self.treeWidget_2,QtCore.SIGNAL("itemSelectionChanged()"),self.episode_activated)
        QtCore.QObject.connect(self.treeWidget_2,QtCore.SIGNAL("itemDoubleClicked(QTreeWidgetItem*,int)"),self.EpisodeDoubleClicked)
        QtCore.QObject.connect(self.treeWidget_4,QtCore.SIGNAL("itemDoubleClicked(QTreeWidgetItem*,int)"),self.LastestEpisodeDoubleClicked)
	QtCore.QObject.connect(self.treeWidget_5,QtCore.SIGNAL("itemDoubleClicked(QTreeWidgetItem*,int)"),self.NewestEpisodeDoubleClicked)

        QtCore.QObject.connect(self.treeWidget,QtCore.SIGNAL("itemClicked(QTreeWidgetItem*,int)"),self.DownloadActivated)
        QtCore.QObject.connect(self.trayIcon,QtCore.SIGNAL("activated(QSystemTrayIcon::ActivationReason)"),self.trayIconActivated)
        QtCore.QObject.connect(self.actionUpdateFeeds,QtCore.SIGNAL("activated()"),self.update_channel)
        QtCore.QObject.connect(self.actionNewFolder,QtCore.SIGNAL("activated()"),self.create_new_foder)
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
        self.QLineEdit1.selectAll()
        self.QPushButton1.setText(QtGui.QApplication.translate("MainWindow", "Add", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_2.setStatusTip(QtGui.QApplication.translate("MainWindow", "epizode", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_2.headerItem().setText(0,QtGui.QApplication.translate("MainWindow", "episode", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_2.headerItem().setText(1,QtGui.QApplication.translate("MainWindow", "size", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_2.headerItem().setText(2,QtGui.QApplication.translate("MainWindow", "date", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_2.header().resizeSection(0, 300)
        self.treeWidget_2.clear()

#        item2 = QtGui.QTreeWidgetItem(self.treeWidget_2)
#        item2.setIcon(0,QtGui.QIcon("images/build.png"))
#        item2.setText(0,QtGui.QApplication.translate("MainWindow", "naziv", None, QtGui.QApplication.UnicodeUTF8))
#        item2.setText(1,QtGui.QApplication.translate("MainWindow", "33 MB", None, QtGui.QApplication.UnicodeUTF8))
#        self.QTextBrowser1.setStatusTip(QtGui.QApplication.translate("MainWindow", "opis", None, QtGui.QApplication.UnicodeUTF8))
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
        self.treeWidget.header().resizeSection(0, 200)
        self.treeWidget.header().resizeSection(1, 200)
        self.treeWidget.clear()

#        item3 = QtGui.QTreeWidgetItem(self.treeWidget)
#        item3.setText(0,QtGui.QApplication.translate("MainWindow", "dl-ch", None, QtGui.QApplication.UnicodeUTF8))
#        item3.setText(1,QtGui.QApplication.translate("MainWindow", "dl-ep", None, QtGui.QApplication.UnicodeUTF8))
#        item3.setText(2,QtGui.QApplication.translate("MainWindow", "dl-size", None, QtGui.QApplication.UnicodeUTF8))
#        item3.setText(3,QtGui.QApplication.translate("MainWindow", "dl-proc", None, QtGui.QApplication.UnicodeUTF8))
#        item3.setText(4,QtGui.QApplication.translate("MainWindow", "dl-speed", None, QtGui.QApplication.UnicodeUTF8))
#        item3.setText(5,QtGui.QApplication.translate("MainWindow", "dl-link", None, QtGui.QApplication.UnicodeUTF8))
        
        
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
        self.treeWidget_4.header().resizeSection(0, 200)
        self.treeWidget_4.header().resizeSection(1, 200)
        self.treeWidget_4.clear()
        
        self.treeWidget_5.headerItem().setText(0,QtGui.QApplication.translate("MainWindow", "Channel", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_5.headerItem().setText(1,QtGui.QApplication.translate("MainWindow", "Episode", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_5.headerItem().setText(2,QtGui.QApplication.translate("MainWindow", "Size", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_5.headerItem().setText(3,QtGui.QApplication.translate("MainWindow", "Date", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_5.headerItem().setText(4,QtGui.QApplication.translate("MainWindow", "Enclosure", None, QtGui.QApplication.UnicodeUTF8))
	self.treeWidget_5.header().resizeSection(0, 200)
        self.treeWidget_5.header().resizeSection(1, 200)
        self.treeWidget_5.clear()

        item6 = QtGui.QTreeWidgetItem(self.treeWidget_4)
        item6.setText(0,QtGui.QApplication.translate("MainWindow", "ch", None, QtGui.QApplication.UnicodeUTF8))
        item6.setText(1,QtGui.QApplication.translate("MainWindow", "ep", None, QtGui.QApplication.UnicodeUTF8))
        item6.setText(2,QtGui.QApplication.translate("MainWindow", "size", None, QtGui.QApplication.UnicodeUTF8))
        item6.setText(3,QtGui.QApplication.translate("MainWindow", "local file", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QtGui.QApplication.translate("MainWindow", "Lastest downloads", None, QtGui.QApplication.UnicodeUTF8))
        
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QtGui.QApplication.translate("MainWindow", "Newest Episodes", None, QtGui.QApplication.UnicodeUTF8))
        
        self.menuPodcasts.setTitle(QtGui.QApplication.translate("MainWindow", "Podcasts", None, QtGui.QApplication.UnicodeUTF8))
        self.toolBar.setWindowTitle(QtGui.QApplication.translate("MainWindow", "toolBar", None, QtGui.QApplication.UnicodeUTF8))
        self.actionCancel.setText(QtGui.QApplication.translate("MainWindow", "Delete feed", None, QtGui.QApplication.UnicodeUTF8))
        self.actionImport.setText(QtGui.QApplication.translate("MainWindow", "Import", None, QtGui.QApplication.UnicodeUTF8))
        self.actionExport.setText(QtGui.QApplication.translate("MainWindow", "Export", None, QtGui.QApplication.UnicodeUTF8))
        self.actionNew.setText(QtGui.QApplication.translate("MainWindow", "Add New", None, QtGui.QApplication.UnicodeUTF8))
        self.actionUpdateAllChannels.setText(QtGui.QApplication.translate("MainWindow", "Update All", None, QtGui.QApplication.UnicodeUTF8))
        self.actionQuit.setText(QtGui.QApplication.translate("MainWindow", "Quit", None, QtGui.QApplication.UnicodeUTF8))
        self.actionUpdateFeeds.setText(QtGui.QApplication.translate("MainWindow", "Fetch Feed", None, QtGui.QApplication.UnicodeUTF8))
        self.actionNewFolder.setText(QtGui.QApplication.translate("MainWindow", "New Folder", None, QtGui.QApplication.UnicodeUTF8))

    
    def trayIconActivated(self, reason):
        if reason==3  or reason ==2:
            if MainWindow.isHidden():
                MainWindow.show()
            else:
                MainWindow.hide()


    def dialog_add(self):
        filename = QtGui.QFileDialog.getOpenFileName(MainWindow, 'Open file','/home')
#        file=open(filename)
#        cd = OpenFile()
#        cd.showDialog()
        print "dialog_add"
        print filename
    
    
    def export_opml(self):
        import opml
        channels = self.db.getAllChannels()
        o=opml.Exporter('brePodder.opml')
        o.write(channels)
        
    def import_opml(self):
        import opml
        filename = QtGui.QFileDialog.getOpenFileName(MainWindow, 'Open file','/home')
#        i=opml.Importer('brePodderImport.opml')
        i=opml.Importer(filename.toAscii().data())
        i.get_model()
        for ch in i.items:
            self.AddChannel(ch['url'])
            
    def activeMenuChannels(self, pos):
        self.actionCancel.setText(QtGui.QApplication.translate("MainWindow", "Delete feed", None, QtGui.QApplication.UnicodeUTF8))
        globalPos = self.listWidget.mapToGlobal(pos)
        globalPos.setY(globalPos.y() + 25)
        t=self.listWidget.indexAt(pos)
        self.menuChannels.popup(globalPos)
        
        
    def activeMenuDownloads(self, pos):
        self.actionCancel.setText(QtGui.QApplication.translate("MainWindow", "Cancel downlaod", None, QtGui.QApplication.UnicodeUTF8))
        globalPos = self.treeWidget.mapToGlobal(pos)
        globalPos.setY(globalPos.y() + 25)
        t=self.treeWidget.indexAt(pos)
        self.menuDownloads.popup(globalPos)
        
    def app_quit(self):
        app.exit()
    


