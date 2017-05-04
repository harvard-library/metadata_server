from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from os import environ
import re
import json
import requests
import base64
from logging import getLogger
logger = getLogger(__name__)
from netaddr import IPNetwork, IPAddress, all_matching_cidrs
from django.conf import settings

# Create your views here.

IIIF_MGMT_ACL = (environ.get("IIIF_MGMT_ACL","128.103.151.0/24,10.34.5.254,10.40.4.69")).split(',')
IIIF_MANIFEST_HOST = environ.get("IIIF_MANIFEST_HOST")

sources = {"drs": "mets", "via": "mods", "hollis": "mods", "huam" : "huam", "ext":"ext"}


def index(request):
  res = None
  if request.method == "OPTIONS":
    do_options(request)
  if request.method == "POST":
    do_post(request)
  if request.method == "GET":
    do_get(request)


def do_options(request):
  response = HttpResponse()
  response['Allow'] = [ "GET", "HEAD", "OPTIONS", "POST" ]
  response['Accept-Post'] = "application/ld+json"
  response.status_code = 200
  return response


def do_get(request):
  response = HttpResponse("stub get response", status=200)
  return response


def do_post(request):
  response = HttpResponse("stub post response", status=200)
  return response
