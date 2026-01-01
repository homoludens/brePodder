"""
Background thread classes for updating channels.

These QThread subclasses handle network operations and database updates
in the background to keep the UI responsive.
"""
from PyQt6 import QtCore
from io import BytesIO
import sqlite3
import feedparser
import requests
from typing import Any, Optional, Union

from config import DATA_DIR, DATABASE_FILE, USER_AGENT, REQUEST_TIMEOUT
from logger import get_logger
from services.feed_parser import parse_episode_for_update, episode_dict_to_tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

logger = get_logger(__name__)


# Module-level function (required for multiprocessing)
def parse_feed_content(content_bytes):
    """Parse feed - runs in separate process to avoid GIL."""
    return feedparser.parse(BytesIO(content_bytes))


class UpdateDatabaseThread(QtCore.QThread):
    """
    Thread for updating the database with fetched channel data.

    This runs database operations in a background thread to keep the UI responsive.
    """
    updateDoneSignal = QtCore.pyqtSignal()

    def __init__(self, updated_channels_list: list, db: Any) -> None:
        QtCore.QThread.__init__(self)
        self.updated_channels_list = updated_channels_list
        self.db = db


    def run(self) -> None:
        con = sqlite3.connect(str(DATABASE_FILE), check_same_thread=False)
        con.isolation_level = None
        cur = con.cursor()

        for channel in self.updated_channels_list:
            if channel is None:
                continue
            try:
                logger.debug("Updating channel: %s", channel['channel_feedlink'])
            except (TypeError, KeyError):
                logger.error("Invalid channel data, skipping")
                continue

            ch = channel['channel_row']
            # logger.info("Updating channel: %s", channel.keys())
            feed = channel['feed']

            old_episodes: list[str] = []

            cc = cur.execute('select id, title, link from sql_channel where title =?', (ch['title'],))
            a = cc.fetchone()
            if a is None:
                logger.error("Channel not found in database: %s", ch['title'])
                continue
            tt = cur.execute('select id, title, status from sql_episode where channel_id = ?', (a[0],))

            channel_id = a[0]
            for j in tt:
                old_episodes.append(j[1])

            # logger.info("Updating channel: %s", feed.keys())
            for entry in feed['entries']:
                # logger.info("Updating entry: %s", entry['title'])

                try:
                    aa = old_episodes.index(entry['title'])
                except ValueError:
                    aa = None

                if 'title' in entry and aa is None:
                    new_episode = parse_episode_for_update(entry)
                    if new_episode:
                        new_episode['channel_id'] = channel_id
                        try:
                            cur.execute(
                                'INSERT INTO sql_episode (title, description, enclosure, status, channel_id, date, size) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                episode_dict_to_tuple(new_episode)
                            )
                        except sqlite3.Error as ex:
                            logger.error("Failed to insert episode: %s", ex)

                elif 'title' not in entry:
                    logger.debug("Episode entry has no title")

        con.commit()
        cur.close()
        con.close()

        logger.info("Database update for all channels completed")
        self.updateDoneSignal.emit()


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
        self.update_progress: int = update_progress
        self.new_episode_exists: int = 0
        self.main_directory: str = str(DATA_DIR) + '/'
        self.headers: dict[str, str] = {
            'User-Agent': USER_AGENT
        }

    def run(self) -> None:
        self.ui.semaphore.acquire(1)

        con = sqlite3.connect(str(DATABASE_FILE), check_same_thread=False)
        con.isolation_level = None
        cur = con.cursor()

        self.update_channel(self.channel, cur)

        con.commit()
        cur.close()

        if self.new_episode_exists:
            self.updatesignal.emit()

        self.updateProgressSignal.emit()

        if self.update_progress == 0:
            self.updateDoneSignal.emit()

        self.ui.semaphore.release(1)

    def update_channel(self, ch: Any = None, cursor: Optional[sqlite3.Cursor] = None) -> Optional[str]:
        """Update channel episodes from feed."""
        cur = cursor
        old_episodes: list[str] = []

        if ch is None:
            a, tt = self.ui.db.get_current_channel(self.ui.current_channel[1])
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
                self.new_episode_exists = 1
                new_episode = parse_episode_for_update(entry)
                if new_episode:
                    new_episode['channel_id'] = channel_id
                    self.ui.db.insert_episode(episode_dict_to_tuple(new_episode))

            elif 'title' not in entry:
                logger.debug("Episode entry has no title")
            else:
                if j[2] != 'old':
                    try:
                        self.ui.db.update_episode_status(j[0])
                    except Exception as ex:
                        logger.error("Failed to update episode status: %s, episode: %s", ex, j)
        return None
