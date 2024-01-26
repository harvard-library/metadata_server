#!/usr/bin/python3

import json, sys
import requests
#from urlparse import urlparse
from django.conf import settings
from os import environ

from logging import getLogger
logger = getLogger(__name__)

#this creates manifests out of IDS (drs file object) images from solr.
# cgoines 17 may 18

imageUriBase =    settings.IIIF['imageUriBase']
imageUriSuffix =  settings.IIIF['imageUriSuffix']
imageInfoSuffix = settings.IIIF['imageInfoSuffix']
thumbnailSuffix = settings.IIIF['thumbnailSuffix']
manifestUriTmpl = settings.IIIF['manifestUriTmpl']
serviceBase =     settings.IIIF['serviceBase']
profileLevel =    settings.IIIF['profileLevel']
serviceContext = settings.IIIF['context']
license = "https://nrs.harvard.edu/urn-3:HUL.eother:idscopyright"
IIIF_MANIFEST_HOST = environ.get("IIIF_MANIFEST_HOST", "localhost")
attribution = "Provided by Harvard University"
captionServerBase = environ.get("CAPTION_API", "http://ids-prod1.lts.harvard.edu:8080/ids/lookup?id=")

def main(data, document_id, source, host, cookie=None):
	manifestUriBase = settings.IIIF['manifestUriTmpl'] % host

	logo = settings.IIIF['logo'] % host

	manifestLabel = " "
	try:
	  req = requests.get(captionServerBase + document_id)
	  if (req.status_code == 200):
	    md_json = json.loads(req.text)
	    if ('caption' in md_json.keys()):
	      if (md_json['caption'] != ""):
	        manifestLabel = md_json['caption']
	except:
	  pass

	genres = []
	viewingHint = "individuals"

	manifest_uri = manifestUriBase + "%s:%s" % (source, document_id)

	## List of different image labels
	## @displayLabel = Full Image, @note = Color digital image available, @note = Harvard Map Collection copy image

	canvasInfo = []

	# can add metadata key/value pairs
	mfjson = {
		"@context":"http://iiif.io/api/presentation/2/context.json",
		"@id": manifest_uri,
		"@type":"sc:Manifest",
		"label":manifestLabel,
		"attribution":attribution,
		"logo":logo,
		"license":license,
		#"description":huam_json["provenance"],
		"sequences": [
			{
				"@id": manifest_uri + "/sequence/normal.json",
				"@type": "sc:Sequence",
				"viewingHint": viewingHint,
				"label":manifestLabel,
				"startCanvas": manifest_uri + "/canvas/canvas-%s.json" % str(document_id),
			}
		],
#		"structures": [
#			{
#				"@id": manifest_uri + "/range/range-1.json",
#				"@type": "sc:Range",
#				"label":manifestLabel,
#			}
#		]
	}

	canvases = []
#	structure_canvases = []

	for cvs in data['response']['docs']:
		if ( ('file_huldrsadmin_accessFlag_string' in cvs.keys()) and
	         ('file_huldrsadmin_accessFlag_string' == "N") ):
			continue

		canvasLabel = " "
		try:
		  req = requests.get(captionServerBase + str(cvs['file_id_num']))
		  req.raise_for_status()
		  if ('caption' in md_json.keys()):
		     canvasLabel = md_json['caption']
		except:
		  pass

		if ( ('file_mix_imageHeight_num' not in cvs.keys()) or ('file_mix_imageWidth_num' not in cvs.keys()) ):
		    try: #call ids for info.json dimensions if missing from solr feed
		      infoReq = requests.get(imageUriBase + str(cvs['file_id_num']) + '/info.json')
		      infoReq.raise_for_status()
		      info_json = json.loads(infoReq.text)
		      logger.debug("ids: missing image dimensions from solr - making info.json call for image id " + str(cvs['file_id_num']) )
		      if ('height' in info_json.keys()):
		        cvs['file_mix_imageHeight_num'] = int(info_json['height'])
		      else:
		        cvs['file_mix_imageHeight_num'] = int(settings.DEFAULT_HEIGHT)
		      if ('width' in info_json.keys()):
		         cvs['file_mix_imageWidth_num'] = int(info_json['width'])
		      else:
		         cvs['file_mix_imageWidth_num'] = int(settings.DEFAULT_WIDTH)
		    except:
		      cvs['file_mix_imageWidth_num'] = int(settings.DEFAULT_WIDTH)
		      cvs['file_mix_imageHeight_num'] = int(settings.DEFAULT_HEIGHT)

		cvsjson = {
			"@id": manifest_uri + "/canvas/canvas-%s.json" % str(cvs['file_id_num']),
			"@type": "sc:Canvas",
			"label": canvasLabel, 
			"height": cvs['file_mix_imageHeight_num'],
			"width": cvs['file_mix_imageWidth_num'],
			"images": [
				{
					"@id":manifest_uri+"/annotation/anno-%s.json" % str(cvs['file_id_num']),
					"@type": "oa:Annotation",
					"motivation": "sc:painting",
					"resource": {
						"@id": imageUriBase + str(cvs['file_id_num']) + imageUriSuffix,
						"@type": "dctypes:Image",
						"format":"image/jpeg",
						"height": cvs['file_mix_imageHeight_num'],
						"width": cvs['file_mix_imageWidth_num'],
						"service": {
						  "@id": imageUriBase + str(cvs['file_id_num']),
						  "@context": serviceContext,
						  "profile": profileLevel
						},
					},
					"on": manifest_uri + "/canvas/canvas-%s.json" % str(cvs['file_id_num'])
				}
			],
			"thumbnail": {
			  "@id": imageUriBase + str(cvs['file_id_num']) + thumbnailSuffix,
			  "@type": "dctypes:Image"
			}
		}
		canvases.append(cvsjson)

	mfjson['sequences'][0]['canvases'] = canvases
#	for canvas in canvases:
#		structure_canvases.append(canvas['@id'])
#	mfjson['structures'][0]['canvases'] = structure_canvases
	output = json.dumps(mfjson, indent=4, sort_keys=True)
	return output

if __name__ == "__main__":
	if (len(sys.argv) < 5):
		sys.stderr.write('not enough args\n')
		sys.stderr.write('usage: ids.py [input] [manifest_identifier] [source] [host]\n')
		sys.exit(0)

	inputfile = sys.argv[1]
	document_id = sys.argv[2]
	source = sys.argv[3]
	outputfile = source + '-' + document_id +  ".json"
	host = sys.argv[4]

	fh = open(inputfile)
	data = fh.read()
	fh.close()

	output = main(data, document_id, source, host)
	fh = file(outputfile, 'w')
	fh.write(output)
	fh.close()
