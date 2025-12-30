"""
Tests for brepodder.data.database module.
"""
import importlib
import sqlite3
import sys
import threading
from pathlib import Path
import uuid

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "brepodder"))


@pytest.fixture
def db_op(tmp_path, monkeypatch):
    """Create an isolated DBOperation instance with a unique temp database."""
    # Use unique name to ensure test isolation
    db_path = tmp_path / f"test_{uuid.uuid4().hex}.sqlite"
    
    # Patch config BEFORE importing database module
    import config
    monkeypatch.setattr(config, "DATABASE_FILE", db_path)
    monkeypatch.setattr(config, "DATABASE_TIMEOUT", 20)
    
    # Force reimport of the database module to get fresh class
    if "data.database" in sys.modules:
        del sys.modules["data.database"]
    
    from data.database import DBOperation
    
    db = DBOperation()
    db.create_db()
    yield db
    db.close()


@pytest.fixture
def sample_channel():
    """Sample channel data for testing."""
    return (
        "Test Podcast",
        "https://example.com/feed.xml",
        "https://example.com",
        "A test podcast description",
        "https://example.com/logo.png",
        "https://example.com/logo_big.png"
    )


@pytest.fixture
def sample_episode():
    """Sample episode data for testing."""
    return (
        "Test Episode Title",
        "https://example.com/episode1.mp3",
        12345678,
        1704067200.0,  # 2024-01-01 00:00:00 UTC
        "This is a test episode description",
        "new",
        1  # channel_id
    )


