#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui, QtNetwork, QtWebKit
#, QtNetwork,  QtTest,  QtWebKit
#import feedparser
import os
#from getfavicon import getIcoUrl
from Download import *
import Image
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

#setup_all()

sys.setappdefaultencoding('utf-8')
# constants

draggable = QtCore.Qt.ItemIsDragEnabled
droppable = QtCore.Qt.ItemIsDropEnabled
editable  = QtCore.Qt.ItemIsEditable
enabled   = QtCore.Qt.ItemIsEnabled
selectable = QtCore.Qt.ItemIsSelectable 
noflags = QtCore.Qt.NoItemFlags


#override od treeViewWidger
class treeViewWidget(QtGui.QTreeWidget):
    def __init__(self, parent=None):
      super(treeViewWidget, self).__init__(parent)
      self.setAcceptDrops(True)
      self.setDragEnabled(True)
      self.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
      self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
      self.sortByColumn(0, 0)

    def dropEvent(self, event):
        if self.itemAt(event.pos()).flags() & droppable:         
#            what = self.selectedItems()[0].text(0)
#            where = self.itemAt(event.pos()).text(0)
#            ch=Channel.query.filter_by(title=self.selectedItems()[0].text(0)).one()
#            tx=Taxonomy.query.filter_by(title=self.itemAt(event.pos()).text(0)).one()           
            con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
            con.isolation_level = None
            cur = con.cursor()
            cur.execute('select id from sql_channel where title = ?', [self.selectedItems()[0].text(0).toUtf8().data(),]) 
            ch_id = cur.fetchone()[0]
            cur.execute('select id from sql_taxonomy where title = ?', (self.itemAt(event.pos()).text(0).toUtf8().data(),))
            tx_id = cur.fetchone()[0]   
            cur.execute('update sql_channel set folder_id = :tx_id  where id = :ch_id', {"tx_id": tx_id, "ch_id": ch_id})
            con.commit()
            cur.close()
            ui.update_channel_list()
        else:
            print 'not folder'

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



class BrePodder(object):
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
        self.BufferSize = 5
#        self.freeBytes = QtCore.QSemaphore(self.BufferSize)
#        self.usedBytes = QtCore.QSemaphore()
        self.Mutex = QtCore.QMutex()
        self.Sem = QtCore.QSemaphore(5)
#        self.freeBytes.acquire()
        self.itemsDownloading=[]
        self.p=re.compile("\W")

    def memory_usage(a):
        """Memory usage of the current process in kilobytes."""
        status = None
        result = {'peak': 0, 'rss': 0}
        try:
            # This will only work on systems with a /proc file system
            # (like Linux).
            status = open('/proc/self/status')
            for line in status:
                parts = line.split()
                key = parts[0][2:-1].lower()
                if key in result:
                    result[key] = int(parts[1])
        finally:
            if status is not None:
                status.close()
        return result
        
    def setupUi(self, MainWindow):      
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(QtCore.QSize(QtCore.QRect(0,0,600,400).size()).expandedTo(MainWindow.minimumSizeHint()))
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

        self.listWidget = treeViewWidget(self.widget)
        
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred,QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.listWidget.sizePolicy().hasHeightForWidth())
        self.listWidget.setSizePolicy(sizePolicy)
        self.listWidget.setMaximumSize(QtCore.QSize(16777215,16777215))
        self.listWidget.setSizeIncrement(QtCore.QSize(0,0))
        self.listWidget.setBaseSize(QtCore.QSize(0,0))
        self.listWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.listWidget.setObjectName("listWidget")
        self.listWidget.setAlternatingRowColors(True)
        self.listWidget.setLineWidth(5)
        self.listWidget.setMidLineWidth(8)
        self.listWidget.setDragEnabled(True)
        self.listWidget.setDragDropOverwriteMode(True)
        self.listWidget.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.listWidget.setAlternatingRowColors(True)
        self.listWidget.setIconSize(QtCore.QSize(18,-1))
        self.listWidget.setIndentation(23)
        self.listWidget.setRootIsDecorated(True)
        self.listWidget.setUniformRowHeights(True)
        self.listWidget.setSortingEnabled(True)
        self.listWidget.setAnimated(True)
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
        
        self.updateProgressBar = QtGui.QProgressBar(self.widget)
        self.updateProgressBar.setValue(42);
        self.updateProgressBar.setSizePolicy(sizePolicy)
        self.updateProgressBar.setMinimumSize(QtCore.QSize(0,0))
        self.updateProgressBar.setMaximumSize(QtCore.QSize(16777215,16777215))
        self.updateProgressBar.hide();
        self.hboxlayout.addWidget(self.updateProgressBar)
        
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
        self.treeWidget_2.setAnimated(True)
        self.treeWidget_2.setAlternatingRowColors(True)
        self.treeWidget_2.setObjectName("treeWidget_2")
        
