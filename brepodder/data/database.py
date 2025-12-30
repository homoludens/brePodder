"""
Database operations for brePodder.

This module provides thread-safe database access using SQLite.
"""
import sqlite3
import threading
from typing import Any, Optional

from config import DATABASE_FILE, DATABASE_TIMEOUT
from logger import get_logger

logger = get_logger(__name__)


class DBOperation:
    """
    Thread-safe database operations class.
    Uses thread-local storage to ensure each thread gets its own connection.
    """
    
    _local = threading.local()
    
    def __init__(self) -> None:
        # Initialize main thread connection
        self._get_connection()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get or create a thread-local database connection."""
        if not hasattr(self._local, 'db') or self._local.db is None:
            self._local.db = sqlite3.connect(str(DATABASE_FILE), timeout=DATABASE_TIMEOUT)
            self._local.db.isolation_level = None
            self._local.cur = self._local.db.cursor()
            self._local.cur.row_factory = sqlite3.Row
        return self._local.db
    
    @property
    def db(self) -> sqlite3.Connection:
        """Thread-local database connection."""
        return self._get_connection()
    
    @property
    def cur(self) -> sqlite3.Cursor:
        """Thread-local database cursor."""
        self._get_connection()  # Ensure connection exists
        return self._local.cur

    def close(self) -> None:
        """Close the current thread's database connection."""
        if hasattr(self._local, 'db') and self._local.db is not None:
            self._local.db.commit()
            self._local.cur.close()
            self._local.db.close()
            self._local.db = None
            self._local.cur = None

    def insertChannel(self, channel: tuple[str, str, str, str, str, str]) -> None:
        self.cur.execute(
            'INSERT INTO sql_channel(title, link, homepage, description, logo, logobig) '
            'VALUES (?,?,?,?,?,?)', 
            channel
        )

    def getFolderChannels(self, folder: int) -> list[sqlite3.Row]:
        self.cur.execute('SELECT * FROM sql_channel WHERE folder_id = ?', (folder,))
        return self.cur.fetchall()

    def getChannelById(self, channel_id: int) -> Optional[dict[str, Any]]:
        channel = self.cur.execute(
            'SELECT * FROM sql_channel WHERE id = ?', 
            (channel_id,)
        ).fetchone()
        return dict(channel) if channel else None

    def getChannelByTitle(self, channel_title: str) -> Optional[sqlite3.Row]:
        return self.cur.execute(
            'SELECT * FROM sql_channel WHERE title = ?', 
            (channel_title,)
        ).fetchone()

    def getChannelByLink(self, channel_link: str) -> Optional[sqlite3.Row]:
        return self.cur.execute(
            'SELECT * FROM sql_channel WHERE link = ?', 
            (channel_link,)
        ).fetchone()

    def getChannelByFeed(self, channel: str) -> sqlite3.Cursor:
        return self.cur.execute(
            'SELECT * FROM sql_channel WHERE title = ?', 
            (channel,)
        )

    def getEpisodeByTitle(self, episode_title: str) -> Optional[sqlite3.Row]:
        return self.cur.execute(
            'SELECT * FROM sql_episode WHERE title = ?', 
            (episode_title,)
        ).fetchone()

    def getAllChannels(self) -> list[sqlite3.Row]:
        return self.cur.execute('SELECT * FROM sql_channel').fetchall()

    def getAllChannelsLinks(self) -> list[sqlite3.Row]:
        return self.cur.execute('SELECT link FROM sql_channel').fetchall()

    def getAllChannelsWOFolder(self) -> list[sqlite3.Row]:
        return self.cur.execute(
            'SELECT * FROM sql_channel WHERE folder_id IS NULL ORDER BY title'
        ).fetchall()

    def is_folder(self, title: str) -> bool:
        test = self.cur.execute(
            "SELECT * FROM sql_taxonomy WHERE title = ?", 
            (title,)
        ).fetchall()
        return bool(test)

    def getFolderEpisodes(self, channel_title: str) -> list[sqlite3.Row]:
        query = """
        SELECT EP.id, (CH.title || " - " || EP.title), EP.enclosure, EP.localfile, 
               EP.size, EP.date, EP.description, EP.channel_id 
        FROM sql_episode EP 
        JOIN sql_channel CH ON EP.channel_id = CH.id
        JOIN sql_taxonomy FLD ON CH.folder_id = FLD.id
        WHERE FLD.title = ? 
        ORDER BY date DESC LIMIT 150
        """
        return self.cur.execute(query, (channel_title,)).fetchall()

    def getAllFolders(self) -> list[sqlite3.Row]:
        return self.cur.execute(
            'SELECT * FROM sql_taxonomy ORDER BY title'
        ).fetchall()

    def getCurrentChannel(self, channel_title: str) -> tuple[Optional[sqlite3.Row], list[sqlite3.Row]]:
        channel = self.getChannelByTitle(channel_title)
        channel_result = self.cur.execute(
            'SELECT id, title, status FROM sql_episode WHERE channel_id = ?', 
            (channel[0],)
        )
        result = channel_result.fetchall()
        return channel, result

    def insertFolder(self, folder_name: str) -> bool:
        self.cur.execute(
            'INSERT INTO sql_taxonomy(title) VALUES (?)', 
            (folder_name,)
        )
        return True

    def getLatestDownloads(self) -> list[sqlite3.Row]:
        self.cur.execute(
            'SELECT * FROM sql_episode EP, sql_channel CH '
            'WHERE EP.channel_id = CH.id AND EP.status="downloaded" '
            'ORDER BY date DESC LIMIT 50'
        )
        return self.cur.fetchall()

    def getLatestEpisodes(self) -> list[sqlite3.Row]:
        self.cur.execute(
            'SELECT * FROM sql_episode EP, sql_channel CH '
            'WHERE EP.channel_id = CH.id ORDER BY date DESC LIMIT 50'
        )
        return self.cur.fetchall()

    def getChannelEpisodes(self, channelTitle: str) -> list[sqlite3.Row]:
        self.cur.execute(
            'SELECT * FROM sql_episode EP, sql_channel CH '
            'WHERE EP.channel_id = CH.id AND CH.title = (?) '
            'ORDER BY date DESC LIMIT 50',
            (channelTitle,)
        )
        return self.cur.fetchall()

    def insertEpisode(self, ep: tuple[str, str, int, str, str, str, int]) -> None:
        self.cur.execute(
            'INSERT INTO sql_episode(title, enclosure, size, date, description, status, channel_id) '
            'VALUES (?,?,?,?,?,?,?)',
            ep
        )

    def updateEpisode(self, episode: tuple[str, str, int]) -> None:
        self.cur.execute(
            'UPDATE sql_episode SET localfile = ?, status = ? WHERE id = ?', 
            episode
        )

    def updateEpisodeStatus(self, episodeId: int) -> None:
        self.cur.execute(
            'UPDATE sql_episode SET status = "old" WHERE sql_episode.id = ?', 
            (episodeId,)
        )
        self.db.commit()

    def deleteAllEpisodes(self, channelTitle: str) -> None:
        channel_id = self.getChannelByTitle(channelTitle)
        try:
            self.cur.execute(
                'DELETE FROM sql_episode WHERE channel_id = ?', 
                (channel_id[0],)
            )
        except (sqlite3.Error, TypeError, IndexError) as e:
            logger.error("Failed to delete episodes for channel '%s': %s", channelTitle, e)
        self.db.commit()

    def deleteChannel(self, channelTitle: str) -> None:
        channel_id = self.getChannelByTitle(channelTitle)
        self.cur.execute(
            'DELETE FROM sql_channel WHERE id = ?', 
            (channel_id[0],)
        )
        self.db.commit()

    def deleteTaxonomy(self, folderTitle: str) -> None:
        self.cur.execute(
            'DELETE FROM sql_taxonomy WHERE title = ?', 
            (folderTitle,)
        )
        self.db.commit()

    def addChannelToFolder(self, channel_title: str, folder_title: Optional[str]) -> None:
        self.cur.execute(
            'SELECT id FROM sql_channel WHERE title = ?', 
            [channel_title]
        )
        channel_id = self.cur.fetchone()[0]
        
        if not folder_title:
            self.cur.execute(
                'UPDATE sql_channel SET folder_id = NULL WHERE id = :ch_id', 
                {"ch_id": channel_id}
            )
        else:
            self.cur.execute(
                'SELECT * FROM sql_channel WHERE title = ?', 
                (folder_title,)
            )
            cc = self.cur.fetchone()
            if not cc:
                self.cur.execute(
                    'SELECT id FROM sql_taxonomy WHERE title = ?', 
                    (folder_title,)
                )
                tx_id = self.cur.fetchone()[0]
            else:
                tx_id = cc[7]
            self.cur.execute(
                'UPDATE sql_channel SET folder_id = :tx_id WHERE id = :ch_id', 
                {"tx_id": tx_id, "ch_id": channel_id}
            )
        self.db.commit()

    def create_db(self) -> None:
        try:
            self.cur.execute('''CREATE TABLE IF NOT EXISTS sql_channel (
                id INTEGER NOT NULL,
                title VARCHAR(30),
                link VARCHAR(256),
                homepage VARCHAR(256),
                description VARCHAR(4096),
                logo VARCHAR(256),
                logobig VARCHAR(256),
                folder_id INTEGER,
                folder INTEGER,
                PRIMARY KEY (id)
            )''')
        except sqlite3.OperationalError:
            logger.debug("Table sql_channel already exists")

        try:
            self.cur.execute('''CREATE TABLE IF NOT EXISTS sql_episode (
                id INTEGER NOT NULL,
                title VARCHAR(60),
                enclosure VARCHAR(256),
                localfile VARCHAR(256),
                size INTEGER,
                date VARCHAR(256),
                description VARCHAR(4096),
                status VARCHAR(16),
                channel_id INTEGER,
                PRIMARY KEY (id),
                CONSTRAINT sql_episode_channel_id_fk 
                    FOREIGN KEY(channel_id) REFERENCES sql_channel (id)
            )''')
        except sqlite3.OperationalError:
            logger.debug("Table sql_episode already exists")

        try:
            self.cur.execute('''CREATE TABLE IF NOT EXISTS sql_taxonomy (
                id INTEGER NOT NULL,
                title VARCHAR(60),
                PRIMARY KEY (id)
            )''')
        except sqlite3.OperationalError:
            logger.debug("Table sql_taxonomy already exists")
        
        self.db.commit()