class TestDBOperationWithInMemoryDB:
    """Tests for DBOperation using in-memory database."""

    def test_create_db_creates_tables(self, db_op):
        """Should create all required tables."""
        # Check tables exist
        tables = db_op.cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t[0] for t in tables]
        
        assert "sql_channel" in table_names
        assert "sql_episode" in table_names
        assert "sql_taxonomy" in table_names
        assert "sql_settings" in table_names
        assert "sql_playlist" in table_names

    def test_insert_channel(self, db_op, sample_channel):
        """Should insert a channel into the database."""
        db_op.insert_channel(sample_channel)
        
        result = db_op.get_all_channels()
        assert len(result) == 1
        assert result[0]["title"] == "Test Podcast"

    def test_get_channel_by_id(self, db_op, sample_channel):
        """Should retrieve channel by ID."""
        db_op.insert_channel(sample_channel)
        
        result = db_op.get_channel_by_id(1)
        
        assert result is not None
        assert result["title"] == "Test Podcast"
        assert result["link"] == "https://example.com/feed.xml"

    def test_get_channel_by_id_not_found(self, db_op):
        """Should return None for non-existent channel ID."""
        result = db_op.get_channel_by_id(999)
        assert result is None

    def test_get_channel_by_title(self, db_op, sample_channel):
        """Should retrieve channel by title."""
        db_op.insert_channel(sample_channel)
        
        result = db_op.get_channel_by_title("Test Podcast")
        
        assert result is not None
        assert result["link"] == "https://example.com/feed.xml"

    def test_get_channel_by_title_not_found(self, db_op):
        """Should return None for non-existent title."""
        result = db_op.get_channel_by_title("Nonexistent Podcast")
        assert result is None

    def test_get_channel_by_link(self, db_op, sample_channel):
        """Should retrieve channel by link."""
        db_op.insert_channel(sample_channel)
        
        result = db_op.get_channel_by_link("https://example.com/feed.xml")
        
        assert result is not None
        assert result["title"] == "Test Podcast"

    def test_get_all_channels(self, db_op, sample_channel):
        """Should retrieve all channels."""
        db_op.insert_channel(sample_channel)
        db_op.insert_channel((
            "Second Podcast",
            "https://example2.com/feed.xml",
            "https://example2.com",
            "Another podcast",
            "logo2.png",
            "logobig2.png"
        ))
        
        result = db_op.get_all_channels()
        
        assert len(result) == 2

    def test_delete_channel(self, db_op, sample_channel):
        """Should delete a channel by title."""
        db_op.insert_channel(sample_channel)
        assert len(db_op.get_all_channels()) == 1
        
        db_op.delete_channel("Test Podcast")
        
        assert len(db_op.get_all_channels()) == 0

    def test_insert_episode(self, db_op, sample_channel, sample_episode):
        """Should insert an episode into the database."""
        db_op.insert_channel(sample_channel)
        db_op.insert_episode(sample_episode)
        
        result = db_op.get_channel_episodes("Test Podcast")
        assert len(result) == 1
        assert result[0]["title"] == "Test Episode Title"

    def test_update_episode(self, db_op, sample_channel, sample_episode):
        """Should update episode localfile and status."""
        db_op.insert_channel(sample_channel)
        db_op.insert_episode(sample_episode)
        
        db_op.update_episode(("/path/to/local.mp3", "downloaded", 1))
        
        episode = db_op.get_episode_by_title("Test Episode Title")
        assert episode["localfile"] == "/path/to/local.mp3"
        assert episode["status"] == "downloaded"

    def test_update_episode_status(self, db_op, sample_channel, sample_episode):
        """Should update episode status to 'old'."""
        db_op.insert_channel(sample_channel)
        db_op.insert_episode(sample_episode)
        
        db_op.update_episode_status(1)
        
        episode = db_op.get_episode_by_title("Test Episode Title")
        assert episode["status"] == "old"

    def test_delete_all_episodes(self, db_op, sample_channel, sample_episode):
        """Should delete all episodes for a channel."""
        db_op.insert_channel(sample_channel)
        db_op.insert_episode(sample_episode)
        db_op.insert_episode((
            "Second Episode",
            "https://example.com/ep2.mp3",
            9999,
            1704153600.0,
            "Second episode desc",
            "new",
            1
        ))
        
        assert len(db_op.get_channel_episodes("Test Podcast")) == 2
        
        db_op.delete_all_episodes("Test Podcast")
        
        assert len(db_op.get_channel_episodes("Test Podcast")) == 0

    def test_get_latest_episodes(self, db_op, sample_channel, sample_episode):
        """Should get latest episodes across all channels."""
        db_op.insert_channel(sample_channel)
        db_op.insert_episode(sample_episode)
        
        result = db_op.get_latest_episodes()
        
        assert len(result) >= 1

    def test_get_latest_downloads(self, db_op, sample_channel):
        """Should get only downloaded episodes."""
        db_op.insert_channel(sample_channel)
        db_op.insert_episode((
            "Downloaded Episode",
            "https://example.com/ep.mp3",
            12345,
            1704067200.0,
            "Desc",
            "downloaded",
            1
        ))
        db_op.insert_episode((
            "New Episode",
            "https://example.com/ep2.mp3",
            12345,
            1704067200.0,
            "Desc",
            "new",
            1
        ))
        
        result = db_op.get_latest_downloads()
        
        assert len(result) == 1
        assert result[0]["title"] == "Downloaded Episode"

    def test_insert_folder(self, db_op):
        """Should insert a folder."""
        result = db_op.insert_folder("My Podcasts")
        
        assert result is True
        folders = db_op.get_all_folders()
        assert len(folders) == 1
        assert folders[0]["title"] == "My Podcasts"

    def test_get_all_folders(self, db_op):
        """Should get all folders ordered by title."""
        db_op.insert_folder("Zebra Folder")
        db_op.insert_folder("Alpha Folder")
        db_op.insert_folder("Middle Folder")
        
        folders = db_op.get_all_folders()
        
        assert len(folders) == 3
        assert folders[0]["title"] == "Alpha Folder"
        assert folders[1]["title"] == "Middle Folder"
        assert folders[2]["title"] == "Zebra Folder"

    def test_delete_taxonomy(self, db_op):
        """Should delete a folder by title."""
        db_op.insert_folder("To Delete")
        assert len(db_op.get_all_folders()) == 1
        
        db_op.delete_taxonomy("To Delete")
        
        assert len(db_op.get_all_folders()) == 0

    def test_is_folder(self, db_op):
        """Should return True for existing folder."""
        db_op.insert_folder("Test Folder")
        
        assert db_op.is_folder("Test Folder") is True
        assert db_op.is_folder("Nonexistent") is False

    def test_add_channel_to_folder(self, db_op, sample_channel):
        """Should add a channel to a folder."""
        db_op.insert_channel(sample_channel)
        db_op.insert_folder("My Folder")
        
        db_op.add_channel_to_folder("Test Podcast", "My Folder")
        
        channels = db_op.get_folder_channels(1)
        assert len(channels) == 1
        assert channels[0]["title"] == "Test Podcast"

    def test_add_channel_to_no_folder(self, db_op, sample_channel):
        """Should remove channel from folder when folder_title is None."""
        db_op.insert_channel(sample_channel)
        db_op.insert_folder("My Folder")
        db_op.add_channel_to_folder("Test Podcast", "My Folder")
        
        db_op.add_channel_to_folder("Test Podcast", None)
        
        channels = db_op.get_folder_channels(1)
        assert len(channels) == 0

    def test_get_all_channels_without_folder(self, db_op, sample_channel):
        """Should get channels not in any folder."""
        db_op.insert_channel(sample_channel)
        db_op.insert_channel((
            "Foldered Podcast",
            "https://example2.com/feed.xml",
            "https://example2.com",
            "Description",
            "logo.png",
            "logobig.png"
        ))
        db_op.insert_folder("Folder")
        db_op.add_channel_to_folder("Foldered Podcast", "Folder")
        
        result = db_op.get_all_channels_without_folder()
        
        assert len(result) == 1
        assert result[0]["title"] == "Test Podcast"


