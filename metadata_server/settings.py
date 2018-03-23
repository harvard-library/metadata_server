"""
Django settings for metadata_server project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import dotenv
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
dotenv.load_dotenv(os.path.join(BASE_DIR, '.env'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = TEMPLATE_DEBUG = os.environ.has_key('DEBUG')

# Elasticsearch vars
ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL', 'localhost:9200')
ELASTICSEARCH_INDEX = os.environ.get('ELASTICSEARCH_INDEX', 'manifests')
ELASTICSEARCH_MAX_HIT_SIZE = os.environ.get('ELASTICSEARCH_MAX_HIT_SIZE', 5000)

# Solr vars
SOLR_BASE =  os.environ.get('SOLR_BASE', 'http://drs2-services.lib.harvard.edu:18280/solr/drs2-collection/')
SOLR_QUERY_PREFIX = 'select?q=object_id_num%3A'
SOLR_OBJ_QUERY = '&fq=doc_type_string%3Aobject+AND+object_huldrsadmin_status_string%3Acurrent+AND+object_huldrsadmin_contentModelID_string%3ACMID-4.0&fl=object_id_num%2C+object_huldrsadmin_contentModelID_string%2C+object_structmap_raw%2C++object_mets_label_text%2C+object_urn_raw_sort%2C+object_file_sec_raw%2C+object_huldrsadmin_harvardMetadataLink_raw_sort%2C+object_huldrsadmin_relatedLink_raw_sort%2C+object_huldrsadmin_ownerCode_string%2C+object_huldrsadmin_owner_organization_name_raw%2C+object_mets_lastModDate_date%2C+object_huldrsadmin_insertionDate_date%2C+object_mets_createDate_date%2C+object_mods_*&wt=json'
SOLR_FILE_QUERY = '&sort=file_id_num%20asc%2C+solr_id%20asc&fl=file_path_raw%2C+file_id_num%2C+object_huldrsadmin_accessFlag_string%2C+file_mix_imageWidth_num%2C+file_mix_imageHeight_num%2C+file_mix_tileWidth_num%2C+file_mix_tileHeight_num%2C+file_huldrsadmin_role_string%2C+object_huldrsadmin_contentModelID_string%2C+file_huldrsadmin_status_string%2C+object_huldrsadmin_status_string&wt=json&rows=100'
SOLR_AMS_QUERY = '&fq=doc_type_string%3Aobject+AND+object_huldrsadmin_status_string%3Acurrent+AND+object_huldrsadmin_contentModelID_string%3ACMID-4.0&fl=object_id_num%2C+object_huldrsadmin_accessFlag_string&wt=json'
SOLR_CURSORMARK = "&cursorMark="

#solr kazoo params
SOLR_Q = "object_id_num" 
SOLR_FQ = "doc_type_string%3Aobject+AND+object_huldrsadmin_status_string%3Acurrent+AND+object_huldrsadmin_contentModelID_string%3ACMID-4.0&fl=object_id_num%2C+object_huldrsadmin_contentModelID_string%2C+object_structmap_raw%2C++object_mets_label_text%2C+object_urn_raw_sort%2C+object_file_sec_raw%2C+object_huldrsadmin_harvardMetadataLink_raw_sort%2C+object_huldrsadmin_relatedLink_raw_sort%2C+object_huldrsadmin_ownerCode_string%2C+object_huldrsadmin_owner_organization_name_raw%2C+object_mets_lastModDate_date%2C+object_huldrsadmin_insertionDate_date%2C+object_mets_createDate_date%2C+object_mods_*" 
SOLR_SORT = "file_id_num%20asc%2C+solr_id%20asc"
SOLR_FL =  "file_path_raw%2C+file_id_num%2C+object_huldrsadmin_accessFlag_string%2C+file_mix_imageWidth_num%2C+file_mix_imageHeight_num%2C+file_mix_tileWidth_num%2C+file_mix_tileHeight_num%2C+file_huldrsadmin_role_string%2C+object_huldrsadmin_contentModelID_string%2C+file_huldrsadmin_status_string%2C+object_huldrsadmin_status_string"
SOLR_ROWS = 100
SOLR_WT = "json"
SOLR_COLLECTION = "drs2-collection"

#Mets drs2 prefix headers
METS_HEADER = "<?xml version=\"1.0\" encoding=\"UTF-8\"?><mets xmlns:hulDrsRights=\"http://hul.harvard.edu/ois/xml/ns/hulDrsRights\" xmlns=\"http://www.loc.gov/METS/\" xmlns:hulDrsAdmin=\"http://hul.harvard.edu/ois/xml/ns/hulDrsAdmin\" xmlns:hulDrsBatch=\"http://hul.harvard.edu/ois/xml/ns/hulDrsBatch\" xmlns:textMD=\"info:lc/xmlns/textMD-v3\" xmlns:fits=\"http://hul.harvard.edu/ois/xml/ns/fits/fits_output\" xmlns:premis=\"info:lc/xmlns/premis-v2\" xmlns:mix=\"http://www.loc.gov/mix/v20\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:schemaLocation=\"http://hul.harvard.edu/ois/xml/ns/hulDrsRights http://hul.harvard.edu/ois/xml/xsd/drs/hulDrsRights.xsd http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/mets.xsd http://hul.harvard.edu/ois/xml/ns/hulDrsAdmin http://hul.harvard.edu/ois/xml/xsd/drs/hulDrsAdmin.xsd http://hul.harvard.edu/ois/xml/ns/hulDrsBatch http://hul.harvard.edu/ois/xml/xsd/drs/hulDrsBatch.xsd info:lc/xmlns/textMD-v3 http://www.loc.gov/standards/textMD/textMD-v3.01a.xsd http://hul.harvard.edu/ois/xml/ns/fits/fits_output http://hul.harvard.edu/ois/xml/xsd/fits/fits_output.xsd info:lc/xmlns/premis-v2 http://www.loc.gov/standards/premis/premis.xsd http://www.loc.gov/mix/v20 http://www.loc.gov/standards/mix/mix20/mix20.xsd\" TYPE=\"PDS DOCUMENT\" PROFILE=\"HUL\"><metsHdr></metsHdr><premis:agentName>DRS2</premis:agentName>"
METS_FOOTER = "</mets>"


ALLOWED_HOSTS = [x for x in os.environ.get('ALLOWED_HOSTS','').split(";") if x != '']

HTTP_PROTOCOL = os.environ.get('HTTP_PROTOCOL', 'http')

IIIF = {
    "imageUriBase":     HTTP_PROTOCOL + '://' + os.environ.get('IMAGE_URI_BASE', 'ids.lib.harvard.edu/ids/iiif/'),
    "serviceBase":      HTTP_PROTOCOL + '://' + os.environ.get('SERVICE_BASE', 'ids.lib.harvard.edu/ids/iiif/'),
    "imageUriSuffix":   "/full/full/0/native.jpg",
    "imageInfoSuffix":  "/info.json",
    "thumbnailSuffix":	"/full/,150/0/native.jpg",
    "manifestUriTmpl":  HTTP_PROTOCOL + "://%s/manifests/",
    "profileLevel":     "http://library.stanford.edu/iiif/image-api/1.1/conformance.html#level1",
    "context": 		"http://iiif.io/api/image/1/context.json",	
    "logo":		HTTP_PROTOCOL + "://%s/static/manifests/harvard_logo.jpg",
    "license":		"http://nrs.harvard.edu/urn-3:hul.ois:hlviewerterms"
}

#permitted subnet for iiif index/delete/refresh methods
IIIF_MGMT_SUBNET = os.environ.get('IIIF_MGMT_SUBNET', '128.103.151.0/24')


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'manifests',
    'proxy',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'manifests.exception_logging.ExceptionLoggingMiddleware',
)

ROOT_URLCONF = 'metadata_server.urls'

WSGI_APPLICATION = 'metadata_server.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR,'static/')
STATIC_URL = '/static/'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)


#logging setup
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'debug.log'),
        },
    },
    'loggers': {
        'manifests': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
