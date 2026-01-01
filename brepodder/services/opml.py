"""
OPML import/export functionality for brePodder.
"""
import xml.dom.minidom
import xml.sax.saxutils
import os.path
import datetime
import requests
from typing import Any, Union, Optional

from brepodder.config import USER_AGENT
from brepodder.logger import get_logger

logger = get_logger(__name__)


class Exporter:
    """
    Helper class to export a list of channel objects
    to a local file in OPML 1.1 format.

    Supports folder structure by nesting channel outlines inside folder outlines.
    See www.opml.org for the OPML specification.
    """

    FEED_TYPE: str = 'rss'

    def __init__(self, filename: str) -> None:
        if filename.endswith('.opml') or filename.endswith('.xml'):
            self.filename = filename
        else:
            self.filename = '%s.opml' % (filename, )

    def create_node(self, doc: xml.dom.minidom.Document, name: str, content: str) -> xml.dom.minidom.Element:
        """
        Creates a simple XML Element node in a document
        with tag name "name" and text content "content",
        as in <name>content</name> and returns the element.
        """
        node = doc.createElement(name)
        node.appendChild(doc.createTextNode(content))
        return node

    def create_outline(self, doc: xml.dom.minidom.Document, channel: tuple[Any, ...]) -> xml.dom.minidom.Element:
        """
        Creates a OPML outline as XML Element node in a
        document for the supplied channel.
        """
        outline = doc.createElement('outline')
        outline.setAttribute('title', channel[1])
        outline.setAttribute('text', channel[4])
        outline.setAttribute('xmlUrl', channel[2])
        outline.setAttribute('type', self.FEED_TYPE)
        return outline

    def create_folder_outline(self, doc: xml.dom.minidom.Document, folder_title: str) -> xml.dom.minidom.Element:
        """
        Creates a folder outline element (no xmlUrl, just contains child channels).
        """
        outline = doc.createElement('outline')
        outline.setAttribute('title', folder_title)
        outline.setAttribute('text', folder_title)
        return outline

    def write(self, channels: list[tuple[Any, ...]], folders: Optional[list[tuple[Any, ...]]] = None,
              get_folder_channels_func: Optional[callable] = None) -> bool:
        """
        Creates a XML document containing metadata for each
        channel object in the "channels" parameter, which
        should be a list of channel objects.

        If folders and get_folder_channels_func are provided, channels will be
        organized into folder outlines in the OPML structure.

        Args:
            channels: List of channels without folders (folder_id is NULL)
            folders: List of folder tuples (id, title)
            get_folder_channels_func: Function to get channels for a folder ID

        Returns True on success or False when there was an
        error writing the file.
        """
        doc = xml.dom.minidom.Document()

        opml = doc.createElement('opml')
        opml.setAttribute('version', '1.1')
        doc.appendChild(opml)

        head = doc.createElement('head')
        head.appendChild(self.create_node(doc, 'title', 'brePodder subscriptions'))
        head.appendChild(self.create_node(doc, 'dateCreated', datetime.datetime.now().ctime()))
        opml.appendChild(head)

        body = doc.createElement('body')

        # Add folders with their channels
        if folders and get_folder_channels_func:
            for folder in folders:
                folder_id = folder[0]
                folder_title = folder[1]
                folder_outline = self.create_folder_outline(doc, folder_title)

                # Get channels in this folder and add as children
                folder_channels = get_folder_channels_func(folder_id)
                for channel in folder_channels:
                    folder_outline.appendChild(self.create_outline(doc, channel))

                body.appendChild(folder_outline)

        # Add channels without folders
        for channel in channels:
            body.appendChild(self.create_outline(doc, channel))

        opml.appendChild(body)

        try:
            with open(self.filename, 'wb') as fp:
                fp.write(doc.toprettyxml(encoding='utf-8'))
        except (IOError, OSError, PermissionError) as e:
            logger.error("Could not write OPML file '%s': %s", self.filename, e)
            return False

        return True


