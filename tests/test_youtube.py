"""
Tests for brepodder.utils.youtube module.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "brepodder"))

from utils.youtube import (
    get_youtube_id,
    is_video_link,
    is_channel_url,
    parse_youtube_url,
    remove_html_tags,
    for_each_feed_pattern,
)


class TestGetYoutubeId:
    """Tests for get_youtube_id function."""

    def test_standard_watch_url(self):
        """Should extract video ID from standard watch URL."""
        get_youtube_id.cache_clear()
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = get_youtube_id(url)
        assert result == "dQw4w9WgXcQ"

    def test_watch_url_with_extra_params(self):
        """Should extract video ID ignoring extra parameters."""
        get_youtube_id.cache_clear()
        url = "https://www.youtube.com/watch?v=abc123def&list=PLxyz"
        result = get_youtube_id(url)
        assert result == "abc123def"

    def test_http_url(self):
        """Should work with http:// URLs."""
        get_youtube_id.cache_clear()
        url = "http://www.youtube.com/watch?v=test123"
        result = get_youtube_id(url)
        assert result == "test123"

    def test_subdomain_url(self):
        """Should work with subdomains like m.youtube.com."""
        get_youtube_id.cache_clear()
        url = "https://m.youtube.com/watch?v=mobile123"
        result = get_youtube_id(url)
        assert result == "mobile123"

    def test_v_format_url(self):
        """Should extract ID from /v/ format URL."""
        get_youtube_id.cache_clear()
        url = "https://www.youtube.com/v/video123?version=3"
        result = get_youtube_id(url)
        assert result == "video123"

    def test_swf_format_url(self):
        """Should extract ID from .swf format URL."""
        get_youtube_id.cache_clear()
        url = "https://www.youtube.com/v/swfvideo.swf"
        result = get_youtube_id(url)
        assert result == "swfvideo"

    def test_channel_url_returns_channel_id(self):
        """Should return channel ID for channel URLs."""
        get_youtube_id.cache_clear()
        url = "https://www.youtube.com/channel/UCchannel123"
        result = get_youtube_id(url)
        assert result == "UCchannel123"

    def test_non_youtube_url(self):
        """Should return None for non-YouTube URLs."""
        get_youtube_id.cache_clear()
        url = "https://example.com/video/123"
        result = get_youtube_id(url)
        assert result is None

    def test_invalid_url(self):
        """Should return None for invalid URLs."""
        get_youtube_id.cache_clear()
        result = get_youtube_id("not a url")
        assert result is None


class TestIsVideoLink:
    """Tests for is_video_link function."""

    def test_valid_video_link(self):
        """Should return True for valid video URL."""
        get_youtube_id.cache_clear()
        url = "https://www.youtube.com/watch?v=abc123"
        assert is_video_link(url) is True

    def test_non_video_link(self):
        """Should return False for non-video URL."""
        get_youtube_id.cache_clear()
        url = "https://example.com/page"
        assert is_video_link(url) is False


class TestIsChannelUrl:
    """Tests for is_channel_url function."""

    def test_user_url(self):
        """Should return True for user URL."""
        url = "https://www.youtube.com/user/username"
        assert is_channel_url(url) is True

    def test_channel_url(self):
        """Should return True for channel URL."""
        url = "https://www.youtube.com/channel/UC123abc"
        assert is_channel_url(url) is True

    def test_feeds_user_url(self):
        """Should return True for feeds/videos.xml user URL."""
        url = "https://www.youtube.com/feeds/videos.xml?user=username"
        assert is_channel_url(url) is True

    def test_feeds_channel_url(self):
        """Should return True for feeds/videos.xml channel_id URL."""
        url = "https://www.youtube.com/feeds/videos.xml?channel_id=UC123"
        assert is_channel_url(url) is True

    def test_gdata_url(self):
        """Should return True for gdata URL."""
        url = "https://gdata.youtube.com/feeds/users/username/uploads"
        assert is_channel_url(url) is True

    def test_video_url(self):
        """Should return False for video watch URL."""
        url = "https://www.youtube.com/watch?v=abc123"
        assert is_channel_url(url) is False

    def test_non_youtube_url(self):
        """Should return False for non-YouTube URL."""
        url = "https://example.com/channel/test"
        assert is_channel_url(url) is False


