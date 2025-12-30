"""
Tests for brepodder.config module.
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "brepodder"))

import config


class TestConfigConstants:
    """Test configuration constants."""

    def test_app_name(self):
        """APP_NAME should be 'brePodder'."""
        assert config.APP_NAME == "brePodder"

    def test_app_version_format(self):
        """APP_VERSION should be a semantic version string."""
        parts = config.APP_VERSION.split(".")
        assert len(parts) >= 2
        assert all(part.isdigit() for part in parts)

    def test_user_agent_contains_app_info(self):
        """USER_AGENT should contain app name and version."""
        assert config.APP_NAME in config.USER_AGENT
        assert config.APP_VERSION in config.USER_AGENT

    def test_data_dir_is_path(self):
        """DATA_DIR should be a Path object."""
        assert isinstance(config.DATA_DIR, Path)

    def test_data_dir_in_home(self):
        """DATA_DIR should be under user's home directory."""
        assert str(Path.home()) in str(config.DATA_DIR)

    def test_database_file_is_path(self):
        """DATABASE_FILE should be a Path object."""
        assert isinstance(config.DATABASE_FILE, Path)

    def test_database_file_in_data_dir(self):
        """DATABASE_FILE should be inside DATA_DIR."""
        assert config.DATABASE_FILE.parent == config.DATA_DIR

    def test_database_file_extension(self):
        """DATABASE_FILE should have .sqlite extension."""
        assert config.DATABASE_FILE.suffix == ".sqlite"

    def test_request_timeout_is_positive(self):
        """REQUEST_TIMEOUT should be a positive number."""
        assert config.REQUEST_TIMEOUT > 0

    def test_max_concurrent_downloads_is_positive(self):
        """MAX_CONCURRENT_DOWNLOADS should be a positive integer."""
        assert config.MAX_CONCURRENT_DOWNLOADS > 0
        assert isinstance(config.MAX_CONCURRENT_DOWNLOADS, int)

    def test_database_timeout_is_positive(self):
        """DATABASE_TIMEOUT should be a positive integer."""
        assert config.DATABASE_TIMEOUT > 0
        assert isinstance(config.DATABASE_TIMEOUT, int)

    def test_episodes_per_page_is_positive(self):
        """EPISODES_PER_PAGE should be a positive integer."""
        assert config.EPISODES_PER_PAGE > 0
        assert isinstance(config.EPISODES_PER_PAGE, int)

    def test_folder_episodes_limit_is_positive(self):
        """FOLDER_EPISODES_LIMIT should be a positive integer."""
        assert config.FOLDER_EPISODES_LIMIT > 0
        assert isinstance(config.FOLDER_EPISODES_LIMIT, int)

    def test_thumbnail_max_size_is_positive(self):
        """THUMBNAIL_MAX_SIZE should be a positive integer."""
        assert config.THUMBNAIL_MAX_SIZE > 0
        assert isinstance(config.THUMBNAIL_MAX_SIZE, int)


class TestEnsureDataDir:
    """Test ensure_data_dir function."""

    def test_ensure_data_dir_creates_directory(self, tmp_path, monkeypatch):
        """ensure_data_dir should create the data directory if it doesn't exist."""
        test_dir = tmp_path / ".brePodder_test"
        monkeypatch.setattr(config, "DATA_DIR", test_dir)
        
        assert not test_dir.exists()
        config.ensure_data_dir()
        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_ensure_data_dir_idempotent(self, tmp_path, monkeypatch):
        """ensure_data_dir should not fail if directory already exists."""
        test_dir = tmp_path / ".brePodder_test"
        test_dir.mkdir()
        monkeypatch.setattr(config, "DATA_DIR", test_dir)
        
        # Should not raise
        config.ensure_data_dir()
        assert test_dir.exists()

    def test_ensure_data_dir_creates_parent_dirs(self, tmp_path, monkeypatch):
        """ensure_data_dir should create parent directories if needed."""
        test_dir = tmp_path / "parent" / "child" / ".brePodder_test"
        monkeypatch.setattr(config, "DATA_DIR", test_dir)
        
        config.ensure_data_dir()
        assert test_dir.exists()