#TODO: make settings fot choosing WebKit insted of QTextBrowser
#        self.QTextBrowser1 = QtWebKit.QWebView(self.splitter) #Qt4.4
        self.QTextBrowser1 = QtGui.QTextBrowser(self.splitter) # Qt4.3
#        self.QTextBrowser1.setOpenExternalLinks(1)
#        self.QTextBrowser1.setOpenLinks(1)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.QTextBrowser1.sizePolicy().hasHeightForWidth())
        self.QTextBrowser1.setSizePolicy(sizePolicy)
        self.QTextBrowser1.setMinimumSize(QtCore.QSize(0,0))
        self.QTextBrowser1.setSizeIncrement(QtCore.QSize(4,0))
        self.QTextBrowser1.setBaseSize(QtCore.QSize(400,0))
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

        #Tab with newest episodes
        self.tab_4 = QtGui.QWidget()
        self.tab_4.setObjectName("tab_4")    
        
        self.treeWidget_5 = QtGui.QTreeWidget(self.tab_4)
        self.treeWidget_5.setWindowModality(QtCore.Qt.NonModal)
        self.treeWidget_5.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeWidget_5.setItemsExpandable(False)
        self.treeWidget_5.setSortingEnabled(True)
        self.treeWidget_5.setAnimated(True)
        self.treeWidget_5.setObjectName("treeWidget_4")
        
        self.gridlayout4 = QtGui.QGridLayout(self.tab_4)
        self.gridlayout4.setObjectName("gridlayout4")
        self.gridlayout4.addWidget(self.treeWidget_5,0,0,1,1)
        self.tabWidget.addTab(self.tab_4,"")
        self.gridlayout.addWidget(self.tabWidget,0,0,1,1)
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
                
                
# TODO: download images from episode description so i can show them in QTextBrowser
# this is beta... :)
    def getImageFromDesc(self, desc,  channel):
#        p=re.compile("\W")  
        ChannelDir = self.p.sub("",channel.title)
        os.chdir(os.path.expanduser('~')+'/.brePodder/'+ChannelDir)
        
        match_obj = self.compile_obj.findall(desc)
        
        for image in match_obj:
            p = re.compile(image)
            i=image.rfind('/')
            desc = p.sub( os.getcwd()+image[i:], desc)
            
            if len(self.downloadList)>0:
                downloadId = self.downloadList[-1][0]+1
            else:
                downloadId = 0
#            print "downloadId: " + str(downloadId)
            self.downloadList.append((downloadId, Download()))
            self.downloadList[downloadId][1].setup(self)
            
            item = QtGui.QTreeWidgetItem(self.treeWidget)
            item.setText(0,channel.title)
            item.setText(5,image)
            
            self.downloadList[downloadId][1].downloadFile(image.replace(" ", "%20"), item, downloadId)
            
        os.chdir(os.path.expanduser('~')+'/.brePodder')            
        return desc
        
    def episode_activated(self):
        if self.treeWidget_2.selectedItems():
            selection = self.treeWidget_2.selectedItems()[0]
            try:
                e=Episode.query.filter_by(title=selection.text(0).toUtf8().data().decode()).one()
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

                self.QTextBrowser1.setHtml("<p>"+desc+"</br>\n\r</p><p><b>FILE: </b><a href="+enc+">"+enc+"</a></p>\
                                            <p><b>LOCALFILE: </b><a href="+localFile+">"+localFile+"</a></p>\
                                            <p>PLAY:<audio_off  controls='controls' src='"+enc+"'/></p>")

            except:
                print "EpisodeActivated exception"
    
    def DownloadActivated(self, a, i):
        self.itemZaPrekid=a
        self.actionCancel.setToolTip("Remove Selected Download")
        self.actionPause.setToolTip("Pause Selected Download")
        self.actionResume.setToolTip("Resume Selected Download")
    
    def EpisodeDoubleClicked(self, a):
