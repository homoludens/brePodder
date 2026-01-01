"""
brePodder Logging Configuration

Provides centralized logging setup for the application.
"""

import logging
import sys
from pathlib import Path

from .config import DATA_DIR, APP_NAME


# Log file path
LOG_FILE: Path = DATA_DIR / "brepodder.log"

# Log format
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configure logging for the application.

    Args:
        level: The logging level (default: INFO)
    """
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Get root logger for the app
    root_logger = logging.getLogger(APP_NAME)
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler
    try:
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except (IOError, OSError) as e:
        root_logger.warning(f"Could not create log file: {e}")

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Args:
        name: The module name (typically __name__)

    Returns:
        A logger instance
    """
    return logging.getLogger(f"{APP_NAME}.{name}")
