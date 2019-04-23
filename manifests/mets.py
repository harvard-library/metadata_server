#!/usr/bin/python

from lxml import etree
import json, sys, re
import urllib2
from urllib import quote_plus
from django.conf import settings
from django.http import HttpResponse
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
thumbnailSuffix = settings.IIIF['thumbnailSuffix']
manifestUriTmpl = settings.IIIF['manifestUriTmpl']
serviceBase = settings.IIIF['serviceBase']
profileLevel = settings.IIIF['profileLevel']
serviceContext = settings.IIIF['context']

attribution = "Provided by Harvard University"
#license = "Use of this material is subject to our Terms of Use: http://nrs.harvard.edu/urn-3:hul.ois:hlviewerterms"
#license is set to just the urn for manifest validation purposes
license = settings.IIIF['license']

METS_API_URL = environ.get("METS_API_URL", "http://pds.lib.harvard.edu/pds/get/")
PDS_WS_URL = environ.get("PDS_WS_URL", "http://pds.lib.harvard.edu/pds/")
HOLLIS_API_URL = "http://webservices.lib.harvard.edu/rest/MODS/hollis/"
HOLLIS_PUBLIC_URL = "http://id.lib.harvard.edu/aleph/{0}/catalog"
 ## Add ISO639-2B language codes here where books are printed right-to-left (not just the language is read that way)
right_to_left_langs = set(['ara','heb'])

# List of mime types: ordering is as defined in pdx_util (internalMets.java), but with txt representations omitted.
MIME_HIERARCHY = ['image/jp2', 'image/jpx', 'image/jpeg', 'image/gif', 'image/tiff']
IIIF_MANIFEST_HOST = environ.get("IIIF_MANIFEST_HOST", "localhost")

DEBUG = environ.get("DEBUG",False)

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
			logger.debug("process_intermediate: processing int div: " + div.get('LABEL') )
                        my_range = process_intermediate(sd)
                if my_range:
			logger.debug("process_intermediate: appending ranges for int div: " + div.get('LABEL') )
                        new_ranges.append(my_range)
		else: #DELETE THIS
			logger.debug("process_intermediate: NOT appending ranges for int div: " + div.get('LABEL') )

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
		logger.debug("get_int_seq_val: first: " + first.get('LABEL') )
                first = first[0]

        if first.get('TYPE') == 'PAGE':
                first_vals = {"seq": first.get('ORDER'), "page": page_num(first)}

        # Drill down last page
        while last.get('TYPE') == 'INTERMEDIATE':
		logger.debug("get_int_seq_val: last: " + last.get('LABEL') )
                last = last[-1]

        if last.get('TYPE') == 'PAGE':
                last_vals = {"seq": last.get('ORDER'), "page": page_num(last)}

	logger.debug("get_int_seq_values: first: " + str(first_vals) + " last: " + str(last_vals) )
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
		logger.debug("process_st_divs: div: " + div.get('LABEL') )
		#logger.debug("process_st_divs: subdivs: " + str(subdivs) )
                if len(subdivs) > 0:
                        ranges.append(process_intermediate(div))
			logger.debug("process_st_divs: appended range of div: " + div.get('LABEL') )

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
			#dedup table of contents?
			if label == "Table of Contents":
				canvas_txt = manifest_uri + "/canvas/canvas-%s.json" % lc
				if canvas_txt not in canvases:
					canvases.append(canvas_txt)
			else:
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


### new methods (naomi) for iiif 2.0 toc
###################
#
# changes to create a prezi 2.0 table of contents
#
def translate_range(range_dict, prefix, manifest_uri):
    # assume it's a dict, and it has only one item
    k = list(range_dict.keys())[0]
    v = range_dict[k]
    parent_range = {
        '@id': '{0}/range/range-{1}.json'.format(manifest_uri, prefix),
        '@type': 'sc:Range',
        'label': k,
        'canvases': [],
        'ranges': [],
    }
    range_list = [parent_range]
    if isinstance(v, str):  # one canvas
        parent_range['canvases'].append('{0}/canvas/canvas-{1}.json'.format(
            manifest_uri, v))
    if isinstance(v, list): # v might be list of canvases or nested ranges
        for i, item in enumerate(v):  # assume v it's a list of str or dicts
            new_prefix = '{}-{}'.format(prefix, i)
            child_range, r_list = translate_range(item, new_prefix, manifest_uri)
            parent_range['ranges'].append(child_range['@id'])
            range_list += r_list
    # remove empty lists
    if not parent_range['canvases']:
        del parent_range['canvases']
    if not parent_range['ranges']:
        del parent_range['ranges']
    return parent_range, range_list

