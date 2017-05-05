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
from django.views.decorators.csrf import csrf_exempt
from inbox import models
from hashids import Hashids
from time import time
from inbox import models

# Create your views here.

IIIF_MGMT_ACL = (environ.get("IIIF_MGMT_ACL","128.103.151.0/24,10.34.5.254,10.40.4.69")).split(',')
IIIF_MANIFEST_HOST = environ.get("IIIF_MANIFEST_HOST", "localhost")
INBOX_BASE_URL = "https://" + IIIF_MANIFEST_HOST + "/inbox/"
DOC_TYPE ="notification"
sources = {"drs": "mets", "via": "mods", "hollis": "mods", "huam" : "huam", "ext":"ext"}


@csrf_exempt
def index(request):
  res = None
  if request.method == "OPTIONS":
    res = do_options(request)
  if request.method == "POST":
    res = do_post(request)
  if request.method == "GET":
    res = do_get(request)
  return res


def do_options(request):
  response = HttpResponse()
  response['Allow'] = [ "GET", "HEAD", "OPTIONS", "POST" ]
  response['Accept-Post'] = "application/ld+json"
  response.status_code = 200
  return response


def do_get(request):
  #list all of the notifications in the inbox
  all_ids = models.get_all_notification_ids()
  contains = map (lambda x: INBOX_BASE_URL + x, all_ids) 
  resp_json = {
    "@context": "http://www.w3.org/ns/ldp",
    "@id": "http://example.org/inbox/",
    "contains": contains
  }
  output = json.dumps(resp_json, indent=4, sort_keys=True)
  response = HttpResponse(output, status=200)
  response['Content-Type'] = "application/ld+json"
  response['Content-Language'] = "en" 
  return response

@csrf_exempt
def do_post(request):
  document=json.loads(request.body)
  target = document['target']
  target_id = target[target.rfind('/')+1:]
  parts = parse_id(target_id)
  drs_id = parts["id"]
  source = parts["source"]
  try:
    notification_id = generate_uid(drs_id)
  except:
    return HttpResponse("Invalid target %s \n" % drs_id, status=500)

  #add to elasticsearch
  try:
    models.add_or_update_notification(notification_id, document, DOC_TYPE)
  except:
    return HttpResponse("Target %s could not be indexed at this time. \n", status=500)

  #return notification url
  response = HttpResponse(status=201)
  response['Location'] = INBOX_BASE_URL + str(uid) 
  return response


def get_notification(id):
  doc = models.get_notification(id)
  output = json.dumps(doc, indent=4, sort_keys=True)
  response = HttpResponse(output, status=200)
  response['Content-Type'] = "application/ld+json"
  response['Content-Language'] = "en"
  return response


def get_all_notifications_for_target(target):
  all_ids = models.get_all_notification_ids_for_target(target, DOC_TYPE)
  contains = map (lambda x: INBOX_BASE_URL + x, all_ids)
  resp_json = {
    "@context": "http://www.w3.org/ns/ldp",
    "@id": "http://example.org/inbox/",
    "contains": contains
  }
  output = json.dumps(resp_json, indent=4, sort_keys=True)
  response = HttpResponse(output, status=200)
  response['Content-Type'] = "application/ld+json"
  response['Content-Language'] = "en"
  return response


def generate_uid(id):
  ts = int(time())
  hashids = Hashids()
  hashid = hashids.encode(int(id), ts)
  return hashid
  

# Parse ID from URL
def parse_id(raw):
  p = {} # p is for parsed!
  source_sep = raw.find(":")
  p["source"] = raw[0:source_sep]
  id_sep = raw.find("$")
  if id_sep == -1:
    id_sep = None
  p["id"] = raw[source_sep+1:id_sep]
  return p
