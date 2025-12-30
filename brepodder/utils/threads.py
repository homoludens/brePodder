"""
Background thread classes for channel operations.

These QThread subclasses handle network operations and database updates
in the background to keep the UI responsive.
"""
from PyQt5 import QtCore, QtWidgets
from io import BytesIO
import os
import sqlite3
import feedparser
import requests
from typing import Any, Optional, Union

from config import DATA_DIR, DATABASE_FILE, USER_AGENT, REQUEST_TIMEOUT
from logger import get_logger
from utils.feed_parser import parse_episode_for_update, episode_dict_to_tuple
from utils.get_favicon import get_icon_url, download_image
from utils.youtube import is_video_link, get_youtube_rss, get_cover
from utils.download import Download

logger = get_logger(__name__)


class UpdateChannelThread_network(QtCore.QThread):
    """
    Thread for fetching channel feed data from the network.
    
    This thread only fetches the feed data and stores it for later processing.
    The actual database update is done in the main thread after all feeds are fetched.
    """
    updatesignal = QtCore.pyqtSignal()
    updateProgressSignal = QtCore.pyqtSignal()
    updateDoneSignal = QtCore.pyqtSignal()
    updatesignal_episodelist = QtCore.pyqtSignal()
    updateAllChannelsDoneSignal = QtCore.pyqtSignal()

    def __init__(self, channel: Any, ui: Any, update_progress: int = 0) -> None:
        QtCore.QThread.__init__(self)
        self.channel: Any = channel
        self.ui: Any = ui
        self.updateProgress: int = update_progress
        self.newEpisodeExists: int = 0
        self.main_directory: str = str(DATA_DIR) + '/'
        self.headers: dict[str, str] = {
            'User-Agent': USER_AGENT
        }

    def run(self) -> None:
        self.ui.Sem.acquire(1)

        self.ui.updated_channes_list.append(self.update_channel(self.channel))

        if len(self.ui.updated_channes_list) == self.ui.numberOfChannels:
            self.updateAllChannelsDoneSignal.emit()

        self.updateProgressSignal.emit()

        if self.updateProgress == 0:
            self.updateDoneSignal.emit()

        self.ui.Sem.release(1)

    def update_channel(self, channel_row: Any = None) -> Optional[dict[str, Any]]:
        """
        Fetch and parse the feed for a channel.
        
        Args:
            channel_row: Database row with channel data
            
        Returns:
            dict: Contains channel_row, channel_feedlink, and parsed feed
        """
        feed_link: str = channel_row['link']

        content: Union[str, BytesIO] = ''
        try:
            resp = requests.get(feed_link, timeout=REQUEST_TIMEOUT, headers=self.headers)
        except requests.ReadTimeout as e:
            logger.warning("Timeout when reading RSS %s: %s", feed_link, e)
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error("Connection error for %s: %s", feed_link, e)
            return None
        except requests.exceptions.HTTPError as e:
            logger.error("HTTP error for %s: %s", feed_link, e)
            return None
        except requests.exceptions.MissingSchema as e:
            logger.error("Missing schema for %s: %s", feed_link, e)
            return None
        else:
            content = BytesIO(resp.content)

        feed = feedparser.parse(content)

        updated_channel_dict: dict[str, Any] = {
            'channel_row': channel_row,
            'channel_feedlink': feed_link,
            'feed': feed
        }

        return updated_channel_dict