class Importer:
    """
    Helper class to import an OPML feed from protocols
    supported by urllib2 (e.g. HTTP) and return a GTK
    ListStore that can be displayed in the GUI.

    This class should support standard OPML feeds and
    contains workarounds to support odeo.com feeds.
    Supports folder structure by detecting nested outline elements.
    """

    VALID_TYPES: tuple[str, str] = ('rss', 'link')

    def read_url(self, url: str) -> Union[bytes, str]:
        headers = {
            'User-Agent': USER_AGENT
        }
        try:
            response = requests.get(url, headers=headers)
        except requests.exceptions.ConnectionError as e:
            logger.error("Connection error for %s: %s", url, e)
            return ''
        except requests.exceptions.HTTPError as e:
            logger.error("HTTP error for %s: %s", url, e)
            return ''
        except requests.exceptions.MissingSchema as e:
            logger.error("Missing schema for %s: %s", url, e)
            return ''
        else:
            return response.content

    def _is_folder_outline(self, outline: xml.dom.minidom.Element) -> bool:
        """Check if an outline element represents a folder (no xmlUrl attribute)."""
        return not outline.getAttribute('xmlUrl') and outline.hasChildNodes()

    def _parse_channel_outline(self, outline: xml.dom.minidom.Element, folder: Optional[str] = None) -> Optional[dict[str, str]]:
        """Parse a channel outline element into a channel dict."""
        if outline.getAttribute('type') not in self.VALID_TYPES:
            return None
        if not outline.getAttribute('xmlUrl'):
            return None

        channel = {
            'url': outline.getAttribute('xmlUrl'),
            'title': outline.getAttribute('title') or outline.getAttribute('text') or outline.getAttribute('xmlUrl'),
            'description': outline.getAttribute('text') or outline.getAttribute('xmlUrl'),
            'folder': folder,
        }

        if channel['description'] == channel['title']:
            channel['description'] = channel['url']

        for attr in ('url', 'title', 'description'):
            channel[attr] = channel[attr].strip()

        return channel

    def __init__(self, url: str) -> None:
        """
        Parses the OPML feed from the given URL into
        a local data structure containing channel metadata.
        Preserves folder structure if present.
        """
        self.items: list[dict[str, str]] = []
        self.folders: set[str] = set()
        try:
            if os.path.exists(url):
                # assume local filename
                doc = xml.dom.minidom.parse(url)
            else:
                doc = xml.dom.minidom.parseString(self.read_url(url))

            # Find the body element
            body_elements = doc.getElementsByTagName('body')
            if not body_elements:
                logger.warning("No body element found in OPML: %s", url)
                return

            body = body_elements[0]

            # Process top-level outlines
            for outline in body.childNodes:
                if outline.nodeType != xml.dom.minidom.Node.ELEMENT_NODE:
                    continue
                if outline.tagName != 'outline':
                    continue

                if self._is_folder_outline(outline):
                    # This is a folder - get folder name and process children
                    folder_name = outline.getAttribute('title') or outline.getAttribute('text')
                    if folder_name:
                        folder_name = folder_name.strip()
                        self.folders.add(folder_name)

                        # Process child outlines as channels in this folder
                        for child in outline.childNodes:
                            if child.nodeType != xml.dom.minidom.Node.ELEMENT_NODE:
                                continue
                            if child.tagName != 'outline':
                                continue

                            channel = self._parse_channel_outline(child, folder_name)
                            if channel:
                                self.items.append(channel)
                else:
                    # This is a channel without folder
                    channel = self._parse_channel_outline(outline, None)
                    if channel:
                        self.items.append(channel)

            if not len(self.items):
                logger.warning("OPML import finished, but no items found: %s", url)
        except IndexError:
            logger.error("Cannot import OPML from URL: %s", url)

    def get_model(self) -> list[dict[str, str]]:
        model = []
        for channel in self.items:
            model.append(channel)

        return model

    def get_folders(self) -> set[str]:
        """Return the set of folder names found in the OPML file."""
        return self.folders
