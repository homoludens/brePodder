from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork #, QtWebKit
import re
from utils import opml
from utils.sql import *
from ui.treeviewwidget import TreeViewWidget
from ui.mylineeditwidget import MyLineEdit
import resources
from utils.audioplayer import AudioPlayer


class MainUi(QtWidgets.QWidget):

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self)
        self.http = []
        self.httpGetId = []
        self.outFile = []
        self.downloadList = []
        self.rawstr = r"""(?:\<img.*?\src=")(.*?)(?:\")"""  #it's better with "\src" (not "\c") but that doesn't work
        self.compile_obj = re.compile(self.rawstr, re.I)
        self.fontBold = QtGui.QFont()
        self.fontBold.setWeight(75)
        self.fontBold.setBold(True)
        self.ChannelForUpdate = None
        self.update_channel_threads = []
#        self.BufferSize = 5
#        self.Mutex = QtCore.QMutex()
        self.itemsDownloading = []
        self.regex_white_space = re.compile("\\W")

        self.db = DBOperation()
        self.Sem = QtCore.QSemaphore(1)
        self.app = parent

    def closeEvent(self, test):
        print('closeevent', test)
        print("closing brePodder")
        self.app.quit()

    def setupUi(self, MainWindow):
        self.MW = MainWindow
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(QtCore.QSize(QtCore.QRect(0, 0, 600, 400).size()).expandedTo(MainWindow.minimumSizeHint()))
        MainWindow.setWindowIcon(QtGui.QIcon(":/icons/musicstore.png"))

        self.centralwidget = QtWidgets.QWidget(MainWindow)

        self.gridlayout = QtWidgets.QGridLayout(self.centralwidget)

        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)

        self.tab = QtWidgets.QWidget()

        self.gridlayout1 = QtWidgets.QGridLayout(self.tab)

        self.splitter_2 = QtWidgets.QSplitter(self.tab)
        self.splitter_2.setOrientation(QtCore.Qt.Horizontal)

        self.splitter_22 = QtWidgets.QSplitter(self.splitter_2)
        self.splitter_22.setOrientation(QtCore.Qt.Vertical)

        self.splitter_223 = QtWidgets.QSplitter(self.splitter_22)
        self.splitter_223.setOrientation(QtCore.Qt.Horizontal)
        self.QLineEdit_search_podcasts = MyLineEdit(self.splitter_223)
        self.QLineEdit_search_podcasts.setText("Search")
        self.QLineEdit_search_podcasts.setMinimumSize(QtCore.QSize(200, 20))
        self.QLineEdit_search_podcasts.setMaximumSize(QtCore.QSize(500, 25))
        self.QLineEdit_search_podcasts.textChanged.connect(lambda x: self.update_channel_list(x))

        self.listWidget = TreeViewWidget(self.splitter_22)
        self.listWidget.updateChannelList.connect(self.update_channel_list)
        self.listWidget.updateChannelList_db.connect(self.db.addChannelToFolder)

        self.listWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.listWidget.setAlternatingRowColors(True)
        self.listWidget.setDragEnabled(True)
        self.listWidget.setDragDropOverwriteMode(True)
        self.listWidget.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)

        self.splitter_222 = QtWidgets.QSplitter(self.splitter_22)
        self.splitter_222.setOrientation(QtCore.Qt.Horizontal)

        # self.QLineEdit1 = QtWidgets.QLineEdit(self.splitter_222)
        self.QLineEdit1 = MyLineEdit(self.splitter_222)


        self.updateProgressBar = QtWidgets.QProgressBar(self.splitter_222)
        self.updateProgressBar.setMaximumHeight(25)
        self.updateProgressBar.hide()
        #self.splitter_222.addWidget( self.updateProgressBar )

        self.QPushButton1 = QtWidgets.QPushButton(self.splitter_222)

        self.QPushButton1.setMinimumSize(QtCore.QSize(20, 20))
        self.QPushButton1.setMaximumSize(QtCore.QSize(50, 25))



        self.splitter_2.setSizes((100, 50))

        self.splitter = QtWidgets.QSplitter(self.splitter_2)
        self.splitter.setOrientation(QtCore.Qt.Vertical)

        self.treeWidget_2 = QtWidgets.QTreeWidget(self.splitter)
        self.treeWidget_2.setAlternatingRowColors(True)

        #TODO: make settings fot choosing WebKit insted of QTextBrowser
        #self.QTextBrowser1 = QtWebKit.QWebView(self.splitter) #Qt4.4
        self.QTextBrowser1 = QtWidgets.QTextBrowser(self.splitter)  # Qt4.3
