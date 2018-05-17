#!/usr/bin/python

import json, sys
import urllib2, requests
from urllib.parse import urlparse
from django.conf import settings
from os import environ

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
license = settings.IIIF['license']
IIIF_MANIFEST_HOST = environ.get("IIIF_MANIFEST_HOST", "localhost")
attribution = "Provided by Harvard University"

def main(data, document_id, source, host, cookie=None):
	manifestUriBase = settings.IIIF['manifestUriTmpl'] % host
	captionServer = urlparse(serviceBase)['netloc']
	captionServerBase = "http://" + captionServer + ":8080/ids/lookup?id="

	logo = settings.IIIF['logo'] % host

	manifestLabel = "No Label"
	req = requests.get(captionServerBase + document_id)
	if (req.status_code == 200):
	  md_json = json.loads(req.text)
	  if ('caption' in md_json.keys()):
	    manifestLabel = md_json['caption']

	genres = []
	viewingHint = "individuals"

	manifest_uri = manifestUriBase + "%s:%s" % (source, document_id)

	## List of different image labels
	## @displayLabel = Full Image, @note = Color digital image available, @note = Harvard Map Collection copy image

	canvasInfo = []

	# can add metadata key/value pairs
	mfjson = {
		"@context":"http://iiif.io/api/presentation/1/context.json",
		"@id": manifest_uri,
		"@type":"sc:Manifest",
		"label":manifestLabel,
		"attribution":attribution,
		"logo":logo,
		#"description":huam_json["provenance"],
		"sequences": [
			{
				"@id": manifest_uri + "/sequence/normal.json",
				"@type": "sc:Sequence",
				"viewingHint":viewingHint,
			}
		]
	}

	canvases = []

	for cvs in data['response']['docs']:
		canvasLabel = "No Label"
		req = requests.get(captionServerBase + str(cvs['file_id_num']))
		if (req.status_code == 200):
		  md_json = json.loads(req.text)
		  if ('caption' in md_json.keys()):
		    canvasLabel = md_json['caption']
		cvsjson = {
			"@id": manifest_uri + "/canvas/canvas-%s.json" % str(cvs['file_id_num']),
			"@type": "sc:Canvas",
			"label": canvasLabel, 
			"height": str(cvs['file_mix_imageHeight_num']),
			"width": str(cvs['file_mix_imageWidth_num']),
			"images": [
				{
					"@id":manifest_uri+"/annotation/anno-%s.json" % str(cvs['file_id_num']),
					"@type": "oa:Annotation",
					"motivation": "sc:painting",
					"resource": {
						"@id": imageUriBase + str(cvs['file_id_num']) + imageUriSuffix,
						"@type": "dctypes:Image",
						"format":"image/jpeg",
						"height": str(cvs['file_mix_imageHeight_num']),
						"width": str(cvs['file_mix_imageWidth_num']),
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
