from django.conf.urls import url
from django.contrib import admin
from django.views.generic import RedirectView

from . import views

app_name = 'whatsnew'
urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', RedirectView.as_view(url='/sites/all/0/'), name='index'),
    url(r'^sites/$', RedirectView.as_view(url='/sites/all/0/'), name='index'),
    url(r'^sites/(?P<tag>[\w-]*)/$',
        RedirectView.as_view(url='./0/'),
        name='index'),
    url(r'^sites/(?P<tag>[\w-]*)/(?P<nsfw>\d)/$',
        views.SitesView.as_view(),
        name='index'),
    url(r'^view/(?P<site_update_id>\d+)/$',
        views.redirect_to_update,
        name='redirect_to_update'),
    url(r'^nope/(?P<site_id>\d+)/$', views.unwatch, name="unwatch"),
]
