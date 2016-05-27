from django.views import generic
from django.contrib import messages
from django.shortcuts import redirect
from django.db.models.aggregates import Max
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import *


def watch(request, site_id):
    return_url = request.META.get('HTTP_REFERER', '/')
    if not request.user.is_anonymous():
        site = Site.objects.get(pk=site_id)
        us = UserSeen.objects.get(user=request.user)
        us.seen[site_id] = site.latest_update.id
        us.save()
        messages.info(request, 'You are now watching %s' % site.name)
    else:
        messages.warning(request, 'You need to sign in to do that!')
    return redirect(return_url)


def unwatch(request, site_id):
    return_url = request.META.get('HTTP_REFERER', '/')
    if not request.user.is_anonymous():
        site = Site.objects.get(pk=site_id)
        us = UserSeen.objects.get(user=request.user)
        del(us.seen[site_id])
        us.save()
        messages.info(request, 'You are no longer watching %s' % site.name)
    else:
        messages.warning(request, 'You need to sign in to do that!')
    return redirect(return_url)


def redirect_to_update(request, site_update_id):
    return_url = request.META.get('HTTP_REFERER', '/')
    update = SiteUpdate.objects.filter(pk=site_update_id).get()
    if not request.user.is_anonymous():
        try:
            us = UserSeen.objects.get(user=request.user)
            if str(update.site_id) in us.seen:
                us.seen[update.site_id] = site_update_id
                us.save()
        except ObjectDoesNotExist:
            messages.error(request, 'Sorry, something went wrong!')
            return redirect(return_url)
    else:
        messages.info(request, 'Sign up to keep track of the comics you like!')
    return redirect(update.url)


class SitesView(generic.ListView):
    template_name = 'all_sites.html'
    context_object_name = 'sites'
    model = Site
    paginate_by = 10

    def get_queryset(self):
        sites = Site.objects.annotate(Max('siteupdate__date')).order_by('-siteupdate__date__max')
        tag = self.kwargs.get("tag", "all")
        nsfw = self.kwargs.get("nsfw", "0")
        watched = self.kwargs.get("watched", "0")
        if tag != "all":
            sites = sites.filter(site_tags__name=tag)
        if nsfw == "0":
            sites = sites.exclude(site_tags__name="nsfw")
        if watched == "1":
            if self.request.user.is_anonymous():
                messages.info(self.request, "You need to sign in to do that!")
            else:
                seen = self.request.user.userseen.seen
                sites = sites.filter(pk__in=seen)

        return sites

    def get_context_data(self, **kwargs):
        context = super(SitesView, self).get_context_data(**kwargs)
        tags = [t.name for t in Tag.objects.all() if t.name != 'nsfw']
        context["tags"] = tags
        context["selected_tag"] = self.kwargs.get("tag", "all")
        context["show_nsfw"] = self.kwargs.get("nsfw", "0")
        context["only_watched"] = self.kwargs.get("watched", "0")

        next_updates = {}

        if not self.request.user.is_anonymous():
            seen = UserSeen.objects.get(user=self.request.user).seen
            for site_id, update_id in seen.iteritems():
                try:
                    update = SiteUpdate.objects.get(pk=update_id)
                    next_update = SiteUpdate.objects.filter(site_id=site_id, date__gt=update.date).order_by('date').first()
                except ObjectDoesNotExist:
                    next_update = None

                if next_update is not None:
                    next_updates[site_id] = next_update.id
                else:
                    next_updates[site_id] = None
        else:
            seen = {}

        context['next_updates'] = next_updates
        context['seen'] = seen

        return context
