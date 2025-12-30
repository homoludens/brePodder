"""
brePodder - Main application module.

This module contains the BrePodder class which is the main application
window and handles user interactions.
"""
from PyQt5 import QtCore, QtWidgets, QtGui
from time import gmtime, strftime
import os
import sqlite3
from typing import Any, Optional, Union

from ui.main_window import MainUi
from workers.download_worker import Download
from workers.update_worker import UpdateChannelThread, UpdateChannelThread_network
from workers.add_worker import AddChannelThread
from services.feed_parser import parse_episode_for_update, episode_dict_to_tuple
from config import DATA_DIR, DATABASE_FILE, USER_AGENT, THUMBNAIL_MAX_SIZE
from config_players import PLAYERS, get_play_command
from logger import get_logger

logger = get_logger(__name__)

# Qt item flags for tree widget items
draggable: QtCore.Qt.ItemFlag = QtCore.Qt.ItemIsDragEnabled
droppable: QtCore.Qt.ItemFlag = QtCore.Qt.ItemIsDropEnabled
enabled: QtCore.Qt.ItemFlag = QtCore.Qt.ItemIsEnabled
selectable: QtCore.Qt.ItemFlag = QtCore.Qt.ItemIsSelectable


class BrePodder(MainUi):
    """
    Main application class for brePodder podcast client.
    
    Inherits from MainUi which provides the UI setup.
    This class handles all user interactions and application logic.
    """

    def __init__(self, app: QtWidgets.QApplication) -> None:
        MainUi.__init__(self, app)
        self.headers: dict[str, str] = {
            'User-Agent': USER_AGENT
        }
        self.app: QtWidgets.QApplication = app
        mainwindow = QtWidgets.QMainWindow()
        self.setupUi(mainwindow)
        mainwindow.show()
        self.update_channel_list()
        self.update_lastest_episodes_list()
        self.update_newest_episodes_list()
        self.playlist: list[Any] = []
        self.updated_channes_list: list[Any] = []
        self.main_directory: str = str(DATA_DIR) + '/'

    def resize_image(self, source_image: str, destination_image: str) -> None:
        """Resize an image to thumbnail size if it's too large."""
        pixmap = QtGui.QPixmap(source_image)
        if pixmap.height() > THUMBNAIL_MAX_SIZE or pixmap.width() > THUMBNAIL_MAX_SIZE:
            pixmap_resized = pixmap.scaled(THUMBNAIL_MAX_SIZE, THUMBNAIL_MAX_SIZE, QtCore.Qt.KeepAspectRatio)
            if not os.path.exists(os.path.dirname(destination_image)):
                os.makedirs(os.path.dirname(destination_image))
            pixmap_resized.save(destination_image)

    def episode_activated(self) -> None:
        """Handle episode selection - display episode details."""
        if self.treeWidget_2.selectedItems():
            selection = self.treeWidget_2.selectedItems()[0]
            try:
                e = self.db.getEpisodeByTitle(selection.text(0))

                enc = e["enclosure"] if e["enclosure"] else 'None'
                desc = e["description"] if e["description"] else 'None'
                local_file = e["localfile"] if e["localfile"] else 'None'

                self.QTextBrowser1.setHtml(
                    "<p>" + desc + "</br>\n\r</p>"
                    "<p><b>FILE: </b><a href=" + enc + ">" + enc + "</a></p>"
                    "<p><b>LOCALFILE: </b><a href=" + local_file + ">" + local_file + "</a></p>"
                    "<p>PLAY:<audio controls='controls' src='" + enc + "'/></p>"
                )

            except (TypeError, KeyError) as e:
                logger.warning("EpisodeActivated exception: %s", e)

    def DownloadActivated(self, item: QtWidgets.QTreeWidgetItem, i: int) -> None:
        """Handle download item selection."""
        self.itemZaPrekid = item
        self.actionCancel.setToolTip("Remove Selected Download")
        self.actionPause.setToolTip("Pause Selected Download")
        self.actionResume.setToolTip("Resume Selected Download")

    def EpisodeDoubleClicked(self, episode_row: Optional[QtWidgets.QTreeWidgetItem]) -> None:
        """Handle double-click on episode - start download."""
        if episode_row:
            episode_row.setFont(0, self.fontBold)
            episodeTitle = episode_row.text(0)
            e = self.db.getEpisodeByTitle(episodeTitle)
        else:
            e = self.episode_row

        self.playlist.append(e)

        channel = self.db.getChannelById(e["channel_id"])
        ChannelDir = self.regex_white_space.sub("", channel["title"])

        os.chdir(str(DATA_DIR / ChannelDir))
        item = QtWidgets.QTreeWidgetItem(self.treeWidget)
        item.setText(0, channel.get("title"))
        item.setText(1, e["title"])
        item.setText(2, self.getReadableSize(e["size"]))
        item.setText(3, '0')
        item.setText(4, '0')

        try:
            item.setText(5, e["enclosure"])
        except TypeError:
            logger.warning("No enclosure link for episode")
            item.setText(5, "No link")

        if len(self.downloadList) > 0:
            downloadId = self.downloadList[-1][0] + 1
        else:
            downloadId = 0

        self.itemsDownloading.append((downloadId, e["enclosure"].replace(" ", "%20")))
        download = Download(e["enclosure"].replace(" ", "%20"), item, downloadId, self)
        download.download_finished.connect(lambda fileName, savePath, dlId: self.on_download_finished(fileName, savePath, dlId, e["title"]))
        self.downloadList.append((downloadId, download))

        os.chdir(str(DATA_DIR))

    def on_download_finished(self, file_name: str, save_path: str, download_id: int, episode_title: str) -> None:
        """Handle download completion - update database and refresh UI."""
        logger.debug("Download completed for episode: %s", episode_title)
        
        # Get the episode from database
        episode = self.db.getEpisodeByTitle(episode_title)
        
        if episode:
            # Update the episode with local file path and downloaded status
            self.db.updateEpisode((save_path, "downloaded", episode["id"]))
            logger.info("Updated episode '%s' with local file: %s", episode_title, save_path)
            
            # Refresh the latest downloads list
            self.update_lastest_episodes_list()
        else:
            logger.warning("Could not find episode '%s' in database to update", episode_title)

    def add_channel(self, new_url: Optional[str] = None) -> None:
        """Add a new channel/podcast subscription."""
        os.chdir(str(DATA_DIR))
        if not new_url:
            feed_link = self.QLineEdit1.text()
        else:
            feed_link = new_url

        self.QLineEdit1.hide()
        self.QPushButton1.hide()
        self.updateProgressBar.setRange(0, 0)
        self.updateProgressBar.show()
        self.numberOfChannels = 1

        addChTr = AddChannelThread(feed_link, self, 0)
        addChTr.addsignal.connect(self.update_channel_list, QtCore.Qt.QueuedConnection)
        addChTr.addsignal_episodelist.connect(self.update_episode_list, QtCore.Qt.QueuedConnection)
        addChTr.addDoneSignal.connect(self.adding_channal_done, QtCore.Qt.BlockingQueuedConnection)
        self.update_channel_threads.append(addChTr)
        addChTr.start()

    def adding_channal_done(self) -> None:
        """Handle completion of channel addition."""
        self.updateProgressBar.hide()
        self.QLineEdit1.show()
        self.QPushButton1.show()

        self.update_channel_list()
        self.sendMessage("Updating Done")

    def channel_activated(self) -> None:
        """Handle channel selection."""
        selection = self.listWidget.currentItem().text(0)

        if selection:
            self.CurrentChannel = selection

        try:
            self.update_episode_list(selection)
        except (TypeError, AttributeError) as e:
            # This can happen when a folder is selected instead of a channel
            logger.debug("Failed to update episode list for '%s': %s", selection, e)
        
        self.actionCancel.setToolTip("Delete Selected Channel")
        self.actionUpdateFeeds.setToolTip("Update Selected Channel")

    def delete_channel(self) -> None:
        """Delete the currently selected channel."""
        if self.tab.isVisible():
            try:
                self.db.deleteAllEpisodes(self.CurrentChannel)
                self.db.deleteChannel(self.CurrentChannel)

                os.chdir(str(DATA_DIR))
                ChannelDir = str(DATA_DIR / self.regex_white_space.sub("", self.CurrentChannel))

                import shutil
                shutil.rmtree(ChannelDir)
            except (TypeError, AttributeError, OSError) as e:
                # Channel deletion failed, try deleting as taxonomy/folder instead
                logger.debug("Channel deletion failed, trying as folder: %s", e)
                try:
                    self.db.deleteTaxonomy(self.CurrentChannel)
                except Exception as folder_error:
                    logger.error("Failed to delete folder: %s", folder_error)

        self.update_channel_list()

    def update_lastest_episodes_list(self) -> None:
        """Update the list of last 50 downloaded episodes."""
        episodes = self.db.getLatestDownloads()
        self.treeWidget_4.clear()

        for e in episodes:
            item = QtWidgets.QTreeWidgetItem(self.treeWidget_4)
            item.setText(0, str(e[10]))
            item.setIcon(0, QtGui.QIcon(QtGui.QPixmap(str(DATA_DIR / e[14]))))
            item.setText(1, e[1])
            item.setText(2, self.getReadableSize(e[4]))
            item.setText(3, str(DATA_DIR / str(e[3])))

    def update_newest_episodes_list(self) -> None:
        """Update the list of newest episodes."""
        episodes = self.db.getLatestEpisodes()
        self.treeWidget_5.clear()

        for e in episodes:
            item = QtWidgets.QTreeWidgetItem(self.treeWidget_5)
            item.setText(0, e[10])
            item.setIcon(0, QtGui.QIcon(QtGui.QPixmap(str(DATA_DIR / e[15]))))
            item.setText(1, e[1])
            if e[4]:
                item.setText(2, self.getReadableSize(e[4]))
            else:
                item.setText(2, '???')
            try:
                b = gmtime(float(e[5]))
                epDate = strftime("%x", b)
            except (ValueError, TypeError, OverflowError) as date_err:
                logger.debug("Failed to parse episode date: %s", date_err)
                b = gmtime()
                epDate = strftime("%x", b)

            item.setText(3, epDate)

            if e[2] and e[2] is not None:
                item.setText(4, e[2])

    def update_play_list(self, episodes: list[Any]) -> None:
        """Update the playlist display."""
        self.treewidget_playlist.clear()

        for e in episodes:
            item = QtWidgets.QTreeWidgetItem(self.treewidget_playlist)
            item.setText(0, str(e['channel_id']))
            item.setText(1, e['title'])
            if e['size']:
                item.setText(2, self.getReadableSize(e['size']))
            else:
                item.setText(2, '???')
            try:
                b = gmtime(float(e['date']))
                epDate = strftime("%x", b)
            except (ValueError, TypeError, OverflowError, KeyError) as date_err:
                logger.debug("Failed to parse playlist episode date: %s", date_err)
                b = gmtime()
                epDate = strftime("%x", b)

            item.setText(3, epDate)

            # Prefer local file if available, otherwise use remote enclosure
            try:
                localfile = e['localfile']
                if localfile:
                    item.setText(4, localfile)  # Local file path
                    item.setIcon(1, QtGui.QIcon(":/icons/mp3.png"))  # Downloaded icon
                else:
                    item.setText(4, e['enclosure'] if e['enclosure'] else '')  # Remote URL
                    item.setIcon(1, QtGui.QIcon(":/icons/build.png"))  # Not downloaded icon
            except (KeyError, IndexError):
                # If localfile doesn't exist, use enclosure
                item.setText(4, e['enclosure'] if e['enclosure'] else '')  # Remote URL
                item.setIcon(1, QtGui.QIcon(":/icons/build.png"))  # Not downloaded icon

    def play_episode(self, path: str) -> None:
        """
        Play an episode from either local file or remote URL.
        
        Uses the configured player from settings.
        
        Args:
            path: Either a local file path or remote URL
        """
        # Get player settings from database
        player_type = self.db.getSetting('player_type') or 'builtin'
        use_custom = self.db.getSetting('use_custom_player') == 'true'
        
        # Determine which command to use
        if use_custom or player_type == 'custom':
            play_command = self.db.getSetting('custom_play_command')
            if not play_command:
                QtWidgets.QMessageBox.warning(
                    self.MW,
                    "No Player Configured",
                    "Custom player is selected but no play command is configured.\n\n"
                    "Please configure a play command in Settings."
                )
                return
            # Substitute the file path
            play_command = play_command.replace('{file}', path)
            self._play_with_external(play_command, path)
        elif player_type == 'builtin':
            # Use built-in player
            self._play_with_builtin(path)
        else:
            # Use predefined external player
            play_command = get_play_command(player_type, path)
            if not play_command:
                QtWidgets.QMessageBox.warning(
                    self.MW,
                    "Player Not Configured",
                    f"No play command defined for player: {player_type}"
                )
                return
            self._play_with_external(play_command, path)

    def _play_with_builtin(self, path: str) -> None:
        """Play using the built-in GStreamer player."""
        # Stop any external player first
        self.AudioPlayer.stopClicked()
        
        if path.startswith('http://') or path.startswith('https://'):
            # Remote URL - GStreamer may not support HTTPS
            logger.warning("Streaming from HTTPS not supported by built-in player.")
            QtWidgets.QMessageBox.warning(
                self.MW,
                "Streaming Not Supported",
                "Your system's GStreamer doesn't support HTTPS streaming.\n\n"
                "Please download the episode first, or select an external player in Settings."
            )
        elif os.path.exists(path):
            # Local file
            logger.debug("Playing local file with built-in player: %s", path)
            self.AudioPlayer.setUrl_local(path)
        else:
            logger.error("File not found: %s", path)
            QtWidgets.QMessageBox.warning(
                self.MW,
                "File Not Found",
                f"Cannot find the episode file:\n{path}"
            )

    def _play_with_external(self, command: str, path: str) -> None:
        """Play using an external player command."""
        # Check if it's a local file that doesn't exist
        if not path.startswith('http://') and not path.startswith('https://'):
            if not os.path.exists(path):
                logger.error("File not found: %s", path)
                QtWidgets.QMessageBox.warning(
                    self.MW,
                    "File Not Found",
                    f"Cannot find the episode file:\n{path}"
                )
                return
        
        # Use AudioPlayer's external player support (handles stopping previous, tracking process)
        if not self.AudioPlayer.playExternal(command, path):
            QtWidgets.QMessageBox.warning(
                self.MW,
                "Player Error",
                "Failed to start external player. Check the logs for details."
            )

    def PlaylistEpisodeDoubleClicked(self, a: QtWidgets.QTreeWidgetItem) -> None:
        """Handle double-click on playlist item - play episode."""
        path = a.text(4)
        if path:
            self.play_episode(path)

    def LastestEpisodeDoubleClicked(self, episode_row: QtWidgets.QTreeWidgetItem) -> None:
        """Handle double-click on latest episode - add to playlist and play."""
        episodeTitle = episode_row.text(1)  # Column 1 is episode title
        episode = self.db.getEpisodeByTitle(episodeTitle)
        if episode:
            self.playlist.append(episode)
            self.update_play_list(self.playlist)
            # Play the episode - prefer local file over remote URL
            try:
                if episode['localfile']:
                    self.play_episode(episode['localfile'])
                elif episode['enclosure']:
                    self.play_episode(episode['enclosure'])
            except (KeyError, IndexError):
                if episode['enclosure']:
                    self.play_episode(episode['enclosure'])
        else:
            logger.warning("Could not find episode '%s' in database", episodeTitle)

    def NewestEpisodeDoubleClicked(self, episode_row: QtWidgets.QTreeWidgetItem) -> None:
        """Handle double-click on newest episode - add to playlist and play."""
        episode_title = episode_row.text(1)
        episode = self.db.getEpisodeByTitle(episode_title)
        if episode:
            self.playlist.append(episode)
            self.update_play_list(self.playlist)
            # Play the episode - prefer local file over remote URL
            try:
                if episode['localfile']:
                    self.play_episode(episode['localfile'])
                elif episode['enclosure']:
                    self.play_episode(episode['enclosure'])
            except (KeyError, IndexError):
                if episode['enclosure']:
                    self.play_episode(episode['enclosure'])
        else:
            logger.warning("Could not find episode '%s' in database", episode_title)

    def getReadableSize(self, size: Optional[Union[int, str]]) -> str:
        """Convert byte size to human-readable format."""
        if size:
            try:
                size_int = int(size)
                if size_int > 1024 * 1024:
                    sizeReadable = str(size_int // 1024 // 1024) + ' MB'
                elif size_int > 1024:
                    sizeReadable = str(size_int // 1024) + ' kB'
                else:
                    sizeReadable = str(size_int) + ' B'
            except (ValueError, TypeError) as e:
                logger.debug("Failed to convert size to readable format: %s", e)
                sizeReadable = str(size)
        else:
            sizeReadable = 'None'
        return sizeReadable

    def update_episode_list(self, channel_Title: str) -> None:
        """Update the episode list for a channel."""
        if self.db.is_folder(channel_Title):
            tt = self.db.getFolderEpisodes(channel_Title)
        else:
            tt = self.db.getChannelEpisodes(channel_Title)
            cc = self.db.getChannelByTitle(channel_Title)
            if cc:
                self.QTextBrowser1.setHtml(
                    "<p>" + cc[4] + "</p>"
                    "<p><b>Feed link:</b> <a href=" + cc[2] + ">" + cc[2] + "</a></p>"
                    "<p><b>Homepage: </b><a href=" + cc[3] + ">" + cc[3] + "</a></p>"
                )
            else:
                return
                
        self.treeWidget_2.clear()
        for t in tt:
            item2 = QtWidgets.QTreeWidgetItem(self.treeWidget_2)

            if not t[3]:  # localfile
                item2.setIcon(0, QtGui.QIcon(":/icons/build.png"))
            else:
                item2.setIcon(0, QtGui.QIcon(":/icons/mp3.png"))
            item2.setText(0, t[1])  # title
            item2.setText(1, self.getReadableSize(t[4]))  # size
            try:
                b = gmtime(float(t[5]))  # date
                epDate = strftime("%x", b)
            except (ValueError, TypeError, OverflowError) as date_err:
                logger.debug("Failed to parse episode date: %s", date_err)
                b = gmtime()
                epDate = strftime("%x", b)
            item2.setText(2, epDate)

            if t[7] == 'new':
                item2.setFont(0, self.fontBold)

    def update_channel_list(self, search_term: str = '') -> None:
        """Update the channel list, optionally filtering by search term."""
        logger.debug("Updating channel list with search term: %s", search_term)
        channels = self.db.getAllChannelsWOFolder()
        folders = self.db.getAllFolders()
        self.listWidget.clear()
        search_term = search_term.lower()

        for folder in folders:
            itemF = QtWidgets.QTreeWidgetItem(self.listWidget)
            itemF.setText(0, folder[1])
            itemF.setIcon(0, QtGui.QIcon(':/icons/folder-blue.png'))
            itemF.setFlags(enabled | droppable)
            itemF.setExpanded(True)
            
            childChannels = self.db.getFolderChannels(folder[0])

            for childChannel in childChannels:
                title_description = childChannel['title'] + childChannel['description']
                if (search_term != '' and search_term in title_description.lower()) or (search_term == ''):
                    itemChildChannel = QtWidgets.QTreeWidgetItem(itemF)
                    itemChildChannel.setText(0, childChannel[1])
                    itemChildChannel.setIcon(0, QtGui.QIcon(
                        QtGui.QPixmap(str(DATA_DIR / childChannel[6]))))
                    itemF.addChild(itemChildChannel)

        for channel in channels:
            title_description = channel['title'] + channel['description']
            if (search_term != '' and search_term in title_description.lower()) or (search_term == ''):
                item = QtWidgets.QTreeWidgetItem(self.listWidget)
                item.setText(0, channel[1])
                item.setIcon(0, QtGui.QIcon(QtGui.QPixmap(str(DATA_DIR / channel[6]))))
                item.setFlags(enabled | draggable | selectable)

    def updateProgressBarFromThread(self) -> None:
        """Update progress bar from background thread."""
        self.updateProgressBar.setValue(self.updateProgressBar.value() + 1)
        if self.updateProgressBar.value() == self.numberOfChannels - 1:
            self.update_done()

    def create_new_foder(self) -> None:
        """Create a new folder for organizing channels."""
        text, ok = QtWidgets.QInputDialog.getText(self.MW, 'Input Dialog', 'Enter name for new folder:')
        if ok:
            self.db.insertFolder(text)
        self.update_channel_list()

    def update_channel(self) -> None:
        """Update the currently selected channel."""
        self.QLineEdit1.hide()
        self.QPushButton1.hide()
        self.updateProgressBar.setRange(0, 0)
        self.updateProgressBar.show()
        self.numberOfChannels = 1

        ch = self.db.getChannelByTitle(self.CurrentChannel)

        self.ChannelForUpdate = ch

        updtChTr = UpdateChannelThread(ch, self, 0)
        updtChTr.updatesignal.connect(self.update_channel_list, QtCore.Qt.QueuedConnection)
        updtChTr.updatesignal_episodelist.connect(self.update_episode_list, QtCore.Qt.QueuedConnection)
        updtChTr.updateDoneSignal.connect(self.update_done, QtCore.Qt.BlockingQueuedConnection)
        self.update_channel_threads.append(updtChTr)
        updtChTr.start()

    def update_all_channels(self) -> None:
        """Update all channels in the background."""
        self.QLineEdit1.hide()
        self.QPushButton1.hide()
        self.updateProgressBar.show()

        updtChTr: list[UpdateChannelThread_network] = []
        allChannels = self.db.getAllChannels()

        self.numberOfChannels = allChannels.__len__() - 1
        self.updateProgressBar.setRange(0, self.numberOfChannels + 1)
        self.updateProgressBar.setValue(0)
        self.updateProgressBar.setFormat("%v" + " of " + "%m")
        
        j = 0
        for i in allChannels:
            updtChTr.append(UpdateChannelThread_network(i, self, j))
            self.update_channel_threads.append(updtChTr[j])
            updtChTr[j].updateProgressSignal.connect(self.updateProgressBarFromThread,
                                                     QtCore.Qt.BlockingQueuedConnection)
            updtChTr[j].updateAllChannelsDoneSignal.connect(self.update_db_with_all_channels,
                                                            QtCore.Qt.QueuedConnection)
            updtChTr[j].start()
            j = j + 1

    def update_db_with_all_channels(self) -> None:
        """
        Process all fetched channel data and update database.
        
        This is called after all network threads have finished fetching feeds.
        """
        con = sqlite3.connect(str(DATABASE_FILE), check_same_thread=False)
        con.isolation_level = None
        cur = con.cursor()

        for channel in self.updated_channes_list:
            try:
                logger.debug("Updating channel: %s", channel['channel_feedlink'])
            except TypeError:
                logger.error("Invalid channel data, skipping")
                continue

            ch = channel['channel_row']
            feed = channel['feed']

            old_episodes: list[str] = []

            cc = cur.execute('select id, title, link from sql_channel where title =?', (ch[1],))
            a = cc.fetchone()
            tt = cur.execute('select id, title, status from sql_episode where channel_id = ?', (a[0],))

            channel_id = a[0]
            for j in tt:
                old_episodes.append(j[1])

            for entry in feed.entries:
                try:
                    aa = old_episodes.index(entry.title)
                except ValueError:
                    aa = None

                if 'title' in entry and aa is None:
                    self.newEpisodeExists = 1
                    new_episode = parse_episode_for_update(entry)
                    if new_episode:
                        new_episode['channel_id'] = channel_id
                        self.db.insertEpisode(episode_dict_to_tuple(new_episode))

                elif 'title' not in entry:
                    logger.debug("Episode entry has no title")
                else:
                    if j[2] != 'old':
                        try:
                            self.db.updateEpisodeStatus(j[0])
                        except Exception as ex:
                            logger.error("Failed to update episode status: %s, episode: %s", ex, j)

        logger.info("Database update for all channels completed")

    def sendMessage(self, message: str) -> None:
        """Log a message."""
        logger.info(message)

    def update_done(self) -> None:
        """Handle completion of channel update."""
        self.updateProgressBar.hide()
        self.QLineEdit1.show()
        self.QPushButton1.show()

        self.update_channel_list()
        self.sendMessage("Updating Done")
