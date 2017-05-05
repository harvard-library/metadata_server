from django.conf.urls import patterns, include, url

from django.contrib import admin
from manifests import views
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'metadata_server.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^manifests/', include('manifests.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^demo$', views.demo, name="demo"),
    url(r'^proxy/', include('proxy.urls')),
    url(r'^inbox/', include('inbox.urls')),
    url(r'^inbox', include('inbox.urls')),
    # Same terrible hack from manifests/urls.py, empty view_type is NON OPTIONAL
    url(r'^(?P<view_type>)images/(?P<filename>.*)$', views.get_image),
    url(r'^(?P<view_type>)+.*skins.*$', views.clean_url),
)
