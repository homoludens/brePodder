"""
Database operations for brePodder.

This module provides thread-safe database access using SQLite.
"""
import sqlite3
import threading
from typing import Any, Optional

from brepodder.config import DATABASE_FILE, DATABASE_TIMEOUT
from brepodder.logger import get_logger

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
        # Create all tables if they don't exist
        self.create_db()

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

    def insert_channel(self, channel: tuple[str, str, str, str, str, str]) -> None:
        """Insert a new channel into the database."""
        self.cur.execute(
            'INSERT INTO sql_channel(title, link, homepage, description, logo, logobig) '
            'VALUES (?,?,?,?,?,?)',
            channel
        )

    def get_folder_channels(self, folder: int) -> list[sqlite3.Row]:
        """Get all channels in a specific folder."""
        self.cur.execute('SELECT * FROM sql_channel WHERE folder_id = ?', (folder,))
        return self.cur.fetchall()

    def get_channel_by_id(self, channel_id: int) -> Optional[dict[str, Any]]:
        """Get a channel by its ID."""
        channel = self.cur.execute(
            'SELECT * FROM sql_channel WHERE id = ?',
            (channel_id,)
        ).fetchone()
        return dict(channel) if channel else None

    def get_channel_by_title(self, channel_title: str) -> Optional[sqlite3.Row]:
        """Get a channel by its title."""
        return self.cur.execute(
            'SELECT * FROM sql_channel WHERE title = ?',
            (channel_title,)
        ).fetchone()

    def get_channel_by_link(self, channel_link: str) -> Optional[sqlite3.Row]:
        """Get a channel by its feed link."""
        return self.cur.execute(
            'SELECT * FROM sql_channel WHERE link = ?',
            (channel_link,)
        ).fetchone()

    def get_channel_by_feed(self, channel: str) -> sqlite3.Cursor:
        """Get a channel by its feed title."""
        return self.cur.execute(
            'SELECT * FROM sql_channel WHERE title = ?',
            (channel,)
        )

    def get_episode_by_title(self, episode_title: str) -> Optional[sqlite3.Row]:
        """Get an episode by its title."""
        return self.cur.execute(
            'SELECT * FROM sql_episode WHERE title = ?',
            (episode_title,)
        ).fetchone()

    def get_all_channels(self) -> list[sqlite3.Row]:
        """Get all channels."""
        return self.cur.execute('SELECT * FROM sql_channel').fetchall()

    def get_all_channels_links(self) -> list[sqlite3.Row]:
        """Get all channel feed links."""
        return self.cur.execute('SELECT link FROM sql_channel').fetchall()

    def get_all_channels_without_folder(self) -> list[sqlite3.Row]:
        """Get all channels that are not in any folder."""
        return self.cur.execute(
            'SELECT * FROM sql_channel WHERE folder_id IS NULL ORDER BY title'
        ).fetchall()

    def is_folder(self, title: str) -> bool:
        """Check if a title corresponds to a folder."""
        test = self.cur.execute(
            "SELECT * FROM sql_taxonomy WHERE title = ?",
            (title,)
        ).fetchall()
        return bool(test)

    def get_folder_episodes(self, channel_title: str) -> list[sqlite3.Row]:
        """Get all episodes from channels in a folder."""
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

    def get_all_folders(self) -> list[sqlite3.Row]:
        """Get all folders ordered by title."""
        return self.cur.execute(
            'SELECT * FROM sql_taxonomy ORDER BY title'
        ).fetchall()

    def get_current_channel(self, channel_title: str) -> tuple[Optional[sqlite3.Row], list[sqlite3.Row]]:
        """Get a channel and its episodes by title."""
        channel = self.get_channel_by_title(channel_title)
        channel_result = self.cur.execute(
            'SELECT id, title, status FROM sql_episode WHERE channel_id = ?',
            (channel[0],)
        )
        result = channel_result.fetchall()
        return channel, result

    def insert_folder(self, folder_name: str) -> bool:
        """Insert a new folder."""
        self.cur.execute(
            'INSERT INTO sql_taxonomy(title) VALUES (?)',
            (folder_name,)
        )
        return True

    def get_latest_downloads(self) -> list[sqlite3.Row]:
        """Get the 50 most recently downloaded episodes."""
        self.cur.execute(
            'SELECT * FROM sql_episode EP, sql_channel CH '
            'WHERE EP.channel_id = CH.id AND EP.status="downloaded" '
            'ORDER BY date DESC LIMIT 50'
        )
        return self.cur.fetchall()

    def get_latest_episodes(self) -> list[sqlite3.Row]:
        """Get the 50 most recent episodes across all channels."""
        self.cur.execute(
            'SELECT * FROM sql_episode EP, sql_channel CH '
            'WHERE EP.channel_id = CH.id ORDER BY date DESC LIMIT 50'
        )
        return self.cur.fetchall()

    def get_channel_episodes(self, channel_title: str) -> list[sqlite3.Row]:
        """Get episodes for a specific channel."""
        self.cur.execute(
            'SELECT * FROM sql_episode EP, sql_channel CH '
            'WHERE EP.channel_id = CH.id AND CH.title = (?) '
            'ORDER BY date DESC LIMIT 50',
            (channel_title,)
        )
        return self.cur.fetchall()

    def insert_episode(self, ep: tuple[str, str, int, str, str, str, int]) -> None:
        """Insert a new episode."""
        self.cur.execute(
            'INSERT INTO sql_episode(title, enclosure, size, date, description, status, channel_id) '
            'VALUES (?,?,?,?,?,?,?)',
            ep
        )

    def update_episode(self, episode: tuple[str, str, int]) -> None:
        """Update an episode's localfile and status."""
        self.cur.execute(
            'UPDATE sql_episode SET localfile = ?, status = ? WHERE id = ?',
            episode
        )

    def update_episode_status(self, episode_id: int) -> None:
        """Mark an episode as 'old'."""
        self.cur.execute(
            'UPDATE sql_episode SET status = "old" WHERE sql_episode.id = ?',
            (episode_id,)
        )
        self.db.commit()

    def delete_all_episodes(self, channel_title: str) -> None:
        """Delete all episodes for a channel."""
        channel_id = self.get_channel_by_title(channel_title)
        try:
            self.cur.execute(
                'DELETE FROM sql_episode WHERE channel_id = ?',
                (channel_id[0],)
            )
        except (sqlite3.Error, TypeError, IndexError) as e:
            logger.error("Failed to delete episodes for channel '%s': %s", channel_title, e)
        self.db.commit()

    def delete_channel(self, channel_title: str) -> None:
        """Delete a channel by title."""
        channel_id = self.get_channel_by_title(channel_title)
        self.cur.execute(
            'DELETE FROM sql_channel WHERE id = ?',
            (channel_id[0],)
        )
        self.db.commit()

    def delete_taxonomy(self, folder_title: str) -> None:
        """Delete a folder by title."""
        self.cur.execute(
            'DELETE FROM sql_taxonomy WHERE title = ?',
            (folder_title,)
        )
        self.db.commit()

    def add_channel_to_folder(self, channel_title: str, folder_title: Optional[str]) -> None:
        """Add a channel to a folder, or remove from folder if folder_title is None."""
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
        """Create all database tables if they don't exist."""
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

        try:
            self.cur.execute('''CREATE TABLE IF NOT EXISTS sql_settings (
                key VARCHAR(60) PRIMARY KEY,
                value TEXT
            )''')
        except sqlite3.OperationalError:
            logger.debug("Table sql_settings already exists")

        try:
            self.cur.execute('''CREATE TABLE IF NOT EXISTS sql_playlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                episode_id INTEGER NOT NULL,
                position INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(episode_id) REFERENCES sql_episode(id)
            )''')
        except sqlite3.OperationalError:
            logger.debug("Table sql_playlist already exists")

        self.db.commit()

    def get_setting(self, key: str) -> Optional[str]:
        """Get a setting value by key."""
        result = self.cur.execute(
            'SELECT value FROM sql_settings WHERE key = ?',
            (key,)
        ).fetchone()
        return result[0] if result else None

    def set_setting(self, key: str, value: str) -> None:
        """Set a setting value (insert or update)."""
        self.cur.execute(
            'INSERT OR REPLACE INTO sql_settings (key, value) VALUES (?, ?)',
            (key, value)
        )
        self.db.commit()

    # Playback position methods
    def get_playback_position(self, episode_id: int) -> int:
        """Get saved playback position for an episode (in seconds)."""
        result = self.cur.execute(
            'SELECT value FROM sql_settings WHERE key = ?',
            (f'playback_pos_{episode_id}',)
        ).fetchone()
        return int(result[0]) if result else 0

    def set_playback_position(self, episode_id: int, position: int) -> None:
        """Save playback position for an episode (in seconds)."""
        self.cur.execute(
            'INSERT OR REPLACE INTO sql_settings (key, value) VALUES (?, ?)',
            (f'playback_pos_{episode_id}', str(position))
        )
        self.db.commit()

    # Playlist methods
    def get_playlist(self) -> list[sqlite3.Row]:
        """Get all episodes in the playlist with their details."""
        return self.cur.execute(
            '''SELECT EP.*, CH.title as channel_title, CH.logo as channel_logo, PL.position as playlist_position
               FROM sql_playlist PL
               JOIN sql_episode EP ON PL.episode_id = EP.id
               JOIN sql_channel CH ON EP.channel_id = CH.id
               ORDER BY PL.id
               LIMIT 50'''
        ).fetchall()

    def add_to_playlist(self, episode_id: int) -> bool:
        """Add an episode to the playlist. Returns False if already in playlist or limit reached."""
        # Check if already in playlist
        exists = self.cur.execute(
            'SELECT id FROM sql_playlist WHERE episode_id = ?',
            (episode_id,)
        ).fetchone()
        if exists:
            return False

        # Check playlist count
        count = self.cur.execute('SELECT COUNT(*) FROM sql_playlist').fetchone()[0]
        if count >= 50:
            return False

        self.cur.execute(
            'INSERT INTO sql_playlist (episode_id, position) VALUES (?, 0)',
            (episode_id,)
        )
        self.db.commit()
        return True

    def remove_from_playlist(self, episode_id: int) -> None:
        """Remove an episode from the playlist."""
        self.cur.execute(
            'DELETE FROM sql_playlist WHERE episode_id = ?',
            (episode_id,)
        )
        self.db.commit()

    def clear_playlist(self) -> None:
        """Remove all episodes from the playlist."""
        self.cur.execute('DELETE FROM sql_playlist')
        self.db.commit()

    def is_in_playlist(self, episode_id: int) -> bool:
        """Check if an episode is in the playlist."""
        result = self.cur.execute(
            'SELECT id FROM sql_playlist WHERE episode_id = ?',
            (episode_id,)
        ).fetchone()
        return result is not None

    # Backward compatibility aliases (deprecated - will be removed in future version)
    # These allow existing code to work while transitioning to new names
    insertChannel = insert_channel
    getFolderChannels = get_folder_channels
    getChannelById = get_channel_by_id
    getChannelByTitle = get_channel_by_title
    getChannelByLink = get_channel_by_link
    getChannelByFeed = get_channel_by_feed
    getEpisodeByTitle = get_episode_by_title
    getAllChannels = get_all_channels
    getAllChannelsLinks = get_all_channels_links
    getAllChannelsWOFolder = get_all_channels_without_folder
    getFolderEpisodes = get_folder_episodes
    getAllFolders = get_all_folders
    getCurrentChannel = get_current_channel
    insertFolder = insert_folder
    getLatestDownloads = get_latest_downloads
    getLatestEpisodes = get_latest_episodes
    getChannelEpisodes = get_channel_episodes
    insertEpisode = insert_episode
    updateEpisode = update_episode
    updateEpisodeStatus = update_episode_status
    deleteAllEpisodes = delete_all_episodes
    deleteChannel = delete_channel
    deleteTaxonomy = delete_taxonomy
    addChannelToFolder = add_channel_to_folder
    getSetting = get_setting
    setSetting = set_setting
    getPlaybackPosition = get_playback_position
    setPlaybackPosition = set_playback_position
    getPlaylist = get_playlist
    addToPlaylist = add_to_playlist
    removeFromPlaylist = remove_from_playlist
    clearPlaylist = clear_playlist
    isInPlaylist = is_in_playlist
