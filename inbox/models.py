from django.db import models
from django.conf import settings
from elasticsearch import Elasticsearch

# Create your models here.

ELASTICSEARCH_URL = settings.ELASTICSEARCH_URL
ELASTICSEARCH_INDEX = "notifications"
ELASTICSEARCH_MAX_HIT_SIZE = settings.ELASTICSEARCH_MAX_HIT_SIZE

# Connect to elasticsearch db
def get_connection():
    return Elasticsearch(ELASTICSEARCH_URL)

# Gets the content of a notification, returns JSON
def get_notification(notification_id, source):
    es = get_connection()
    return es.get(index=ELASTICSEARCH_INDEX, doc_type=source, id=notification_id)["_source"]

# Inserts JSON document into elasticsearch with the given notification_id
# Either adds new document or replaces existing document
def add_or_update_notification(notification_id, document, source):
    es = get_connection()
    es.index(index=ELASTICSEARCH_INDEX, doc_type=source, id=notification_id, body=document)

# Deletes notification from elasticsearch (need to refresh index?)
def delete_notification(notification_id, source):
    es = get_connection()
    es.delete(index=ELASTICSEARCH_INDEX, doc_type=source, id=notification_id)

# Checks if notification exists in elasticsearch, returns boolean
def notification_exists(notification_id, source):
    es = get_connection()
    return es.exists(index=ELASTICSEARCH_INDEX, doc_type=source, id=notification_id)

def get_all_notification_ids_for_target(target, source):
    es = get_connection()
    results = es.search(index=ELASTICSEARCH_INDEX, doc_type=source, fields="[]", 
      body={ 'query':{ 'match':{ 'target': target } } }, size=ELASTICSEARCH_MAX_HIT_SIZE)
    ids = []
    for r in results["hits"]["hits"]:
        ids.append(str(r["_id"]))
    return ids

def get_all_notification_ids():
    es = get_connection()
    results = es.search(index=ELASTICSEARCH_INDEX, fields="[]", size=ELASTICSEARCH_MAX_HIT_SIZE)
    ids = []
    for r in results["hits"]["hits"]:
        ids.append(str(r["_id"]))
    return ids

def get_notification_title(notification_id, source):
    es = get_connection()
    return es.get(index=ELASTICSEARCH_INDEX, doc_type=source, id=notification_id)["_source"]["label"]
