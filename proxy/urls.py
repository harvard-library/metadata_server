from django.conf.urls import url
from django.conf import settings

from proxy import views

urlpatterns = [
                       url(r'^(?P<method>[^/]*)/(?P<record_id>[^/?]*)$', views.proxy, name='proxy')
                       ]
