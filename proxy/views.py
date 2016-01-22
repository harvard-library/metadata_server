from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from manifests import ams
from manifests import webclient
from os import environ
from logging import getLogger

logger = getLogger(__name__)

WEB_SERVICE_URL = environ['PDS_WS_URL']
methods = {"printpdf": "application/pdf",
           "find": "application/xml",
           "get": "application/xml",
           "related": "application/xml",
           "hasocr": "application/json",
	   "getcaption": "application/json",
           "cite": "application/json"}


# view for proxy url
def proxy(request, method, record_id):
    if not method in methods.keys():
        return HttpResponseForbidden("Method not allowed by proxy")

    ams_cookie = request.COOKIES.get('hulaccess', None)

    return HttpResponse(webclient.get(WEB_SERVICE_URL + method + "/" + record_id + "?" + request.GET.urlencode(), ams_cookie), content_type=methods[method])
