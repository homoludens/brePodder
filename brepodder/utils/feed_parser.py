"""
Feed parsing utilities for extracting episode data from RSS/Atom feeds.
"""
from time import gmtime, mktime
from logger import get_logger

logger = get_logger(__name__)


def parse_episode_from_feed_entry(entry, channel_id):
    """
    Parse a feed entry and extract episode data.
    
    Args:
        entry: A feedparser entry object
        channel_id: The database ID of the channel this episode belongs to
        
    Returns:
        dict: Episode data with keys: title, enclosure, size, date, description, status, channel_id
    """
    new_episode = {
        'title': '',
        'enclosure': '',
        'size': 0,
        'date': '',
        'description': '',
        'status': 'new',
        'channel_id': channel_id
    }

    if 'title' in entry:
        new_episode['title'] = entry.title

    if 'enclosures' in entry:
        try:
            new_episode['enclosure'] = entry.enclosures[0].href
            new_episode['size'] = entry.enclosures[0].length
        except IndexError:
            pass
        except AttributeError:
            pass

    if 'yt_videoid' in entry:
        try:
            new_episode['enclosure'] = entry.link
        except AttributeError:
            pass

    if 'updated_parsed' in entry:
        new_episode['date'] = mktime(entry.updated_parsed)
    elif 'published_parsed' in entry:
        new_episode['date'] = mktime(entry.published_parsed)
    else:
        new_episode['date'] = mktime(gmtime())

    if 'summary_detail' in entry:
        try:
            new_episode['description'] = entry.summary_detail.value
        except AttributeError:
            pass

    return new_episode


def parse_episode_for_update(entry):
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
        
    new_episode = {}
    
    if entry.title:
        new_episode['title'] = entry.title
    else:
        new_episode['title'] = 'No Title'
        
    if 'enclosures' in entry:
        try:
            new_episode['enclosure'] = entry.enclosures[0].href
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
        new_episode['description'] = entry.summary_detail.value
    else:
        new_episode['description'] = 'No description'

    episode_date = mktime(gmtime())
    if 'updated' in entry:
        if entry.updated_parsed:
            episode_date = mktime(entry.updated_parsed)
    elif 'published' in entry:
        episode_date = mktime(entry.published_parsed)

    new_episode['date'] = episode_date
    
    return new_episode


def episode_dict_to_tuple(episode):
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
