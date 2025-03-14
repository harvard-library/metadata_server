from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from manifests import huam
from manifests import mets
from manifests import mods
from manifests import models
from manifests import ams
from manifests import ids
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

METS_DRS_URL = environ.get("METS_DRS_URL", "http://fds.lib.harvard.edu/fds/deliver/")
METS_API_URL = environ.get("METS_API_URL", "http://pds.lib.harvard.edu/pds/get/")
MODS_DRS_URL = "http://webservices.lib.harvard.edu/rest/MODS/"
HUAM_API_URL = "http://api.harvardartmuseums.org/object/"
HUAM_API_KEY = environ["HUAM_API_KEY"]
COOKIE_DOMAIN = environ.get("COOKIE_DOMAIN", ".hul.harvard.edu")
PDS_VIEW_URL = environ.get("PDS_VIEW_URL", "http://pds.lib.harvard.edu/pds/view/")
PDS_WS_URL = environ.get("PDS_WS_URL", "http://pds.lib.harvard.edu/pds/")
IDS_VIEW_URL = environ.get("IDS_VIEW_URL", "https://ids.lib.harvard.edu/ids/")
FTS_VIEW_URL = environ.get("FTS_VIEW_URL","http://fts.lib.harvard.edu/fts/search")
IIIF_MGMT_ACL = (environ.get("IIIF_MGMT_ACL","128.103.151.0/24,10.34.5.254,10.40.4.69")).split(',')
CORS_WHITELIST = (environ.get("CORS_WHITELIST", "http://harvard.edu")).split(',')
IIIF_MANIFEST_HOST = environ.get("IIIF_MANIFEST_HOST")
CAPTION_API_URL = (environ.get("CAPTION_API","http://ids.lib.harvard.edu:8080/ids/lookup?id="))
VERSION = "v1.7.1"

sources = {"drs": "mets", "via": "mods", "hollis": "mods", "huam" : "huam", "ext": "ext", "ids": "ids" }

def index(request, source=None):
	request_ip = request.META['REMOTE_ADDR']
	if not all_matching_cidrs(request_ip, IIIF_MGMT_ACL):
		if not all_matching_cidrs(get_xfwd_ip(request), IIIF_MGMT_ACL):
			return HttpResponse("Access Denied.", status=403)
	source = source if source else "drs"
	document_ids = models.get_all_manifest_ids_with_type(source)
	host = IIIF_MANIFEST_HOST
	if host == None:
		host = request.META['HTTP_HOST']
	cookie = request.COOKIES.get('hulaccess', None)
	manifests = ({"uri": "/manifests/view/%s:%s" % (source, d_id), "title": (models.get_manifest_title(d_id, source) or "Untitled Item") + " (id: %s)" % d_id} for d_id in document_ids)
	if source == "ids":
		return render(request, 'manifests/ids.html', {'manifests': manifests})
	else:
		return render(request, 'manifests/index.html', {'manifests': manifests})

