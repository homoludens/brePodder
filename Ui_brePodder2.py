# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/homoludens/projekti/eric4/brePodder/brePodder2.ui'
#
# Created: Sun Aug  3 20:09:11 2008
#      by: PyQt4 UI code generator 4.3.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(QtCore.QSize(QtCore.QRect(0,0,902,554).size()).expandedTo(MainWindow.minimumSizeHint()))
        MainWindow.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        MainWindow.setAcceptDrops(True)
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

        self.layoutWidget = QtGui.QWidget(self.splitter_2)
        self.layoutWidget.setObjectName("layoutWidget")

        self.vboxlayout = QtGui.QVBoxLayout(self.layoutWidget)
        self.vboxlayout.setObjectName("vboxlayout")

        self.treeWidget_3 = QtGui.QTreeWidget(self.layoutWidget)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred,QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.treeWidget_3.sizePolicy().hasHeightForWidth())
        self.treeWidget_3.setSizePolicy(sizePolicy)
        self.treeWidget_3.setAcceptDrops(True)
        self.treeWidget_3.setLineWidth(5)
        self.treeWidget_3.setMidLineWidth(8)
        self.treeWidget_3.setDragEnabled(True)
        self.treeWidget_3.setDragDropOverwriteMode(True)
        self.treeWidget_3.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.treeWidget_3.setAlternatingRowColors(True)
        self.treeWidget_3.setIconSize(QtCore.QSize(18,-1))
        self.treeWidget_3.setIndentation(23)
        self.treeWidget_3.setRootIsDecorated(True)
        self.treeWidget_3.setUniformRowHeights(True)
        self.treeWidget_3.setSortingEnabled(True)
        self.treeWidget_3.setAnimated(True)
        self.treeWidget_3.setObjectName("treeWidget_3")
        self.vboxlayout.addWidget(self.treeWidget_3)

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setObjectName("hboxlayout")

        self.QLineEdit1 = QtGui.QLineEdit(self.layoutWidget)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.QLineEdit1.sizePolicy().hasHeightForWidth())
        self.QLineEdit1.setSizePolicy(sizePolicy)
        self.QLineEdit1.setMinimumSize(QtCore.QSize(0,0))
        self.QLineEdit1.setMaximumSize(QtCore.QSize(16777215,16777215))
        self.QLineEdit1.setObjectName("QLineEdit1")
        self.hboxlayout.addWidget(self.QLineEdit1)

        self.QPushButton1 = QtGui.QPushButton(self.layoutWidget)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum,QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.QPushButton1.sizePolicy().hasHeightForWidth())
        self.QPushButton1.setSizePolicy(sizePolicy)
        self.QPushButton1.setMinimumSize(QtCore.QSize(20,0))
        self.QPushButton1.setMaximumSize(QtCore.QSize(50,16777215))
        self.QPushButton1.setObjectName("QPushButton1")
        self.hboxlayout.addWidget(self.QPushButton1)

        spacerItem = QtGui.QSpacerItem(50,26,QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)
        self.vboxlayout.addLayout(self.hboxlayout)

        self.splitter = QtGui.QSplitter(self.splitter_2)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.splitter.sizePolicy().hasHeightForWidth())
        self.splitter.setSizePolicy(sizePolicy)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName("splitter")

        self.treeWidget_2 = QtGui.QTreeWidget(self.splitter)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.treeWidget_2.sizePolicy().hasHeightForWidth())
        self.treeWidget_2.setSizePolicy(sizePolicy)
        self.treeWidget_2.setMinimumSize(QtCore.QSize(200,0))
        self.treeWidget_2.setBaseSize(QtCore.QSize(200,0))

        font = QtGui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.treeWidget_2.setFont(font)
        self.treeWidget_2.setProperty("cursor",QtCore.QVariant(QtCore.Qt.ArrowCursor))
        self.treeWidget_2.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeWidget_2.setRootIsDecorated(True)
        self.treeWidget_2.setUniformRowHeights(True)
        self.treeWidget_2.setItemsExpandable(False)
        self.treeWidget_2.setSortingEnabled(False)
        self.treeWidget_2.setAnimated(True)
        self.treeWidget_2.setObjectName("treeWidget_2")

        self.QTextBrowser1 = QtGui.QTextBrowser(self.splitter)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.QTextBrowser1.sizePolicy().hasHeightForWidth())
        self.QTextBrowser1.setSizePolicy(sizePolicy)
        self.QTextBrowser1.setMinimumSize(QtCore.QSize(0,0))
        self.QTextBrowser1.setSizeIncrement(QtCore.QSize(4,0))
        self.QTextBrowser1.setBaseSize(QtCore.QSize(400,0))
        self.QTextBrowser1.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        self.QTextBrowser1.setOpenExternalLinks(True)
        self.QTextBrowser1.setObjectName("QTextBrowser1")
        self.gridlayout1.addWidget(self.splitter_2,0,0,1,1)
        self.tabWidget.addTab(self.tab,"")

        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName("tab_2")

        self.gridlayout2 = QtGui.QGridLayout(self.tab_2)
        self.gridlayout2.setObjectName("gridlayout2")

        self.treeWidget = QtGui.QTreeWidget(self.tab_2)
        self.treeWidget.setWindowModality(QtCore.Qt.NonModal)
        self.treeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeWidget.setItemsExpandable(False)
        self.treeWidget.setSortingEnabled(True)
        self.treeWidget.setAnimated(True)
        self.treeWidget.setObjectName("treeWidget")
        self.gridlayout2.addWidget(self.treeWidget,0,0,1,1)
        self.tabWidget.addTab(self.tab_2,"")

        self.tab_3 = QtGui.QWidget()
        self.tab_3.setObjectName("tab_3")

        self.gridlayout3 = QtGui.QGridLayout(self.tab_3)
        self.gridlayout3.setObjectName("gridlayout3")

        self.treeWidget_4 = QtGui.QTreeWidget(self.tab_3)
        self.treeWidget_4.setWindowModality(QtCore.Qt.NonModal)
        self.treeWidget_4.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeWidget_4.setItemsExpandable(False)
        self.treeWidget_4.setSortingEnabled(True)
        self.treeWidget_4.setAnimated(True)
        self.treeWidget_4.setObjectName("treeWidget_4")
        self.gridlayout3.addWidget(self.treeWidget_4,0,0,1,1)
        self.tabWidget.addTab(self.tab_3,"")
        self.gridlayout.addWidget(self.tabWidget,0,0,1,1)
        MainWindow.setCentralWidget(self.centralwidget)

        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0,0,902,28))
        self.menubar.setObjectName("menubar")

        self.menuPodcasts = QtGui.QMenu(self.menubar)
        self.menuPodcasts.setWindowModified(True)
        self.menuPodcasts.setTearOffEnabled(False)
        self.menuPodcasts.setObjectName("menuPodcasts")

        self.menuDownloads = QtGui.QMenu(self.menubar)
        self.menuDownloads.setTearOffEnabled(True)
        self.menuDownloads.setObjectName("menuDownloads")
        MainWindow.setMenuBar(self.menubar)

        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.toolBar = QtGui.QToolBar(MainWindow)
        self.toolBar.setBaseSize(QtCore.QSize(100,0))
        self.toolBar.setMouseTracking(True)
        self.toolBar.setObjectName("toolBar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea,self.toolBar)

        self.EpisodeDubleclicked = QtGui.QAction(MainWindow)
        self.EpisodeDubleclicked.setObjectName("EpisodeDubleclicked")

        self.EpisodeActivated = QtGui.QAction(MainWindow)
        self.EpisodeActivated.setObjectName("EpisodeActivated")

        self.ChannelActivated = QtGui.QAction(MainWindow)
        self.ChannelActivated.setObjectName("ChannelActivated")

        self.AddChannel = QtGui.QAction(MainWindow)
        self.AddChannel.setObjectName("AddChannel")

        self.actionCancel = QtGui.QAction(MainWindow)
        self.actionCancel.setIcon(QtGui.QIcon("images/cancel.png"))
        self.actionCancel.setObjectName("actionCancel")

        self.actionUpdateFeeds = QtGui.QAction(MainWindow)
        self.actionUpdateFeeds.setIcon(QtGui.QIcon("images/reload.png"))
        self.actionUpdateFeeds.setObjectName("actionUpdateFeeds")

        self.actionNew = QtGui.QAction(MainWindow)
        self.actionNew.setObjectName("actionNew")

        self.actionUpdate = QtGui.QAction(MainWindow)
        self.actionUpdate.setObjectName("actionUpdate")

        self.actionPause = QtGui.QAction(MainWindow)
        self.actionPause.setObjectName("actionPause")

        self.actionCancel_All = QtGui.QAction(MainWindow)
        self.actionCancel_All.setObjectName("actionCancel_All")

        self.actionPause_All = QtGui.QAction(MainWindow)
        self.actionPause_All.setObjectName("actionPause_All")

        self.actionImport = QtGui.QAction(MainWindow)
        self.actionImport.setObjectName("actionImport")

        self.actionExport = QtGui.QAction(MainWindow)
        self.actionExport.setObjectName("actionExport")

        self.actionQuit = QtGui.QAction(MainWindow)
        self.actionQuit.setIcon(QtGui.QIcon("images/exit.png"))
        self.actionQuit.setObjectName("actionQuit")
        self.menuPodcasts.addAction(self.actionNew)
        self.menuPodcasts.addAction(self.actionUpdate)
        self.menuPodcasts.addAction(self.actionImport)
        self.menuPodcasts.addAction(self.actionExport)
        self.menuPodcasts.addSeparator()
        self.menuPodcasts.addAction(self.actionQuit)
        self.menuDownloads.addAction(self.actionPause)
        self.menuDownloads.addAction(self.actionPause_All)
        self.menuDownloads.addAction(self.actionCancel)
        self.menuDownloads.addAction(self.actionCancel_All)
        self.menubar.addAction(self.menuPodcasts.menuAction())
        self.menubar.addAction(self.menuDownloads.menuAction())
        self.toolBar.addAction(self.actionUpdateFeeds)
        self.toolBar.addAction(self.actionCancel)

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QObject.connect(self.actionCancel,QtCore.SIGNAL("activated()"),self.AddChannel.trigger)
        QtCore.QObject.connect(self.actionUpdateFeeds,QtCore.SIGNAL("activated()"),self.AddChannel.trigger)
        QtCore.QObject.connect(self.actionNew,QtCore.SIGNAL("activated()"),self.AddChannel.trigger)
        QtCore.QObject.connect(self.treeWidget_2,QtCore.SIGNAL("itemDoubleClicked(QTreeWidgetItem*,int)"),self.EpisodeDubleclicked.trigger)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        MainWindow.setTabOrder(self.QLineEdit1,self.QPushButton1)
        MainWindow.setTabOrder(self.QPushButton1,self.QTextBrowser1)
        MainWindow.setTabOrder(self.QTextBrowser1,self.tabWidget)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "brePodder", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_3.headerItem().setText(0,QtGui.QApplication.translate("MainWindow", "Channels", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_3.clear()

        item = QtGui.QTreeWidgetItem(self.treeWidget_3)
        item.setText(0,QtGui.QApplication.translate("MainWindow", "New Item", None, QtGui.QApplication.UnicodeUTF8))
        item.setIcon(0,QtGui.QIcon("images/edit_add.png"))

        item1 = QtGui.QTreeWidgetItem(self.treeWidget_3)
        item1.setText(0,QtGui.QApplication.translate("MainWindow", "New Item", None, QtGui.QApplication.UnicodeUTF8))
        item1.setIcon(0,QtGui.QIcon("images/edit_add.png"))

        item2 = QtGui.QTreeWidgetItem(item1)
        item2.setText(0,QtGui.QApplication.translate("MainWindow", "New Sub Item", None, QtGui.QApplication.UnicodeUTF8))
        item2.setIcon(0,QtGui.QIcon("images/mp3.png"))

        item3 = QtGui.QTreeWidgetItem(self.treeWidget_3)
        item3.setText(0,QtGui.QApplication.translate("MainWindow", "New Item", None, QtGui.QApplication.UnicodeUTF8))
        self.QLineEdit1.setText(QtGui.QApplication.translate("MainWindow", "add episode", None, QtGui.QApplication.UnicodeUTF8))
        self.QPushButton1.setText(QtGui.QApplication.translate("MainWindow", "Add", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_2.setStatusTip(QtGui.QApplication.translate("MainWindow", "epizode", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_2.headerItem().setText(0,QtGui.QApplication.translate("MainWindow", "status", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_2.headerItem().setText(1,QtGui.QApplication.translate("MainWindow", "episode", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_2.headerItem().setText(2,QtGui.QApplication.translate("MainWindow", "size", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget_2.clear()

        item4 = QtGui.QTreeWidgetItem(self.treeWidget_2)
        item4.setText(0,"")
        item4.setIcon(0,QtGui.QIcon("images/build.png"))
        item4.setText(1,QtGui.QApplication.translate("MainWindow", "naziv", None, QtGui.QApplication.UnicodeUTF8))
        item4.setIcon(1,QtGui.QIcon("images/build.png"))
        item4.setText(2,QtGui.QApplication.translate("MainWindow", "33 MB", None, QtGui.QApplication.UnicodeUTF8))
        self.QTextBrowser1.setStatusTip(QtGui.QApplication.translate("MainWindow", "opis", None, QtGui.QApplication.UnicodeUTF8))
        self.QTextBrowser1.setHtml(QtGui.QApplication.translate("MainWindow", "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
        "p, li { white-space: pre-wrap; }\n"
        "</style></head><body style=\" font-family:\'Luxi Sans\'; font-size:8pt; font-weight:400; font-style:normal;\">\n"
        "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Sans Serif\';\">tekst u tekst browseru</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QtGui.QApplication.translate("MainWindow", "Channels", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.setToolTip(QtGui.QApplication.translate("MainWindow", "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
        "p, li { white-space: pre-wrap; }\n"
        "</style></head><body style=\" font-family:\'Sans Serif\'; font-size:8pt; font-weight:400; font-style:normal;\">\n"
        "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">jn</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(0,QtGui.QApplication.translate("MainWindow", "Channel", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(1,QtGui.QApplication.translate("MainWindow", "Episode", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(2,QtGui.QApplication.translate("MainWindow", "Size", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(3,QtGui.QApplication.translate("MainWindow", "%", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(4,QtGui.QApplication.translate("MainWindow", "Speed", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(5,QtGui.QApplication.translate("MainWindow", "Link", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.clear()

        item5 = QtGui.QTreeWidgetItem(self.treeWidget)
        item5.setText(0,QtGui.QApplication.translate("MainWindow", "dl-ch", None, QtGui.QApplication.UnicodeUTF8))
        item5.setText(1,QtGui.QApplication.translate("MainWindow", "dl-ep", None, QtGui.QApplication.UnicodeUTF8))
        item5.setText(2,QtGui.QApplication.translate("MainWindow", "dl-size", None, QtGui.QApplication.UnicodeUTF8))
        item5.setText(3,QtGui.QApplication.translate("MainWindow", "dl-proc", None, QtGui.QApplication.UnicodeUTF8))
        item5.setText(4,QtGui.QApplication.translate("MainWindow", "dl-speed", None, QtGui.QApplication.UnicodeUTF8))
        item5.setText(5,QtGui.QApplication.translate("MainWindow", "dl-link", None, QtGui.QApplication.UnicodeUTF8))
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
        self.menuPodcasts.setTitle(QtGui.QApplication.translate("MainWindow", "Podcasts", None, QtGui.QApplication.UnicodeUTF8))
        self.menuDownloads.setTitle(QtGui.QApplication.translate("MainWindow", "Downloads", None, QtGui.QApplication.UnicodeUTF8))
        self.toolBar.setWindowTitle(QtGui.QApplication.translate("MainWindow", "toolBar", None, QtGui.QApplication.UnicodeUTF8))
        self.EpisodeDubleclicked.setText(QtGui.QApplication.translate("MainWindow", "EpisodeDubleclicked", None, QtGui.QApplication.UnicodeUTF8))
        self.EpisodeActivated.setText(QtGui.QApplication.translate("MainWindow", "EpisodeActivated", None, QtGui.QApplication.UnicodeUTF8))
        self.ChannelActivated.setText(QtGui.QApplication.translate("MainWindow", "ChannelActivated", None, QtGui.QApplication.UnicodeUTF8))
        self.AddChannel.setText(QtGui.QApplication.translate("MainWindow", "AddChannel", None, QtGui.QApplication.UnicodeUTF8))
        self.actionCancel.setText(QtGui.QApplication.translate("MainWindow", "Cancel", None, QtGui.QApplication.UnicodeUTF8))
        self.actionUpdateFeeds.setText(QtGui.QApplication.translate("MainWindow", "UpdateFeeds", None, QtGui.QApplication.UnicodeUTF8))
        self.actionNew.setText(QtGui.QApplication.translate("MainWindow", "Add New", None, QtGui.QApplication.UnicodeUTF8))
        self.actionUpdate.setText(QtGui.QApplication.translate("MainWindow", "Update", None, QtGui.QApplication.UnicodeUTF8))
        self.actionPause.setText(QtGui.QApplication.translate("MainWindow", "Pause", None, QtGui.QApplication.UnicodeUTF8))
        self.actionCancel_All.setText(QtGui.QApplication.translate("MainWindow", "Cancel All", None, QtGui.QApplication.UnicodeUTF8))
        self.actionPause_All.setText(QtGui.QApplication.translate("MainWindow", "Pause All", None, QtGui.QApplication.UnicodeUTF8))
        self.actionImport.setText(QtGui.QApplication.translate("MainWindow", "Import", None, QtGui.QApplication.UnicodeUTF8))
        self.actionExport.setText(QtGui.QApplication.translate("MainWindow", "Export", None, QtGui.QApplication.UnicodeUTF8))
        self.actionQuit.setText(QtGui.QApplication.translate("MainWindow", "Quit", None, QtGui.QApplication.UnicodeUTF8))



if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
