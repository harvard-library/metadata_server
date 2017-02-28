#!/usr/bin/python

import urllib2, requests
import re
from os import environ
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from logging import getLogger
logger = getLogger(__name__)

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
    regex2 = re.compile('Is Drs2: ([YN])')
    match = regex.search(req.text)
    match2 = regex2.search(req.text) 
    flag = None
    drs2 = None

    if match2:
	drs2 = match2.group(1)
    if match:
        flag = match.group(1)
    if flag:
	logger.debug("getaccessflag for id " + str(drsId) + ": " + str(flag) + ", " + str(drs2) )
        return [flag, drs2]
    else:
        return ''

def checkCookie(cookies, drsId):
    if 'hulaccess' in cookies:
        return None
    else:  #redirect to AMS
        return amsRedirectBase + drsId

def getAMSredirectUrl(cookies, drsId):
    flag = getAccessFlag(drsId)
    if flag[0] == 'R':
	logger.debug("getAMSredirectUrl for id " + str(drsId) + ": " + "R, " + str(checkCookie(cookies, drsId)) )
        return ['R', flag[1], checkCookie(cookies, drsId)]
    elif flag[0] == 'N':
	logger.debug("getAMSredirectUrl for id " + str(drsId) + ": N, None")
	return ['N', None]
    else:
	logger.debug("getAMSredirectUrl for id " + str(drsId) + ": " + "OK, " + str(flag[1]) )
    	return ['OK', flag[1]]
