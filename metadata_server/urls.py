from django.conf.urls import include, url

from manifests import views

urlpatterns = [
    # Examples:
    # url(r'^$', 'metadata_server.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^manifests/', include('manifests.urls')),
    url(r'^demo$', views.demo, name="demo"),
    url(r'^proxy/', include('proxy.urls')),
    # Same terrible hack from manifests/urls.py, empty view_type is NON OPTIONAL
    url(r'^(?P<view_type>)images/(?P<filename>.*)$', views.get_image),
    url(r'^(?P<view_type>)+.*skins.*$', views.clean_url),
    url('^version/', views.version, name="version"),
    url('', views.version, name="version")
]
