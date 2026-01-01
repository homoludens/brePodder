"""
brePodder Configuration

Centralized configuration constants for the application.
"""

from pathlib import Path

# Application info
APP_NAME: str = "brePodder"
APP_VERSION: str = "0.1.0"
USER_AGENT: str = f"{APP_NAME}/{APP_VERSION}"

# Paths
DATA_DIR: Path = Path.home() / ".brePodder"
DATABASE_FILE: Path = DATA_DIR / "podcasts.sqlite"
DEFAULT_OPML_FILE: Path = Path(__file__).parent.parent / "brepodder/resources/brepodder.opml"

# Network settings
REQUEST_TIMEOUT: float = 10.0
MAX_CONCURRENT_DOWNLOADS: int = 20

# Database settings
DATABASE_TIMEOUT: int = 20

# UI settings
EPISODES_PER_PAGE: int = 50
FOLDER_EPISODES_LIMIT: int = 150
DEFAULT_FONT_SIZE: int = 10  # Default application font size in points

# Image settings
THUMBNAIL_MAX_SIZE: int = 300  # pixels (width and height)


def ensure_data_dir() -> None:
    """Create the data directory if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
