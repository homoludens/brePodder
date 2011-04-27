import sgmllib
import urllib

def getIcoUrl(url):
    """
    Get the favicon used for site at url.
    - First try parsing for a favicon link in the html head.
    - Then try just /favicon.ico.
    - If neither found, return None
    """
    #print url
    class FaviconFinder(sgmllib.SGMLParser):
        """
        A Parser class for finding the favicon used (if specified).
        """
        
        def __init__(self, verbose=0):
            sgmllib.SGMLParser.__init__(self, verbose)
            self.favicon_url = None

        def start_link(self, attributes):
            attributes = dict(attributes)
            if not self.favicon_url:
                if 'rel' in attributes and 'icon' in attributes['rel']:
                    if 'href' in attributes:
                        self.favicon_url = attributes['href']


    # Try to parse html at url and get favicon
    if not url.startswith('http://') or url.startswith('https://'):
        url = 'http://%s' % url
    try:
        site = urllib.urlopen(url)
        contents = site.read()
    
        favicon_parser = FaviconFinder()
        favicon_parser.feed(contents)
    except:
        pass

    # Another try block in case the parser throws an exception
    # AFTER finding the appropriate url.
    try:
        if favicon_parser.favicon_url:
	    
	   if (favicon_parser.favicon_url[0] == '/'):
		imageURL = url +  favicon_parser.favicon_url
	   else:
		imageURL = favicon_parser.favicon_url

           return imageURL

        else:
            url = '/'.join(url.split('/',3)[2:])
            root_directory = url.split('/')[0]
            favicon = httplib.HTTPConnection(root_directory)
            favicon.request('GET','/favicon.ico')
            response = favicon.getresponse()
            if response.status == 200:
                return 'http://%s/favicon.ico' % root_directory
            favicon = httplib.HTTPConnection('www.' + root_directory)
            favicon.request('GET','/favicon.ico')
            response = favicon.getresponse()
            if response.status == 200:
                return 'http://%s/favicon.ico' % ('www.' + root_directory)
    except:
        pass
    return None






def getIcoUrl_OLD(url):
	import urllib
	import urlparse
	import re
	"""Return the URL of the favourite icon associated with input.
	Returns None if input isn't a valid address."""
	try:
		fp = urllib.urlopen(url)
	except IOError, e:
		print 'greska'
		if e[1] == "unknown url type":
		# The given URL isn't a web address so adding
		# /favicon.ico won't work. Might as well
		# jump straight to giving up
			return None
#else:
	if fp.headers['content-type'].startswith('text/html') or fp.headers['content-type'].startswith('application/xhtml+xml'):
		data = fp.read()
		fp.close()
		# Try to find any links to shortcut icons
		#ICONREGEX = "<link rel="shortcut icon" (?:.*)href=(?:['|"])(.[^'|"|\s]{0,})(?:['|"])(?:.*)>"
		ICONREGEX = "<link rel=\"shortcut\ icon\" (?:.*?)href=(?:['|\"])(.[^'|\"|\s]{0,})(?:['|\"])(?:.*)/>"
		results = re.search(ICONREGEX, data, re.I)
	if results != None:
		# Found the requested URL of the favourite icon
		icourl = results.groups()[0]
        # the base url is already known to be valid, so we
		# don't need to check that the join works.
		# If the icon's url is invalid, we'll let
		# loadResizeImage handle the inability to retrieve it
		return urlparse.urljoin(url, icourl)
	else:
		print 'nema reziltata'
		fp.close()
		# Return the default of url/favicon.ico
		return urlparse.urljoin(url, '/favicon.ico')