# TODO: change backgroundColor or something else with QBrush
        a.setFont(0, self.fontBold)   
        e=Episode.query.filter_by(title=a.text(0).toUtf8().data().decode('UTF8')).one()
#        p=re.compile("\W")  
        ChannelDir = self.p.sub("",e.channel.title)
        
        os.chdir(os.path.expanduser('~')+'/.brePodder/'+ChannelDir)
        item = QtGui.QTreeWidgetItem(self.treeWidget)
        item.setText(0,e.channel.title)
        item.setText(1,e.title)
        item.setText(2,self.getReadableSize(e.size))
        item.setText(3,'0')
        item.setText(4,'0')

        try:
            item.setText(5,e.enclosure)
        except TypeError:
            print TypeError
            item.setText(5,"No link")
        
        session.commit()
        
        if len(self.downloadList)>0:
            downloadId = self.downloadList[-1][0]+1
        else:
            downloadId = 0
#        print "downloadId: " + str(downloadId)
        self.itemsDownloading.append((downloadId, e.enclosure.replace(" ", "%20"))) 
        self.downloadList.append((downloadId, Download()))
        self.downloadList[downloadId][1].setup(self)
        self.downloadList[downloadId][1].downloadFile(e.enclosure.replace(" ", "%20"), item, downloadId)
 
          
        os.chdir(os.path.expanduser('~')+'/.brePodder') 

    def AddChannel(self, newUrl = None):
        import feedparser
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
            
#        p=re.compile("\W")  
        ChannelDir = self.p.sub("",ChannelTitle)
        try:
            os.mkdir(ChannelDir)
        except:
            print "directory exists"
        os.chdir(ChannelDir)
#        os.makedirs(ChannelTitle.decode())
#        os.chdir(ChannelTitle)

#        logo_file=ChannelTitle + '/favicon.png' 
        item.setText(0,ChannelTitle)
# download Channel logo
        if w.feed.has_key('image'):
            if w.feed.image.href != None:
#            item = QtGui.QTreeWidgetItem(self.treeWidget)
#            item.setText(0,w.feed.title)
                item.setText(1,w.feed.image.href)
                item.setText(5,w.feed.image.href)
 
 
                 
                
                if len(self.downloadList)>0:
                    downloadId = self.downloadList[-1][0]+1
                else:
                    downloadId = 0
#                print "downloadId: " + str(downloadId)
                self.itemsDownloading.append((downloadId, w.feed.image.href))
                self.downloadList.append((downloadId, Download()))
                self.downloadList[downloadId][1].setup(self)
                self.downloadList[downloadId][1].downloadFile(w.feed.image.href, item, downloadId)


                url_done = QtCore.QUrl(w.feed.image.href)
                fileInfo = QtCore.QFileInfo(url_done.path())
                fileName = QtCore.QString(fileInfo.fileName())
                
    #            i = w.feed.image.href.rfind('/')
    #            logo_fileBig = ChannelTitle+"/"+w.feed.image.href[i+1:]

    # should we put original or 128px version of logo
                logo_fileBig = ChannelDir+"/"+fileName.toUtf8().data()
            else: logo_fileBig=u"images/musicstore2.png"
        else: logo_fileBig=u"images/musicstore2.png"
