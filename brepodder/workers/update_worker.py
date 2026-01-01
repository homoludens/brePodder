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

from brepodder.config import DATA_DIR, DATABASE_FILE, USER_AGENT, REQUEST_TIMEOUT
from brepodder.logger import get_logger
from brepodder.services.feed_parser import parse_episode_for_update, episode_dict_to_tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

logger = get_logger(__name__)


# Module-level function (required for multiprocessing)
def parse_feed_content(content_bytes):
    """Parse feed - runs in separate process to avoid GIL."""
    return feedparser.parse(BytesIO(content_bytes))


class UpdateDatabaseThread(QtCore.QThread):
    """Thread for updating the database with fetched channel data."""

    updateDoneSignal = QtCore.pyqtSignal()
    progressSignal = QtCore.pyqtSignal(int, int)  # current, total
    channelUpdatedSignal = QtCore.pyqtSignal(str)  # channel name

    def __init__(self, updated_channels_list: list, db: Any) -> None:
        super().__init__()
        self.updated_channels_list = updated_channels_list
        self.db = db

    def run(self) -> None:
        con = sqlite3.connect(str(DATABASE_FILE), check_same_thread=False)
        cur = con.cursor()

        total = len(self.updated_channels_list)
        new_episodes_batch = []

        for idx, channel in enumerate(self.updated_channels_list):
            if channel is None or channel.get('feed') is None:
                continue

            try:
                ch = channel['channel_row']
                feed = channel['feed']
            except (TypeError, KeyError):
                logger.error("Invalid channel data, skipping")
                continue

            # Emit progress
            self.progressSignal.emit(idx + 1, total)
            self.channelUpdatedSignal.emit(ch.get('title', 'Unknown'))

            # Get channel ID
            cur.execute('SELECT id FROM sql_channel WHERE title = ?', (ch['title'],))
            row = cur.fetchone()
            if row is None:
                logger.error("Channel not found in database: %s", ch['title'])
                continue
            channel_id = row[0]

            # Get existing episodes as a SET (O(1) lookup instead of O(n))
            cur.execute('SELECT title FROM sql_episode WHERE channel_id = ?', (channel_id,))
            old_episodes = {row[0] for row in cur.fetchall()}

            # Collect new episodes
            for entry in feed.get('entries', []):
                title = entry.get('title')
                if not title:
                    continue

                if title not in old_episodes:
                    new_episode = parse_episode_for_update(entry)
                    if new_episode:
                        new_episode['channel_id'] = channel_id
                        new_episodes_batch.append(episode_dict_to_tuple(new_episode))

        # Batch insert all new episodes in one transaction
        if new_episodes_batch:
            try:
                cur.executemany(
                    'INSERT INTO sql_episode (title, description, enclosure, status, channel_id, date, size) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?)',
                    new_episodes_batch
                )
                con.commit()
                logger.info("Inserted %d new episodes", len(new_episodes_batch))
            except sqlite3.Error as ex:
                logger.error("Failed to batch insert episodes: %s", ex)
                con.rollback()

        cur.close()
        con.close()

        logger.info("Database update completed")
        self.updateDoneSignal.emit()
