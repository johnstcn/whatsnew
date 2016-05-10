from django.conf.urls import url
from django.contrib import admin
from django.views.generic import RedirectView

from . import views

app_name = 'whatsnew'
urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.AllSitesView.as_view(), {'nsfw': '0', 'tag': 'all'}, name='index'),
    url(r'^sites/$', views.AllSitesView.as_view(), {'nsfw': '0', 'tag': 'all'}, name='index'),
    url(r'^sites/(?P<tag>[\w-]*)/$', RedirectView.as_view(), {'nsfw': 0}, name='index'),
    url(r'^sites/(?P<tag>[\w-]*)/(?P<nsfw>\d)/$', views.AllSitesView.as_view(), name='index'),
    url(r'^view/(?P<site_update_id>\d+)/$', views.redirect_to_update, name='redirect_to_update'),
]
