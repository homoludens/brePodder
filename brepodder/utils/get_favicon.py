import requests
import favicon
import os
from logger import get_logger

logger = get_logger(__name__)


def get_icon_url(url):
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


def get_icon(url, local_file_name):
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


def download_image(url, local_file_path):
    headers = {
        'User-Agent': 'brePodder/0.02'
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
