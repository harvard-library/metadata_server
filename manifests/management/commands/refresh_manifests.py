from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from os import environ
import json
import urllib2
import requests
import manifests.webclient
from manifests import models, views


METS_DRS_URL = environ.get("METS_DRS_URL", "http://fds.lib.harvard.edu/fds/deliver/")
METS_API_URL = environ.get("METS_API_URL", "http://pds.lib.harvard.edu/pds/get/")
MODS_DRS_URL = "http://webservices.lib.harvard.edu/rest/MODS/"
HUAM_API_URL = "http://api.harvardartmuseums.org/object/"
HUAM_API_KEY = environ["HUAM_API_KEY"]
COOKIE_DOMAIN = environ.get("COOKIE_DOMAIN", ".hul.harvard.edu")
PDS_VIEW_URL = environ.get("PDS_VIEW_URL", "http://pds.lib.harvard.edu/pds/view/")
IIIF_MANIFEST_HOST = environ.get("IIIF_MANIFEST_HOST")

sources = {"drs": "mets", "via": "mods", "hollis": "mods", "huam" : "huam"}

class Command(BaseCommand):
    help = """Refresh manifests from metadata sources.
    This command has three modes of operation:

        * If no argument, refresh "drs" source manifests
        * If a source, refresh all manifests belonging to that source
        * If a single item id (source:id_number), refresh that manifest
    """

    def handle(self, *args, **options):

        if len(args) == 0:
            source = "drs"
        else:
            source = args[0]

        if ":" in source:
            (source, single_id) = source.split(":")
            document_ids = (single_id,)
        else:
            document_ids = models.get_all_manifest_ids_with_type(source)
        for id in document_ids:
            self.stdout.write("Starting {0}:{1}".format(source, id))
            try:
                (success, response_doc, real_id, real_source) = views.get_manifest(id, source, True, IIIF_MANIFEST_HOST, None)
            except (urllib2.HTTPError, urllib2.URLError) as e:
                self.stdout.write( "{0}:{1} failed due to HTTPError:\n".format(source, id))
                self.stdout.write("\t{0}".format(e.reason))
                success = False

            if success:
                self.stdout.write("{0}:{1} successfully refreshed\n".format(source, id))
            else:
                self.stdout.write("{0}:{1} FAILED to refresh\n".format(source, id))
