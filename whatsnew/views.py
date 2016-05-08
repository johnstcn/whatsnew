from django.views import generic
from django.contrib import messages
from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist

from operator import itemgetter

from .models import *


def unwatch(request, site_id):
    try:
        site = Site.objects.get(pk=site_id)
        if request.session.get('viewed', {}).get(site_id):
            del(request.session['viewed'][site_id])
            request.session.save()
            messages.info(request, "You're no longer watching %s." % (site.name))
    except ObjectDoesNotExist:
        messages.error(request, 'Sorry, something went wrong!')
    finally:
        return redirect(request.META['HTTP_REFERER'])


def redirect_to_update(request, site_update_id):
    try:
        update = SiteUpdate.objects.filter(pk=site_update_id).get()
        if request.session.get('viewed'):
            request.session['viewed'][update.site_id] = site_update_id
        else:
            request.session['viewed'] = { update.site_id: site_update_id }
        request.session.save()
        return redirect(update.url)
    except ObjectDoesNotExist:
        messages.error(request, 'Sorry, something went wrong!')
        return redirect(request.META['HTTP_REFERER'])


class SitesView(generic.ListView):
    template_name = 'sites.html'
    context_object_name = 'info'

    def get_queryset(self):
        tag = self.kwargs.get("tag", "all")
        personal = self.get_personal_queryset()
        exclude_ids = map(itemgetter("site_id"), personal)
        generic = self.get_generic_queryset(exclude_ids=exclude_ids)
        tags = [t.name for t in Tag.objects.exclude(name="nsfw")]

        return {
            "personal": self.postprocess_items(personal),
            "generic": self.postprocess_items(generic, limit=10),
            "tags": tags,
        }

    def postprocess_items(self, queryset, limit=None):
        out = {
            "items": list(queryset),
            "more": 0
        }
        tag = self.kwargs.get("tag", "all")
        if limit is not None and tag == "all":
            out["more"] = len(queryset) - limit
            out["items"] = out["items"][:limit]

        out["items"].sort(key=itemgetter("highlight", "date"), reverse=True)
        return out

    def highlight(self, site_update):
        site_id = unicode(site_update.site.id)
        site_update_id = unicode(site_update.id)
        viewed = self.request.session.get('viewed', {})
        watching_site = site_id in viewed
        is_latest_update = viewed.get(site_id, -1) == site_update_id
        return watching_site and not is_latest_update

    def convert_to_dict(self, site_update):
        return {
            "name": site_update.site.name,
            "date": site_update.date,
            "tags": [t.name for t in site_update.site.site_tags.all()],
            "update_id": site_update.id,
            "site_id": site_update.site.id,
            "highlight": self.highlight(site_update)
        }

    def get_next_site_update(self, site_update):
        next_update = SiteUpdate.objects.filter(site_id=site_update.site.id,
                                                date__gt=site_update.date)\
                                        .order_by("date").first()
        return (next_update or site_update)

    def get_personal_queryset(self):
        items = []
        viewed = self.request.session.get("viewed", {})
        nsfw = bool(int(self.kwargs.get("nsfw", 0)))
        tag = self.kwargs.get("tag", "all")
        for site_id, site_update_id in viewed.items():
            site = Site.objects.get(pk=site_id)
            site_update = SiteUpdate.objects.get(pk=site_update_id)
            tags = [t.name for t in site.site_tags.all()]
            if site.broken:
                continue
            if tag != 'all' and tag not in tags:
                continue
            if not nsfw and 'nsfw' in tags:
                continue
            update = self.get_next_site_update(site_update)
            items.append(self.convert_to_dict(update))
        return sorted(items, key=itemgetter("date"))

    def get_generic_queryset(self, exclude_ids=[]):
        nsfw = bool(int(self.kwargs.get("nsfw", 0)))
        tag = self.kwargs.get("tag", "all")
        sites = Site.objects.filter(broken=False)\
                            .exclude(id__in=exclude_ids)
        if tag != 'all':
            sites = sites.filter(site_tags__name=tag)
        if not nsfw:
            sites = sites.exclude(site_tags__name='nsfw')
        
        return [self.convert_to_dict(s.latest_update) for s in sites]
