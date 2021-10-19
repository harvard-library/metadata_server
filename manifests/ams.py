#!/usr/bin/python

import requests
import re, json
from os import environ
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from django.conf import settings

#replace olivia w/ http://libsearch-elb.lib.harvard.edu:18280/solr/drs2-collection/select?q=object_id_num%3A434603714&fq=doc_type_string%3Aobject+AND+object_huldrsadmin_status_string%3Acurrent+AND+object_huldrsadmin_contentModelID_string%3ACMID-4.0&fl=object_id_num%2C+object_huldrsadmin_accessFlag_string&wt=json&indent=true

amsRedirectBase = environ.get("AMS_REDIRECT_BASE","")
amsRedirectIdsBase = environ.get("AMS_REDIRECT_IDS_BASE","")

def getAccessFlag(drsId):
    solrUrl = settings.SOLR_BASE + settings.SOLR_QUERY_PREFIX + drsId + settings.SOLR_AMS_QUERY 
    solrFileUrl = settings.SOLR_BASE + settings.SOLR_FILE_QUERY_PREFIX + drsId + settings.SOLR_AMS_FILE_QUERY
    req = requests.get(solrUrl)
    if req.status_code == 200:
      md_json = json.loads(req.text)
      numFound = md_json['response']['numFound']
      if (numFound > 0):
         flag = md_json['response']['docs'][0]['object_huldrsadmin_accessFlag_string']
         return flag
      else:
        req = requests.get(solrFileUrl)
        if req.status_code == 200:
          md_json = json.loads(req.text)
          numFound = md_json['response']['numFound']
          if (numFound > 0):
            flag = md_json['response']['docs'][0]['file_huldrsadmin_accessFlag_string']
            return flag
          else:
            return ''
        else:
          return ''
    else:
      return ''

def checkCookie(cookies, drsId, isIDS=False):
	if 'hulaccess' in cookies:
		return None
	else:  #redirect to AMS
		if (isIDS):
			return amsRedirectIdsBase + drsId
	  	else:
			return amsRedirectBase + drsId

def getAMSredirectUrl(cookies, drsId, isIDS=False):
	flag = getAccessFlag(drsId)
	if flag == '':
		return None
	if flag == 'R':
		return ['R', checkCookie(cookies, drsId, isIDS)]
	elif flag == 'N':
		return ['N', None]
	else:
		return ['OK', None]