#  download favicon
        from getfavicon import getIcoUrl
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
#        if '.ico' in logo_file :
#            logo_file = logo_file.replace('.ico','.icon')
        item2 = QtGui.QTreeWidgetItem(self.treeWidget)
        item2.setText(0,w.feed.title)
        item2.setText(1,url)
        item2.setText(5,url)
        
        if len(self.downloadList)>0:
            downloadId = self.downloadList[-1][0]+1
        else:
            downloadId = 0
        self.itemsDownloading.append((downloadId, url))
        self.downloadList.append((downloadId, Download()))
        self.downloadList[downloadId][1].setup(self)
        self.downloadList[downloadId][1].faviconFound=True
        self.downloadList[downloadId][1].downloadFile(url, item2, downloadId)
        
        
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
#            ChannelHomepage = w.feed.links[1].href
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
        

    def channel_activated(self):
        selection = self.listWidget.selectedItems()
        if selection:
            self.update_episode_list(selection[0].text(0).toUtf8().data().decode('UTF8'))
            self.CurrentChannel=selection[0].text(0).toUtf8().data().decode('UTF8')
            self.actionCancel.setToolTip("Delete Selected Channel")
            self.actionUpdateFeeds.setToolTip("Update Selected Channel")
        
    
    def delete_channel(self):
        if self.tab.isVisible():
            c=self.CurrentChannel
            ch=Channel.query.filter_by(title=self.CurrentChannel).one()
            j=0
            for i in ch.episode:
                ch.episode[j].delete()
                j=j+1
            ch.delete()

#            p=re.compile("\W")  
            os.chdir(os.path.expanduser('~')+'/.brePodder/')
            ChannelDir = os.path.expanduser('~')+'/.brePodder/'+self.p.sub("",ch.title)
            
            import shutil
            shutil.rmtree(ChannelDir)
            session.commit()
            self.update_channel_list()

#last 20 downloadowed episodes
    def update_lastest_episodes_list(self):

        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
        con.isolation_level = None
        cur = con.cursor()
        cur.execute('SELECT * FROM sql_episode WHERE status="downloaded" ORDER BY date DESC LIMIT 50')
        episodes = cur.fetchall()

        self.treeWidget_4.clear()

        #episodes=Episode.query.filter_by(status=u'downloaded').order_by(Episode.id.desc()).limit(50).all()
        for e in episodes:
            item = QtGui.QTreeWidgetItem(self.treeWidget_4)
            item.setText(0,str(e[8]))
            item.setText(1,e[1])
            item.setText(2,self.getReadableSize(e[4]))
            item.setText(3,os.path.expanduser('~')+'/.brePodder/'+str(e[3]))
            
#newest episodes
    def update_newest_episodes_list(self):
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
        con.isolation_level = None
        cur = con.cursor()
        cur.execute('SELECT * FROM sql_episode EP, sql_channel CH WHERE EP.channel_id = CH.id ORDER BY date DESC LIMIT 50')
        episodes = cur.fetchall()
        
#        episodes=Episode.query.order_by(Episode.date.desc()).limit(40).all()
        self.treeWidget_5.clear()
        for e in episodes:
            item = QtGui.QTreeWidgetItem(self.treeWidget_5)
            item.setText(0,str(e[10]))
            item.setIcon(0, QtGui.QIcon(QtGui.QPixmap(os.path.expanduser('~')+'/.brePodder/'+e[14])))
            item.setText(1,e[1])
            if e[4]:
                item.setText(2,self.getReadableSize(e[4]))
            else:
                item.setText(2,'???')
            try:
                b=gmtime(float(e[5]))
                epDate=strftime("%x", b)
            except:
                b=gmtime()
                epDate=strftime("%x", b)
            item.setText(3,epDate)
    
    def LastestEpisodeDoubleClicked(self, a):