# view any number of MODS, METS, or HUAM objects
def view(request, view_type, document_id):
	doc_ids = filter(lambda x:x, document_id.split(';'))
	manifests_data = []
	manifests_wobjects = []
	ams_cookie = None
	view_mapping = {"i": "ImageView",
					"t": "ThumbnailsView",
					"s": "ScrollView",
					"b": "BookView",
					None: "ImageView"}

	# Parse ID from URL
	def parse_id(raw):
		p = {} # p is for parsed!
		source_sep = raw.find(":")
		p["source"] = raw[0:source_sep]
		id_sep = raw.find("$")
		if id_sep == -1:
			id_sep = None
		p["id"] = raw[source_sep+1:id_sep]
		if id_sep:
			m = re.match(r"(\d+)([ibst])?", raw[id_sep+1:])
			(p["seq"], p["view"]) = [x if x else None for x in m.groups()]
			try:
				p["seq"] = int(p["seq"])
			except(ValueError):
				p["seq"] = None
		else:
			p["seq"] = p["view"] = None

		p["view"] = view_mapping[p["view"]]
		# TODO: k:v pairs for now, planned structure is "$key=val,..."
		# TODO: validate id! Throw interesting errors!
		return p

	def layout_string(n):
		"""Return nxn formatted string of y, x arrangement for windows"""
		return "{0}x{1}".format((n / 2) + (n % 2), 1 if n == 1 else 2)

	if 'hulaccess' in request.COOKIES:
		ams_cookie = request.COOKIES['hulaccess']
	host = IIIF_MANIFEST_HOST
	if host == None:
		host = request.META['HTTP_HOST']
	s = requests.Session()
	for doc_id in doc_ids:
		parts = parse_id(doc_id)

		# drs: check AMS to see if this is a restricted obj
		# TODO:  move this check into get_manifest() for hollis
		drs_object = False
		ams_redirect = None
		success = False
		if (('drs' == parts["source"]) or ('ids' == parts['source'])):
			drs_object = True
		if ('drs' == parts["source"]):
			ams_redirect = ams.getAMSredirectUrl(request.COOKIES, parts["id"])
		elif ('ids' == parts['source']):
			ams_redirect = ams.getAMSredirectUrl(request.COOKIES, parts["id"], isIDS=True)
		if (drs_object == True and ams_redirect == None):
			return HttpResponse("Invalid object id", status=404)
		if (drs_object == True and ams_redirect[0] == 'N'):
			return HttpResponse("The object you have requested is not intended for delivery", status=403) # 403 HttpResponse object
		elif (drs_object == True and ams_redirect[0] == 'R'):
			if ams_redirect[1] != None:
				return HttpResponseRedirect(ams_redirect[1])

		if parts['source'] == 'ext':
			success = True
			try:
				response = (s.get(base64.urlsafe_b64decode(parts["id"].encode('ascii')))).text
			except:
				success = False
			real_source = parts["source"]
		else:
			#print source, id
			(success, response, real_id, real_source) = get_manifest(parts["id"], parts["source"], False, host, ams_cookie)

		if success:
			if parts['source'] == 'ext':
				location = "Unknown"
				uri = (base64.urlsafe_b64decode(parts["id"].encode('ascii'))).decode("utf-8")
				title = "Unknown"
			else:
				title = models.get_manifest_title(real_id, real_source)
				uri = settings.HTTP_PROTOCOL + "://%s/manifests/%s:%s" % (host,real_source,real_id)
				location = "Harvard University"


			jsdir = "dev" if view_type == "view-dev" else "prod"
			path_data = json.dumps({
				"i18nPath": "/static/manifests/%s/locales/" % jsdir,
				"logosLocation": "/static/manifests/%s/images/logos/" % jsdir
			})

			# Data - what gets loaded
			mfdata = { "manifestUri": uri,
					   "location": location,
					   "title": title }

			manifests_data.append(json.dumps(mfdata))
		else:
			return HttpResponse("Invalid object id", status=404)

			# Window objects - what gets displayed
		if parts['source'] == 'ids':
			mfwobject = {"loadedManifest": uri,
			"bottomPanel": False,
			"sidePanel": False,
			"displayLayout": False,
			"availableViews": ['ImageView'],
			"viewType": parts["view"] }
		else:
			mfwobject = {"loadedManifest": uri,
				"viewType": parts["view"] }
			if view_type == "view-dev": #mirador 3 preview
				mfwobject = {"loadedManifest": uri,
						   "thumbnailNavigationPosition": "far-bottom"}

		# Load manifest as JSON, get sequence info, use canvasID to page into object
		mfjson = json.loads(response)["sequences"][0]["canvases"]
		try:
			if parts["seq"] and 0 < parts["seq"] <= len(mfjson):
				mfwobject["canvasID"] = mfjson[parts["seq"] - 1]["@id"]
		except(ValueError):
			pass

		manifests_wobjects.append(json.dumps(mfwobject))
	s.close()

	if len(manifests_data) > 0:
		view_locals = {'path_data':          path_data,
					   'manifests_data' :    manifests_data,
					   'manifests_wobjects': manifests_wobjects,
					   'num_manifests':      len(manifests_data),
					   'pds_view_url':       PDS_VIEW_URL,
					   'pds_ws_url':         PDS_WS_URL,
			   'ids_view_url':       IDS_VIEW_URL,
			   'fts_view_url':	     FTS_VIEW_URL,
			   'ids_caption_url':    CAPTION_API_URL,
					   'layout_string':      layout_string(len(manifests_data))
				   }
		# Check if its an experimental/dev Mirador codebase, otherwise use production
		if (view_type == "view-dev"):
			return render(request, 'manifests/dev.html', view_locals)
		else:
			if parts['source'] == 'ids':
				return render(request, 'manifests/ids.html', view_locals)
			else:
				return render(request, 'manifests/manifest.html', view_locals)
	else:
		return HttpResponse("The requested document ID(s) %s could not be displayed" % document_id, status=404) # 404 HttpResponse object

