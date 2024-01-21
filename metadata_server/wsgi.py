"""
WSGI config for metadata_server project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "metadata_server.settings")

import collections.abc
# imports for python 3.10 and higher.
collections.Iterator = collections.abc.Iterator
collections.Iterable = collections.abc.Iterable
collections.Mapping = collections.abc.Mapping
collections.MutableSet = collections.abc.MutableSet
collections.MutableMapping = collections.abc.MutableMapping

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
