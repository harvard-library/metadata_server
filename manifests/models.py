from django.db import models
from django.conf import settings
from elasticsearch import Elasticsearch

# Create your models here.

ELASTICSEARCH_URL = settings.ELASTICSEARCH_URL
ELASTICSEARCH_INDEX = settings.ELASTICSEARCH_INDEX
ELASTICSEARCH_MAX_HIT_SIZE = settings.ELASTICSEARCH_MAX_HIT_SIZE

# Connect to elasticsearch db
def get_connection():
    return Elasticsearch(ELASTICSEARCH_URL, use_ssl=True)

# Gets the content of a manifest, returns JSON
def get_manifest(manifest_id, source):
    es = get_connection()
    return es.get(index=ELASTICSEARCH_INDEX, doc_type=source, id=manifest_id)["_source"]

# Inserts JSON document into elasticsearch with the given manifest_id
# Either adds new document or replaces existing document
def add_or_update_manifest(manifest_id, document, source):
    es = get_connection()
    es.index(index=ELASTICSEARCH_INDEX, doc_type=source, id=manifest_id, body=document)

# Deletes manifest from elasticsearch (need to refresh index?)
def delete_manifest(manifest_id, source):
    es = get_connection()
    es.delete(index=ELASTICSEARCH_INDEX, doc_type=source, id=manifest_id)

# Checks if manifest exists in elasticsearch, returns boolean
def manifest_exists(manifest_id, source):
    es = get_connection()
    return es.exists(index=ELASTICSEARCH_INDEX, doc_type=source, id=manifest_id)

def get_all_manifest_ids_with_type(source):
    es = get_connection()
    results = es.search(index=ELASTICSEARCH_INDEX, doc_type=source, fields="[]", size=ELASTICSEARCH_MAX_HIT_SIZE)
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
    return es.get(index=ELASTICSEARCH_INDEX, doc_type=source, id=manifest_id)["_source"]["label"]
