"""
Main window UI for brePodder.

This module sets up the entire PyQt6 interface for the podcast client.
"""
from PyQt6 import QtCore, QtGui, QtWidgets, QtNetwork
import re

from services import opml
from data.database import DBOperation
from ui.widgets.tree_view import TreeViewWidget
from ui.widgets.line_edit import ClearOnFocusLineEdit
from ui.widgets.audio_player import AudioPlayer
from ui.dialogs.settings_dialog import SettingsDialog
import resources
from config import MAX_CONCURRENT_DOWNLOADS
from logger import get_logger

logger = get_logger(__name__)


class MainUi(QtWidgets.QWidget):
    """
    Main window UI class.
    
    Sets up all UI components and connects signals/slots.
    """

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self)
        self.http = []
        self.http_get_id = []
        self.out_file = []
        self.download_list = []
        self.font_bold = QtGui.QFont()
        self.font_bold.setWeight(QtGui.QFont.Weight.Bold)
        self.font_bold.setBold(True)
        self.channel_for_update = None
        self.update_channel_threads = []
        self.items_downloading = []
        self.regex_white_space = re.compile("\\W")

        self.db = DBOperation()
        self.semaphore = QtCore.QSemaphore(MAX_CONCURRENT_DOWNLOADS)
        self.app = parent

    def closeEvent(self, test):
        logger.info("Closing brePodder")
        self.app.quit()

    def setup_ui(self, main_window):
        """Set up the main window UI components."""
        self.main_window = main_window
        main_window.setObjectName("MainWindow")
        main_window.resize(QtCore.QSize(QtCore.QRect(0, 0, 600, 400).size()).expandedTo(main_window.minimumSizeHint()))
        main_window.setWindowIcon(QtGui.QIcon(":/icons/musicstore.png"))

        self.central_widget = QtWidgets.QWidget(main_window)

        self.grid_layout = QtWidgets.QGridLayout(self.central_widget)

        self.tab_widget = QtWidgets.QTabWidget(self.central_widget)

        self.tab = QtWidgets.QWidget()

        self.grid_layout_1 = QtWidgets.QGridLayout(self.tab)

        self.splitter_2 = QtWidgets.QSplitter(self.tab)
        self.splitter_2.setOrientation(QtCore.Qt.Orientation.Horizontal)

        self.splitter_22 = QtWidgets.QSplitter(self.splitter_2)
        self.splitter_22.setOrientation(QtCore.Qt.Orientation.Vertical)

        self.splitter_223 = QtWidgets.QSplitter(self.splitter_22)
        self.splitter_223.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.QLineEdit_search_podcasts = ClearOnFocusLineEdit(self.splitter_223)
        self.QLineEdit_search_podcasts.setText("Search")
        self.QLineEdit_search_podcasts.setMinimumSize(QtCore.QSize(200, 20))
        self.QLineEdit_search_podcasts.setMaximumSize(QtCore.QSize(500, 25))
        self.QLineEdit_search_podcasts.textChanged.connect(lambda x: self.update_channel_list(x))

        self.listWidget = TreeViewWidget(self.splitter_22)
        self.listWidget.updateChannelList.connect(self.update_channel_list)
        self.listWidget.updateChannelList_db.connect(self.db.addChannelToFolder)

        self.listWidget.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.listWidget.setAlternatingRowColors(True)
        self.listWidget.setDragEnabled(True)
        self.listWidget.setDragDropOverwriteMode(True)
        self.listWidget.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)

        self.splitter_222 = QtWidgets.QSplitter(self.splitter_22)
        self.splitter_222.setOrientation(QtCore.Qt.Orientation.Horizontal)

        self.line_edit_feed_url = ClearOnFocusLineEdit(self.splitter_222)

        self.update_progress_bar = QtWidgets.QProgressBar(self.splitter_222)
        self.update_progress_bar.setMaximumHeight(25)
        self.update_progress_bar.hide()

        self.button_add = QtWidgets.QPushButton(self.splitter_222)

        self.button_add.setMinimumSize(QtCore.QSize(20, 20))
        self.button_add.setMaximumSize(QtCore.QSize(50, 25))



        self.splitter_2.setSizes([100, 50])

        self.splitter = QtWidgets.QSplitter(self.splitter_2)
        self.splitter.setOrientation(QtCore.Qt.Orientation.Vertical)

        self.tree_widget_episodes = QtWidgets.QTreeWidget(self.splitter)
        self.tree_widget_episodes.setAlternatingRowColors(True)

        self.text_browser_details = QtWidgets.QTextBrowser(self.splitter)

        self.grid_layout_1.addWidget(self.splitter_2, 0, 0, 1, 1)

        self.tab_widget.addTab(self.tab, "")

        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")

        self.grid_layout_2 = QtWidgets.QGridLayout(self.tab_2)
        self.grid_layout_2.setObjectName("gridlayout2")

        self.tree_widget_downloads = QtWidgets.QTreeWidget(self.tab_2)
        self.tree_widget_downloads.setAlternatingRowColors(True)
        self.tree_widget_downloads.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_widget_downloads.setObjectName("treeWidget")
        self.grid_layout_2.addWidget(self.tree_widget_downloads, 0, 0, 1, 1)
        self.tab_widget.addTab(self.tab_2, "")

        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")

        self.tree_widget_latest_downloads = QtWidgets.QTreeWidget(self.tab_3)
        self.tree_widget_latest_downloads.setObjectName("treeWidget_4")

        self.grid_layout_3 = QtWidgets.QGridLayout(self.tab_3)
        self.grid_layout_3.setObjectName("gridlayout3")
        self.grid_layout_3.addWidget(self.tree_widget_latest_downloads, 0, 0, 1, 1)
        self.tab_widget.addTab(self.tab_3, "")
        self.grid_layout.addWidget(self.tab_widget, 0, 0, 1, 1)

        self.splitter_3 = QtWidgets.QSplitter(self.tab_3)
        self.splitter_3.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.grid_layout_3.addWidget(self.splitter_3)

        main_window.setCentralWidget(self.central_widget)

        #Tab with newest episodes
        self.tab_4 = QtWidgets.QWidget()
        self.tab_4.setObjectName("tab_4")

        self.tree_widget_newest_episodes = QtWidgets.QTreeWidget(self.tab_4)

        self.grid_layout_4 = QtWidgets.QGridLayout(self.tab_4)
        self.grid_layout_4.setObjectName("gridlayout4")
        self.grid_layout_4.addWidget(self.tree_widget_newest_episodes, 0, 0, 1, 1)
        self.tab_widget.addTab(self.tab_4, "")
        self.grid_layout.addWidget(self.tab_widget, 0, 0, 1, 1)

        self.splitter_4 = QtWidgets.QSplitter(self.tab_4)
        self.splitter_4.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.grid_layout_4.addWidget(self.splitter_4)

        # tab with playlist
        self.tab_playlist = QtWidgets.QWidget()
        self.tab_playlist.setObjectName("tab_playlist")
        self.tree_widget_playlist = QtWidgets.QTreeWidget(self.tab_playlist)
        self.grid_layout_playlist = QtWidgets.QGridLayout(self.tab_playlist)
        self.grid_layout_playlist.setObjectName("gridlayout5")
        self.grid_layout_playlist.addWidget(self.tree_widget_playlist, 0, 0, 1, 1)
        self.tab_widget.addTab(self.tab_playlist, "")
        self.grid_layout.addWidget(self.tab_widget, 0, 0, 1, 1)
        self.splitter_playlist = QtWidgets.QSplitter(self.tab_playlist)
        self.splitter_playlist.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.grid_layout_playlist.addWidget(self.splitter_playlist)

        # Clear Playlist button
        self.clear_playlist_btn = QtWidgets.QPushButton("Clear Playlist", self.splitter_playlist)
        self.clear_playlist_btn.setMaximumWidth(120)

        self.audio_player = AudioPlayer("", self.splitter_playlist)

        main_window.setCentralWidget(self.central_widget)

        self.menubar = QtWidgets.QMenuBar(main_window)
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


        self.actionNew = QtGui.QAction(main_window)
        self.actionNew.setIcon(QtGui.QIcon(":/icons/edit_add.png"))
        self.actionNew.setObjectName("actionNew")

        self.actionUpdateAllChannels = QtGui.QAction(main_window)
        self.actionUpdateAllChannels.setIcon(QtGui.QIcon(":/icons/reload.png"))
        self.actionUpdateAllChannels.setObjectName("actionUpdate")

        self.actionImport = QtGui.QAction(main_window)
        self.actionImport.setIcon(QtGui.QIcon(":/icons/fileimport.png"))
        self.actionImport.setObjectName("actionImport")

        self.actionExport = QtGui.QAction(main_window)
        self.actionExport.setIcon(QtGui.QIcon(":/icons/fileexport.png"))
        self.actionExport.setObjectName("actionExport")

        self.actionQuit = QtGui.QAction(main_window)
        self.actionQuit.setIcon(QtGui.QIcon(":/icons/exit.png"))
        self.actionQuit.setObjectName("actionQuit")

        self.actionSettings = QtGui.QAction(main_window)
        self.actionSettings.setObjectName("actionSettings")

        self.menuPodcasts.addAction(self.actionNew)
        self.menuPodcasts.addAction(self.actionUpdateAllChannels)
        self.menuPodcasts.addAction(self.actionImport)
        self.menuPodcasts.addAction(self.actionExport)
        self.menuPodcasts.addSeparator()
        self.menuPodcasts.addAction(self.actionSettings)
        self.menuPodcasts.addSeparator()
        self.menuPodcasts.addAction(self.actionQuit)

        main_window.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(main_window)
        self.statusbar.setObjectName("statusbar")
        main_window.setStatusBar(self.statusbar)

        self.toolBar = QtWidgets.QToolBar(main_window)
        self.toolBar.setBaseSize(QtCore.QSize(100,0))
        self.toolBar.setMouseTracking(True)
        self.toolBar.setObjectName("toolBar")
        main_window.addToolBar(QtCore.Qt.ToolBarArea.TopToolBarArea,self.toolBar)

        self.menubar.addAction(self.menuPodcasts.menuAction())

        self.actionUpdateFeeds = QtGui.QAction(main_window)
        self.actionUpdateFeeds.setIcon(QtGui.QIcon(":/icons/reload.png"))
        self.actionUpdateFeeds.setObjectName("actionUpdateFeeds")

        self.actionNewFolder = QtGui.QAction(main_window)
        self.actionNewFolder.setIcon(QtGui.QIcon(":/icons/reload.png"))
        self.actionNewFolder.setObjectName("actionNewFolder")

        self.actionCancel = QtGui.QAction(main_window)
        self.actionCancel.setIcon(QtGui.QIcon(":/icons/cancel.png"))
        self.actionCancel.setObjectName("actionCancel")

        self.actionPause = QtGui.QAction(main_window)
        self.actionPause.setIcon(QtGui.QIcon(":/icons/pause.png"))
        self.actionPause.setObjectName("actionPause")

        self.actionResume = QtGui.QAction(main_window)
        self.actionResume.setIcon(QtGui.QIcon(":/icons/resume.png"))
        self.actionResume.setObjectName("actionResume")


        self.actionAddToPlaylist = QtGui.QAction(main_window)
        self.actionAddToPlaylist.setIcon(QtGui.QIcon(":/icons/play.png"))
        self.actionAddToPlaylist.setObjectName("actionAddToPlaylist")

        self.actionDownloadEpisode = QtGui.QAction(main_window)
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
        self.menuEpisodeList.addSeparator()
        self.menuEpisodeList.addAction(self.actionDownloadEpisode)

        self.tray_icon = QtWidgets.QSystemTrayIcon(QtGui.QIcon(":/icons/musicstore.png"), main_window)
        self.tray_icon.setContextMenu(self.menuPodcasts)
        self.tray_icon.show()

        self.retranslate_ui(main_window)
        self.tab_widget.setCurrentIndex(0)
        self.listWidget.itemSelectionChanged.connect(self.channel_activated)
        self.button_add.clicked.connect(self.add_channel)
        self.button_add.clicked.connect(self.line_edit_feed_url.clear)

        self.tree_widget_episodes.itemSelectionChanged.connect(self.episode_activated)
        self.tree_widget_episodes.itemDoubleClicked.connect(self.episode_double_clicked)
        self.tree_widget_episodes.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)

        self.tree_widget_latest_downloads.itemDoubleClicked.connect(self.latest_episode_double_clicked)
        self.tree_widget_newest_episodes.itemDoubleClicked.connect(self.newest_episode_double_clicked)
        self.tree_widget_playlist.itemDoubleClicked.connect(self.playlist_episode_double_clicked)
        self.clear_playlist_btn.clicked.connect(self.clear_playlist)

        self.tree_widget_downloads.itemClicked.connect(self.download_activated)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.actionUpdateFeeds.triggered.connect(self.update_channel)
        self.actionNewFolder.triggered.connect(self.create_new_folder)
        self.actionQuit.triggered.connect(self.close)
        self.actionCancel.triggered.connect(self.delete_channel)
        self.actionUpdateAllChannels.triggered.connect(self.update_all_channels)
        self.actionNew.triggered.connect(self.dialog_add)
        self.actionExport.triggered.connect(self.export_opml)
        self.actionImport.triggered.connect(self.import_opml)
        self.actionSettings.triggered.connect(self.open_settings)

        self.listWidget.customContextMenuRequested.connect(self.activeMenuChannels)
        self.tree_widget_downloads.customContextMenuRequested.connect(self.activeMenuDownloads)

        self.actionAddToPlaylist.triggered.connect(self.addItemToPlaylist)
        self.actionDownloadEpisode.triggered.connect(self.episode_double_clicked)
        self.tree_widget_episodes.customContextMenuRequested.connect(self.activeMenuEpisode)

        QtCore.QMetaObject.connectSlotsByName(main_window)

        main_window.setTabOrder(self.line_edit_feed_url, self.button_add)
        main_window.setTabOrder(self.button_add, self.text_browser_details)
        main_window.setTabOrder(self.text_browser_details, self.tab_widget)

    def retranslate_ui(self, main_window):
        """Set up UI text and translations."""
        main_window.setWindowTitle(QtCore.QCoreApplication.translate("MainWindow", "brePodder", None))
        self.listWidget.setStatusTip(QtCore.QCoreApplication.translate("MainWindow", "kanali", None))
        self.listWidget.clear()

        item = QtWidgets.QTreeWidgetItem(self.listWidget)
        item.setText(0, QtCore.QCoreApplication.translate("MainWindow", "naziv podkasta", None))
        item.setIcon(0, QtGui.QIcon(":/icons/musicstore.png"))
        self.listWidget.headerItem().setText(0, QtCore.QCoreApplication.translate("MainWindow", "Channels", None))
        item1 = QtWidgets.QTreeWidgetItem(self.listWidget)
        item1.setText(0, QtCore.QCoreApplication.translate("MainWindow", "New Item", None))

        self.line_edit_feed_url.setText(QtCore.QCoreApplication.translate("MainWindow", "Copy RSS or Youtube link", None))
        self.line_edit_feed_url.selectAll()
        self.line_edit_feed_url.hasFocus()
        self.button_add.setText(QtCore.QCoreApplication.translate("MainWindow", "Add", None))

        self.tree_widget_episodes.setStatusTip(QtCore.QCoreApplication.translate("MainWindow", "epizode", None))
        self.tree_widget_episodes.headerItem().setText(0, QtCore.QCoreApplication.translate("MainWindow", "episode", None))
        self.tree_widget_episodes.headerItem().setText(1, QtCore.QCoreApplication.translate("MainWindow", "size", None))
        self.tree_widget_episodes.headerItem().setText(2, QtCore.QCoreApplication.translate("MainWindow", "date", None))
        self.tree_widget_episodes.header().resizeSection(0, 300)

        self.tree_widget_episodes.clear()

        self.text_browser_details.setHtml(QtCore.QCoreApplication.translate("MainWindow", " ", None))

        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab), QtCore.QCoreApplication.translate("MainWindow", "Channels", None))
        self.tree_widget_downloads.headerItem().setText(0,QtCore.QCoreApplication.translate("MainWindow", "Channel", None))
        self.tree_widget_downloads.headerItem().setText(1,QtCore.QCoreApplication.translate("MainWindow", "Episode", None))
        self.tree_widget_downloads.headerItem().setText(2,QtCore.QCoreApplication.translate("MainWindow", "Size", None))
        self.tree_widget_downloads.headerItem().setText(3,QtCore.QCoreApplication.translate("MainWindow", "%", None))
        self.tree_widget_downloads.headerItem().setText(4,QtCore.QCoreApplication.translate("MainWindow", "Speed", None))
        self.tree_widget_downloads.headerItem().setText(5,QtCore.QCoreApplication.translate("MainWindow", "Link", None))
        self.tree_widget_downloads.header().resizeSection(0, 200)
        self.tree_widget_downloads.header().resizeSection(1, 200)
        self.tree_widget_downloads.clear()


        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_2), QtCore.QCoreApplication.translate("MainWindow", "Downloads", None))


        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_2), QtCore.QCoreApplication.translate("MainWindow", "Downloads", None))
        self.tree_widget_latest_downloads.setToolTip(QtCore.QCoreApplication.translate("MainWindow", "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
        "p, li { white-space: pre-wrap; }\n"
        "</style></head><body style=\" font-family:\'Sans Serif\'; font-size:8pt; font-weight:400; font-style:normal;\">\n"
        "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">jn</p></body></html>", None))
        self.tree_widget_latest_downloads.headerItem().setText(0,QtCore.QCoreApplication.translate("MainWindow", "Channel", None))
        self.tree_widget_latest_downloads.headerItem().setText(1,QtCore.QCoreApplication.translate("MainWindow", "Episode", None))
        self.tree_widget_latest_downloads.headerItem().setText(2,QtCore.QCoreApplication.translate("MainWindow", "Size", None))
        self.tree_widget_latest_downloads.headerItem().setText(3,QtCore.QCoreApplication.translate("MainWindow", "Local Link", None))
        self.tree_widget_latest_downloads.header().resizeSection(0, 200)
        self.tree_widget_latest_downloads.header().resizeSection(1, 200)
        self.tree_widget_latest_downloads.clear()

        self.tree_widget_newest_episodes.headerItem().setText(0,QtCore.QCoreApplication.translate("MainWindow", "Channel", None))
        self.tree_widget_newest_episodes.headerItem().setText(1,QtCore.QCoreApplication.translate("MainWindow", "Episode", None))
        self.tree_widget_newest_episodes.headerItem().setText(2,QtCore.QCoreApplication.translate("MainWindow", "Size", None))
        self.tree_widget_newest_episodes.headerItem().setText(3,QtCore.QCoreApplication.translate("MainWindow", "Date", None))
        self.tree_widget_newest_episodes.headerItem().setText(4,QtCore.QCoreApplication.translate("MainWindow", "Enclosure", None))
        self.tree_widget_newest_episodes.header().resizeSection(0, 200)
        self.tree_widget_newest_episodes.header().resizeSection(1, 200)
        self.tree_widget_newest_episodes.clear()

        self.tree_widget_playlist.headerItem().setText(0, QtCore.QCoreApplication.translate("MainWindow", "Channel", None))
        self.tree_widget_playlist.headerItem().setText(1, QtCore.QCoreApplication.translate("MainWindow", "Episode", None))
        self.tree_widget_playlist.headerItem().setText(2, QtCore.QCoreApplication.translate("MainWindow", "Size", None))
        self.tree_widget_playlist.headerItem().setText(3, QtCore.QCoreApplication.translate("MainWindow", "Date", None))
        self.tree_widget_playlist.headerItem().setText(4, QtCore.QCoreApplication.translate("MainWindow", "Enclosure", None))
        self.tree_widget_playlist.header().resizeSection(0, 200)
        self.tree_widget_playlist.header().resizeSection(1, 200)
        self.tree_widget_playlist.clear()

        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_playlist),
                                  QtCore.QCoreApplication.translate("MainWindow", "Playlist", None))

        item6 = QtWidgets.QTreeWidgetItem(self.tree_widget_latest_downloads)
        item6.setText(0, QtCore.QCoreApplication.translate("MainWindow", "ch", None))
        item6.setText(1, QtCore.QCoreApplication.translate("MainWindow", "ep", None))
        item6.setText(2, QtCore.QCoreApplication.translate("MainWindow", "size", None))
        item6.setText(3, QtCore.QCoreApplication.translate("MainWindow", "local file", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_3), QtCore.QCoreApplication.translate("MainWindow", "Latest downloads", None))

        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_4), QtCore.QCoreApplication.translate("MainWindow", "Newest Episodes", None))

        self.menuPodcasts.setTitle(QtCore.QCoreApplication.translate("MainWindow", "Podcasts", None))
        self.toolBar.setWindowTitle(QtCore.QCoreApplication.translate("MainWindow", "toolBar", None))
        self.actionCancel.setText(QtCore.QCoreApplication.translate("MainWindow", "Delete feed", None))
        self.actionImport.setText(QtCore.QCoreApplication.translate("MainWindow", "Import", None))
        self.actionExport.setText(QtCore.QCoreApplication.translate("MainWindow", "Export", None))
        self.actionNew.setText(QtCore.QCoreApplication.translate("MainWindow", "Add New", None))
        self.actionUpdateAllChannels.setText(QtCore.QCoreApplication.translate("MainWindow", "Update All", None))
        self.actionQuit.setText(QtCore.QCoreApplication.translate("MainWindow", "Quit", None))
        self.actionSettings.setText(QtCore.QCoreApplication.translate("MainWindow", "Settings...", None))
        self.actionUpdateFeeds.setText(QtCore.QCoreApplication.translate("MainWindow", "Fetch Feed", None))
        self.actionNewFolder.setText(QtCore.QCoreApplication.translate("MainWindow", "New Folder", None))
        self.actionAddToPlaylist.setText(QtCore.QCoreApplication.translate("MainWindow", "Add to playlist", None))
        self.actionDownloadEpisode.setText(QtCore.QCoreApplication.translate("MainWindow", "Download episode", None))

    def tray_icon_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QtWidgets.QSystemTrayIcon.ActivationReason.Trigger or reason == QtWidgets.QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.main_window.isHidden():
                self.main_window.show()
            else:
                self.main_window.hide()

    def dialog_add(self):
        """Open file dialog to add a podcast."""
        filename = QtWidgets.QFileDialog.getOpenFileName(self.main_window, 'Open file', '/home')
        logger.debug("Opening file: %s", filename)

    def export_opml(self):
        """Export channels to OPML file."""
        channels = self.db.get_all_channels()
        opml_file = opml.Exporter('brePodder.opml')
        opml_file.write(channels)

    def import_opml(self):
        """Import channels from OPML file."""
        filename = QtWidgets.QFileDialog.getOpenFileName(self.main_window, 'Open OPML file for import', '/home',  "(*.opml)")
        i = opml.Importer(filename[0])
        i.get_model()
        channels = self.db.get_all_channels_links()

        for channel in i.items:
            if (channel['url'], ) not in channels:
                self.add_channel(channel['url'])

    def activeMenuChannels(self, pos):
        logger.debug("activeMenuChannels")
        globalPos = self.listWidget.mapToGlobal(pos)
        globalPos.setY(globalPos.y() + 25)
        t = self.listWidget.indexAt(pos)
        self.menuChannels.popup(globalPos)

    def activeMenuDownloads(self, pos):
        self.actionCancel.setText(QtCore.QCoreApplication.translate("MainWindow", "Cancel downlaod", None))
        globalPos = self.tree_widget_downloads.mapToGlobal(pos)
        globalPos.setY(globalPos.y() + 25)
        t = self.tree_widget_downloads.indexAt(pos)
        self.menuDownloads.popup(globalPos)

    def activeMenuEpisode(self, pos):
        if pos:
            globalPos = self.tree_widget_episodes.mapToGlobal(pos)
            globalPos.setY(globalPos.y() + 25)
            t = self.tree_widget_episodes.indexAt(pos)
            self.menuEpisodeList.popup(globalPos)
            self.episodeTitle = t.siblingAtColumn(0).data()
            self.episode_row = self.db.getEpisodeByTitle(self.episodeTitle)


    def addItemToPlaylist(self, episode_row):
        logger.debug("addItemToPlaylist: %s", episode_row)
        self.playlist.append(self.episode_row)
        self.update_playlist(self.playlist)

    def open_settings(self):
        """Open the settings dialog."""
        dialog = SettingsDialog(self.main_window)
        dialog.exec()
