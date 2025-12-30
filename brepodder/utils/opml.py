import xml.dom.minidom
import xml.sax.saxutils
import os.path
import datetime
import requests

from config import USER_AGENT

class Exporter(object):
    """
    Helper class to export a list of channel objects
    to a local file in OPML 1.1 format.

    See www.opml.org for the OPML specification.
    """

    FEED_TYPE = 'rss'

    def __init__(self, filename):
        if filename.endswith('.opml') or filename.endswith('.xml'):
            self.filename = filename
        else:
            self.filename = '%s.opml' % (filename, )

    def create_node(self, doc, name, content):
        """
        Creates a simple XML Element node in a document
        with tag name "name" and text content "content",
        as in <name>content</name> and returns the element.
        """
        node = doc.createElement(name)
        node.appendChild(doc.createTextNode(content))
        return node

    def create_outline(self, doc, channel):
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

    def write(self, channels):
        """
        Creates a XML document containing metadata for each
        channel object in the "channels" parameter, which
        should be a list of channel objects.

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
        for channel in channels:
            body.appendChild(self.create_outline(doc, channel))
        opml.appendChild(body)

        try:
            with open(self.filename, 'wb') as fp:
                fp.write(doc.toprettyxml(encoding='utf-8'))
        except (IOError, OSError, PermissionError) as e:
            print(f"Could not write OPML file '{self.filename}': {e}")
            return False

        return True


class Importer(object):
    """
    Helper class to import an OPML feed from protocols
    supported by urllib2 (e.g. HTTP) and return a GTK
    ListStore that can be displayed in the GUI.

    This class should support standard OPML feeds and
    contains workarounds to support odeo.com feeds.
    """

    VALID_TYPES = ('rss', 'link')

    def read_url(self, url):
        headers = {
            'User-Agent': USER_AGENT
        }
        try:
            response = requests.get(url, headers=headers)
        except requests.exceptions.ConnectionError as e:
            print('404', e)
            return ''
        except requests.exceptions.HTTPError as e:
            print('404', e)
            return ''
        except requests.exceptions.MissingSchema as e:
            print('MissingSchema', e)
            return ''
        else:
            return response.content

    def __init__(self, url):
        """
        Parses the OPML feed from the given URL into
        a local data structure containing channel metadata.
        """
        self.items = []
        try:
            if os.path.exists(url):
                # assume local filename
                doc = xml.dom.minidom.parse(url)
            else:
                doc = xml.dom.minidom.parseString(self.read_url(url))

            for outline in doc.getElementsByTagName('outline'):
                if outline.getAttribute('type') in self.VALID_TYPES and outline.getAttribute('xmlUrl'):
                    channel = {
                        'url': outline.getAttribute('xmlUrl'),
                        'title': outline.getAttribute('title') or outline.getAttribute('text') or outline.getAttribute('xmlUrl'),
                        'description': outline.getAttribute('text') or outline.getAttribute('xmlUrl'),
                    }

                    if channel['description'] == channel['title']:
                        channel['description'] = channel['url']

                    for attr in ('url', 'title', 'description'):
                        channel[attr] = channel[attr].strip()

                    self.items.append(channel)
            if not len(self.items):
                print('OPML import finished, but no items found: ' + url)
#                log( 'OPML import finished, but no items found: %s', url, sender = self)
        except IndexError:
            print('Cannot import OPML from URL: ' + url)
#            log( 'Cannot import OPML from URL: %s', url, sender = self)

    def format_channel(self, channel):
        return channel
        # return '<b>%s</b>\n<span size="small">%s</span>' % (xml.sax.saxutils.escape(
        #     urllib.unquote_plus(channel['title']))
        #     xml.sax.saxutils.escape(channel['description']), )

    def get_model(self):
        model = []
        for channel in self.items:
            model.append(channel)

        return model
