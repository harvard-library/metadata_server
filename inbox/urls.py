from django.conf.urls import patterns, url
from django.conf import settings

from inbox import views

#urlpatterns = patterns('',
#    url(r'^demo$', views.demo, name='demo'),
#    url(r'^(?P<view_type>view(-dev)?)/(?P<document_id>([a-z]+:[^;]+;?)+)$', views.view, name='view'),
#    url(r'^(?P<document_id>[a-z]+:[A-Za-z\d]+)$', views.manifest, name='manifest'),


# Restricted URLS available only on dev/qa servers
# if settings.DEBUG:
# methods now restricted via ip subnet
#urlpatterns += patterns('',
#                            url(r'^index(?:/(?P<source>[a-zA-z]+))?/$', views.index, name="index"),
#                            url(r'^delete/(?P<document_id>[a-z]+:[A-Za-z\d]+)$', views.delete, name='delete'),
#                            url(r'^refresh/(?P<document_id>[a-z]+:[A-Za-z\d]+)$', views.refresh, name='refresh'),
#                            url(r'^refresh/source/(?P<source>[a-z]+)$', views.refresh_by_source, name='refresh_by_source'),)
