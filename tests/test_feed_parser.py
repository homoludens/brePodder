"""
Tests for brepodder.services.feed_parser module.
"""
import sys
from pathlib import Path
from time import gmtime, mktime

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "brepodder"))

from services.feed_parser import (
    parse_episode_from_feed_entry,
    parse_episode_for_update,
    episode_dict_to_tuple,
)


class FeedEntry(dict):
    """
    Mock feedparser entry that supports both attribute access and 'in' checks.
    Feedparser entries work like dicts but also have attribute access.
    """
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
    
    def __setattr__(self, name, value):
        self[name] = value
    
    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


def make_feed_entry(**kwargs):
    """Create a feed entry mock with specified attributes."""
    entry = FeedEntry()
    for key, value in kwargs.items():
        entry[key] = value
    return entry


class Enclosure:
    """Mock enclosure object."""
    def __init__(self, href=None, length=None):
        if href is not None:
            self.href = href
        if length is not None:
            self.length = length


class SummaryDetail:
    """Mock summary_detail object."""
    def __init__(self, value):
        self.value = value


class TestParseEpisodeFromFeedEntry:
    """Tests for parse_episode_from_feed_entry function."""

    def test_basic_parsing(self):
        """Should parse a standard feed entry correctly."""
        entry = make_feed_entry(
            title="Test Episode",
            enclosures=[Enclosure(href="https://example.com/episode.mp3", length="12345678")],
            updated_parsed=(2024, 1, 15, 12, 0, 0, 0, 15, 0),
            summary_detail=SummaryDetail("<p>Episode description</p>")
        )
        
        result = parse_episode_from_feed_entry(entry, channel_id=1)
        
        assert result["title"] == "Test Episode"
        assert result["enclosure"] == "https://example.com/episode.mp3"
        assert result["size"] == "12345678"
        assert result["description"] == "<p>Episode description</p>"
        assert result["status"] == "new"
        assert result["channel_id"] == 1

    def test_youtube_entry(self):
        """Should handle YouTube entries with yt_videoid."""
        entry = make_feed_entry(
            title="YouTube Video Title",
            link="https://www.youtube.com/watch?v=abc123",
            yt_videoid="abc123",
            updated_parsed=(2024, 1, 15, 12, 0, 0, 0, 15, 0),
            summary_detail=SummaryDetail("Video description")
        )
        
        result = parse_episode_from_feed_entry(entry, channel_id=2)
        
        assert result["title"] == "YouTube Video Title"
        assert result["enclosure"] == "https://www.youtube.com/watch?v=abc123"
        assert result["channel_id"] == 2

    def test_missing_title(self):
        """Should handle entry without title."""
        entry = make_feed_entry(
            updated_parsed=gmtime()
        )
        
        result = parse_episode_from_feed_entry(entry, channel_id=1)
        
        assert result["title"] == ""

    def test_missing_enclosures(self):
        """Should handle entry without enclosures."""
        entry = make_feed_entry(
            title="No Enclosure Episode",
            updated_parsed=gmtime(),
            summary_detail=SummaryDetail("Description")
        )
        
        result = parse_episode_from_feed_entry(entry, channel_id=1)
        
        assert result["enclosure"] == ""
        assert result["size"] == 0

    def test_empty_enclosures_list(self):
        """Should handle empty enclosures list."""
        entry = make_feed_entry(
            title="Empty Enclosure Episode",
            enclosures=[],
            updated_parsed=gmtime(),
            summary_detail=SummaryDetail("Description")
        )
        
        result = parse_episode_from_feed_entry(entry, channel_id=1)
        
        assert result["enclosure"] == ""

    def test_published_date_fallback(self):
        """Should use published_parsed if updated_parsed is missing."""
        entry = make_feed_entry(
            title="Episode",
            enclosures=[],
            published_parsed=(2024, 6, 15, 10, 30, 0, 5, 167, 0),
            summary_detail=SummaryDetail("Description")
        )
        
        result = parse_episode_from_feed_entry(entry, channel_id=1)
        
        expected_date = mktime((2024, 6, 15, 10, 30, 0, 5, 167, 0))
        assert result["date"] == expected_date

    def test_current_time_fallback(self):
        """Should use current time if no date fields present."""
        entry = make_feed_entry(
            title="Episode",
            enclosures=[],
            summary_detail=SummaryDetail("Description")
        )
        
        result = parse_episode_from_feed_entry(entry, channel_id=1)
        
        # Date should be close to now (within a few seconds)
        now = mktime(gmtime())
        assert abs(result["date"] - now) < 5

    def test_missing_summary(self):
        """Should handle entry without summary_detail."""
        entry = make_feed_entry(
            title="No Summary Episode",
            enclosures=[],
            updated_parsed=gmtime()
        )
        
        result = parse_episode_from_feed_entry(entry, channel_id=1)
        
        assert result["description"] == ""

    def test_enclosure_without_href(self):
        """Should handle enclosure without href attribute."""
        entry = make_feed_entry(
            title="Episode",
            enclosures=[Enclosure(length="1000")],  # No href
            updated_parsed=gmtime(),
            summary_detail=SummaryDetail("Description")
        )
        
        result = parse_episode_from_feed_entry(entry, channel_id=1)
        
        # Should remain empty due to AttributeError
        assert result["enclosure"] == ""


