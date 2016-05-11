#!/usr/bin/python

from lxml import etree
import json, sys, re
import urllib2
from django.conf import settings
import webclient
from os import environ

from logging import getLogger
logger = getLogger(__name__)

XMLNS = {
	'mets':		'http://www.loc.gov/METS/',
	'mods':		'http://www.loc.gov/mods/v3',
	'xlink':	'http://www.w3.org/1999/xlink',
	'premis':	'info:lc/xmlns/premis-v2',
	'hulDrsAdmin':	'http://hul.harvard.edu/ois/xml/ns/hulDrsAdmin',
	'mix':		'http://www.loc.gov/mix/v20'
}

# Globals
imageHash = {}
canvasInfo = []
rangesJsonList = []
manifestUriBase = u""

## TODO: Other image servers?
imageUriBase = settings.IIIF['imageUriBase']
imageUriSuffix = settings.IIIF['imageUriSuffix']
imageInfoSuffix = settings.IIIF['imageInfoSuffix']
manifestUriTmpl = settings.IIIF['manifestUriTmpl']
serviceBase = settings.IIIF['serviceBase']
profileLevel = settings.IIIF['profileLevel']

attribution = "Provided by Harvard University"
license = "Use of this material is subject to our Terms of Use: http://nrs.harvard.edu/urn-3:hul.ois:hlviewerterms"

METS_API_URL = environ.get("METS_API_URL", "http://pds.lib.harvard.edu/pds/get/")
HOLLIS_API_URL = "http://webservices.lib.harvard.edu/rest/MODS/hollis/"
HOLLIS_PUBLIC_URL = "http://id.lib.harvard.edu/aleph/{0}/catalog"
 ## Add ISO639-2B language codes here where books are printed right-to-left (not just the language is read that way)
right_to_left_langs = set(['ara','heb'])

# List of mime types: ordering is as defined in pdx_util (internalMets.java), but with txt representations omitted.
MIME_HIERARCHY = ['image/jp2', 'image/jpx', 'image/jpeg', 'image/gif', 'image/tiff']

def get_display_image(fids):
        """Goes through list of file IDs for a page, and returns the best choice for delivery (according to mime hierarchy)."""

        def proc_fid(out, fid):
                """Internal fn mapped over all images. Sets last image of each mime-type in out hash."""
                img = imageHash.get(fid, [])
                if len(img) == 2:
                        out[img["mime"]] = (img["img"], fid)
                return out

        versions = reduce(proc_fid, fids, {})
        display_img = None
        for mime in MIME_HIERARCHY:
                display_img = versions.get(mime)
                if display_img:
                        break

        return display_img or (None, None)

def process_page(sd):
	# first check if PAGE has label, otherwise get parents LABEL/ORDER
        label = get_rangeKey(sd)

        display_image, fid = get_display_image(sd.xpath('./mets:fptr/@FILEID', namespaces=XMLNS))

        my_range = None

        if display_image:
                info = {}
                info['label'] = label
                info['image'] = display_image
                #if info not in canvasInfo: #accept split intermediate/page nodes
		canvasInfo.append(info)
                my_range = {}
                my_range[label] = imageHash[fid]["img"]

        return my_range

def is_page(div):
        return 'TYPE' in div.attrib and div.get('TYPE') == 'PAGE'

# Regex for determining if page number exists in label
page_re = re.compile(r"[pP](?:age|\.) \[?(\d+)\]?")

# RangeKey used for table of contents
# Logic taken from pds/**/navsection.jsp, cleaned up for redundant cases
#
# Note: Doesn't use page_num because it does deduplication
#       in cases where ORDERLABEL is represented in LABEL
def get_rangeKey(div):
        if is_page(div):
                label = div.get('LABEL', "").strip()
                pn = page_num(div)
                seq = div.get('ORDER')
                seq_s = u"(seq. {0})".format(seq)
                if label:
                        match = page_re.search(label)
                        pn_from_label = match and match.group(1)


                # Both label and orderlabel exist and are not empty
                if label and pn:
                        # ORDERLABEL duplicates info in LABEL
                        if pn == pn_from_label:
                                return u"{0} {1}".format(label, seq_s)
                        else:
				#return u"{0}, p. {1} {2}".format(label, pn, seq_s)
                                return u"{0}, {1}".format(label, seq_s)
                elif not label and pn:
                        return u"p. {0} {1}".format(pn, seq_s)
                elif label and not pn:
                        return u"{0} {1}".format(label, seq_s)
                else:
                        return seq_s
        # Intermediates
	else:
                label = div.get('LABEL', "").strip()
                f, l = get_intermediate_seq_values(div[0], div[-1])
                display_ss = ""
                if f["page"] and l["page"]:
                        label += ","
                        if f["page"] == l["page"]:
                                display_ss = u"p. {0} ".format(f["page"])
                        else:
                                display_ss = u"pp. {0}-{1} ".format(f["page"], l["page"])

                return " ".join(filter(None, [label,
                                              display_ss,
                                              u"(seq. {0})".format(f["seq"]) if f["seq"] == l["seq"] else u"(seq. {0}-{1})".format(f["seq"], l["seq"])]))

