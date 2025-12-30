"""
Shared pytest fixtures for brePodder tests.
"""
import os
import sys
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add brepodder to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "brepodder"))


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def temp_db_path(tmp_path):
    """Provide a temporary database file path."""
    return tmp_path / "test_podcasts.sqlite"


@pytest.fixture
def mock_config(tmp_path, monkeypatch):
    """Mock the config module with temporary paths."""
    db_path = tmp_path / "podcasts.sqlite"
    monkeypatch.setattr("config.DATA_DIR", tmp_path)
    monkeypatch.setattr("config.DATABASE_FILE", db_path)
    return {"DATA_DIR": tmp_path, "DATABASE_FILE": db_path}


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database with the schema."""
    conn = sqlite3.connect(":memory:")
    conn.isolation_level = None
    cur = conn.cursor()
    
    # Create tables
    cur.execute('''CREATE TABLE IF NOT EXISTS sql_channel (
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
    
    cur.execute('''CREATE TABLE IF NOT EXISTS sql_episode (
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
    
    cur.execute('''CREATE TABLE IF NOT EXISTS sql_taxonomy (
        id INTEGER NOT NULL,
        title VARCHAR(60),
        PRIMARY KEY (id)
    )''')
    
    cur.execute('''CREATE TABLE IF NOT EXISTS sql_settings (
        key VARCHAR(60) PRIMARY KEY,
        value TEXT
    )''')
    
    cur.execute('''CREATE TABLE IF NOT EXISTS sql_playlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        episode_id INTEGER NOT NULL,
        position INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY(episode_id) REFERENCES sql_episode(id)
    )''')
    
    conn.commit()
    
    yield conn
    conn.close()


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


@pytest.fixture
def sample_feed_entry():
    """Sample feedparser entry object for testing."""
    entry = MagicMock()
    entry.title = "Test Episode"
    entry.enclosures = [MagicMock(href="https://example.com/episode.mp3", length="12345678")]
    entry.updated_parsed = (2024, 1, 15, 12, 0, 0, 0, 15, 0)
    entry.summary_detail = MagicMock(value="<p>Episode description</p>")
    return entry


@pytest.fixture
def sample_feed_entry_youtube():
    """Sample YouTube feedparser entry for testing."""
    entry = MagicMock()
    entry.title = "YouTube Video Title"
    entry.link = "https://www.youtube.com/watch?v=abc123"
    entry.yt_videoid = "abc123"
    entry.updated_parsed = (2024, 1, 15, 12, 0, 0, 0, 15, 0)
    entry.summary_detail = MagicMock(value="Video description")
    # No enclosures for YouTube
    del entry.enclosures
    return entry


@pytest.fixture
def sample_feed_entry_minimal():
    """Minimal feedparser entry with only title."""
    entry = MagicMock()
    entry.title = "Minimal Episode"
    # Remove optional attributes
    del entry.enclosures
    del entry.updated_parsed
    del entry.published_parsed
    del entry.summary_detail
    return entry


@pytest.fixture
def sample_opml_content():
    """Sample OPML file content for testing."""
    return '''<?xml version="1.0" encoding="utf-8"?>
<opml version="1.1">
    <head>
        <title>Test Subscriptions</title>
    </head>
    <body>
        <outline title="Podcast One" text="First podcast" 
                 xmlUrl="https://example.com/feed1.xml" type="rss"/>
        <outline title="Podcast Two" text="Second podcast" 
                 xmlUrl="https://example.com/feed2.xml" type="rss"/>
    </body>
</opml>'''


@pytest.fixture
def mock_requests_get(mocker):
    """Mock requests.get for network tests."""
    mock = mocker.patch("requests.get")
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.content = b"mock content"
    mock_response.text = "mock text"
    mock.return_value = mock_response
    return mock
