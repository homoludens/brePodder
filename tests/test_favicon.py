"""
Tests for brepodder.utils.favicon module.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "brepodder"))

from utils.favicon import get_icon_url, get_icon, download_image


class TestGetIconUrl:
    """Tests for get_icon_url function."""

    def test_returns_icon_url(self, mocker):
        """Should return favicon URL when found."""
        mock_icon = MagicMock()
        mock_icon.url = "https://example.com/favicon.ico"
        mocker.patch("favicon.get", return_value=[mock_icon])
        
        result = get_icon_url("https://example.com")
        
        assert result == "https://example.com/favicon.ico"

    def test_returns_none_on_connection_error(self, mocker):
        """Should return None on connection error."""
        import requests
        mocker.patch("favicon.get", side_effect=requests.exceptions.ConnectionError())
        
        result = get_icon_url("https://example.com")
        
        assert result is None

    def test_returns_none_when_no_icons(self, mocker):
        """Should return None when no icons found."""
        mocker.patch("favicon.get", return_value=[])
        
        result = get_icon_url("https://example.com")
        
        assert result is None

    def test_returns_none_on_http_error(self, mocker):
        """Should return None on HTTP error."""
        import requests
        mocker.patch("favicon.get", side_effect=requests.exceptions.HTTPError())
        
        result = get_icon_url("https://example.com")
        
        assert result is None

    def test_returns_none_on_missing_schema(self, mocker):
        """Should return None on missing schema error."""
        import requests
        mocker.patch("favicon.get", side_effect=requests.exceptions.MissingSchema())
        
        result = get_icon_url("example.com")
        
        assert result is None

    def test_returns_none_on_invalid_url(self, mocker):
        """Should return None on invalid URL error."""
        import requests
        mocker.patch("favicon.get", side_effect=requests.exceptions.InvalidURL())
        
        result = get_icon_url("not://valid")
        
        assert result is None


class TestGetIcon:
    """Tests for get_icon function."""

    def test_downloads_icon(self, mocker, tmp_path):
        """Should download icon to local file."""
        mock_icon = MagicMock()
        mock_icon.url = "https://example.com/favicon.ico"
        mock_icon.format = "ico"
        mocker.patch("favicon.get", return_value=[mock_icon])
        
        mock_download = mocker.patch("utils.favicon.download_image")
        
        get_icon("https://example.com", str(tmp_path / "icon"))
        
        mock_download.assert_called_once()

    def test_handles_http_error(self, mocker):
        """Should handle HTTP error gracefully."""
        import requests
        mocker.patch("favicon.get", side_effect=requests.exceptions.HTTPError())
        
        # Should not raise
        get_icon("https://example.com", "/tmp/icon")

    def test_handles_connection_error(self, mocker):
        """Should handle connection error gracefully."""
        import requests
        mocker.patch("favicon.get", side_effect=requests.exceptions.ConnectionError())
        
        # Should not raise
        get_icon("https://example.com", "/tmp/icon")

    def test_handles_missing_schema(self, mocker):
        """Should handle missing schema error gracefully."""
        import requests
        mocker.patch("favicon.get", side_effect=requests.exceptions.MissingSchema())
        
        # Should not raise
        get_icon("example.com", "/tmp/icon")

    def test_handles_invalid_url(self, mocker):
        """Should handle invalid URL error gracefully."""
        import requests
        mocker.patch("favicon.get", side_effect=requests.exceptions.InvalidURL())
        
        # Should not raise
        get_icon("invalid", "/tmp/icon")


class TestDownloadImage:
    """Tests for download_image function."""

    def test_downloads_image_to_file(self, mocker, tmp_path):
        """Should download image content to file."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content = lambda chunk_size: [b"image data"]
        mocker.patch("requests.get", return_value=mock_response)
        
        output_path = tmp_path / "image.png"
        download_image("https://example.com/image.png", str(output_path))
        
        assert output_path.exists()
        assert output_path.read_bytes() == b"image data"

    def test_downloads_image_in_chunks(self, mocker, tmp_path):
        """Should download image in chunks."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content = lambda chunk_size: [b"chunk1", b"chunk2", b"chunk3"]
        mocker.patch("requests.get", return_value=mock_response)
        
        output_path = tmp_path / "image.png"
        download_image("https://example.com/image.png", str(output_path))
        
        assert output_path.read_bytes() == b"chunk1chunk2chunk3"

    def test_uses_user_agent(self, mocker, tmp_path):
        """Should include User-Agent header."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content = lambda chunk_size: [b"data"]
        mock_get = mocker.patch("requests.get", return_value=mock_response)
        
        output_path = tmp_path / "image.png"
        download_image("https://example.com/image.png", str(output_path))
        
        call_kwargs = mock_get.call_args[1]
        assert "headers" in call_kwargs
        assert "User-Agent" in call_kwargs["headers"]

    def test_skips_on_non_200_status(self, mocker, tmp_path):
        """Should not write file on non-200 status."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mocker.patch("requests.get", return_value=mock_response)
        
        output_path = tmp_path / "image.png"
        download_image("https://example.com/notfound.png", str(output_path))
        
        assert not output_path.exists()

    def test_handles_connection_error(self, mocker, tmp_path):
        """Should handle connection error gracefully."""
        import requests
        mocker.patch("requests.get", side_effect=requests.exceptions.ConnectionError())
        
        output_path = tmp_path / "image.png"
        # Should not raise
        download_image("https://example.com/image.png", str(output_path))
        
        assert not output_path.exists()

    def test_handles_http_error(self, mocker, tmp_path):
        """Should handle HTTP error gracefully."""
        import requests
        mocker.patch("requests.get", side_effect=requests.exceptions.HTTPError())
        
        output_path = tmp_path / "image.png"
        # Should not raise
        download_image("https://example.com/image.png", str(output_path))
        
        assert not output_path.exists()

    def test_handles_missing_schema(self, mocker, tmp_path):
        """Should handle missing schema error gracefully."""
        import requests
        mocker.patch("requests.get", side_effect=requests.exceptions.MissingSchema())
        
        output_path = tmp_path / "image.png"
        # Should not raise
        download_image("example.com/image.png", str(output_path))
        
        assert not output_path.exists()

    def test_handles_invalid_url(self, mocker, tmp_path):
        """Should handle invalid URL error gracefully."""
        import requests
        mocker.patch("requests.get", side_effect=requests.exceptions.InvalidURL())
        
        output_path = tmp_path / "image.png"
        # Should not raise
        download_image("not://valid/image.png", str(output_path))
        
        assert not output_path.exists()

    def test_streams_download(self, mocker, tmp_path):
        """Should use streaming download."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content = lambda chunk_size: [b"data"]
        mock_get = mocker.patch("requests.get", return_value=mock_response)
        
        output_path = tmp_path / "image.png"
        download_image("https://example.com/image.png", str(output_path))
        
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs.get("stream") is True
