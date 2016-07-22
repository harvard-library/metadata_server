#!/usr/bin/python

from lxml import etree
import json, sys
import urllib2
from django.conf import settings
import webclient, re

XMLNS = {'mods': 'http://www.loc.gov/mods/v3'}

imageUriBase = settings.IIIF['imageUriBase']
imageUriSuffix = settings.IIIF['imageUriSuffix']
imageInfoSuffix = settings.IIIF['imageInfoSuffix']
manifestUriTmpl = settings.IIIF['manifestUriTmpl']
serviceBase = settings.IIIF['serviceBase']
profileLevel = settings.IIIF['profileLevel']

attribution = "Provided by Harvard University"
license = "Use of this material is subject to our Terms of Use: http://nrs.harvard.edu/urn-3:hul.ois:hlviewerterms"

def main(data, document_id, source, host, cookie=None):
	manifestUriBase = settings.IIIF['manifestUriTmpl'] % host

	logo = settings.IIIF['logo'] % host

	data = re.sub('(?i)encoding=[\'\"]utf\-8[\'\"]','', data)
	utf8_parser = etree.XMLParser(encoding='utf-8')
	dom = etree.XML(data, parser=utf8_parser)

	manifestLabel = dom.xpath('/mods:mods/mods:titleInfo/mods:title/text()', namespaces=XMLNS)[0]
	type = dom.xpath('/mods:mods/mods:typeOfResource/text()', namespaces=XMLNS)[0]
	genres = dom.xpath('/mods:mods/mods:genre/text()', namespaces=XMLNS)

	if "handscroll" in genres:
		viewingHint = "continuous"
	else:
		# XXX Put in other mappings here
		viewingHint = "individuals"
	## TODO: add viewingDirection

	manifest_uri = manifestUriBase + "%s:%s" % (source, document_id)

	## List of different image labels
	## @displayLabel = Full Image, @note = Color digital image available, @note = Harvard Map Collection copy image
	images = dom.xpath('/mods:mods//mods:location/mods:url[@displayLabel="Full Image" or contains(@note, "Color digital image") or contains(@note, "copy image")]/text()', namespaces=XMLNS)

	print "Images list", images

	canvasInfo = []
	for (counter, im) in enumerate(images):
		info = {}
		info['label'] = str(counter+1)
		#response = urllib2.urlopen(im)
		response = webclient.get(im, cookie)
		ids_url = response.geturl()
		url_idx = ids_url.rfind('/')
		q_idx = ids_url.rfind('?') # and before any ? in URL
		if q_idx != -1:
			image_id = ids_url[url_idx+1:q_idx]
		else:
			image_id = ids_url[url_idx+1:]

		d_idx = image_id.find('drs:')
		if d_idx != -1:
			image_id = image_id[4:]
		s_idx = image_id.find('$')
		if s_idx != -1:
			image_id = image_id[0:s_idx-1]

		if "pds.lib.harvard.edu" in ids_url:
			# this is a hollis record that points to a PDS/METS object, should not keep processing as a MODS
			return json.dumps({"pds":image_id}, indent=4, sort_keys=True)

		info['image'] = image_id
		canvasInfo.append(info)

	mfjson = {
		"@context":"http://www.shared-canvas.org/ns/context.json",
		"@id": manifest_uri,
		"@type":"sc:Manifest",
		"label":manifestLabel,
		#"attribution":attribution,
		"license":license,
		"logo":logo,
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
		#response = urllib2.urlopen(imageUriBase + cvs['image'] + imageInfoSuffix)
		response = webclient.get(imageUriBase + cvs['image'] + imageInfoSuffix, cookie)
		infojson = json.load(response)
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
						"@type": "dcterms:Image",
						"format":"image/jpeg",
						"height": infojson['height'],
						"width": infojson['width'],
						"service": {
						  "@id": imageUriBase + cvs['image'],
						  "profile": profileLevel
						},
					},
					"on": manifest_uri + "/canvas/canvas-%s.json" % cvs['image']
				}
			]
		}
		canvases.append(cvsjson)

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
	isDrs1 = True; # add functionality for drs2
	host = sys.argv[4]

	fh = file(inputfile)
	data = fh.read()
	fh.close()

	output = main(data, document_id, source, host)
	fh = file(outputfile, 'w')
	fh.write(output)
	fh.close()