#        self.QTextBrowser1.setOpenExternalLinks(1)
#        self.QTextBrowser1.setOpenLinks(1)

        self.gridlayout1.addWidget(self.splitter_2, 0, 0, 1, 1)

        self.tabWidget.addTab(self.tab, "")

        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")

        self.gridlayout2 = QtWidgets.QGridLayout(self.tab_2)
        self.gridlayout2.setObjectName("gridlayout2")

        self.treeWidget = QtWidgets.QTreeWidget(self.tab_2)
        self.treeWidget.setAlternatingRowColors(True)
        self.treeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeWidget.setObjectName("treeWidget")
        self.gridlayout2.addWidget(self.treeWidget, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab_2, "")

        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")

        self.treeWidget_4 = QtWidgets.QTreeWidget(self.tab_3)
        self.treeWidget_4.setObjectName("treeWidget_4")

        self.gridlayout3 = QtWidgets.QGridLayout(self.tab_3)
        self.gridlayout3.setObjectName("gridlayout3")
        self.gridlayout3.addWidget(self.treeWidget_4, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab_3, "")
        self.gridlayout.addWidget(self.tabWidget, 0, 0, 1, 1)

        self.splitter_3 = QtWidgets.QSplitter(self.tab_3)
        self.splitter_3.setOrientation(QtCore.Qt.Horizontal)
        self.gridlayout3.addWidget(self.splitter_3)

        # self.AudioPlayer_latestDownloads = AudioPlayer("", self.splitter_3)

        MainWindow.setCentralWidget(self.centralwidget)

        #Tab with newest episodes
        self.tab_4 = QtWidgets.QWidget()
        self.tab_4.setObjectName("tab_4")

        self.treeWidget_5 = QtWidgets.QTreeWidget(self.tab_4)

        self.gridlayout4 = QtWidgets.QGridLayout(self.tab_4)
        self.gridlayout4.setObjectName("gridlayout4")
        self.gridlayout4.addWidget(self.treeWidget_5, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab_4, "")
        self.gridlayout.addWidget(self.tabWidget, 0, 0, 1, 1)

        self.splitter_4 = QtWidgets.QSplitter(self.tab_4)
        self.splitter_4.setOrientation(QtCore.Qt.Horizontal)
        self.gridlayout4.addWidget(self.splitter_4)

        # tab with playlist
        self.tab_playlist = QtWidgets.QWidget()
        self.tab_playlist.setObjectName("tab_playlist")
        self.treewidget_playlist = QtWidgets.QTreeWidget(self.tab_playlist)
        self.gridlayout_playlist = QtWidgets.QGridLayout(self.tab_playlist)
        self.gridlayout_playlist.setObjectName("gridlayout5")
        self.gridlayout_playlist.addWidget(self.treewidget_playlist, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab_playlist, "")
        self.gridlayout.addWidget(self.tabWidget, 0, 0, 1, 1)
        self.splitter_playlist = QtWidgets.QSplitter(self.tab_playlist)
        self.splitter_playlist.setOrientation(QtCore.Qt.Horizontal)
        self.gridlayout_playlist.addWidget(self.splitter_playlist)

        self.AudioPlayer = AudioPlayer("", self.splitter_playlist)

        MainWindow.setCentralWidget(self.centralwidget)

        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 604, 28))
        self.menubar.setObjectName("menubar")

        self.menuPodcasts = QtWidgets.QMenu(self.menubar)
        self.menuPodcasts.setObjectName("menuPodcasts")

        self.menuChannels = QtWidgets.QMenu(self.menubar)
        self.menuChannels.setObjectName("menuChannels")

        self.menuDownloads = QtWidgets.QMenu(self.menubar)
        self.menuDownloads.setObjectName("menuDownloads")

        self.menuEpisodeList = QtWidgets.QMenu(self.menubar)
        self.menuEpisodeList.setObjectName("menuEpisodeList")
        self.menuEpisodeList.addSeparator()

        self.actionNew = QtWidgets.QAction(MainWindow)
        self.actionNew.setIcon(QtGui.QIcon(":/icons/edit_add.png"))
        self.actionNew.setObjectName("actionNew")

        self.actionUpdateAllChannels = QtWidgets.QAction(MainWindow)
        self.actionUpdateAllChannels.setIcon(QtGui.QIcon(":/icons/reload.png"))
        #self.actionUpdateAllChannels.setIcon(QtGui.QIcon.fromTheme("call-start"))
        self.actionUpdateAllChannels.setObjectName("actionUpdate")

        self.actionImport = QtWidgets.QAction(MainWindow)
        self.actionImport.setIcon(QtGui.QIcon(":/icons/fileimport.png"))
        self.actionImport.setObjectName("actionImport")

        self.actionExport = QtWidgets.QAction(MainWindow)
        self.actionExport.setIcon(QtGui.QIcon(":/icons/fileexport.png"))
        self.actionExport.setObjectName("actionExport")

        self.actionQuit = QtWidgets.QAction(MainWindow)
        self.actionQuit.setIcon(QtGui.QIcon(":/icons/exit.png"))
        self.actionQuit.setObjectName("actionQuit")

        self.menuPodcasts.addAction(self.actionNew)
        self.menuPodcasts.addAction(self.actionUpdateAllChannels)
        self.menuPodcasts.addAction(self.actionImport)
        self.menuPodcasts.addAction(self.actionExport)
        self.menuPodcasts.addSeparator()
        self.menuPodcasts.addAction(self.actionQuit)

        MainWindow.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.toolBar = QtWidgets.QToolBar(MainWindow)
        self.toolBar.setBaseSize(QtCore.QSize(100,0))
        self.toolBar.setMouseTracking(True)
        self.toolBar.setObjectName("toolBar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea,self.toolBar)

        self.menubar.addAction(self.menuPodcasts.menuAction())

        self.actionUpdateFeeds = QtWidgets.QAction(MainWindow)
        self.actionUpdateFeeds.setIcon(QtGui.QIcon(":/icons/reload.png"))
        #self.actionUpdateFeeds.setIcon(QtGui.QIcon.fromTheme("call-start"))
        self.actionUpdateFeeds.setObjectName("actionUpdateFeeds")

        self.actionNewFolder = QtWidgets.QAction(MainWindow)
        self.actionNewFolder.setIcon(QtGui.QIcon(":/icons/reload.png"))
        self.actionNewFolder.setObjectName("actionNewFolder")

        self.actionCancel = QtWidgets.QAction(MainWindow)
        self.actionCancel.setIcon(QtGui.QIcon(":/icons/cancel.png"))
        self.actionCancel.setObjectName("actionCancel")

        self.actionPause = QtWidgets.QAction(MainWindow)
        self.actionPause.setIcon(QtGui.QIcon(":/icons/pause.png"))
        self.actionPause.setObjectName("actionPause")

        self.actionResume = QtWidgets.QAction(MainWindow)
        self.actionResume.setIcon(QtGui.QIcon(":/icons/resume.png"))
        self.actionResume.setObjectName("actionResume")


        self.actionAddToPlaylist = QtWidgets.QAction(MainWindow)
        self.actionAddToPlaylist.setIcon(QtGui.QIcon(":/icons/play.png"))
        self.actionAddToPlaylist.setObjectName("actionAddToPlaylist")

        self.actionDownloadEpisode = QtWidgets.QAction(MainWindow)
        self.actionDownloadEpisode.setObjectName("actionDownloadEpisode")

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

        self.menuEpisodeList.addAction(self.actionAddToPlaylist)
        self.menuEpisodeList.addAction(self.actionDownloadEpisode)

        self.trayIcon = QtWidgets.QSystemTrayIcon(QtGui.QIcon(":/icons/musicstore.png"), MainWindow)
        self.trayIcon.setContextMenu(self.menuPodcasts)
        self.trayIcon.show()

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        self.listWidget.itemSelectionChanged.connect(self.channel_activated)
        # self.QPushButton1.clicked.connect(self.AddChannel)
        self.QPushButton1.clicked.connect(self.add_channel)
        self.QPushButton1.clicked.connect(self.QLineEdit1.clear)

        self.treeWidget_2.itemSelectionChanged.connect(self.episode_activated)
        self.treeWidget_2.itemDoubleClicked.connect(self.EpisodeDoubleClicked)
        self.treeWidget_2.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.treeWidget_4.itemDoubleClicked.connect(self.LastestEpisodeDoubleClicked)
        self.treeWidget_5.itemDoubleClicked.connect(self.NewestEpisodeDoubleClicked)
        self.treewidget_playlist.itemDoubleClicked.connect(self.PlaylistEpisodeDoubleClicked)
        self.treeWidget_5.itemClicked.connect(self.NewestEpisodeClicked)
        self.treeWidget.itemClicked.connect(self.DownloadActivated)
        self.trayIcon.activated.connect(self.trayIconActivated)
        self.actionUpdateFeeds.triggered.connect(self.update_channel)
        self.actionNewFolder.triggered.connect(self.create_new_foder)
        # self.actionQuit.triggered.connect(self.app_quit)
        self.actionQuit.triggered.connect(self.close)
        self.actionCancel.triggered.connect(self.delete_channel)
        self.actionUpdateAllChannels.triggered.connect(self.update_all_channels)
        self.actionNew.triggered.connect(self.dialog_add)
        self.actionExport.triggered.connect(self.export_opml)
        self.actionImport.triggered.connect(self.import_opml)

        self.listWidget.customContextMenuRequested.connect(self.activeMenuChannels)
        self.treeWidget.customContextMenuRequested.connect(self.activeMenuDownloads)

        self.actionAddToPlaylist.triggered.connect(self.addItemToPlaylist)
        self.actionDownloadEpisode.triggered.connect(self.EpisodeDoubleClicked)
        self.treeWidget_2.customContextMenuRequested.connect(self.addToPlaylist)

        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        MainWindow.setTabOrder(self.QLineEdit1, self.QPushButton1)
        MainWindow.setTabOrder(self.QPushButton1, self.QTextBrowser1)
        MainWindow.setTabOrder(self.QTextBrowser1, self.tabWidget)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtWidgets.QApplication.translate("MainWindow", "brePodder", None))
        self.listWidget.setStatusTip(QtWidgets.QApplication.translate("MainWindow", "kanali", None))
        self.listWidget.clear()

        item = QtWidgets.QTreeWidgetItem(self.listWidget)
        item.setText(0, QtWidgets.QApplication.translate("MainWindow", "naziv podkasta", None))
        item.setIcon(0, QtGui.QIcon(":/icons/musicstore.png"))
        self.listWidget.headerItem().setText(0, QtWidgets.QApplication.translate("MainWindow", "Channels", None))
        item1 = QtWidgets.QTreeWidgetItem(self.listWidget)
        item1.setText(0, QtWidgets.QApplication.translate("MainWindow", "New Item", None))

        self.QLineEdit1.setText(QtWidgets.QApplication.translate("MainWindow", "Copy RSS or Youtube link", None))
        self.QLineEdit1.selectAll()
        self.QLineEdit1.hasFocus()
        self.QPushButton1.setText(QtWidgets.QApplication.translate("MainWindow", "Add", None))

        self.treeWidget_2.setStatusTip(QtWidgets.QApplication.translate("MainWindow", "epizode", None))
        self.treeWidget_2.headerItem().setText(0, QtWidgets.QApplication.translate("MainWindow", "episode", None))
        self.treeWidget_2.headerItem().setText(1, QtWidgets.QApplication.translate("MainWindow", "size", None))
        self.treeWidget_2.headerItem().setText(2, QtWidgets.QApplication.translate("MainWindow", "date", None))
        self.treeWidget_2.header().resizeSection(0, 300)

        self.treeWidget_2.clear()

        self.QTextBrowser1.setHtml(QtWidgets.QApplication.translate("MainWindow", " ", None))

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QtWidgets.QApplication.translate("MainWindow", "Channels", None))
        self.treeWidget.headerItem().setText(0,QtWidgets.QApplication.translate("MainWindow", "Channel", None))
        self.treeWidget.headerItem().setText(1,QtWidgets.QApplication.translate("MainWindow", "Episode", None))
        self.treeWidget.headerItem().setText(2,QtWidgets.QApplication.translate("MainWindow", "Size", None))
        self.treeWidget.headerItem().setText(3,QtWidgets.QApplication.translate("MainWindow", "%", None))
        self.treeWidget.headerItem().setText(4,QtWidgets.QApplication.translate("MainWindow", "Speed", None))
        self.treeWidget.headerItem().setText(5,QtWidgets.QApplication.translate("MainWindow", "Link", None))
        self.treeWidget.header().resizeSection(0, 200)
        self.treeWidget.header().resizeSection(1, 200)
        self.treeWidget.clear()


        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QtWidgets.QApplication.translate("MainWindow", "Downloads", None))


        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QtWidgets.QApplication.translate("MainWindow", "Downloads", None))
        self.treeWidget_4.setToolTip(QtWidgets.QApplication.translate("MainWindow", "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
        "p, li { white-space: pre-wrap; }\n"
        "</style></head><body style=\" font-family:\'Sans Serif\'; font-size:8pt; font-weight:400; font-style:normal;\">\n"
        "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">jn</p></body></html>", None))
        self.treeWidget_4.headerItem().setText(0,QtWidgets.QApplication.translate("MainWindow", "Channel", None))
        self.treeWidget_4.headerItem().setText(1,QtWidgets.QApplication.translate("MainWindow", "Episode", None))
        self.treeWidget_4.headerItem().setText(2,QtWidgets.QApplication.translate("MainWindow", "Size", None))
        self.treeWidget_4.headerItem().setText(3,QtWidgets.QApplication.translate("MainWindow", "Local Link", None))
        self.treeWidget_4.header().resizeSection(0, 200)
        self.treeWidget_4.header().resizeSection(1, 200)
        self.treeWidget_4.clear()

        self.treeWidget_5.headerItem().setText(0,QtWidgets.QApplication.translate("MainWindow", "Channel", None))
        self.treeWidget_5.headerItem().setText(1,QtWidgets.QApplication.translate("MainWindow", "Episode", None))
        self.treeWidget_5.headerItem().setText(2,QtWidgets.QApplication.translate("MainWindow", "Size", None))
        self.treeWidget_5.headerItem().setText(3,QtWidgets.QApplication.translate("MainWindow", "Date", None))
        self.treeWidget_5.headerItem().setText(4,QtWidgets.QApplication.translate("MainWindow", "Enclosure", None))
        self.treeWidget_5.header().resizeSection(0, 200)
        self.treeWidget_5.header().resizeSection(1, 200)
        self.treeWidget_5.clear()

        self.treewidget_playlist.headerItem().setText(0, QtWidgets.QApplication.translate("MainWindow", "Channel", None))
        self.treewidget_playlist.headerItem().setText(1, QtWidgets.QApplication.translate("MainWindow", "Episode", None))
        self.treewidget_playlist.headerItem().setText(2, QtWidgets.QApplication.translate("MainWindow", "Size", None))
        self.treewidget_playlist.headerItem().setText(3, QtWidgets.QApplication.translate("MainWindow", "Date", None))
        self.treewidget_playlist.headerItem().setText(4, QtWidgets.QApplication.translate("MainWindow", "Enclosure", None))
        self.treewidget_playlist.header().resizeSection(0, 200)
        self.treewidget_playlist.header().resizeSection(1, 200)
        self.treewidget_playlist.clear()

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_playlist),
                                  QtWidgets.QApplication.translate("MainWindow", "Playlist", None))

        item6 = QtWidgets.QTreeWidgetItem(self.treeWidget_4)
        item6.setText(0, QtWidgets.QApplication.translate("MainWindow", "ch", None))
        item6.setText(1, QtWidgets.QApplication.translate("MainWindow", "ep", None))
        item6.setText(2, QtWidgets.QApplication.translate("MainWindow", "size", None))
        item6.setText(3, QtWidgets.QApplication.translate("MainWindow", "local file", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QtWidgets.QApplication.translate("MainWindow", "Lastest downloads", None))

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QtWidgets.QApplication.translate("MainWindow", "Newest Episodes", None))

        self.menuPodcasts.setTitle(QtWidgets.QApplication.translate("MainWindow", "Podcasts", None))
        self.toolBar.setWindowTitle(QtWidgets.QApplication.translate("MainWindow", "toolBar", None))
        self.actionCancel.setText(QtWidgets.QApplication.translate("MainWindow", "Delete feed", None))
        self.actionImport.setText(QtWidgets.QApplication.translate("MainWindow", "Import", None))
        self.actionExport.setText(QtWidgets.QApplication.translate("MainWindow", "Export", None))
        self.actionNew.setText(QtWidgets.QApplication.translate("MainWindow", "Add New", None))
        self.actionUpdateAllChannels.setText(QtWidgets.QApplication.translate("MainWindow", "Update All", None))
        self.actionQuit.setText(QtWidgets.QApplication.translate("MainWindow", "Quit", None))
        self.actionUpdateFeeds.setText(QtWidgets.QApplication.translate("MainWindow", "Fetch Feed", None))
        self.actionNewFolder.setText(QtWidgets.QApplication.translate("MainWindow", "New Folder", None))
        self.actionAddToPlaylist.setText(QtWidgets.QApplication.translate("MainWindow", "Add to playlist", None))
        self.actionDownloadEpisode.setText(QtWidgets.QApplication.translate("MainWindow", "Download episode", None))

    def trayIconActivated(self, reason):
        if reason == 3 or reason == 2:
            if self.MW.isHidden():
                self.MW.show()
            else:
                self.MW.hide()

    def dialog_add(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self.MW, 'Open file', '/home')
