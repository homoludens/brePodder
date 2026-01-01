"""
Favicon fetching utilities for brePodder.
"""
import requests
import favicon
import os
from typing import Optional

from brepodder.logger import get_logger

logger = get_logger(__name__)


def get_icon_url(url: str) -> Optional[str]:
    """
    Get the favicon URL for a website.

    Args:
        url: The website URL to get the favicon for

    Returns:
        The favicon URL, or None if not found
    """
    try:
        icons = favicon.get(url)
        icon = icons[0]
        return icon.url
    except requests.exceptions.ConnectionError as e:
        logger.debug("Connection error for %s: %s", url, e)
    except IndexError as e:
        logger.debug("No icon found for %s: %s", url, e)
    except requests.exceptions.HTTPError as e:
        logger.debug("HTTP error for %s: %s", url, e)
    except requests.exceptions.MissingSchema as e:
        logger.debug("Missing schema for %s: %s", url, e)
    except requests.exceptions.InvalidURL as e:
        logger.debug("Invalid URL %s: %s", url, e)
    return None


def get_icon(url: str, local_file_name: str) -> None:
    """
    Download a favicon to a local file.

    Args:
        url: The website URL to get the favicon from
        local_file_name: The base filename to save to (extension added automatically)
    """
    logger.debug("get_icon called for: %s", url)
    try:
        icons = favicon.get(url)
        icon = icons[0]
        download_image(url, f'{local_file_name}.{format(icon.format)}')
    except requests.exceptions.HTTPError as e:
        logger.debug("HTTP error for %s: %s", url, e)
    except requests.exceptions.ConnectionError as e:
        logger.debug("Connection error for %s: %s", url, e)
    except requests.exceptions.MissingSchema as e:
        logger.debug("Missing schema for %s: %s", url, e)
    except requests.exceptions.InvalidURL as e:
        logger.debug("Invalid URL %s: %s", url, e)


def download_image(url: str, local_file_path: str) -> None:
    """
    Download an image from a URL to a local file.

    Args:
        url: The image URL to download
        local_file_path: The local path to save the image to
    """
    from brepodder.config import USER_AGENT

    headers = {
        'User-Agent': USER_AGENT
    }

    try:
        response = requests.get(url, stream=True, headers=headers)
    except requests.exceptions.ConnectionError as e:
        logger.debug("Connection error downloading %s: %s", url, e)
        return
    except requests.exceptions.HTTPError as e:
        logger.debug("HTTP error downloading %s: %s", url, e)
        return
    except requests.exceptions.MissingSchema as e:
        logger.debug("Missing schema for %s: %s", url, e)
        return
    except requests.exceptions.InvalidURL as e:
        logger.debug("Invalid URL %s: %s", url, e)
        return
    else:
        if response.status_code == 200:
            with open(local_file_path, 'wb') as image:
                for chunk in response.iter_content(1024):
                    image.write(chunk)