# Demo URL - a canned list of manifests
def demo(request):
	return render(request, 'manifests/demo.html', {'pds_view_url' : PDS_VIEW_URL})

# Returns a IIIF manifest of a METS, MODS or HUAM JSON object
# Checks if DB has it, otherwise creates it
def manifest(request, document_id):
	parts = document_id.split(":")
	host = IIIF_MANIFEST_HOST

	if host == None:
		host = request.META['HTTP_HOST']
	cookie = request.COOKIES.get('hulaccess', None)
	if len(parts) != 2:
		return HttpResponse("Invalid document ID. Format: [data source]:[ID]", status=404)
	source = parts[0]
	id = parts[1]

	#check ams
	drs_object = False
	ams_redirect = None
	if ('drs' == source):
		ams_redirect = ams.getAMSredirectUrl(request.COOKIES, id)
		drs_object = True
	elif ('ids' == source):
		ams_redirect = ams.getAMSredirectUrl(request.COOKIES, id, isIDS=True)
		drs_object = True
	if (drs_object and ams_redirect == None):
		return HttpResponse("Invalid object id", status=404)
	if (drs_object and ams_redirect[0] == 'N'):
		return HttpResponse("The object you have requested is not intended for delivery", status=403) # 403 HttpResponse object
	elif (drs_object and ams_redirect[0] == 'R'):
		if ams_redirect[1] != None:
				return HttpResponseRedirect(ams_redirect[1])

	(success, response_doc, real_id, real_source) = get_manifest(id, source, False, host, cookie)
	if success:
		response = HttpResponse(response_doc, content_type="application/javascript; charset=UTF-8")
		add_headers(response, request)
		return response
	else:
		return response_doc # 404 HttpResponse

# Delete any document from db
def delete(request, document_id):
	request_ip = request.META['REMOTE_ADDR']
	if not all_matching_cidrs(request_ip, IIIF_MGMT_ACL):
		if not all_matching_cidrs(get_xfwd_ip(request), IIIF_MGMT_ACL):
			return HttpResponse("Access Denied.", status=403)
	# Check if manifest exists
	parts = document_id.split(":")
	if len(parts) != 2:
		return HttpResponse("Invalid document ID. Format: [data source]:[ID]", status=404)
	source = parts[0]
	id = parts[1]
	has_manifest = models.manifest_exists(id, source)

	if has_manifest:
		models.delete_manifest(id, source)
		return HttpResponse("Document ID %s has been deleted" % document_id)
	else:
		logger.debug("Failed delete request for document id %s - does not exist in db" % document_id)
		return HttpResponse("Document ID %s does not exist in the database" % document_id, status=404)

# Force refresh a single document
# Pull METS, MODS or HUAM JSON, rerun conversion script, and store in db
def refresh(request, document_id):
	request_ip = request.META['REMOTE_ADDR']
	if not all_matching_cidrs(request_ip, IIIF_MGMT_ACL):
		if not all_matching_cidrs(get_xfwd_ip(request), IIIF_MGMT_ACL):
			return HttpResponse("Access Denied.", status=403)
	parts = document_id.split(":")
	host = IIIF_MANIFEST_HOST
	if host == None:
		host = request.META['HTTP_HOST']
	cookie = request.COOKIES.get('hulaccess', None)
	if len(parts) != 2:
		return HttpResponse("Invalid document ID. Format: [data source]:[ID]", status=404)
	source = parts[0]
	id = parts[1]

	# drs: check AMS to see if this is a restricted obj
	if (('drs' == source) or ('ids' == source)):
		access_flag = ams.getAccessFlag(id)
		if access_flag == 'N':
			return HttpResponse("The object you have requested is not intended for delivery", status=403) # 403 HttpResponse object

	(success, response_doc, real_id, real_source) = get_manifest(id, source, True, host, cookie)

	if success:
		response = HttpResponse(response_doc)
		add_headers(response, request)
		return response
	else:
		return response_doc # This is actually the 404 HttpResponse, so return and end the function