class UpdateChannelThread(QtCore.QThread):
    """
    Thread for updating a single channel with database operations.
    
    Note: This class is being replaced by UpdateChannelThread_network
    which separates network and database operations for better thread safety.
    """
    updatesignal = QtCore.pyqtSignal()
    updateProgressSignal = QtCore.pyqtSignal()
    updateDoneSignal = QtCore.pyqtSignal()
    updatesignal_episodelist = QtCore.pyqtSignal()

    def __init__(self, channel: Any, ui: Any, update_progress: int = 0) -> None:
        QtCore.QThread.__init__(self)
        self.channel: Any = channel
        self.ui: Any = ui
        self.updateProgress: int = update_progress
        self.newEpisodeExists: int = 0
        self.main_directory: str = str(DATA_DIR) + '/'
        self.headers: dict[str, str] = {
            'User-Agent': USER_AGENT
        }

    def run(self) -> None:
        self.ui.Sem.acquire(1)
        
        con = sqlite3.connect(str(DATABASE_FILE), check_same_thread=False)
        con.isolation_level = None
        cur = con.cursor()

        self.update_channel(self.channel, cur)

        con.commit()
        cur.close()

        if self.newEpisodeExists:
            self.updatesignal.emit()

        self.updateProgressSignal.emit()

        if self.updateProgress == 0:
            self.updateDoneSignal.emit()

        self.ui.Sem.release(1)

    def update_channel(self, ch: Any = None, cursor: Optional[sqlite3.Cursor] = None) -> Optional[str]:
        """Update channel episodes from feed."""
        cur = cursor
        old_episodes: list[str] = []
        
        if ch is None:
            a, tt = self.ui.db.getCurrentChannel(self.ui.CurrentChannel[1])
        else:
            cc = cur.execute('select id,title,link from sql_channel where title =?', (ch[1],))
            a = cc.fetchone()
            tt = cur.execute('select id,title,status from sql_episode where channel_id = ?', (a[0],))

        channel_id = a[0]
        for j in tt:
            old_episodes.append(j[1])

        feed_link: str = a[2]

        content: Union[str, BytesIO] = ''
        try:
            resp = requests.get(feed_link, timeout=REQUEST_TIMEOUT, headers=self.headers)
        except requests.ReadTimeout as e:
            logger.warning("Timeout when reading RSS %s: %s", feed_link, e)
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error("Connection error for %s: %s", feed_link, e)
            return None
        except requests.exceptions.HTTPError as e:
            logger.error("HTTP error for %s: %s", feed_link, e)
            return None
        except requests.exceptions.MissingSchema as e:
            logger.error("Missing schema for %s: %s", feed_link, e)
            return None
        else:
            content = BytesIO(resp.content)

        feed = feedparser.parse(content)

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
                    self.ui.db.insertEpisode(episode_dict_to_tuple(new_episode))

            elif 'title' not in entry:
                logger.debug("Episode entry has no title")
            else:
                if j[2] != 'old':
                    try:
                        self.ui.db.updateEpisodeStatus(j[0])
                    except Exception as ex:
                        logger.error("Failed to update episode status: %s, episode: %s", ex, j)
        return None