class TestSettings:
    """Tests for settings operations."""

    def test_set_and_get_setting(self, db_op):
        """Should store and retrieve a setting."""
        db_op.set_setting("theme", "dark")
        
        result = db_op.get_setting("theme")
        
        assert result == "dark"

    def test_get_nonexistent_setting(self, db_op):
        """Should return None for nonexistent setting."""
        result = db_op.get_setting("nonexistent")
        assert result is None

    def test_update_existing_setting(self, db_op):
        """Should update an existing setting."""
        db_op.set_setting("volume", "50")
        db_op.set_setting("volume", "75")
        
        result = db_op.get_setting("volume")
        
        assert result == "75"

    def test_set_playback_position(self, db_op):
        """Should store playback position for episode."""
        db_op.set_playback_position(episode_id=42, position=3600)
        
        result = db_op.get_playback_position(42)
        
        assert result == 3600

    def test_get_default_playback_position(self, db_op):
        """Should return 0 for episode without saved position."""
        result = db_op.get_playback_position(999)
        assert result == 0


class TestPlaylist:
    """Tests for playlist operations."""

    def test_add_to_playlist(self, db_op, sample_channel, sample_episode):
        """Should add episode to playlist."""
        db_op.insert_channel(sample_channel)
        db_op.insert_episode(sample_episode)
        
        result = db_op.add_to_playlist(1)
        
        assert result is True
        assert db_op.is_in_playlist(1) is True

    def test_add_duplicate_to_playlist(self, db_op, sample_channel, sample_episode):
        """Should return False when adding duplicate."""
        db_op.insert_channel(sample_channel)
        db_op.insert_episode(sample_episode)
        db_op.add_to_playlist(1)
        
        result = db_op.add_to_playlist(1)
        
        assert result is False

    def test_is_in_playlist(self, db_op, sample_channel, sample_episode):
        """Should check if episode is in playlist."""
        db_op.insert_channel(sample_channel)
        db_op.insert_episode(sample_episode)
        
        assert db_op.is_in_playlist(1) is False
        
        db_op.add_to_playlist(1)
        
        assert db_op.is_in_playlist(1) is True

    def test_remove_from_playlist(self, db_op, sample_channel, sample_episode):
        """Should remove episode from playlist."""
        db_op.insert_channel(sample_channel)
        db_op.insert_episode(sample_episode)
        db_op.add_to_playlist(1)
        
        db_op.remove_from_playlist(1)
        
        assert db_op.is_in_playlist(1) is False

    def test_clear_playlist(self, db_op, sample_channel, sample_episode):
        """Should remove all episodes from playlist."""
        db_op.insert_channel(sample_channel)
        db_op.insert_episode(sample_episode)
        db_op.insert_episode((
            "Episode 2",
            "https://example.com/ep2.mp3",
            1000,
            1704067200.0,
            "Desc",
            "new",
            1
        ))
        db_op.add_to_playlist(1)
        db_op.add_to_playlist(2)
        
        db_op.clear_playlist()
        
        assert db_op.is_in_playlist(1) is False
        assert db_op.is_in_playlist(2) is False

    def test_get_playlist(self, db_op, sample_channel, sample_episode):
        """Should get playlist with episode details."""
        db_op.insert_channel(sample_channel)
        db_op.insert_episode(sample_episode)
        db_op.add_to_playlist(1)
        
        playlist = db_op.get_playlist()
        
        assert len(playlist) == 1
        assert playlist[0]["title"] == "Test Episode Title"
        assert playlist[0]["channel_title"] == "Test Podcast"

    def test_playlist_limit(self, db_op, sample_channel):
        """Should respect playlist limit of 50."""
        db_op.insert_channel(sample_channel)
        
        # Insert 51 episodes and try to add them all
        for i in range(51):
            db_op.insert_episode((
                f"Episode {i}",
                f"https://example.com/ep{i}.mp3",
                1000,
                1704067200.0 + i,
                "Desc",
                "new",
                1
            ))
        
        # Add first 50
        for i in range(1, 51):
            db_op.add_to_playlist(i)
        
        # 51st should fail
        result = db_op.add_to_playlist(51)
        
        assert result is False


