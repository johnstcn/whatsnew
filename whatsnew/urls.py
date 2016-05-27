from django.conf.urls import url
from django.contrib import admin

from . import views

app_name = 'whatsnew'
urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$',views.SitesView.as_view(), {'nsfw': '0', 'tag': 'all', 'watched': '0'}, name='index'),
    url(r'^sites/(?P<tag>[\w-]*)/(?P<nsfw>\d)/$', views.SitesView.as_view(), {'watched': '0'}, name='index'),
    url(r'^sites/(?P<tag>[\w-]*)/(?P<nsfw>\d)/(?P<watched>\d)/$', views.SitesView.as_view(), name='index'),
    url(r'^view/(?P<site_update_id>\d+)/$', views.redirect_to_update, name='redirect_to_update'),
    url(r'^watch/(?P<site_id>\d+)/$', views.watch, name='watch'),
    url(r'^unwatch/(?P<site_id>\d+)/$', views.unwatch, name='unwatch')
]
