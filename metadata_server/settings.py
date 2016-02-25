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

ALLOWED_HOSTS = [x for x in os.environ.get('ALLOWED_HOSTS','').split(";") if x != '']

IIIF = {
    "imageUriBase":     os.environ.get('IMAGE_URI_BASE', 'http://ids.lib.harvard.edu/ids/iiif/'),
    "serviceBase":      os.environ.get('SERVICE_BASE', 'http://ids.lib.harvard.edu/ids/iiif/'),
    "imageUriSuffix":   "/full/full/full/native",
    "imageInfoSuffix":  "/info.json",
    "manifestUriTmpl":  "http://%s/manifests/",
    "profileLevel":     "http://library.stanford.edu/iiif/image-api/1.1/conformance.html#level1"
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
