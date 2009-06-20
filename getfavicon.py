def getIcoUrl(url):
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
		print 'ima rezultata'
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
