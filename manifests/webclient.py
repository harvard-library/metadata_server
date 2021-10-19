#!/usr/bin/python

import urllib

def get(url, cookie_value=None):
    opener = urllib.request.build_opener()
    if cookie_value:
        opener.addheaders.append(('Cookie', 'hulaccess='+cookie_value))
    response = opener.open(url)
    return response