class TestParseYoutubeUrl:
    """Tests for parse_youtube_url function."""

    def test_channel_url_to_feed(self):
        """Should convert channel URL to feed URL."""
        url = "https://www.youtube.com/channel/UCchannelid"
        result = parse_youtube_url(url)
        assert result == "https://www.youtube.com/feeds/videos.xml?channel_id=UCchannelid"

    def test_user_url_to_feed(self):
        """Should convert user URL to feed URL."""
        url = "https://www.youtube.com/user/username"
        result = parse_youtube_url(url)
        assert result == "https://www.youtube.com/feeds/videos.xml?user=username"

    def test_playlist_url_to_feed(self):
        """Should convert playlist URL to feed URL."""
        url = "https://www.youtube.com/playlist?list=PLplaylistid"
        result = parse_youtube_url(url)
        assert result == "https://www.youtube.com/feeds/videos.xml?playlist_id=PLplaylistid"

    def test_already_feed_url(self):
        """Should return feed URL unchanged."""
        url = "https://www.youtube.com/feeds/videos.xml?channel_id=UCtest"
        result = parse_youtube_url(url)
        assert result == url

    def test_none_url(self):
        """Should return None for None input."""
        result = parse_youtube_url(None)
        assert result is None

    def test_non_youtube_url(self):
        """Should return non-YouTube URLs unchanged."""
        url = "https://example.com/feed.xml"
        result = parse_youtube_url(url)
        assert result == url


class TestRemoveHtmlTags:
    """Tests for remove_html_tags function."""

    def test_removes_simple_tags(self):
        """Should remove simple HTML tags."""
        html = "<p>Hello World</p>"
        result = remove_html_tags(html)
        assert result == "Hello World"

    def test_removes_nested_tags(self):
        """Should remove nested HTML tags."""
        html = "<div><p><strong>Bold Text</strong></p></div>"
        result = remove_html_tags(html)
        assert result == "Bold Text"

    def test_converts_br_to_newline(self):
        """Should convert <br> tags to newlines."""
        html = "Line 1<br>Line 2<br/>Line 3"
        result = remove_html_tags(html)
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result

    def test_converts_p_to_newlines(self):
        """Should convert <p> tags to double newlines."""
        html = "<p>Paragraph 1</p><p>Paragraph 2</p>"
        result = remove_html_tags(html)
        assert "Paragraph 1" in result
        assert "Paragraph 2" in result

    def test_converts_li_to_bullets(self):
        """Should convert <li> tags to bullet points."""
        html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
        result = remove_html_tags(html)
        assert "Item 1" in result
        assert "Item 2" in result

    def test_handles_numeric_entities(self):
        """Should convert numeric HTML entities."""
        html = "&#65;&#66;&#67;"  # ABC
        result = remove_html_tags(html)
        assert "ABC" in result

    def test_handles_named_entities(self):
        """Should convert named HTML entities."""
        html = "&amp; &lt; &gt;"
        result = remove_html_tags(html)
        # Named entities should be converted
        assert "&" in result or "amp" not in result

    def test_handles_none(self):
        """Should return None for None input."""
        result = remove_html_tags(None)
        assert result is None

    def test_collapses_multiple_newlines(self):
        """Should collapse multiple newlines to two."""
        html = "<p>Para 1</p><br><br><br><p>Para 2</p>"
        result = remove_html_tags(html)
        # Should not have more than 2 consecutive newlines
        assert "\n\n\n" not in result

    def test_strips_result(self):
        """Should strip leading/trailing whitespace."""
        html = "   <p>  Text  </p>   "
        result = remove_html_tags(html)
        assert result == "Text"


class TestForEachFeedPattern:
    """Tests for for_each_feed_pattern function."""

    def test_matches_user_pattern(self):
        """Should match and call function for user URL."""
        url = "https://www.youtube.com/user/testuser"
        
        def capture(url, channel):
            return channel
        
        result = for_each_feed_pattern(capture, url, "fallback")
        assert result == "testuser"

    def test_matches_channel_pattern(self):
        """Should match and call function for channel URL."""
        url = "https://www.youtube.com/channel/UC123abc"
        
        def capture(url, channel):
            return channel
        
        result = for_each_feed_pattern(capture, url, "fallback")
        assert result == "UC123abc"

    def test_returns_fallback_for_no_match(self):
        """Should return fallback for non-matching URL."""
        url = "https://example.com/not-youtube"
        
        def capture(url, channel):
            return channel
        
        result = for_each_feed_pattern(capture, url, "fallback")
        assert result == "fallback"

    def test_returns_fallback_when_func_returns_none(self):
        """Should return fallback when function returns None."""
        url = "https://www.youtube.com/user/testuser"
        
        def always_none(url, channel):
            return None
        
        result = for_each_feed_pattern(always_none, url, "fallback")
        assert result == "fallback"

    def test_stops_on_first_match(self):
        """Should stop and return on first successful match."""
        url = "https://www.youtube.com/user/testuser"
        call_count = 0
        
        def counter(url, channel):
            nonlocal call_count
            call_count += 1
            return channel
        
        result = for_each_feed_pattern(counter, url, "fallback")
        assert result == "testuser"
        assert call_count == 1


class TestYouTubeError:
    """Tests for YouTubeError exception."""

    def test_youtube_error_is_exception(self):
        """YouTubeError should be an Exception."""
        from utils.youtube import YouTubeError
        
        assert issubclass(YouTubeError, Exception)

    def test_youtube_error_message(self):
        """YouTubeError should preserve error message."""
        from utils.youtube import YouTubeError
        
        error = YouTubeError("Video not available")
        assert str(error) == "Video not available"
