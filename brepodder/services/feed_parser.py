"""
Feed parsing utilities for extracting episode data from RSS/Atom feeds.
"""
from time import gmtime, mktime
from typing import Any, Optional, Union

from brepodder.logger import get_logger

logger = get_logger(__name__)



def safe_mktime(value) -> Optional[float]:
    """Safely convert to timestamp, return None on failure."""
    try:
        return mktime(value)
    except Exception:
        return None


def get_episode_date(entry: dict) -> float:
    """Extract episode date from entry, trying multiple fields in priority order."""

    # Priority order: published_parsed > published > updated_parsed > updated
    date_fields = ['published_parsed', 'published', 'updated_parsed', 'updated']

    for field in date_fields:
        if field in entry:
            timestamp = safe_mktime(entry[field])
            if timestamp is not None:
                return timestamp
            else:
                entry.pop(field)  # Remove invalid field

    return mktime(gmtime())  # Fallback to now


def parse_episode_from_feed_entry(entry: Any, channel_id: int) -> dict[str, Any]:
    """
    Parse a feed entry and extract episode data.

    Args:
        entry: A feedparser entry object
        channel_id: The database ID of the channel this episode belongs to

    Returns:
        dict: Episode data with keys: title, enclosure, size, date, description, status, channel_id
    """
    new_episode: dict[str, Any] = {
        'title': '',
        'enclosure': '',
        'size': 0,
        'date': '',
        'description': '',
        'status': 'new',
        'channel_id': channel_id
    }

    if 'title' in entry:
        new_episode['title'] = entry['title']

    if 'enclosures' in entry:
        try:
            print(entry['enclosures'][0])
            new_episode['enclosure'] = entry['enclosures'][0]['href']
            new_episode['size'] = entry['enclosures'][0]['length']
        except IndexError:
            pass
        except AttributeError:
            pass

    if 'yt_videoid' in entry:
        try:
            new_episode['enclosure'] = entry['link']
        except AttributeError:
            pass

    new_episode['date'] = get_episode_date(entry)

    if 'summary_detail' in entry:
        try:
            new_episode['description'] = entry['summary_detail']['value']
        except AttributeError:
            pass

    return new_episode


def parse_episode_for_update(entry: Any) -> Optional[dict[str, Any]]:
    """
    Parse a feed entry for channel update operations.

    Args:
        entry: A feedparser entry object

    Returns:
        dict or None: Episode data dict, or None if entry has no title
    """
    if 'title' not in entry:
        logger.debug("Episode entry has no title")
        return None

    new_episode: dict[str, Any] = {}

    if entry['title']:
        new_episode['title'] = entry['title']
    else:
        new_episode['title'] = 'No Title'

    if 'enclosures' in entry:
        try:
            new_episode['enclosure'] = entry['enclosures'][0]['href']
        except (IndexError, AttributeError) as e:
            logger.warning("Failed to parse enclosure href: %s", e)
            new_episode['enclosure'] = "None"

        try:
            new_episode['size'] = int(entry.enclosures[0].length)
        except (IndexError, AttributeError, ValueError, TypeError) as e:
            logger.warning("Failed to parse enclosure size: %s", e)
            new_episode['size'] = '1'
        new_episode['status'] = 'new'
    else:
        new_episode['enclosure'] = 'no file'
        new_episode['size'] = '0'
        new_episode['status'] = 'none'

    if 'summary_detail' in entry:
        new_episode['description'] = entry['summary_detail']['value']
    else:
        new_episode['description'] = 'No description'

    new_episode['date'] = get_episode_date(entry)

    return new_episode


def episode_dict_to_tuple(episode: dict[str, Any]) -> tuple[str, str, Union[int, str], float, str, str, int]:
    """
    Convert an episode dictionary to a tuple for database insertion.

    Args:
        episode: dict with episode data

    Returns:
        tuple: (title, enclosure, size, date, description, status, channel_id)
    """
    return (
        episode['title'],
        episode['enclosure'],
        episode['size'],
        episode['date'],
        episode['description'],
        episode['status'],
        episode['channel_id']
    )