class TestThreadSafety:
    """Tests for thread-safe database access."""

    def test_thread_local_connections(self, tmp_path, monkeypatch):
        """Should use separate connections per thread."""
        db_path = tmp_path / f"thread_test_{uuid.uuid4().hex}.sqlite"
        
        import config
        monkeypatch.setattr(config, "DATABASE_FILE", db_path)
        monkeypatch.setattr(config, "DATABASE_TIMEOUT", 20)
        
        # Force reimport
        if "data.database" in sys.modules:
            del sys.modules["data.database"]
        
        from data.database import DBOperation
        
        db = DBOperation()
        db.create_db()
        
        connection_ids = []
        
        def worker():
            # Each thread should get its own connection
            conn_id = id(db.db)
            connection_ids.append(conn_id)
        
        threads = [threading.Thread(target=worker) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All connection IDs should be different
        assert len(set(connection_ids)) == 3
        
        db.close()

    def test_close_cleans_up_connection(self, tmp_path, monkeypatch):
        """Should clean up thread-local connection on close."""
        db_path = tmp_path / f"close_test_{uuid.uuid4().hex}.sqlite"
        
        import config
        monkeypatch.setattr(config, "DATABASE_FILE", db_path)
        monkeypatch.setattr(config, "DATABASE_TIMEOUT", 20)
        
        # Force reimport
        if "data.database" in sys.modules:
            del sys.modules["data.database"]
        
        from data.database import DBOperation
        
        db = DBOperation()
        db.create_db()
        
        # Access to ensure connection is created
        _ = db.db
        
        db.close()
        
        # After close, _local.db should be None
        assert not hasattr(db._local, 'db') or db._local.db is None