def process_intermediate(div, new_ranges=None):
        """Processes intermediate divs in the structMap."""

        new_ranges = new_ranges or []

        for sd in div:
                # leaf node, get canvas info
                if is_page(sd):
                        my_range = process_page(sd)
                else:
                        my_range = process_intermediate(sd)
                if my_range:
                        new_ranges.append(my_range)

        # this is for the books where every single page is labeled (like Book of Hours)
        # most books do not do this
        if len(new_ranges) == 1:

                return {get_rangeKey(div): new_ranges[0].values()[0]}

        return {get_rangeKey(div): new_ranges}


# Get page number from ORDERLABEL or, failing that, LABEL, or, failing that, return None
def page_num(div):
        if 'ORDERLABEL' in div.attrib:
                return div.get('ORDERLABEL')
        else:
                match = page_re.search(div.get('LABEL', ''))
                return match and match.group(1)

def get_intermediate_seq_values(first, last):
        """Gets bookend values for constructing pp. and seq. range display, e.g. pp. 8-9 (seq. 10-17)."""

        # Drill down to first page
        while first.get('TYPE') == 'INTERMEDIATE':
                first = first[0]

        if first.get('TYPE') == 'PAGE':
                first_vals = {"seq": first.get('ORDER'), "page": page_num(first)}

        # Drill down last page
        while last.get('TYPE') == 'INTERMEDIATE':
                last = last[-1]

        if last.get('TYPE') == 'PAGE':
                last_vals = {"seq": last.get('ORDER'), "page": page_num(last)}

        return first_vals, last_vals

def process_struct_divs(div, ranges):
        """Toplevel processing function.  Run over contents of the CITATION div (or the stitched subdiv if present)."""
	rangeKey = get_rangeKey(div)

	# when the top level div is a PAGE
	if is_page(div):
		p_range = process_page(div)
                if p_range: 
                        ranges.append(p_range)
        else:
                subdivs = div.xpath('./mets:div', namespaces = XMLNS)
                if len(subdivs) > 0:
                        ranges.append(process_intermediate(div))

	return ranges

def process_structMap(smap):
        divs = smap.xpath('./mets:div[@TYPE="CITATION"]/mets:div', namespaces=XMLNS)

        # Check if the object has a stitched version(s) already made.  Use only those
	# broken per randy's req
        #for st in divs:
        #        stitchCheck = st.xpath('./@LABEL[contains(., "stitched")]', namespaces=XMLNS)
        #        if stitchCheck:
        #                divs = st
        #                break

def get_leaf_canvases(ranges, leaf_canvases):
	for range in ranges:
		if type(range) is dict:
			value = range.get(range.keys()[0])
		else:
			value = range
		#if type(value) is list:
		if any(isinstance(x, dict) for x in value):
			get_leaf_canvases(value, leaf_canvases)
		else:
			leaf_canvases.append(value)

def create_range_json(ranges, manifest_uri, range_id, within, label):
	# this is either a nested list of dicts or one or more image ids in the METS
	if any(isinstance(x, dict) for x in ranges):
		leaf_canvases = []
		get_leaf_canvases(ranges, leaf_canvases)
		canvases = []
		for lc in leaf_canvases:
			canvases.append(manifest_uri + "/canvas/canvas-%s.json" % lc)
	else:
		canvases = [manifest_uri + "/canvas/canvas-%s.json" % ranges]

	rangejson =  {"@id": range_id,
		      "@type": "sc:Range",
		      "label": label,
		      "canvases": canvases
		      }
	# top level "within" equals the manifest_uri, so this range is a top level
	if within != manifest_uri:
		rangejson["within"] = within
	rangesJsonList.append(rangejson)

