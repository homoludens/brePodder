# should use this: https://github.com/scottwernervt/favicon

from html.parser import HTMLParser
import urllib
import urllib.request
import http.client
import sys

def getIcoUrl(url):
    """
    Get the favicon used for site at url.
    - First try parsing for a favicon link in the html head.
    - Then try just /favicon.ico.
    - If neither found, return None
    """
    print("getIcoUrl(url): ")
    print(url)
    class FaviconFinder(HTMLParser):
        """
        A Parser class for finding the favicon used (if specified).
        """

        def __init__(self, verbose=0):
            self.favicon_url = None

        def start_link(self, attributes):
            attributes = dict(attributes)
            if not self.favicon_url:
                if 'rel' in attributes and 'icon' in attributes['rel']:
                    if 'href' in attributes:
                        self.favicon_url = attributes['href']


    # Try to parse html at url and get favicon
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'http://%s' % url
    
    favicon_parser = FaviconFinder()
    try:
        site = urllib.request.urlopen(url)
        contents = site.read().decode('utf-8')
        favicon_parser.feed(contents)
    except (urllib.error.URLError, urllib.error.HTTPError, UnicodeDecodeError, 
            http.client.HTTPException, OSError) as e:
        print(f"Failed to fetch favicon from {url}: {e}")

    # Another try block in case the parser throws an exception
    # AFTER finding the appropriate url.
    try:
        if favicon_parser.favicon_url:

            if (favicon_parser.favicon_url[0] == '/'):
                imageURL = url + favicon_parser.favicon_url
            else:
                imageURL = favicon_parser.favicon_url

            return imageURL

        else:
            url = '/'.join(url.split('/',3)[2:])
            root_directory = url.split('/')[0]
            favicon = http.client.HTTPConnection(root_directory)
            favicon.request('GET','/favicon.ico')
            response = favicon.getresponse()

            if response.status == 200:
                return 'http://%s/favicon.ico' % root_directory

            favicon = http.client.HTTPConnection('www.' + root_directory)
            favicon.request('GET','/favicon.ico')
            response = favicon.getresponse()

            if response.status == 200:
                return 'http://%s/favicon.ico' % ('www.' + root_directory)
    except (http.client.HTTPException, OSError, AttributeError) as e:
        print(f"Failed to find favicon.ico: {e}")
    return None