# Force refresh all records from a single source
# WARNING: this could take a long time
# Pull all METS, MODS or HUAM JSON, rerun conversion script, and store in db
def refresh_by_source(request, source):
	request_ip = request.META['REMOTE_ADDR']
	if not all_matching_cidrs(request_ip, IIIF_MGMT_ACL):
		if not all_matching_cidrs(get_xfwd_ip(request), IIIF_MGMT_ACL):
			return HttpResponse("Access Denied.", status=403)
	document_ids = models.get_all_manifest_ids_with_type(source)
	counter = 0
	host = IIIF_MANIFEST_HOST
	if host == None:
		host = request.META['HTTP_HOST']
	cookie = request.COOKIES.get('hulaccess', None)
	for id in document_ids:
		(success, response_doc, real_id, real_source) = get_manifest(id, source, True,  host, cookie)
		if success:
			counter = counter + 1

	response = HttpResponse("Refreshed %s out of %s total documents in %s" % (counter, len(document_ids), source))
	return response

# this is a hack because the javascript uses relative paths for the PNG files, and Django creates the incorrect URL for them
# Need to find a better and more permanent solution
def get_image(request, view_type, filename):
	if view_type == "view-dev":
		return HttpResponseRedirect("/static/manifests/dev/images/%s" % filename)
	elif view_type == "view-annotator":
		return HttpResponseRedirect("/static/manifests/annotator/images/%s" % filename)
	elif view_type == "view-m1":
		return HttpResponseRedirect("/static/manifests/m1/images/%s" % filename)
	elif view_type == "view-m2":
		return HttpResponseRedirect("/static/manifests/m2/images/%s" % filename)
	else:
		return HttpResponseRedirect("/static/manifests/prod/images/%s" % filename)

def clean_url(request, view_type):
	cleaned = "/static" + request.path.replace("//","/").replace("view-","")
	return HttpResponseRedirect(cleaned)

## HELPER FUNCTIONS ##
# Gets METS XML from DRS
def get_mets(document_id, source, cookie=None):
	#solr fetch replaces FDS call
	mets_url = settings.SOLR_BASE + settings.SOLR_QUERY_PREFIX + document_id + settings.SOLR_OBJ_QUERY
	try:
		mets_resp = requests.get(mets_url)
		mets_resp.raise_for_status()
		mets_json = mets_resp.json()
	except:
		logger.debug("Failed solr request %s" % mets_url)
		return (False, HttpResponse("The document ID %s does not exist" % document_id, status=404))
	#response_doc = settings.METS_HEADER + mets_json['response']['docs'][0]['object_file_sec_raw'] + \
	#mets_json['response']['docs'][0]['object_structmap_raw'] + settings.METS_FOOTER
	response_doc = mets_json
	numFound = mets_json['response']['numFound']
	if numFound == 0:
		return (False, HttpResponse("The document ID %s does not exist" % document_id, status=404))
	else:
	  return (True, response_doc)

# Gets IDS images from DRS
def get_ids(document_id, source, cookie=None):
	ids_url = settings.SOLR_BASE + settings.SOLR_FILE_QUERY_PREFIX + document_id + settings.SOLR_AMS_FILE_QUERY
	try:
		ids_resp = requests.get(ids_url)
		ids_resp.raise_for_status()
		ids_json = ids_resp.json()
	except:
		logger.debug("Failed solr request %s" % ids_url)
		return (False, HttpResponse("The document ID %s does not exist" % document_id, status=404))
	response_doc = ids_json
	numFound = ids_json['response']['numFound']
	if numFound == 0:
		logger.debug("Failed solr request %s" % ids_url)
		return (False, HttpResponse("The document ID %s does not exist" % document_id, status=404))
	else:
	  return (True, response_doc)

# Gets MODS XML from Presto API
def get_mods(document_id, source, cookie=None):
	mods_url = MODS_DRS_URL+source+"/"+document_id
	#print mods_url
	try:
		mods_resp = requests.get(mods_url)
		mods_resp.raise_for_status()
		mods = mods_resp.text
	except:
		# document does not exist in DRS
		logger.debug("Failed mods request %s" % mods_url)
		return (False, HttpResponse("The document ID %s does not exist" % document_id, status=404))

	return (True, mods)