def translate_ranges(mets_ranges, manifest_uri):
    """
     returns list of iiif ranges
     mets_ranges: list of one dict
     manifest_uri: includes protocol://hostname:port/path_prefix
    """
    parent_range, child_range = translate_range(mets_ranges[0], '0', manifest_uri)
    toc = child_range[0]
    # per iiif prezi 2.0, table of contents should have viewingHint
    toc['viewingHint'] = 'top'
    return child_range
#
# changes to create a prezi 2.0 table of contents
#
###################


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

	global drs2ImageWidths
	drs2ImageWidths = []
	global drs2ImageHeights
	drs2ImageHeights = []
	global drs2AccessFlags
	drs2AccessFlags = []

	logo = settings.IIIF['logo'] % host

	drs2json = None
	if 'response' in data:
	#if 'object_structmap_raw' in data:
		drs2json = data['response']['docs'][0]
		data = settings.METS_HEADER + drs2json['object_file_sec_raw'] + \
                   drs2json['object_structmap_raw'] + settings.METS_FOOTER


	#logger.debug("LOADING object " + str(document_id) + " into the DOM tree" )
	data = re.sub('(?i)encoding=[\'\"]utf\-8[\'\"]','', data)
	utf8_parser = etree.XMLParser(encoding='utf-8')
	dom = etree.XML(data, parser=utf8_parser)
	#logger.debug("object " + str(document_id) + " LOADED into the DOM tree" )
	# Check if this is a DRS2 object since some things, like hollis ID are in a different location

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

	if drs2json != None:
		metsLabel = None
		if ('object_mets_label_text' in drs2json):
			metsLabel = drs2json['object_mets_label_text']
		if metsLabel != None:
			manifestLabel = metsLabel

		modsName = None
		if ('object_mods_name_text' in drs2json and len(drs2json['object_mods_name_text']) > 0):
			modsName = drs2json['object_mods_name_text'][0]
		modsPlace = None
		if ('object_mods_placeTerm_text' in drs2json and len(drs2json['object_mods_placeTerm_text']) > 1):
			modsPlace = drs2json['object_mods_placeTerm_text'][1]
		modsOrigin = None
		if ('object_mods_origin_text' in drs2json and len(drs2json['object_mods_origin_text']) > 0):
			modsOrigin = drs2json['object_mods_origin_text'][0]
		modsDate = None
		modsDateIssued = None
		if ('object_mods_dateIssued_date' in drs2json and len(drs2json['object_mods_dateIssued_date']) > 0):
			modsDateIssued = drs2json['object_mods_dateIssued_date'][0]
		modsPublisher = None
		if ('object_mods_publisher_text' in drs2json and len(drs2json['object_mods_publisher_text']) > 0):
			modsPublisher = drs2json['object_mods_publisher_text'][0]
		modsDateCreated = None
		if ('object_mods_dateCreated_date' in drs2json and len(drs2json['object_mods_dateCreated_date']) > 0):
			modsDateCreated = drs2json['object_mods_dateCreated_date'][0]
		modsTitle = None
		if ('object_mods_title_text' in drs2json and len(drs2json['object_mods_title_text']) > 0):
			modsTitle = drs2json['object_mods_title_text'][0]
		
		if modsDateIssued != None:
			modsDate = modsDateIssued
		if modsDateCreated != None:
			modsDate = modsDateCreated

		#assemble manifestLabel according to drs2 mods format
		if (modsTitle != None) and (metsLabel == None):
			if (modsTitle.endswith('.') is False):
				modsTitle = modsTitle + "."
			manifestLabel = modsTitle
			if modsName != None:
				if modsName.endswith('.'):
					manifestLabel = modsName + " " + manifestLabel
				else:
					manifestLabel = modsName + ". " + manifestLabel
			if modsPlace != None:
				manifestLabel = manifestLabel + " " + modsPlace
			if modsPublisher != None:
				if modsPublisher.endswith('.'): 
					modsPublisher = modsPublisher[:-1]
				if modsPlace != None:
					manifestLabel = manifestLabel + ": " + modsPublisher
				else:
					manifestLabel = manifestLabel + " " + modsPublisher
			if modsDate != None:
				if ( (modsPublisher != None) and (modsPlace != None) ):
					manifestLabel = manifestLabel + ", " + modsDate
				else:
					manifestLabel = manifestLabel + " " + modsDate
			if (manifestLabel.endswith('.') is False):
				manifestLabel = manifestLabel + "."

	
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

	#logger.debug("dom check: hollis check..." )
	hollisCheck = dom.xpath('/mets:mets/mets:amdSec/mets:techMD/mets:mdWrap/mets:xmlData/hulDrsAdmin:hulDrsAdmin/hulDrsAdmin:drsObject/hulDrsAdmin:harvardMetadataLinks/hulDrsAdmin:metadataIdentifier[../hulDrsAdmin:metadataType/text()="Aleph"]/text()', namespaces=XMLNS)

	if len(hollisCheck) > 0:
		hollisID = hollisCheck[0].strip()
		seeAlso = HOLLIS_PUBLIC_URL.format(hollisID.rjust(9,"0"))
		try:
			response = urllib2.urlopen(HOLLIS_API_URL+hollisID).read()
		except:
			logger.debug("HOLLIS lookup failed for Hollis id: " + hollisID)
		else:
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
	# this has been intentionally removed to show full drs structure instead -cg
	#for st in struct:
	#	stitchCheck = st.xpath('./@LABEL[contains(., "stitched")]', namespaces=XMLNS)
	#	if stitchCheck:
	#		struct = st
	#		break

	for img in images:
		imageHash[img.xpath('./@ID', namespaces=XMLNS)[0]] = {"img": img.xpath('./mets:FLocat/@xlink:href', namespaces = XMLNS)[0], "mime": img.attrib['MIMETYPE']}

	#check solr, make call for image md from there if above fails
	if ( (len(drs2ImageWidths) == 0) and (len(drs2ImageHeights) == 0) ):
        	metadata_url_base = settings.SOLR_BASE + settings.SOLR_QUERY_PREFIX + document_id + settings.SOLR_FILE_QUERY + settings.SOLR_CURSORMARK
		cursormark_val = "*"

		not_paged = True 
		while not_paged:
        	  try:
			metadata_url =  metadata_url_base + cursormark_val
            		response = webclient.get(metadata_url, cookie)
        	  except urllib2.HTTPError, err:
			not_paged = False
            		logger.debug("Failed solr file metadata request %s" % metadata_url)
            		return (False, HttpResponse("The document ID %s does not exist in solr index" % document_id, status=404))
        	  md_json = json.loads(response.read())
		  for md in md_json['response']['docs']:
		  #for md in md_json:
			if (('object_huldrsadmin_accessFlag_string' in md) and ('file_id_num' not in md)):
				access_flag = md['object_huldrsadmin_accessFlag_string']
				if access_flag == "N":
				  return (False, HttpResponse("Document ID %s is not intended for delivery and cannot be indexed." % document_id, status=404))
				else:
				  continue
			if (('file_mix_imageHeight_num' in md) and ('file_mix_imageWidth_num' in md)):
				drs2ImageHeights.append(md['file_mix_imageHeight_num'])
				drs2ImageWidths.append(md['file_mix_imageWidth_num'])
				drs2AccessFlags.append(md['object_huldrsadmin_accessFlag_string'])
			else: #call ids (info.json request)
				file_ext = md['file_path_raw'][-3:]
				if (file_ext == 'jp2' or file_ext == 'tif' or file_ext == 'jpg' or file_ext == 'gif'):
				  logger.debug("solr missing image dimensions - making info.json call for image id " + str(md['file_id_num']) )
				  if 'object_huldrsadmin_accessFlag_string' in md:
				    drs2AccessFlags.append(md['object_huldrsadmin_accessFlag_string'])
				  try: 
				    info_resp = webclient.get(imageUriBase.replace("https","http") + str(md['file_id_num']) + imageInfoSuffix, cookie)
				    iiif_info = json.load(info_resp)
				    drs2ImageHeights.append(iiif_info['height'])
				    drs2ImageWidths.append(iiif_info['width'])
				  except urllib2.HTTPError, err:
				    logger.debug("failed to get image dimensions for image id " + str(md['file_id_num']) )
				else:
				  continue
		  next_cursormark = quote_plus(md_json['nextCursorMark'])
		  if next_cursormark == cursormark_val:
			not_paged = False
		  cursormark_val = next_cursormark
			
	rangeList = []
	rangeInfo = []
	for st in struct:
		ranges = process_struct_divs(st, [])
		if ranges: #dedup thumbnail bar
			rangeList.extend(ranges)

	rangeInfo = [{"Table of Contents" : rangeList}]

	mfjson = {
		"@context":"http://iiif.io/api/presentation/2/context.json",
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
				"viewingDirection":viewingDirection,
			}
		],
		"structures": []
	}

	if (seeAlso != u""):
		mfjson["related"] = seeAlso

	canvases = []
	infocount = 0
	uniqCanvases = {}
	for cvs in canvasInfo:
		infojson= {}
		try:
			infojson['width'] = int(drs2ImageWidths[infocount])
			infojson['height'] = int(drs2ImageHeights[infocount])
			#infojson['tile_width'] = int(drs2TileWidths[infocount])
			#infojson['tile_height'] = int(drs2TileHeights[infocount])
			#note replace this w/ drs2InfoFormats
			infojson['formats'] = ['jpg']
			infojson['scale_factors'] = [1]
			infojson['access_flag'] = drs2AccessFlags[infocount]
			infocount = infocount + 1
		except: # image not in drs
			try:
				logger.debug("missing image dimensions - making info.json call for image id " + cvs['image']  )
				response = webclient.get(imageUriBase.replace("https","http") + cvs['image'] + imageInfoSuffix, cookie)
				infojson = json.load(response)
				infocount = infocount + 1
			except:
				#infojson['width'] = ''
				#infojson['height'] = ''
				#infojson['tile_width'] = ''
				#infojson['tile_height'] = ''
				infojson['formats'] = ['jpg']
				infojson['scale_factors'] = [1]
				infocount = infocount + 1

		if 'access_flag' in infojson:
			if infojson['access_flag'] == "N":
			  continue
		formats = []
		if 'formats' in infojson:
			formats = infojson['formats']
		else:
			formats = infojson['profile'][1]['formats']
                if "gif" in formats:
                        fmt = "image/gif"
                elif "jpg" in formats:
                        fmt = "image/jpeg"

		cvsjson = {
			"@id": manifest_uri + "/canvas/canvas-%s.json" % cvs['image'],
			"@type": "sc:Canvas",
			"label": cvs['label'],
			#"height": infojson['height'],
			#"width": infojson['width'],
			"images": [
				{
					"@id":manifest_uri+"/annotation/anno-%s.json" % cvs['image'],
					"@type": "oa:Annotation",
					"motivation": "sc:painting",
					"resource": {
						"@id": imageUriBase + cvs['image'] + imageUriSuffix,
						"@type": "dctypes:Image",
						"format": fmt,
						#"height": infojson['height'],
						#"width": infojson['width'],
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
		if ( ('height' in infojson) and ('width' in infojson) ):
			cvsjson['height'] = infojson['height']
			cvsjson['width'] = infojson['width']
			cvsjson['images'][0]['resource']['height'] = infojson['height']
			cvsjson['images'][0]['resource']['width'] = infojson['width']

		#dedup split node canvases
		if uniqCanvases.has_key(cvs['image']) == False:
			canvases.append(cvsjson)
			uniqCanvases[cvs['image']] = True 

	# build table of contents using Range and Structures
	#create_ranges(rangeInfo, manifest_uri, manifest_uri)
	iiif2_toc = translate_ranges(rangeInfo, manifest_uri)

	mfjson['sequences'][0]['canvases'] = canvases
	#mfjson['structures'] = rangesJsonList
	mfjson['structures'] = iiif2_toc

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
