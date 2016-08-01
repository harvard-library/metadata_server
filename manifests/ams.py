#!/usr/bin/python

import urllib2, requests
import re
from os import environ
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest

oliviaServletBase = environ.get("OLIVIA_SERVLET_BASE", "http://olivia.lib.harvard.edu:9016/olivia/servlet/OliviaServlet?storedProcedure=getRestrictFlagForObject&callingApplication=call1&oliviaUserName=iiif&oracleID=")
oliviaServletBase2 = environ.get("OLIVIA_SERVLET_BASE2","http://olivia.lib.harvard.edu:9016/olivia/servlet/OliviaServlet?storedProcedure=getRestrictFlag&callingApplication=call1&oliviaUserName=iiif&oracleID=");
amsRedirectBase = environ.get("AMS_REDIRECT_BASE","")


def getAccessFlag(drsId):
    oliviaServletURL = oliviaServletBase + drsId	
    oliviaServletURL2 = oliviaServletBase2 + drsId
    req = requests.get(oliviaServletURL)
    if req.status_code != 200: #obj call failed, try file access flag
        req = requests.get(oliviaServletURL2)
    regex = re.compile('Restrict Flag: ([A-Z])')
    match = regex.search(req.text)
    flag = None
    if match:
        flag = match.group(1)
    if flag:
        return flag
    else:
        return ''

def checkCookie(cookies, drsId):
    if 'hulaccess' in cookies:
        return None
    else:  #redirect to AMS
        return amsRedirectBase + drsId

def getAMSredirectUrl(cookies, drsId):
    flag = getAccessFlag(drsId)
    if flag == 'R':
        return checkCookie(cookies, drsId)
    elif flag == 'N':
	return 'N'
    else:
    	return None