# Gets HUAM JSON from HUAM API
def get_huam(document_id, source):
	huam_url = HUAM_API_URL+document_id+"?apikey="+HUAM_API_KEY
	try:
		huam_resp = requests.get(huam_url)
		huam_resp.raise_for_status()
		huam = huam_resp.text
		huam_json = huam_resp.json()
		if ("error" in huam_json.keys()):
			logger.debug("Failed huam request %s" % huam_url)
			return (False, HttpResponse("The document ID %s does not exist" % document_id, status=404))
	except:
		logger.debug("Failed huam request %s" % huam_url)
		return (False, HttpResponse("The document ID %s does not exist" % document_id, status=404))

	return (True, huam)

# Adds headers to Response for returning JSON that other Mirador instances can access
def add_headers(response, request):
	#if 'hulaccess' in request.COOKIES:
	#   origin = request.META.get('HTTP_ORIGIN')
	#   if origin in CORS_WHITELIST:
	#      response["Access-Control-Allow-Origin"] = origin
	#   else:
	#      response["Access-Control-Allow-Origin"] = "http://harvard.edu/"
	#   response["Access-Control-Allow-Credentials"] = "true"
	#   response["Vary"] = "Origin"
	#else:
	#   response["Access-Control-Allow-Origin"] = "*"
	#response["Access-Control-Allow-Origin"] = "http://harvard.edu/"
	#response["Access-Control-Allow-Credentials"] = "true"
	#response["Access-Control-Allow-Origin"] = "*"
	response["Content-Type"] = "application/ld+json"
	return response

# Uses other helper methods to create JSON
def get_manifest(document_id, source, force_refresh, host, cookie=None):
	# Check if manifest exists
	has_manifest = models.manifest_exists(document_id, source)

	## TODO: add last modified check

	if not has_manifest or force_refresh:
		# If not, get MODS, METS, or HUAM JSON
		data_type = sources[source]
		if data_type == "mods":
			## TODO: check image types??
			(success, response) = get_mods(document_id, source, cookie)
		elif data_type == "mets":
			(success, response) = get_mets(document_id, source, cookie)
		elif data_type == "ids":
			(success, response) = get_ids(document_id, source, cookie)
		elif data_type == "huam":
			(success, response) = get_huam(document_id, source)
		else:
			success = False
			response = HttpResponse("Invalid source type", status=404)

		if not success:
			return (success, response, document_id, source) # This is actually the 404 HttpResponse, so return and end the function

		# Convert to shared canvas model if successful
		if data_type == "mods":
			converted_json = mods.main(response, document_id, source, host, cookie)
			# check if this is, in fact, a PDS object masked as a hollis request
			# If so, get the manifest with the DRS METS ID and return that
			json_doc = json.loads(converted_json)
			if 'pds' in json_doc:
				id = json_doc['pds']
				return get_manifest(id, 'drs', False, host, cookie)
		elif data_type == "mets":
			converted_json = mets.main(response, document_id, source, host, cookie)
		elif data_type == "ids":
			converted_json = ids.main(response, document_id, source, host, cookie)
		elif data_type == "huam":
			converted_json = huam.main(response, document_id, source, host)
		else:
			pass
		# Store to elasticsearch
		models.add_or_update_manifest(document_id, converted_json, source)
		# Return the documet_id and source in case this is a hollis record
		# that also has METS/PDS
		return (success, converted_json, document_id, source)
	else:
		# return JSON from db
		json_doc = models.get_manifest(document_id, source)
		return (True, json.dumps(json_doc), document_id, source)


#x forward ip - will be removed soon
def get_xfwd_ip(request):
	if 'HTTP_X_FORWARDED_FOR' in request.META:
	 return( request.META['HTTP_X_FORWARDED_FOR'].split(",")[0].strip() )

# Version URL - return the current version of this app
def version(request):
	return render(request, 'manifests/version.html', {'version' : VERSION})

# Healthcheck URL - return a 200 OK
def healthcheck(request):
	url = environ.get("HEALTHCHECK_URL")
	health_resp = requests.get(url)
	if health_resp.status_code != 200:
		return HttpResponse("Healthcheck failed", status=500)
	else:
		return HttpResponse("OK", status=200)