#        print  a.text(3).toUtf8().data().decode('UTF8')
        os.system("mplayer "+a.text(3).toUtf8().data().decode('UTF8'))
        
    def getReadableSize(self,  size):
        if size:
            if (size) > 1024*1024:
                sizeReadable = str(size/1024/1024)+' MB'
            elif (size) > 1024:
                sizeReadable = str(size/1024)+' kB'
            else:   
                sizeReadable = str(size)+' B'
        else:
            sizeReadable = 'None'
        return sizeReadable
    
    def update_episode_list(self,channel_Title):
#        cc = Channel.query.filter_by(title=channel_Title.toUtf8().data()).one()
#        cc = Channel.query.filter_by(title=channel_Title).one()
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
        con.isolation_level = None
        cur = con.cursor()       
        cur.execute('select * from sql_channel where title = ?',(channel_Title,))
        cc = cur.fetchone()
#        self.QTextBrowser1.setHtml("<p><img src="+"'"+cc.logobig+"'"+"><br>\n\n</p><p>"+cc.description+"</p><p><b>Homepage: </b><a href="+cc.homepage+">"+cc.homepage+"</a><p>")
#        self.QTextBrowser1.setHtml("<p>"+cc.description+"</p><p><b>Homepage: </b><a href="+cc.homepage+">"+cc.homepage+"</a></p>")
        self.QTextBrowser1.setHtml("<p>"+cc[4]+"</p><p><b>Homepage: </b><a href="+cc[3]+">"+cc[3]+"</a></p>")

        tt = Episode.query.filter(Episode.channel.has(title=channel_Title)).order_by(Episode.date.desc()).all() 
        self.treeWidget_2.clear()
        for t in tt:
            item2 = QtGui.QTreeWidgetItem(self.treeWidget_2)
            if not t.localfile:
                item2.setIcon(0,QtGui.QIcon("images/build.png"))
            else:
                item2.setIcon(0,QtGui.QIcon("images/mp3.png"))
            item2.setText(0,t.title)
            item2.setText(1,self.getReadableSize(t.size))
            try:
                b=gmtime(float(t.date))
                epDate=strftime("%x", b)
            except:
                b=gmtime()
                epDate=strftime("%x", b)
                print "date exception"
            item2.setText(2,epDate)
            if t.status=='new':
                item2.setFont(0, self.fontBold)
         
    def update_channel_list(self):
        
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
        con.isolation_level = None
        cur = con.cursor()
        
        cur.execute('select * from sql_channel where folder_id IS NULL')
        channels = cur.fetchall()
        
        cur.execute('select * from sql_taxonomy')
        folders = cur.fetchall()
        
#        channels = Channel.query.all()
#        folders = Taxonomy.query.all()
        
        self.listWidget.clear()
        
        for folder in folders:
            itemF = QtGui.QTreeWidgetItem(self.listWidget)
            itemF.setText(0, folder[1])
            itemF.setIcon(0, QtGui.QIcon(QtGui.QPixmap(os.path.expanduser('~')+'/.brePodder/images/directory.png')))
            itemF.setFlags(enabled|droppable)      
#            childChannels = Channel.query.filter_by(folder_id=folder.id).all()
            cur.execute('select * from sql_channel where folder_id = ?',(folder[0],))
            childChannels = cur.fetchall()
            
            
            for childChannel in childChannels:
                itemChildChannel = QtGui.QTreeWidgetItem(itemF)
                itemChildChannel.setText(0, childChannel[1])
                itemChildChannel.setIcon(0, QtGui.QIcon(QtGui.QPixmap(os.path.expanduser('~')+'/.brePodder/'+childChannel[5])))
                itemF.addChild(itemChildChannel)
            
        for channel in channels:
            item = QtGui.QTreeWidgetItem(self.listWidget)
#            if channel.episode[-1].status == u'new':
#                item.setFont(0, self.fontBold)
            item.setText(0, channel[1])
            item.setIcon(0, QtGui.QIcon(QtGui.QPixmap(os.path.expanduser('~')+'/.brePodder/'+channel[5])))
#            item.setToolTip(0,"<p><img src="+"'"+channel.logobig+"'"+"></p><p style='font-size:20pt'><b>"+channel.title+"</b></p><a href="+channel.link+">"+channel.link+"</a>")
            item.setFlags(enabled|draggable|selectable)
