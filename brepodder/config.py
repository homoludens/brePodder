"""
brePodder Configuration

Centralized configuration constants for the application.
"""

from pathlib import Path

# Application info
APP_NAME = "brePodder"
APP_VERSION = "0.1.0"
USER_AGENT = f"{APP_NAME}/{APP_VERSION}"

# Paths
DATA_DIR = Path.home() / ".brePodder"
DATABASE_FILE = DATA_DIR / "podcasts.sqlite"

# Network settings
REQUEST_TIMEOUT = 10.0
MAX_CONCURRENT_DOWNLOADS = 20

# Database settings
DATABASE_TIMEOUT = 20

# UI settings
EPISODES_PER_PAGE = 50
FOLDER_EPISODES_LIMIT = 150

# Image settings
THUMBNAIL_MAX_SIZE = 300  # pixels (width and height)

# Ensure data directory exists
def ensure_data_dir():
    """Create the data directory if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