class AddChannelThread(QtCore.QThread):
    """
    Thread for adding a new channel/podcast subscription.
    
    Handles fetching the feed, downloading channel artwork,
    and adding all episodes to the database.
    """
    addsignal = QtCore.pyqtSignal()
    addProgressSignal = QtCore.pyqtSignal()
    addDoneSignal = QtCore.pyqtSignal()
    addsignal_episodelist = QtCore.pyqtSignal()

    def __init__(self, channel_url: str, ui: Any, update_progress: int = 0) -> None:
        QtCore.QThread.__init__(self)
        self.channel_url: str = channel_url
        self.ui: Any = ui
        self.updateProgress: int = update_progress
        self.newEpisodeExists: int = 0
        self.main_directory: str = str(DATA_DIR) + '/'

    def run(self) -> None:
        self.ui.Sem.acquire(1)
        
        con = sqlite3.connect(str(DATABASE_FILE), check_same_thread=False)
        con.isolation_level = None
        cur = con.cursor()

        self.add_channel(self.channel_url, cur)

        con.commit()
        cur.close()

        if self.newEpisodeExists:
            self.addsignal.emit()

        self.addProgressSignal.emit()

        if self.updateProgress == 0:
            self.addDoneSignal.emit()

        self.ui.Sem.release(1)

    def add_channel(self, new_url: Optional[str] = None, cursor: Optional[sqlite3.Cursor] = None) -> None:
        """Add a new channel from URL."""
        os.chdir(self.main_directory)

        feed_link = new_url
        if is_video_link(feed_link):
            feed_link = get_youtube_rss(feed_link)

        headers: dict[str, str] = {
            'User-Agent': USER_AGENT
        }
        try:
            resp = requests.get(feed_link, timeout=REQUEST_TIMEOUT, headers=headers)
        except requests.ReadTimeout as e:
            logger.warning("Timeout when reading RSS %s: %s", feed_link, e)
            return
        except requests.exceptions.ConnectTimeout as e:
            logger.warning("Connect timeout for %s: %s", feed_link, e)
            return
        except requests.exceptions.ConnectionError as e:
            logger.error("Connection error for %s: %s", feed_link, e)
            return

        content = BytesIO(resp.content)
        feed_content = feedparser.parse(content)

        item = QtWidgets.QTreeWidgetItem(self.ui.treeWidget)

        if 'title' in feed_content.feed:
            ChannelTitle: str = feed_content.feed.title
        elif 'link' in feed_content.feed:
            ChannelTitle = feed_content.feed.link
        else:
            ChannelTitle = feed_link

        if self.ui.db.getChannelByLink(feed_link):
            logger.info("Channel already exists: %s", feed_link)
            return

        if self.ui.db.getChannelByTitle(ChannelTitle):
            logger.info("Channel already exists: %s", ChannelTitle)
            return

        ChannelDir: str = self.ui.regex_white_space.sub("", ChannelTitle)

        if not os.path.exists(self.main_directory + ChannelDir):
            os.makedirs(self.main_directory + ChannelDir)

        os.chdir(self.main_directory + ChannelDir)
        item.setText(0, ChannelTitle)

        # Download channel logo
        logo_fileBig: str = ''
        imageURL: str = ''
        if 'image' in feed_content.feed:
            if feed_content.feed.image.href is not None:
                if feed_content.feed.image.href[0] == '/':
                    imageURL = feed_content.feed.link + feed_content.feed.image.href
                else:
                    imageURL = feed_content.feed.image.href

            url_done = QtCore.QUrl(imageURL)
            fileInfo = QtCore.QFileInfo(url_done.path())
            fileName = fileInfo.fileName()
            logo_fileBig = ChannelDir + "/" + fileName

        if is_video_link(new_url):
            imageURL = get_cover(new_url)
            logo_fileBig = ChannelDir + "/" + "logo.jpg"

        if imageURL:
            download_image(imageURL, self.main_directory + logo_fileBig)
            self.ui.resize_image(self.main_directory + logo_fileBig, self.main_directory + logo_fileBig)

        # Download favicon
        if "link" in feed_content.feed:
            logger.debug("Feed link: %s", feed_content.feed.link)
            favicon_url = get_icon_url("https://" + QtCore.QUrl(feed_content.feed.link).host())
        else:
            favicon_url = get_icon_url(feed_link)

        if favicon_url:
            url: str = favicon_url
        else:
            url = ''

        url_favicon = QtCore.QUrl(url)
        favicon_info = QtCore.QFileInfo(url_favicon.path())
        favicon_name = favicon_info.fileName()
        logo_file: str = ChannelDir + '/' + favicon_name

        download_image(url, self.main_directory + logo_file)
        self.ui.resize_image(self.main_directory + logo_file, self.main_directory + logo_file)

        item2 = QtWidgets.QTreeWidgetItem(self.ui.treeWidget)

        if 'title' in feed_content.feed:
            item2.setText(0, feed_content.feed.title)
        else:
            item2.setText(0, "No title")

        item2.setText(1, url)
        item2.setText(5, url)

        if len(self.ui.downloadList) > 0:
            downloadId: int = self.ui.downloadList[-1][0] + 1
        else:
            downloadId = 0

        self.ui.itemsDownloading.append((downloadId, url))
        self.ui.downloadList.append((downloadId, Download(url, item2, downloadId, self.ui)))

        self.ui.downloadList[downloadId][1].faviconFound = True

        if 'subtitle' in feed_content.feed:
            ChannelSubtitle: str = feed_content.feed.subtitle
        else:
            ChannelSubtitle = 'No description'

        if 'links' in feed_content.feed:
            ChannelHomepage: str = feed_content.feed.links[0].href
        else:
            ChannelHomepage = 'http://google.com'

        newChannel: tuple[str, str, str, str, str, str] = (ChannelTitle, feed_link, ChannelHomepage, ChannelSubtitle, logo_file, logo_fileBig)
        self.ui.db.insertChannel(newChannel)

        ChannelId = self.ui.db.getChannelByTitle(ChannelTitle)

        for episode in feed_content.entries:
            self.add_episode(ChannelId[0], episode)

        os.chdir(str(DATA_DIR))

    def add_episode(self, channel_id: int, episode: Any) -> None:
        """Add an episode to the database."""
        from utils.feed_parser import parse_episode_from_feed_entry
        
        new_episode = parse_episode_from_feed_entry(episode, channel_id)
        self.ui.db.insertEpisode(tuple(new_episode.values()))