# dodati bold za channel koji ima novu epizodu. mislim da je to najefikasnije preko novog polja u bazi. 

        cur.close()

    def updateProgressBarFromThread(self):
        ui.updateProgressBar.setValue(ui.updateProgressBar.value()+1)
        if ui.updateProgressBar.value() == ui.numberOfChannels-1:
            self.update_done()
            
    def create_new_foder(self):
        text, ok = QtGui.QInputDialog.getText(MainWindow, 'Input Dialog', 'Enter name for new folder:')
        
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
        con.isolation_level = None
        cur = con.cursor()

        if ok:
            con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
            con.isolation_level = None
            cur2 = con.cursor()
            cur2.execute('insert into sql_taxonomy(title) values (?)', (text.toUtf8().data(),))
       
        ui.update_channel_list()

        
    def update_channel(self):
        self.QLineEdit1.hide()
        self.QPushButton1.hide()
        self.updateProgressBar.setRange(0,0)
        self.updateProgressBar.show()
        self.numberOfChannels = 1

        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
        con.isolation_level = None
        cur = con.cursor()       
        cur.execute('select * from sql_channel where title = ?',(self.CurrentChannel,))
        ch = cur.fetchone()

            

#        ch=Channel.query.filter_by(title=self.CurrentChannel).one()
        
        self.ChannelForUpdate=ch
#        print ch.title
#        ui.Sem.acquire()
        updtChTr=updateChannelThread(ch,0)
        QtCore.QObject.connect(updtChTr,QtCore.SIGNAL("updatesignal"),self.update_channel_list,QtCore.Qt.QueuedConnection)
        QtCore.QObject.connect(updtChTr,QtCore.SIGNAL("updatesignal_episodelist(PyQt_PyObject)"),self.update_episode_list,QtCore.Qt.QueuedConnection)
        QtCore.QObject.connect(updtChTr,QtCore.SIGNAL("updateDoneSignal"),self.update_done, QtCore.Qt.BlockingQueuedConnection)
        self.ttthread=updtChTr
        updtChTr.start()
        

        
    def update_all_channels(self):
        self.QLineEdit1.hide()
        self.QPushButton1.hide()
        
        self.updateProgressBar.show()
        
        updtChTr=[]
#        allChannels=Channel.query.all()
        
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
        con.isolation_level = None
        cur = con.cursor()       
        cur.execute('select * from sql_channel')
        allChannels = cur.fetchall()


        self.numberOfChannels = allChannels.__len__()-1
        self.updateProgressBar.setRange(0,self.numberOfChannels+1)
        self.updateProgressBar.setValue(0)
        self.updateProgressBar.setFormat(QtCore.QString("%v" + " of " + "%m"))
        j=0
        for i in allChannels:   
            updtChTr.append(updateChannelThread(i,j))
            self.TTThread.append(updtChTr[j])
            QtCore.QObject.connect(updtChTr[j],QtCore.SIGNAL("updateProgressSignal"),self.updateProgressBarFromThread,QtCore.Qt.BlockingQueuedConnection)
            updtChTr[j].start()
            j=j+1
    
    def sendMessage(self, message):
        try:
            import pynotify
            if pynotify.init("brePodder"):
                n = pynotify.Notification("brePodder", message)
#                n = pynotify.Notification("Title", "message", "icon-name")
                n.show()
            else:
                print "there was a problem initializing the pynotify module"
        except:
            print "you don't seem to have pynotify installed"        

    def update_done(self):
            self.updateProgressBar.hide()
            self.QLineEdit1.show()
            self.QPushButton1.show()
            self.update_channel_list()
            self.sendMessage("Updating Done")
            
    def dialog_add(self):
        filename = QtGui.QFileDialog.getOpenFileName(MainWindow, 'Open file','/home')
