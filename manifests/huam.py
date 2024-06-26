#!/usr/bin/python3

import json, sys
import requests
from django.conf import settings
from os import environ

from logging import getLogger
logger = getLogger(__name__)

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

def main(data, document_id, source, host):
	manifestUriBase = settings.IIIF['manifestUriTmpl'] % host

	huam_json = json.loads(data)
	attribution = huam_json["creditline"]
	logo = settings.IIIF['logo'] % host

	manifestLabel = huam_json["title"]
	#genres = dom.xpath('/mods:mods/mods:genre/text()', namespaces=ALLNS)
	#TODO: determine if there are different viewingHints for HUAM data
	genres = []
	if "handscroll" in genres:
		viewingHint = "continuous"
	else:
		# XXX Put in other mappings here
		viewingHint = "individuals"
	## TODO: add viewingDirection

	manifest_uri = manifestUriBase + "%s:%s" % (source, document_id)

	## List of different image labels
	## @displayLabel = Full Image, @note = Color digital image available, @note = Harvard Map Collection copy image
	images = huam_json["images"]

	#print "Images list", images

	s = requests.Session()

	canvasInfo = []
	for (counter, im) in enumerate(images):
		info = {}
		if im["publiccaption"]:
			info['label'] = im["publiccaption"]
		else:
			info['label'] = str(counter+1)
		response = s.head(im["baseimageurl"], allow_redirects=True)
		ids_url = response.url
		url_idx = ids_url.rfind('/')
		q_idx = ids_url.rfind('?') # and before any ? in URL
		if q_idx != -1:
			image_id = ids_url[url_idx+1:q_idx]
		else:
			image_id = ids_url[url_idx+1:]

		info['image'] = image_id
		canvasInfo.append(info)

	# can add metadata key/value pairs
	mfjson = {
		"@context":"http://iiif.io/api/presentation/2/context.json",
		"@id": manifest_uri,
		"@type":"sc:Manifest",
		"label":manifestLabel,
		"attribution":attribution,
		"logo":logo,
		"description":huam_json["provenance"],
		"sequences": [
			{
				"@id": manifest_uri + "/sequence/normal.json",
				"@type": "sc:Sequence",
				"viewingHint":viewingHint,
			}
		]
	}

	canvases = []

	for cvs in canvasInfo:
		response = s.get(imageUriBase + cvs['image'] + imageInfoSuffix)
		try:
			response.raise_for_status()
		except requests.exceptions.HTTPError as e:
			logger.debug("huam: error getting image info for %s" % cvs['image'], exc_info=True)
			continue
		infojson = response.json()
		cvsjson = {
			"@id": manifest_uri + "/canvas/canvas-%s.json" % cvs['image'],
			"@type": "sc:Canvas",
			"label": cvs['label'],
			"height": infojson['height'],
			"width": infojson['width'],
			"images": [
				{
					"@id":manifest_uri+"/annotation/anno-%s.json" % cvs['image'],
					"@type": "oa:Annotation",
					"motivation": "sc:painting",
					"resource": {
						"@id": imageUriBase + cvs['image'] + imageUriSuffix,
						"@type": "dctypes:Image",
						"format":"image/jpeg",
						"height": infojson['height'],
						"width": infojson['width'],
						"service": {
						  "@id": imageUriBase + cvs['image'],
						  "@context": serviceContext,
						  "profile": profileLevel
						},
					},
					"on": manifest_uri + "/canvas/canvas-%s.json" % cvs['image']
				}
			],
			"thumbnail": {
			  "@id": imageUriBase + cvs['image'] + thumbnailSuffix,
			  "@type": "dctypes:Image"
			}
		}
		canvases.append(cvsjson)
	s.close()
	mfjson['sequences'][0]['canvases'] = canvases
	output = json.dumps(mfjson, indent=4, sort_keys=True)
	return output

if __name__ == "__main__":
	if (len(sys.argv) < 5):
		sys.stderr.write('not enough args\n')
		sys.stderr.write('usage: mods.py [input] [manifest_identifier] [source] [host]\n')
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
