#!/usr/bin/python

import json, sys
import urllib2
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

	logo = settings.IIIF['logo'] % host

	manifestLabel = data['response']['docs'][0]['object_mets_label_text']
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
		cvsjson = {
			"@id": manifest_uri + "/canvas/canvas-%s.json" % cvs['file_id_num'],
			"@type": "sc:Canvas",
			"label": cvs['object_mets_label_text'],
			"height": cvs['file_mix_imageHeight_num'],
			"width": cvs['file_mix_imageWidth_num'],
			"images": [
				{
					"@id":manifest_uri+"/annotation/anno-%s.json" % cvs['file_id_num'],
					"@type": "oa:Annotation",
					"motivation": "sc:painting",
					"resource": {
						"@id": imageUriBase + cvs['file_id_num'] + imageUriSuffix,
						"@type": "dctypes:Image",
						"format":"image/jpeg",
						"height": cvs['file_mix_imageHeight_num'],
						"width": cvs['file_mix_imageWidth_num'],
						"service": {
						  "@id": imageUriBase + cvs['file_id_num'],
						  "@context": serviceContext,
						  "profile": profileLevel
						},
					},
					"on": manifest_uri + "/canvas/canvas-%s.json" % cvs['file_id_num']
				}
			],
			"thumbnail": {
			  "@id": imageUriBase + cvs['file_id_num'] + thumbnailSuffix,
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