class TestParseEpisodeForUpdate:
    """Tests for parse_episode_for_update function."""

    def test_basic_parsing(self):
        """Should parse a standard feed entry for update."""
        entry = make_feed_entry(
            title="Test Episode",
            enclosures=[Enclosure(href="https://example.com/episode.mp3", length="12345678")],
            updated="Mon, 15 Jan 2024 12:00:00 GMT",
            updated_parsed=(2024, 1, 15, 12, 0, 0, 0, 15, 0),
            summary_detail=SummaryDetail("<p>Episode description</p>")
        )
        
        result = parse_episode_for_update(entry)
        
        assert result is not None
        assert result["title"] == "Test Episode"
        assert result["enclosure"] == "https://example.com/episode.mp3"
        assert result["status"] == "new"

    def test_returns_none_for_missing_title(self):
        """Should return None if entry has no title field."""
        entry = make_feed_entry(
            enclosures=[]
        )
        
        result = parse_episode_for_update(entry)
        
        assert result is None

    def test_empty_title_gets_default(self):
        """Should use 'No Title' for empty title."""
        entry = make_feed_entry(
            title="",
            enclosures=[],
            summary_detail=SummaryDetail("Description")
        )
        
        result = parse_episode_for_update(entry)
        
        assert result["title"] == "No Title"

    def test_no_enclosures(self):
        """Should handle entry without enclosures."""
        entry = make_feed_entry(
            title="Episode Title",
            summary_detail=SummaryDetail("Description")
        )
        
        result = parse_episode_for_update(entry)
        
        assert result["enclosure"] == "no file"
        assert result["size"] == "0"
        assert result["status"] == "none"

    def test_enclosure_without_href(self):
        """Should handle enclosure missing href."""
        entry = make_feed_entry(
            title="Episode",
            enclosures=[Enclosure(length="1000")],  # No href
            summary_detail=SummaryDetail("Desc")
        )
        
        result = parse_episode_for_update(entry)
        
        assert result["enclosure"] == "None"

    def test_enclosure_with_invalid_size(self):
        """Should handle enclosure with non-numeric size."""
        entry = make_feed_entry(
            title="Episode",
            enclosures=[Enclosure(href="https://example.com/ep.mp3", length="invalid")],
            summary_detail=SummaryDetail("Desc")
        )
        
        result = parse_episode_for_update(entry)
        
        assert result["size"] == "1"

    def test_missing_summary(self):
        """Should use default description when missing."""
        entry = make_feed_entry(
            title="Episode"
        )
        
        result = parse_episode_for_update(entry)
        
        assert result["description"] == "No description"

    def test_updated_date_parsing(self):
        """Should parse updated date correctly."""
        entry = make_feed_entry(
            title="Episode",
            updated="Mon, 15 Jan 2024 12:00:00 GMT",
            updated_parsed=(2024, 1, 15, 12, 0, 0, 0, 15, 0),
            summary_detail=SummaryDetail("Desc")
        )
        
        result = parse_episode_for_update(entry)
        
        expected_date = mktime((2024, 1, 15, 12, 0, 0, 0, 15, 0))
        assert result["date"] == expected_date

    def test_published_date_fallback(self):
        """Should use published date if updated not available."""
        entry = make_feed_entry(
            title="Episode",
            published="Mon, 15 Jan 2024 12:00:00 GMT",
            published_parsed=(2024, 1, 15, 12, 0, 0, 0, 15, 0),
            summary_detail=SummaryDetail("Desc")
        )
        
        result = parse_episode_for_update(entry)
        
        expected_date = mktime((2024, 1, 15, 12, 0, 0, 0, 15, 0))
        assert result["date"] == expected_date


class TestEpisodeDictToTuple:
    """Tests for episode_dict_to_tuple function."""

    def test_converts_to_tuple(self):
        """Should convert episode dict to tuple in correct order."""
        episode = {
            "title": "Test Episode",
            "enclosure": "https://example.com/ep.mp3",
            "size": 12345678,
            "date": 1704067200.0,
            "description": "Episode description",
            "status": "new",
            "channel_id": 1
        }
        
        result = episode_dict_to_tuple(episode)
        
        assert result == (
            "Test Episode",
            "https://example.com/ep.mp3",
            12345678,
            1704067200.0,
            "Episode description",
            "new",
            1
        )

    def test_tuple_order(self):
        """Should return tuple in specific order for DB insertion."""
        episode = {
            "channel_id": 5,
            "status": "downloaded",
            "description": "Desc",
            "date": 1000.0,
            "size": 999,
            "enclosure": "url",
            "title": "Title"
        }
        
        result = episode_dict_to_tuple(episode)
        
        # Order should be: title, enclosure, size, date, description, status, channel_id
        assert result[0] == "Title"
        assert result[1] == "url"
        assert result[2] == 999
        assert result[3] == 1000.0
        assert result[4] == "Desc"
        assert result[5] == "downloaded"
        assert result[6] == 5

    def test_result_is_tuple(self):
        """Should return a tuple type."""
        episode = {
            "title": "T",
            "enclosure": "E",
            "size": 0,
            "date": 0.0,
            "description": "D",
            "status": "S",
            "channel_id": 1
        }
        
        result = episode_dict_to_tuple(episode)
        
        assert isinstance(result, tuple)
        assert len(result) == 7