def create_ranges(ranges, previous_id, manifest_uri):
        if not any(isinstance(x, dict) for x in ranges):
		return

	counter = 0
	for ri in ranges:
		counter = counter + 1
		label = ri.keys()[0]
		if previous_id == manifest_uri:
			# these are for the top level divs
			range_id = manifest_uri + "/range/range-%s.json" % counter
		else:
			# otherwise, append the counter to the parent's id
			range_id = previous_id[0:previous_id.rfind('.json')] + "-%s.json" % counter
		new_ranges = ri.get(label)
		create_range_json(new_ranges, manifest_uri, range_id, previous_id, label)
		create_ranges(new_ranges, range_id, manifest_uri)

def main(data, document_id, source, host, cookie=None):

	# clear global variables
	global imageHash
	imageHash = {}
	global canvasInfo
	canvasInfo = []
	global rangesJsonList
	rangesJsonList = []
	global manifestUriBase
	manifestUriBase = settings.IIIF['manifestUriTmpl'] % host

	#logger.debug("LOADING object " + str(document_id) + " into the DOM tree" )
	data = re.sub('(?i)encoding=[\'\"]utf\-8[\'\"]','', data)
	utf8_parser = etree.XMLParser(encoding='utf-8')
	dom = etree.XML(data, parser=utf8_parser)
	#logger.debug("object " + str(document_id) + " LOADED into the DOM tree" )
	# Check if this is a DRS2 object since some things, like hollis ID are in a different location
	isDrs1 = True;
	drs_check = dom.xpath('/mets:mets//premis:agentName/text()', namespaces=XMLNS)
	if len(drs_check) > 0 and 'DRS2' in '\t'.join(drs_check):
		isDrs1 = False
		#logger.debug("processing DRS2 object " + str(document_id) )

	#logger.debug("dom check: mets label candidates..." )
	mets_label_candidates = dom.xpath('/mets:mets/@LABEL', namespaces=XMLNS)
	#logger.debug("dom check: mets label candidates found" )
	if (len(mets_label_candidates) > 0) and (mets_label_candidates[0] != ""):
		manifestLabel = mets_label_candidates[0]
	else:
		#logger.debug("dom check: title candidates...")
		mods_title_candidates = dom.xpath('//mods:mods/mods:titleInfo/mods:title', namespaces=XMLNS)
		#logger.debug("dom check: title candidates found")
		if len(mods_title_candidates) > 0:
			manifestLabel = mods_title_candidates[0].text
		else:
			manifestLabel = 'No Label'

	#logger.debug("dom check: manifest types check..." )
	manifestType = dom.xpath('/mets:mets/@TYPE', namespaces=XMLNS)[0]
	#logger.debug("dom check: manifest type found" )

	if manifestType in ["PAGEDOBJECT", "PDS DOCUMENT"]:
		viewingHint = "paged"
	else:
		# XXX Put in other mappings here
		viewingHint = "individuals"

	## get language(s) from HOLLIS record, if there is one, (because METS doesn't have it) to determine viewing direction
	## TODO: top to bottom and bottom to top viewing directions
	## TODO: add Finding Aid links
	viewingDirection = 'left-to-right' # default
	seeAlso = u""
	if isDrs1:
		hollisCheck = dom.xpath('/mets:mets/mets:dmdSec/mets:mdWrap/mets:xmlData/mods:mods/mods:identifier[@type="hollis"]/text()', namespaces=XMLNS)
	else:
		#logger.debug("dom check: hollis check..." )
		#hollisCheck = dom.xpath('/mets:mets/mets:amdSec//hulDrsAdmin:hulDrsAdmin/hulDrsAdmin:drsObject/hulDrsAdmin:harvardMetadataLinks/hulDrsAdmin:metadataIdentifier[../hulDrsAdmin:metadataType/text()="Aleph"]/text()', namespaces=XMLNS)
		hollisCheck = dom.xpath('/mets:mets/mets:amdSec/mets:techMD/mets:mdWrap/mets:xmlData/hulDrsAdmin:hulDrsAdmin/hulDrsAdmin:drsObject/hulDrsAdmin:harvardMetadataLinks/hulDrsAdmin:metadataIdentifier[../hulDrsAdmin:metadataType/text()="Aleph"]/text()', namespaces=XMLNS)

		## TODO: fix for gif files / mixed set of image formats
		#logger.debug("dom check: hollis check done" )
		# get info.json dimensions from mets file instead of info.json calls for drs2 objects
		#drs2ImageIds = dom.xpath('/mets:mets/mets:amdSec//premis:object[@xsi:type="premis:file"]/premis:objectIdentifier/premis:objectIdentifierValue', namespaces=XMLNS)
		#logger.debug("DOM parsing iiif width coords for DRS2 object " + str(document_id) )
		drs2ImageWidths = dom.xpath('/mets:mets/mets:amdSec/mets:techMD/mets:mdWrap/mets:xmlData/premis:object/premis:objectCharacteristics/premis:objectCharacteristicsExtension/mix:mix/mix:BasicImageInformation/mix:BasicImageCharacteristics/mix:imageWidth/text()', namespaces=XMLNS)
		#logger.debug("DOM parsing iiif height coords for DRS2 object " + str(document_id) )
		drs2ImageHeights = dom.xpath('/mets:mets/mets:amdSec/mets:techMD/mets:mdWrap/mets:xmlData/premis:object/premis:objectCharacteristics/premis:objectCharacteristicsExtension/mix:mix/mix:BasicImageInformation/mix:BasicImageCharacteristics/mix:imageHeight/text()', namespaces=XMLNS)
		#logger.debug("DOM parsing iiif image format for DRS2 object " + str(document_id) )
		drs2ImageFormats = dom.xpath('/mets:mets/mets:amdSec/mets:techMD/mets:mdWrap/mets:xmlData/premis:object/premis:objectCharacteristics/premis:format/premis:formatDesignation/premis:formatName/text()', namespaces=XMLNS)
		##logger.debug("DOM parsing iiif tile width coords for DRS2 object " + str(document_id) )
		#drs2TileWidths = dom.xpath('/mets:mets/mets:amdSec/mets:techMD/mets:mdWrap/mets:xmlData/premis:object/premis:objectCharacteristics/premis:objectCharacteristicsExtension/mix:mix/mix:BasicImageInformation/mix:SpecialFormatCharacteristics/mix:JPEG2000/mix:EncodingOptions/mix:Tiles/mix:tileWidth/text()', namespaces=XMLNS)
		##logger.debug("DOM parsing iiif tile height coords for DRS2 object " + str(document_id) )
		#drs2TileHeights = dom.xpath('/mets:mets/mets:amdSec/mets:techMD/mets:mdWrap/mets:xmlData/premis:object/premis:objectCharacteristics/premis:objectCharacteristicsExtension/mix:mix/mix:BasicImageInformation/mix:SpecialFormatCharacteristics/mix:JPEG2000/mix:EncodingOptions/mix:Tiles/mix:tileHeight/text()', namespaces=XMLNS)
		##logger.debug("DOM iiif parsing COMPLETED for DRS2 object " + str(document_id) )

	if len(hollisCheck) > 0:
		hollisID = hollisCheck[0].strip()
		seeAlso = HOLLIS_PUBLIC_URL.format(hollisID.rjust(9,"0"))
		response = urllib2.urlopen(HOLLIS_API_URL+hollisID).read()
		response_data = re.sub('(?i)encoding=[\'\"]utf\-8[\'\"]','', response)
		response_doc = unicode(response_data, encoding="utf-8")
		mods_dom = etree.XML(response_doc)
		hollis_langs = set(mods_dom.xpath('/mods:mods/mods:language/mods:languageTerm/text()', namespaces=XMLNS))
		citeAs = mods_dom.xpath('/mods:mods/mods:note[@type="preferred citation"]/text()', namespaces=XMLNS)
		titleInfo = mods_dom.xpath('/mods:mods/mods:titleInfo/mods:title/text()', namespaces=XMLNS)[0]
		if len(citeAs) > 0:
			manifestLabel = citeAs[0] + " " + titleInfo
		# intersect both sets and determine if there are common elements
		if len(hollis_langs & right_to_left_langs) > 0:
			viewingDirection = 'right-to-left'

	manifest_uri = manifestUriBase + "%s:%s" % (source, document_id)

	#logger.debug("dom check: images and structs..." )
	images = dom.xpath('/mets:mets/mets:fileSec/mets:fileGrp/mets:file[starts-with(@MIMETYPE, "image/")]', namespaces=XMLNS)
        struct = dom.xpath('/mets:mets/mets:structMap/mets:div[@TYPE="CITATION"]/mets:div', namespaces=XMLNS)
	#logger.debug("dom check: images and structs found." )

	# Check if the object has a stitched version(s) already made.  Use only those
	# randy intentionally broke this so stitched objects now look weird. -cg
	#for st in struct:
	#	stitchCheck = st.xpath('./@LABEL[contains(., "stitched")]', namespaces=XMLNS)
	#	if stitchCheck:
	#		struct = st
	#		break

	for img in images:
		imageHash[img.xpath('./@ID', namespaces=XMLNS)[0]] = {"img": img.xpath('./mets:FLocat/@xlink:href', namespaces = XMLNS)[0], "mime": img.attrib['MIMETYPE']}

	rangeList = []
	rangeInfo = []
	for st in struct:
		ranges = process_struct_divs(st, [])
		if ranges: #dedup thumbnail bar
			rangeList.extend(ranges)

	rangeInfo = [{"Table of Contents" : rangeList}]
	logger.debug(rangeInfo)

	mfjson = {
		"@context":"http://www.shared-canvas.org/ns/context.json",
		"@id": manifest_uri,
		"@type":"sc:Manifest",
		"label":manifestLabel,
		#"attribution":attribution,
		"license":license,
		"sequences": [
			{
				"@id": manifest_uri + "/sequence/normal.json",
				"@type": "sc:Sequence",
				"viewingHint":viewingHint,
				"viewingDirection":viewingDirection,
			}
		],
		"structures": []
	}

	if (seeAlso != u""):
		mfjson["related"] = seeAlso

	canvases = []
	infocount = 0
	for cvs in canvasInfo:
		if isDrs1:
			#logger.debug("making info.json call for image id " + cvs['image']  )
                	response = webclient.get(imageUriBase + cvs['image'] + imageInfoSuffix, cookie)
                	infojson = json.load(response)
		else:
			#logger.debug("Getting iiif cords internally from DRS2 object for image id " + cvs['image'] )
			infojson= {}
			try:
				infojson['width'] = drs2ImageWidths[infocount]
				infojson['height'] = drs2ImageHeights[infocount]
				#infojson['tile_width'] = drs2TileWidths[infocount]
				#infojson['tile_height'] = drs2TileHeights[infocount]
				#note replace this w/ drs2InfoFormats
				infojson['formats'] = ['jpg']
				infojson['scale_factors'] = [1]
				infocount = infocount + 1
			except: # image not in drs
				infojson['width'] = ''
				infojson['height'] = ''
				infojson['height'] = ''
				#infojson['tile_width'] = ''
				#infojson['tile_height'] = ''
				infojson['formats'] = ['jpg']
				infojson['scale_factors'] = [1]
				infocount = infocount + 1

                if "gif" in infojson['formats']:
                        fmt = "image/gif"
                elif "jpg" in infojson['formats']:
                        fmt = "image/jpeg"

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
						"format": fmt,
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

	# build table of contents using Range and Structures
	create_ranges(rangeInfo, manifest_uri, manifest_uri)

	mfjson['sequences'][0]['canvases'] = canvases
	mfjson['structures'] = rangesJsonList

	#logger.debug("Dumping json for DRS2 object " + str(document_id) )
	output = json.dumps(mfjson, indent=4, sort_keys=True)
	#logger.debug("Dumping complete for DRS2 object " + str(document_id) )
	return output

if __name__ == "__main__":
	if (len(sys.argv) < 5):
		sys.stderr.write('not enough args\n')
		sys.stderr.write('usage: mets.py [input] [manifest_identifier] [data_source] [host]\n')
		sys.exit(0)

	inputfile = sys.argv[1]
	document_id = sys.argv[2]
	source = sys.argv[3]
	outputfile = source + '-' + document_id +  ".json"
	host = sys.argv[4]

	fh = file(inputfile)
	data = fh.read()
	fh.close()

	output = main(data, document_id, source, host)
	fh = file(outputfile, 'w')
	fh.write(output)
	fh.close()
