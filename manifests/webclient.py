#!/usr/bin/python

import urllib2

from logging import getLogger
logger = getLogger(__name__)
from timeit import default_timer as timer

def get(url, cookie_value=None):
    start = timer()
    opener = urllib2.build_opener()
    if cookie_value:
        opener.addheaders.append(('Cookie', 'hulaccess='+cookie_value))
    response = opener.open(url)
    end = timer()
    elapsed = end - start
    logger.debug("elapsed time for " + unicode(url) + " " + unicode(str(elapsed)) + " secs")
    return response
