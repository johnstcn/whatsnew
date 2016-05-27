from __future__ import unicode_literals

from datetime import timedelta, datetime, date
from pytz import utc

from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import User

class Site(models.Model):
    name = models.CharField(max_length=200)
    base_url = models.URLField()
    url_template = models.URLField(null=True, blank=True)
    navigation = models.CharField(max_length=200, null=True, blank=True)
    ref_xpath = models.CharField(max_length=200)
    ref_filter = models.CharField(max_length=200)
    check_period = models.IntegerField(default=60)
    last_checked = models.DateTimeField(default=datetime.fromtimestamp(0))
    broken = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    @property
    def updates(self):
        return self.siteupdate_set.all().order_by('-date')

    @property
    def latest_update(self):
        try:
            return self.updates[:1].get()
        except ObjectDoesNotExist:
            return None

    @property
    def next_check(self):
        return self.last_checked + timedelta(minutes=self.check_period)

    @property
    def needs_check(self):
        return self.next_check < datetime.now(utc)


class SiteUpdate(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    date = models.DateTimeField()
    url = models.URLField()
    ref = models.CharField(max_length=200)

    def __str__(self):
        return "%s:%s" % (self.site.name, self.ref)


class Tag(models.Model):
    site = models.ManyToManyField(Site, blank=True, related_name='site_tags')
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class UserSeen(models.Model):
    user = models.OneToOneField(User, null=False, blank=False)
    seen = JSONField(dict)
