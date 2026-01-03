"""
Background thread class for adding new channels.

This QThread subclass handles adding new podcast subscriptions
in the background to keep the UI responsive.
"""
from PyQt6 import QtCore, QtWidgets
from io import BytesIO
import os
import sqlite3
import feedparser
import requests
from typing import Any, Optional

from brepodder.config import DATA_DIR, DATABASE_FILE, USER_AGENT, REQUEST_TIMEOUT
from brepodder.logger import get_logger
from brepodder.services.feed_parser import parse_episode_from_feed_entry
from brepodder.utils.favicon import get_icon_url, download_image
from brepodder.utils.youtube import is_video_link, get_youtube_rss, get_cover
from brepodder.workers.download_worker import Download

logger = get_logger(__name__)


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
        self.update_progress: int = update_progress
        self.new_episode_exists: int = 0
        self.main_directory: str = str(DATA_DIR) + '/'

    def run(self) -> None:
        self.ui.semaphore.acquire(1)

        con = sqlite3.connect(str(DATABASE_FILE), check_same_thread=False)
        con.isolation_level = None
        cur = con.cursor()

        self.add_channel(self.channel_url, cur)

        con.commit()
        cur.close()

        if self.new_episode_exists:
            self.addsignal.emit()

        self.addProgressSignal.emit()

        if self.update_progress == 0:
            self.addDoneSignal.emit()

        self.ui.semaphore.release(1)

    def add_channel(self, new_url: Optional[str] = None, cursor: Optional[sqlite3.Cursor] = None) -> None:
        """Add a new channel from URL."""
        os.chdir(self.main_directory)

        feed_link = new_url


        if self.ui.db.get_channel_by_link(feed_link):
            logger.info("Channel already exists: %s", feed_link)
            return

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

        item = QtWidgets.QTreeWidgetItem(self.ui.tree_widget_downloads)

        if 'title' in feed_content.feed:
            channel_title: str = feed_content.feed.title
        elif 'link' in feed_content.feed:
            channel_title = feed_content.feed.link
        else:
            channel_title = feed_link

        if self.ui.db.get_channel_by_title(channel_title):
            logger.info("Channel already exists: %s", channel_title)
            return

        channel_dir: str = self.ui.regex_white_space.sub("", channel_title)

        if not os.path.exists(self.main_directory + channel_dir):
            os.makedirs(self.main_directory + channel_dir)

        os.chdir(self.main_directory + channel_dir)
        item.setText(0, channel_title)

        # Download channel logo
        logo_file_big: str = ''
        image_url: str = ''
        if 'image' in feed_content.feed:
            if feed_content.feed.image.href is not None:
                if feed_content.feed.image.href[0] == '/':
                    image_url = feed_content.feed.link + feed_content.feed.image.href
                else:
                    image_url = feed_content.feed.image.href

            url_done = QtCore.QUrl(image_url)
            file_info = QtCore.QFileInfo(url_done.path())
            file_name = file_info.fileName()
            logo_file_big = channel_dir + "/" + file_name

        if is_video_link(new_url):
            image_url = get_cover(new_url)
            logo_file_big = channel_dir + "/" + "logo.jpg"

        if image_url:
            download_image(image_url, self.main_directory + logo_file_big)
            self.ui.resize_image(self.main_directory + logo_file_big, self.main_directory + logo_file_big)

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
        logo_file: str = channel_dir + '/' + favicon_name

        download_image(url, self.main_directory + logo_file)
        self.ui.resize_image(self.main_directory + logo_file, self.main_directory + logo_file)

        item2 = QtWidgets.QTreeWidgetItem(self.ui.tree_widget_downloads)

        if 'title' in feed_content.feed:
            item2.setText(0, feed_content.feed.title)
        else:
            item2.setText(0, "No title")

        item2.setText(1, url)
        item2.setText(5, url)

        if len(self.ui.download_list) > 0:
            download_id: int = self.ui.download_list[-1][0] + 1
        else:
            download_id = 0

        self.ui.items_downloading.append((download_id, url))
        self.ui.download_list.append((download_id, Download(url, item2, download_id, self.ui)))

        self.ui.download_list[download_id][1].favicon_found = True

        if 'subtitle' in feed_content.feed:
            channel_subtitle: str = feed_content.feed.subtitle
        else:
            channel_subtitle = 'No description'

        if 'links' in feed_content.feed:
            channel_homepage: str = feed_content.feed.links[0].href
        else:
            channel_homepage = 'http://google.com'

        new_channel: tuple[str, str, str, str, str, str] = (channel_title, feed_link, channel_homepage, channel_subtitle, logo_file, logo_file_big)
        self.ui.db.insert_channel(new_channel)

        channel_id = self.ui.db.get_channel_by_title(channel_title)

        for episode in feed_content.entries:
            self.add_episode(channel_id[0], episode)

        os.chdir(str(DATA_DIR))

    def add_episode(self, channel_id: int, episode: Any) -> None:
        """Add an episode to the database."""
        new_episode = parse_episode_from_feed_entry(episode, channel_id)
        self.ui.db.insert_episode(tuple(new_episode.values()))