#        file=open(filename)
#        cd = OpenFile()
#        cd.showDialog()
        print "dialog_add"
        print filename
    
    
    def export_opml(self):
        import opml
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
        con.isolation_level = None
        cur = con.cursor()       
        cur.execute('select * from sql_channel')
        channels = cur.fetchall()
        
        o=opml.Exporter('brePodder.opml')
        o.write(channels)
        
    def import_opml(self):
        import opml
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
    

class updateChannelThread(QtCore.QThread):
    def __init__(self,channel, updateProgress = 0):
        QtCore.QThread.__init__(self)
#        self.test = ui.ChannelForUpdate
        self.channel = channel
        self.updateProgress = updateProgress
        self.newEpisodeExists = 0
#        ui.freeBytes.acquire()
       
    def run(self):
#        ui.Mutex.lock()
        print ui.Sem.available() 
        ui.Sem.acquire(1)
        con = sqlite3.connect(os.path.expanduser('~')+"/.brePodder/podcasts.sqlite", check_same_thread = False)
        con.isolation_level = None
        cur = con.cursor()
        self.updateChannel(self.channel,cur)
       
        con.commit()
        cur.close()
        if self.newEpisodeExists:
            self.emit(QtCore.SIGNAL("updatesignal2"))
#        ui.Mutex.unlock()

        #TODO problem sa prolaskom preko ove linije kada koristim semafore
        self.emit(QtCore.SIGNAL("updateProgressSignal"))
        
        if self.updateProgress == 0:
            self.emit(QtCore.SIGNAL("updateDoneSignal"))
        ui.Sem.release(1)
#        if self.updateProgress == ui.numberOfChannels-1:
#            ui.updateProgressBar.hide()
#            ui.QLineEdit1.show()
#            ui.QPushButton1.show()
#            ui.update_channel_list()
#        ui.usedBytes.acquire()
#        ui.freeBytes.release()
    

    def updateChannel(self, ch = None, cursor=None):
        newEpisode={}
        cur=cursor
        oldEpisodes=[]
        if ch == None:
            cc = cur.execute('select id,title from sql_channel where title =?', (self.CurrentChannel,))
            a = cc.fetchone()
            tt = cur.execute('select id,title,status from sql_episode where channel_id = ?', (a[0]))
        else:
            cc = cur.execute('select id,title,link from sql_channel where title =?', (ch[1],))
            a = cc.fetchone()
            tt = cur.execute('select id,title,status from sql_episode where channel_id = ?', (a[0],))
        newEpisode['channel_id'] = a[0]    
#        print a[1]
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
                aa=None
            
            if i.has_key('title') and aa==None:
#                print 'epizoda NE postoji'
                self.newEpisodeExists=1
                if i.title:
                    newEpisode['title']=i.title
                else:
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
                    if i.updated_parsed:
                        epDate=mktime(i.updated_parsed)
                    else:
                        epDate=mktime(gmtime())
                else:
                    epDate=mktime(gmtime())
                newEpisode['date'] = epDate
                nEpisode=(newEpisode['title'], newEpisode['enclosure'], newEpisode['size'], newEpisode['date'], newEpisode['description'], newEpisode['status'], newEpisode['channel_id'])
                cur.execute('insert into sql_episode(title, enclosure, size, date, description, status, channel_id) values (?,?,?,?,?,?,?) ', nEpisode)
            elif not i.has_key('title'):
                print "NEMA NASLOVA EPIZODE"
            else:
                if j[2]!=u"old":
                    cur.execute('update  sql_episode set status= "old" where sql_episode.id = ?',(j[0],) )

    
if __name__ == "__main__":
    import sys
    os.chdir(os.path.expanduser('~'))
    if not os.path.isdir('.brePodder'):
        os.makedirs('.brePodder')
    os.chdir('.brePodder')
#    os.makedirs('images')
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = BrePodder()
    baza = BaseOperation()
#    print ui.memory_usage()
    ui.setupUi(MainWindow)
    MainWindow.show()
    ui.update_channel_list()
    ui.update_lastest_episodes_list()
    ui.update_newest_episodes_list()
#    print ui.memory_usage()
    sys.exitui = BrePodder()(app.exec_())
