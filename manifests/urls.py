from django.conf.urls import url
from django.conf import settings

from manifests import views

urlpatterns = [
    url(r'^demo$', views.demo, name='demo'),
    url(r'^health$', views.healthcheck, name='healthcheck'),
    url(r'^(?P<view_type>view(-dev)?)/(?P<document_id>([a-z]+:[^;]+;?)+)$', views.view, name='view'),
    url(r'^(?P<document_id>[a-z]+:[A-Za-z\d]+)$', views.manifest, name='manifest'),



    # probably won't find a better solution for images because won't actually serve
    # HTML pages with mirador out of django (it's just for testing/demo purposes)
    url(r'^(?P<view_type>view(-dev|-annotator|-m1|-m2)?)/images/(?P<filename>.*)$', views.get_image),
    url(r'^(?P<view_type>view(-dev|-annotator|-m1|-m2)?)/+.*skins.*$', views.clean_url),

# Restricted URLS available only on dev/qa servers
# if settings.DEBUG:
# methods now restricted via ip subnet
    url(r'^index(?:/(?P<source>[a-zA-z]+))?/$', views.index, name="index"),
    url(r'^delete/(?P<document_id>[a-z]+:[A-Za-z\d]+)$', views.delete, name='delete'),
    url(r'^refresh/(?P<document_id>[a-z]+:[A-Za-z\d]+)$', views.refresh, name='refresh'),
    url(r'^refresh/source/(?P<source>[a-z]+)$', views.refresh_by_source, name='refresh_by_source')
]
