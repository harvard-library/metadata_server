#!/usr/bin/python

import urllib2, requests
import re
from os import environ
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest

oliviaServletBase = environ.get("OLIVIA_SERVLET_BASE", "http://olivia.lib.harvard.edu:9016/olivia/servlet/OliviaServlet?storedProcedure=getRestrictFlag&callingApplication=call1&oliviaUserName=iiif&oracleID=")


def getAccessFlag(drsId):
    oliviaServletURL = oliviaServletBase + drsId	
    req = requests.get(oliviaServletURL)
    regex = re.compile('Restrict Flag: ([A-Z])')
    flag = regex.search(req.text).group(1)
    return flag

def checkCookie(cookies, drsId):
    if 'hulaccess' in cookies:
        return None
    else:  #redirect to AMS
        return oliviaServletBase + drsId

def getAMSredirectUrl(cookies, drsId):
    flag = getAccessFlag(drsId)
    if flag == 'R':
        return checkCookie(cookies, drsId)
    return None