#        file=open(filename)
#        cd = OpenFile()
#        cd.showDialog()
#         print("dialog_add")
        print(filename)

    def export_opml(self):
        channels = self.db.getAllChannels()
        opml_file = opml.Exporter('brePodder.opml')
        opml_file.write(channels)

    def import_opml(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self.MW, 'Open OPML file for import', '/home',  "(*.opml)")
#        i = opml.Importer('brePodderImport.opml')
        i = opml.Importer(filename[0])
        i.get_model()
        channels = self.db.getAllChannelsLinks()
        #print channels

        for channel in i.items:
            if (channel['url'], ) not in channels:
                #print ch['url']
                # self.AddChannel(channel['url'])
                self.add_channel(channel['url'])

    def activeMenuChannels(self, pos):
        print("activeMenuChannels")
        # self.actionCancel.setText(QtWidgets.QApplication.translate("MainWindow", "Delete feed", None))
        globalPos = self.listWidget.mapToGlobal(pos)
        globalPos.setY(globalPos.y() + 25)
        t = self.listWidget.indexAt(pos)
        self.menuChannels.popup(globalPos)

    def activeMenuDownloads(self, pos):
        self.actionCancel.setText(QtWidgets.QApplication.translate("MainWindow", "Cancel downlaod", None))
        globalPos = self.treeWidget.mapToGlobal(pos)
        globalPos.setY(globalPos.y() + 25)
        t = self.treeWidget.indexAt(pos)
        self.menuDownloads.popup(globalPos)

    def downloadEpisode(self, pos):
        self.actionCancel.setText(QtWidgets.QApplication.translate("MainWindow", "Download", None))
        globalPos = self.treeWidget_2.mapToGlobal(pos)
        globalPos.setY(globalPos.y() + 25)
        t = self.treeWidget_2.indexAt(pos)
        self.menuDownloads.popup(globalPos)

    def addToPlaylist(self, pos):
        # self.actionAddToPlaylist.setText(QtWidgets.QApplication.translate("MainWindow", "Add to playlist", None))
        if pos:
            globalPos = self.treeWidget_2.mapToGlobal(pos)
            globalPos.setY(globalPos.y() + 25)
            t = self.treeWidget_2.indexAt(pos)
            self.menuEpisodeList.popup(globalPos)
            self.episodeTitle = t.siblingAtColumn(0).data()
            self.episode_row = self.db.getEpisodeByTitle(self.episodeTitle)


    def addItemToPlaylist(self, episode_row):
        print(f"addItemToPlaylist {episode_row}")
        self.playlist.append(self.episode_row)
        self.update_play_list(self.playlist)


    # def activeListEpisode(self, pos):
    #     self.actionCancel.setText(QtWidgets.QApplication.translate("MainWindow", "Cancel downlaod", None))
    #     globalPos = self.treeWidget.mapToGlobal(pos)
    #     globalPos.setY(globalPos.y() + 25)
    #     t = self.treeWidget.indexAt(pos)
    #     self.menuDownloads.popup(globalPos)

    # def app_quit(self):
    #     self.db.db.commit()
    #     self.close()
    #     # self.parent.exit()
    #     # self,c
    #     # app.exit()

