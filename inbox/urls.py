from django.conf.urls import patterns, url
from django.conf import settings

from inbox import views

urlpatterns = patterns('', 
		url(r'^$', views.index, name='index'),
		url(r'^delete/(?P<notification_id>[a-z]+:[A-Za-z\d]+)$', views.delete, name='delete'),
                url(r'^empty$', views.empty, name='empty') ),
		url(r'^(?P<notification_id>[A-Za-z\d]+)$', views.get_notification)
	      )

