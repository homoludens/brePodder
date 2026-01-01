"""
brePodder - Main application module.

This module contains the BrePodder class which is the main application
window and handles user interactions.
"""
from PyQt6 import QtCore, QtWidgets, QtGui
from time import gmtime, strftime
import os
import sqlite3
from typing import Any, Optional, Union

from urllib3.connection import log

from ui.main_window import MainUi
from workers.download_worker import Download
from workers.update_worker import UpdateChannelThread, UpdateDatabaseThread
from workers.add_worker import AddChannelThread
from services.feed_parser import parse_episode_for_update, episode_dict_to_tuple
from config import DATA_DIR, DATABASE_FILE, USER_AGENT, THUMBNAIL_MAX_SIZE
from config_players import PLAYERS, get_play_command
from logger import get_logger

logger = get_logger(__name__)

# Qt item flags for tree widget items
DRAGGABLE: QtCore.Qt.ItemFlag = QtCore.Qt.ItemFlag.ItemIsDragEnabled
DROPPABLE: QtCore.Qt.ItemFlag = QtCore.Qt.ItemFlag.ItemIsDropEnabled
ENABLED: QtCore.Qt.ItemFlag = QtCore.Qt.ItemFlag.ItemIsEnabled
SELECTABLE: QtCore.Qt.ItemFlag = QtCore.Qt.ItemFlag.ItemIsSelectable
REQUEST_TIMEOUT = 10

from concurrent.futures import ProcessPoolExecutor
from functools import partial

# Module-level function (required for multiprocessing)
import copy

def make_serializable(obj):
    """Recursively convert feedparser objects to plain dicts/lists."""
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(item) for item in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif hasattr(obj, '__dict__'):
        return make_serializable(vars(obj))
    else:
        return str(obj)  # Fallback: convert to string


def fetch_and_parse_channel(channel_dict, headers, timeout):
    """Fetch and parse a channel - runs in separate process."""
    import requests
    import feedparser

    feed_link = channel_dict['link']
    try:
        resp = requests.get(feed_link, timeout=timeout, headers=headers)
        resp.raise_for_status()

        feed = feedparser.parse(resp.content)

        # Convert entire feed to serializable format
        feed_data = {
            'entries': [make_serializable(dict(e)) for e in feed.entries],
            'feed': make_serializable(dict(feed.feed)),
        }

        return {
            'channel_row': channel_dict,
            'channel_feedlink': feed_link,
            'feed': feed_data
        }
    except Exception as e:
        return {
            'channel_row': channel_dict,
            'channel_feedlink': feed_link,
            'feed': None,
            'error': str(e)
        }


