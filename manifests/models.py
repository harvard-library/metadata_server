from django.db import models
from django.conf import settings
from elasticsearch import Elasticsearch
import certifi

# Create your models here.

ELASTICSEARCH_URL = settings.ELASTICSEARCH_URL
ELASTICSEARCH_INDEX = settings.ELASTICSEARCH_INDEX
ELASTICSEARCH_MAX_HIT_SIZE = settings.ELASTICSEARCH_MAX_HIT_SIZE
ELASTICSEARCH_SSL = settings.ELASTICSEARCH_SSL
ELASTICSEARCH_SSL_VERIFY = settings.ELASTICSEARCH_SSL_VERIFY

#indexes per doctype. now have to use separate indexes for elasticsearch 6.x+
INDEX_TYPE = {"drs": ELASTICSEARCH_INDEX, "via": "via", "hollis": "hollis", "huam" : "huam", "ext": "ext", "ids": "ids" }

# Connect to elasticsearch db
def get_connection():
      return Elasticsearch(ELASTICSEARCH_URL, use_ssl=ELASTICSEARCH_SSL, verify_certs=ELASTICSEARCH_SSL_VERIFY, ca_certs=certifi.where())

# Gets the content of a manifest, returns JSON
def get_manifest(manifest_id, source):
    es = get_connection()
    idx = get_index(source)
    return es.get(index=idx, doc_type=source, id=manifest_id)["_source"]

# Inserts JSON document into elasticsearch with the given manifest_id
# Either adds new document or replaces existing document
def add_or_update_manifest(manifest_id, document, source):
    es = get_connection()
    idx = get_index(source)
    es.index(index=idx, doc_type=source, id=manifest_id, body=document)

# Deletes manifest from elasticsearch (need to refresh index?)
def delete_manifest(manifest_id, source):
    es = get_connection()
    idx = get_index(source)
    es.delete(index=idx, doc_type=source, id=manifest_id)

# Checks if manifest exists in elasticsearch, returns boolean
def manifest_exists(manifest_id, source):
    es = get_connection()
    idx = get_index(source)
    return es.exists(index=idx, doc_type=source, id=manifest_id)

def get_all_manifest_ids_with_type(source):
    es = get_connection()
    idx = get_index(source)
    results = es.search(index=idx, doc_type=source, fields="[]", size=ELASTICSEARCH_MAX_HIT_SIZE)
    ids = []
    for r in results["hits"]["hits"]:
        ids.append(str(r["_id"]))
    return ids

def get_all_manifest_ids():
    es = get_connection()
    results = es.search(index=ELASTICSEARCH_INDEX, fields="[]", size=ELASTICSEARCH_MAX_HIT_SIZE)
    ids = []
    for r in results["hits"]["hits"]:
        ids.append(str(r["_id"]))
    return ids

def get_manifest_title(manifest_id, source):
    es = get_connection()
    idx = get_index(source)
    return es.get(index=idx, doc_type=source, id=manifest_id)["_source"]["label"]

#get appropriate index. now use separate indexes for elasticsearch 6.x+
def get_index(source):
    idx = INDEX_TYPE[source]
    if (idx == None):
        idx = ELASTICSEARCH_INDEX
    return idx
