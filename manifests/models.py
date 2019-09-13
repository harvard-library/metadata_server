from django.db import models
from django.conf import settings
import certifi
import ssl
import json
from pymongo import MongoClient

MONGO_URL = settings.MONGO_URL
MONGO_INDEX = settings.MONGO_INDEX
MONGO_SSL_CERT = settings.MONGO_SSL_CERT

#indexes per doctype. now have to use separate indexes for elasticsearch 6.x+
INDEX_TYPE = {"drs": MONGO_INDEX, "via": "via", "hollis": "hollis", "huam" : "huam", "ext": "ext", "ids": "ids" }

#Connect to mongo db
def get_connection():
  client = MongoClient(MONGO_URL, ssl=True, ssl_cert_reqs=ssl.CERT_REQUIRED, ssl_ca_certs=MONGO_SSL_CERT)
  return client

# Gets the content of a manifest, returns JSON
def get_manifest(manifest_id, source):
  mg = get_connection()
  idx = get_index(source)
  db = mg["manifests"]
  col = db[idx]
  query  = { "id": manifest_id }
  doc = col.find(query)
  manifest = json.loads(doc[0]['manifest'])
  mg.close()
  return manifest

# Inserts JSON document into elasticsearch with the given manifest_id
# Either adds new document or replaces existing document
def add_or_update_manifest(manifest_id, document, source):
  mg = get_connection()
  idx = get_index(source)
  db = mg["manifests"]
  col = db[idx]
  record = { "id": manifest_id , "manifest": document }
  col.insert_one(record)
  mg.close()

# Deletes manifest from mongo (need to refresh index?)
def delete_manifest(manifest_id, source):
  mg  = get_connection()
  idx = get_index(source)
  db = mg["manifests"]
  query  = { "id": manifest_id }
  col = db[idx]
  col.delete_one(query)
  mg.close()

# Checks if manifest exists in elasticsearch, returns boolean
def manifest_exists(manifest_id, source):
  mg = get_connection()
  idx = get_index(source)
  db = mg["manifests"]
  col = db[idx]
  query  = { "id": manifest_id }
  doc = col.find_one(query)  
  mg.close()
  if (doc == None):
    return False
  else:
   return True

def get_all_manifest_ids_with_type(source):
  mg = get_connection()
  idx = get_index(source)
  db = mg["manifests"]
  col = db[idx]
  ids = []
  manifests = col.find()
  for m in manifests:
    ids.append(str(m['id'])) 
  mg.close()
  return ids

def get_manifest_title(manifest_id, source):
  mg = get_connection()
  idx = get_index(source)
  db = mg["manifests"]
  col = db[idx]
  query  = { "id": manifest_id }
  doc = col.find(query)
  manifest = doc[0]['manifest']
  mg.close()
  mf = json.loads(manifest)
  return mf["label"]

#get appropriate collection
def get_index(source):
    idx = INDEX_TYPE[source]
    if (idx == None):
        idx = MONGO_INDEX
    return idx