class BrePodder(MainUi):
    """
    Main application class for brePodder podcast client.

    Inherits from MainUi which provides the UI setup.
    This class handles all user interactions and application logic.
    """

    def __init__(self, app: QtWidgets.QApplication) -> None:
        MainUi.__init__(self, app)
        # super().__init__()
        self.headers: dict[str, str] = {
            'User-Agent': USER_AGENT
        }
        self.app: QtWidgets.QApplication = app
        mainwindow = QtWidgets.QMainWindow()
        self.setup_ui(mainwindow)
        mainwindow.show()

        # Give AudioPlayer access to database for position saving
        self.audio_player._db = self.db

        self.update_channel_list()
        self.update_latest_episodes_list()
        self.update_newest_episodes_list()
        self.playlist: list[Any] = []
        self.updated_channels_list: list[Any] = []
        self.main_directory: str = str(DATA_DIR) + '/'

        self.update_channel_threads = []
        self.worker_threads = []  # Keep references to threads
        self.updated_channels_list = []

        self.executor = None
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.check_futures)
        self.futures = []

        # Load saved playlist from database
        self._load_playlist_from_db()

    def resize_image(self, source_image: str, destination_image: str) -> None:
        """Resize an image to thumbnail size if it's too large."""
        pixmap = QtGui.QPixmap(source_image)
        if pixmap.height() > THUMBNAIL_MAX_SIZE or pixmap.width() > THUMBNAIL_MAX_SIZE:
            pixmap_resized = pixmap.scaled(THUMBNAIL_MAX_SIZE, THUMBNAIL_MAX_SIZE, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
            if not os.path.exists(os.path.dirname(destination_image)):
                os.makedirs(os.path.dirname(destination_image))
            pixmap_resized.save(destination_image)

    def episode_activated(self) -> None:
        """Handle episode selection - display episode details."""
        if self.tree_widget_episodes.selectedItems():
            selection = self.tree_widget_episodes.selectedItems()[0]
            try:
                e = self.db.get_episode_by_title(selection.text(0))

                enc = e["enclosure"] if e["enclosure"] else 'None'
                desc = e["description"] if e["description"] else 'None'
                local_file = e["localfile"] if e["localfile"] else 'None'

                self.text_browser_details.setHtml(
                    "<p>" + desc + "</br>\n\r</p>"
                    "<p><b>FILE: </b><a href=" + enc + ">" + enc + "</a></p>"
                    "<p><b>LOCALFILE: </b><a href=" + local_file + ">" + local_file + "</a></p>"
                    "<p>PLAY:<audio controls='controls' src='" + enc + "'/></p>"
                )

            except (TypeError, KeyError) as e:
                logger.warning("episode_activated exception: %s", e)

    def download_activated(self, item: QtWidgets.QTreeWidgetItem, i: int) -> None:
        """Handle download item selection."""
        self.item_for_cancel = item
        self.actionCancel.setToolTip("Remove Selected Download")
        self.actionPause.setToolTip("Pause Selected Download")
        self.actionResume.setToolTip("Resume Selected Download")

    def episode_double_clicked(self, episode_row: Optional[QtWidgets.QTreeWidgetItem]) -> None:
        """Handle double-click on episode - start download."""
        if episode_row:
            episode_row.setFont(0, self.font_bold)
            episode_title = episode_row.text(0)
            e = self.db.get_episode_by_title(episode_title)
        else:
            e = self.episode_row

        self.playlist.append(e)

        channel = self.db.get_channel_by_id(e["channel_id"])
        channel_dir = self.regex_white_space.sub("", channel["title"])

        os.chdir(str(DATA_DIR / channel_dir))
        item = QtWidgets.QTreeWidgetItem(self.tree_widget_downloads)
        item.setText(0, channel.get("title"))
        item.setText(1, e["title"])
        item.setText(2, self.get_readable_size(e["size"]))
        item.setText(3, '0')
        item.setText(4, '0')

        try:
            item.setText(5, e["enclosure"])
        except TypeError:
            logger.warning("No enclosure link for episode")
            item.setText(5, "No link")

        if len(self.download_list) > 0:
            download_id = self.download_list[-1][0] + 1
        else:
            download_id = 0

        self.items_downloading.append((download_id, e["enclosure"].replace(" ", "%20")))
        download = Download(e["enclosure"].replace(" ", "%20"), item, download_id, self)
        download.download_finished.connect(lambda fileName, savePath, dlId: self.on_download_finished(fileName, savePath, dlId, e["title"]))
        self.download_list.append((download_id, download))

        os.chdir(str(DATA_DIR))

    def on_download_finished(self, file_name: str, save_path: str, download_id: int, episode_title: str) -> None:
        """Handle download completion - update database and refresh UI."""
        logger.debug("Download completed for episode: %s", episode_title)

        # Get the episode from database
        episode = self.db.get_episode_by_title(episode_title)

        if episode:
            # Update the episode with local file path and downloaded status
            self.db.update_episode((save_path, "downloaded", episode["id"]))
            logger.info("Updated episode '%s' with local file: %s", episode_title, save_path)

            # Refresh the latest downloads list
            self.update_latest_episodes_list()
        else:
            logger.warning("Could not find episode '%s' in database to update", episode_title)

    def add_channel(self, new_url: Optional[str] = None) -> None:
        """Add a new channel/podcast subscription."""
        os.chdir(str(DATA_DIR))
        if not new_url:
            feed_link = self.line_edit_feed_url.text()
        else:
            feed_link = new_url

        self.line_edit_feed_url.hide()
        self.button_add.hide()
        self.update_progress_bar.setRange(0, 0)
        self.update_progress_bar.show()
        self.number_of_channels = 1

        add_channel_thread = AddChannelThread(feed_link, self, 0)
        add_channel_thread.addsignal.connect(self.update_channel_list, QtCore.Qt.ConnectionType.QueuedConnection)
        add_channel_thread.addsignal_episodelist.connect(self.update_episode_list, QtCore.Qt.ConnectionType.QueuedConnection)
        add_channel_thread.addDoneSignal.connect(self.adding_channel_done, QtCore.Qt.ConnectionType.BlockingQueuedConnection)
        self.update_channel_threads.append(add_channel_thread)
        add_channel_thread.start()

    def adding_channel_done(self) -> None:
        """Handle completion of channel addition."""
        self.update_progress_bar.hide()
        self.line_edit_feed_url.show()
        self.button_add.show()

        self.update_channel_list()
        self.send_message("Updating Done")

    def channel_activated(self) -> None:
        """Handle channel selection."""
        selection = self.listWidget.currentItem().text(0)

        if selection:
            self.current_channel = selection

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
                self.db.delete_all_episodes(self.current_channel)
                self.db.delete_channel(self.current_channel)

                os.chdir(str(DATA_DIR))
                channel_dir = str(DATA_DIR / self.regex_white_space.sub("", self.current_channel))

                import shutil
                shutil.rmtree(channel_dir)
            except (TypeError, AttributeError, OSError) as e:
                # Channel deletion failed, try deleting as taxonomy/folder instead
                logger.debug("Channel deletion failed, trying as folder: %s", e)
                try:
                    self.db.delete_taxonomy(self.current_channel)
                except Exception as folder_error:
                    logger.error("Failed to delete folder: %s", folder_error)

        self.update_channel_list()

    def update_latest_episodes_list(self) -> None:
        """Update the list of last 50 downloaded episodes."""
        episodes = self.db.get_latest_downloads()
        self.tree_widget_latest_downloads.clear()

        for e in episodes:
            item = QtWidgets.QTreeWidgetItem(self.tree_widget_latest_downloads)
            item.setText(0, str(e[10]))
            item.setIcon(0, QtGui.QIcon(QtGui.QPixmap(str(DATA_DIR / e[14]))))
            item.setText(1, e[1])
            item.setText(2, self.get_readable_size(e[4]))
            item.setText(3, str(DATA_DIR / str(e[3])))

    def update_newest_episodes_list(self) -> None:
        """Update the list of newest episodes."""
        episodes = self.db.get_latest_episodes()
        self.tree_widget_newest_episodes.clear()

        for e in episodes:
            item = QtWidgets.QTreeWidgetItem(self.tree_widget_newest_episodes)
            item.setText(0, e[10])
            item.setIcon(0, QtGui.QIcon(QtGui.QPixmap(str(DATA_DIR / e[15]))))
            item.setText(1, e[1])
            if e[4]:
                item.setText(2, self.get_readable_size(e[4]))
            else:
                item.setText(2, '???')
            try:
                b = gmtime(float(e[5]))
                ep_date = strftime("%x", b)
            except (ValueError, TypeError, OverflowError) as date_err:
                logger.debug("Failed to parse episode date: %s", date_err)
                b = gmtime()
                ep_date = strftime("%x", b)

            item.setText(3, ep_date)

            if e[2] and e[2] is not None:
                item.setText(4, e[2])

    def update_playlist(self, episodes: list[Any]) -> None:
        """Update the playlist display."""
        self.tree_widget_playlist.clear()

        for e in episodes:
            item = QtWidgets.QTreeWidgetItem(self.tree_widget_playlist)
            # Store episode_id as hidden data for later use
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, e['id'])
            item.setText(0, str(e['channel_id']))
            item.setText(1, e['title'])
            if e['size']:
                item.setText(2, self.get_readable_size(e['size']))
            else:
                item.setText(2, '???')
            try:
                b = gmtime(float(e['date']))
                ep_date = strftime("%x", b)
            except (ValueError, TypeError, OverflowError, KeyError) as date_err:
                logger.debug("Failed to parse playlist episode date: %s", date_err)
                b = gmtime()
                ep_date = strftime("%x", b)

            item.setText(3, ep_date)

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

    def _load_playlist_from_db(self) -> None:
        """Load the playlist from database on startup."""
        playlist_rows = self.db.get_playlist()
        self.playlist = []
        for row in playlist_rows:
            # Convert Row to dict-like access
            self.playlist.append(row)
        self.update_playlist(self.playlist)
        logger.debug("Loaded %d episodes from saved playlist", len(self.playlist))

    def add_episode_to_playlist(self, episode) -> bool:
        """
        Add an episode to the playlist.

        Returns True if added, False if already in playlist or limit reached.
        """
        if len(self.playlist) >= 50:
            QtWidgets.QMessageBox.warning(
                self.main_window,
                "Playlist Full",
                "Playlist is limited to 50 episodes.\n\n"
                "Please remove some episodes before adding more."
            )
            return False

        episode_id = episode['id']

        # Add to database
        if not self.db.add_to_playlist(episode_id):
            logger.debug("Episode already in playlist or limit reached")
            return False

        # Add to local list
        self.playlist.append(episode)
        self.update_playlist(self.playlist)
        return True

    def clear_playlist(self) -> None:
        """Clear all episodes from the playlist."""
        self.db.clear_playlist()
        self.playlist = []
        self.update_playlist(self.playlist)
        logger.info("Playlist cleared")

    def play_episode(self, path: str) -> None:
        """
        Play an episode from either local file or remote URL.

        Uses the configured player from settings.

        Args:
            path: Either a local file path or remote URL
        """
        # Get player settings from database
        player_type = self.db.get_setting('player_type') or 'builtin'
        use_custom = self.db.get_setting('use_custom_player') == 'true'

        # Determine which command to use
        if use_custom or player_type == 'custom':
            play_command = self.db.get_setting('custom_play_command')
            if not play_command:
                QtWidgets.QMessageBox.warning(
                    self.main_window,
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
                    self.main_window,
                    "Player Not Configured",
                    f"No play command defined for player: {player_type}"
                )
                return
            self._play_with_external(play_command, path)

    def _play_with_builtin_and_id(self, path: str, episode_id: int) -> None:
        """Play using built-in player with episode ID for position tracking."""
        # Stop any external player first
        self.audio_player.stop_clicked()

        if os.path.exists(path):
            logger.debug("Playing local file with position tracking: %s", path)
            self.audio_player.set_url_local(path, episode_id)
        else:
            logger.error("File not found: %s", path)
            QtWidgets.QMessageBox.warning(
                self.main_window,
                "File Not Found",
                f"Cannot find the episode file:\n{path}"
            )

    def _play_with_builtin(self, path: str) -> None:
        """Play using the built-in GStreamer player."""
        # Stop any external player first
        self.audio_player.stop_clicked()

        if path.startswith('http://') or path.startswith('https://'):
            # Remote URL - GStreamer may not support HTTPS
            logger.warning("Streaming from HTTPS not supported by built-in player.")
            QtWidgets.QMessageBox.warning(
                self.main_window,
                "Streaming Not Supported",
                "Your system's GStreamer doesn't support HTTPS streaming.\n\n"
                "Please download the episode first, or select an external player in Settings."
            )
        elif os.path.exists(path):
            # Local file
            logger.debug("Playing local file with built-in player: %s", path)
            self.audio_player.set_url_local(path)
        else:
            logger.error("File not found: %s", path)
            QtWidgets.QMessageBox.warning(
                self.main_window,
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
                    self.main_window,
                    "File Not Found",
                    f"Cannot find the episode file:\n{path}"
                )
                return

        # Use AudioPlayer's external player support (handles stopping previous, tracking process)
        if not self.audio_player.play_external(command, path):
            QtWidgets.QMessageBox.warning(
                self.main_window,
                "Player Error",
                "Failed to start external player. Check the logs for details."
            )

    def playlist_episode_double_clicked(self, a: QtWidgets.QTreeWidgetItem) -> None:
        """Handle double-click on playlist item - play episode."""
        path = a.text(4)
        episode_id = a.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if path:
            if episode_id and os.path.exists(path):
                # Local file with episode_id - use built-in player with position tracking
                self._play_with_builtin_and_id(path, episode_id)
            else:
                self.play_episode(path)

    def latest_episode_double_clicked(self, episode_row: QtWidgets.QTreeWidgetItem) -> None:
        """Handle double-click on latest episode - add to playlist and play."""
        episode_title = episode_row.text(1)  # Column 1 is episode title
        episode = self.db.get_episode_by_title(episode_title)
        if episode:
            self.add_episode_to_playlist(episode)
            # Play the episode - prefer local file over remote URL
            self._play_episode_with_id(episode)
        else:
            logger.warning("Could not find episode '%s' in database", episode_title)

    def newest_episode_double_clicked(self, episode_row: QtWidgets.QTreeWidgetItem) -> None:
        """Handle double-click on newest episode - add to playlist and play."""
        episode_title = episode_row.text(1)
        episode = self.db.get_episode_by_title(episode_title)
        if episode:
            self.add_episode_to_playlist(episode)
            # Play the episode - prefer local file over remote URL
            self._play_episode_with_id(episode)
        else:
            logger.warning("Could not find episode '%s' in database", episode_title)

    def _play_episode_with_id(self, episode) -> None:
        """Play an episode, passing episode_id for position tracking."""
        episode_id = episode['id']
        try:
            if episode['localfile']:
                self._play_with_builtin_and_id(episode['localfile'], episode_id)
            elif episode['enclosure']:
                self.play_episode(episode['enclosure'])
        except (KeyError, IndexError):
            if episode['enclosure']:
                self.play_episode(episode['enclosure'])

    def get_readable_size(self, size: Optional[Union[int, str]]) -> str:
        """Convert byte size to human-readable format."""
        if size:
            try:
                size_int = int(size)
                if size_int > 1024 * 1024:
                    size_readable = str(size_int // 1024 // 1024) + ' MB'
                elif size_int > 1024:
                    size_readable = str(size_int // 1024) + ' kB'
                else:
                    size_readable = str(size_int) + ' B'
            except (ValueError, TypeError) as e:
                logger.debug("Failed to convert size to readable format: %s", e)
                size_readable = str(size)
        else:
            size_readable = 'None'
        return size_readable

    def update_episode_list(self, channel_title: str) -> None:
        """Update the episode list for a channel."""
        if self.db.is_folder(channel_title):
            tt = self.db.get_folder_episodes(channel_title)
        else:
            tt = self.db.get_channel_episodes(channel_title)
            cc = self.db.get_channel_by_title(channel_title)
            if cc:
                self.text_browser_details.setHtml(
                    "<p>" + cc[4] + "</p>"
                    "<p><b>Feed link:</b> <a href=" + cc[2] + ">" + cc[2] + "</a></p>"
                    "<p><b>Homepage: </b><a href=" + cc[3] + ">" + cc[3] + "</a></p>"
                )
            else:
                return

        self.tree_widget_episodes.clear()
        for t in tt:
            item2 = QtWidgets.QTreeWidgetItem(self.tree_widget_episodes)

            if not t[3]:  # localfile
                item2.setIcon(0, QtGui.QIcon(":/icons/build.png"))
            else:
                item2.setIcon(0, QtGui.QIcon(":/icons/mp3.png"))
            item2.setText(0, t[1])  # title
            item2.setText(1, self.get_readable_size(t[4]))  # size
            try:
                b = gmtime(float(t[5]))  # date
                ep_date = strftime("%x", b)
            except (ValueError, TypeError, OverflowError) as date_err:
                logger.debug("Failed to parse episode date: %s", date_err)
                b = gmtime()
                ep_date = strftime("%x", b)
            item2.setText(2, ep_date)

            if t[7] == 'new':
                item2.setFont(0, self.font_bold)

    def update_channel_list(self, search_term: str = '') -> None:
        """Update the channel list, optionally filtering by search term."""
        logger.debug("Updating channel list with search term: %s", search_term)
        channels = self.db.get_all_channels_without_folder()
        folders = self.db.get_all_folders()
        self.listWidget.clear()
        search_term = search_term.lower()

        for folder in folders:
            item_folder = QtWidgets.QTreeWidgetItem(self.listWidget)
            item_folder.setText(0, folder[1])
            item_folder.setIcon(0, QtGui.QIcon(':/icons/folder-blue.png'))
            item_folder.setFlags(ENABLED | DROPPABLE)
            item_folder.setExpanded(True)

            child_channels = self.db.get_folder_channels(folder[0])

            for child_channel in child_channels:
                title_description = child_channel['title'] + child_channel['description']
                if (search_term != '' and search_term in title_description.lower()) or (search_term == ''):
                    item_child_channel = QtWidgets.QTreeWidgetItem(item_folder)
                    item_child_channel.setText(0, child_channel[1])
                    item_child_channel.setIcon(0, QtGui.QIcon(
                        QtGui.QPixmap(str(DATA_DIR / child_channel[6]))))
                    item_folder.addChild(item_child_channel)

        for channel in channels:
            title_description = channel['title'] + channel['description']
            if (search_term != '' and search_term in title_description.lower()) or (search_term == ''):
                item = QtWidgets.QTreeWidgetItem(self.listWidget)
                item.setText(0, channel[1])
                item.setIcon(0, QtGui.QIcon(QtGui.QPixmap(str(DATA_DIR / channel[6]))))
                item.setFlags(ENABLED | DRAGGABLE | SELECTABLE)



    def update_progress_bar_from_thread(self) -> None:
        """Update progress bar from background thread."""
        self.update_progress_bar.setValue(self.update_progress_bar.value() + 1)
        if self.update_progress_bar.value() == self.number_of_channels - 1:
            self.update_done()

    def create_new_folder(self) -> None:
        """Create a new folder for organizing channels."""
        text, ok = QtWidgets.QInputDialog.getText(self.main_window, 'Input Dialog', 'Enter name for new folder:')
        if ok:
            self.db.insert_folder(text)
        self.update_channel_list()


    def update_channel(self) -> None:
        """Update the currently selected channel."""
        self.line_edit_feed_url.hide()
        self.button_add.hide()
        self.update_progress_bar.setRange(0, 0)
        self.update_progress_bar.show()
        self.number_of_channels = 1

        ch = self.db.get_channel_by_title(self.current_channel)

        self.channel_for_update = ch

        update_channel_thread = UpdateChannelThread(ch, self, 0)
        update_channel_thread.updatesignal.connect(self.update_channel_list, QtCore.Qt.ConnectionType.QueuedConnection)
        update_channel_thread.updatesignal_episodelist.connect(self.update_episode_list, QtCore.Qt.ConnectionType.QueuedConnection)
        update_channel_thread.updateDoneSignal.connect(self.update_done, QtCore.Qt.ConnectionType.BlockingQueuedConnection)
        self.update_channel_threads.append(update_channel_thread)
        update_channel_thread.start()


    def update_all_channels(self) -> None:
        """Update all channels using process pool."""

        self.line_edit_feed_url.hide()
        self.button_add.hide()
        self.update_progress_bar.show()

        self.updated_channels_list.clear()

        all_channels = self.db.get_all_channels()

        all_channels = all_channels[10:20]  # Test on 10 channels

        self.number_of_channels = len(all_channels)
        self.update_progress_bar.setRange(0, self.number_of_channels)
        self.update_progress_bar.setValue(0)
        self.update_progress_bar.setFormat("%v of %m")

        # Use ProcessPoolExecutor to avoid GIL
        self.executor = ProcessPoolExecutor(max_workers=4)
        self.futures = []

        headers = {'User-Agent': USER_AGENT}
        for channel in all_channels:
            # Convert sqlite Row to dict if needed
            channel_dict = dict(channel) if hasattr(channel, 'keys') else channel
            future = self.executor.submit(
                fetch_and_parse_channel,
                channel_dict,
                headers,
                REQUEST_TIMEOUT
            )
            self.futures.append(future)

        # Poll for completion using timer (non-blocking)
        self.completed_count = 0
        self.timer.start(200)  # Check every 100ms


    def check_futures(self):
        """Check if any futures completed."""
        for future in self.futures[:]:
            if future.done():
                self.futures.remove(future)
                try:
                    result = future.result()
                    if result and result.get('feed'):
                        self.updated_channels_list.append(result)
                    elif result and result.get('error'):
                        logger.warning("Channel %s failed: %s",
                                    result['channel_feedlink'],
                                    result['error'])
                except Exception as e:
                    logger.error("Future error: %s", e)

                self.completed_count += 1
                self.update_progress_bar.setValue(self.completed_count)

        if not self.futures:
            self.timer.stop()
            self.executor.shutdown(wait=False)
            self.update_db_with_all_channels()


    def on_thread_finished(self, thread, semaphore):
        """Cleanup when thread finishes"""
        logger.info(f"on_thread_finished    Thread {thread} finished")
        semaphore.release(1)
        thread.deleteLater()

    def update_db_with_all_channels(self) -> None:
        """
        Process all fetched channel data and update database.

        This is called after all network threads have finished fetching feeds.
        Runs database operations in a background thread to keep UI responsive.
        """
        self.db_update_thread = UpdateDatabaseThread(self.updated_channels_list, self.db)
        self.db_update_thread.updateDoneSignal.connect(self.update_done)
        self.db_update_thread.start()

    def send_message(self, message: str) -> None:
        """Log a message."""
        logger.info(message)

    def update_done(self) -> None:
        """Handle completion of channel update."""
        self.update_progress_bar.hide()
        self.line_edit_feed_url.show()
        self.button_add.show()

        self.update_channel_list()
        self.send_message("Updating Done")
