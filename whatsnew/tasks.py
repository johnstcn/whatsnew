from __future__ import absolute_import
from celery import Task, shared_task
from celery.decorators import periodic_task
from celery.task.schedules import crontab
from celery.utils.log import get_task_logger

from datetime import timedelta, datetime
from pytz import utc
from whatsnew.models import *

import lxml.html
import requests
import re


log = get_task_logger(__name__)


@shared_task()
def debug_task(self):
    log.info('Request: {0!r}'.format(self.request))


@shared_task()
def fetch(url, navigation):
    log.info("Fetching %s" % url)
    resp = requests.get(url, timeout=30, verify=False)
    page = lxml.html.fromstring(resp.content)
    page.make_links_absolute(base_url=url)
    if navigation:
        nav_url = page.xpath(navigation)[0]
        log.info("Navigating to %s" % (nav_url))
        nav_resp = requests.get(nav_url, timeout=30, verify=False)
        page = lxml.html.fromstring(nav_resp.content)
        page.make_links_absolute(base_url=nav_url)
    return page


@shared_task()
def extract(ref_xpath, ref_filter, url_template, page):
    url = page.xpath(ref_xpath)[0]
    ref = re.search(ref_filter, url).group(1)
    if url_template:
        url = url_template % (ref)
    return url, ref


@shared_task()
def store(site_id, url, ref):
    site = Site.objects.filter(id=site_id).get()
    last_item = site.latest_update
    is_new_item = last_item is None or ref != last_item.ref
    if is_new_item:
        new_item = SiteUpdate(site=site,
                              date=datetime.now(utc),
                              url=url,
                              ref=ref)
        new_item.save()
        log.info("(%s) Stored ref:%s" % (site.name, ref))
    else:
        log.info("No update for %s" % (site.name))


@shared_task()
def check(site_id):
    site = Site.objects.filter(id=site_id).get()
    # If previous tasks failed due to e.g. networking issues they will be
    # requeued, checking last_checked here so we fail fast
    if not site.needs_check:
        return "ALREADY_CHECKED"

    log.info("Checking %s for updates" % (site.name))
    site.broken = True
    status = ""
    try:
        page = fetch(site.base_url, site.navigation)
    except requests.exceptions.Timeout:
        log.error("Timeout fetching %s" % (site.base_url))
        site.last_checked = datetime.now(utc)
        site.save()
        return "FETCH_TIMEOUT"
    except IndexError:
        log.error("No match for navigation XPath %s" % (site.navigation))
        site.last_checked = datetime.now(utc)
        site.save()
        return "NAVIGATION_FAILED"

    try:
        url, ref = extract(site.ref_xpath,
                           site.ref_filter,
                           site.url_template,
                           page)
        store(site_id, url, ref)
        status = "SUCCESS"
        site.broken = False
    except IndexError:
        log.error("No matches for XPath expression %s" % (site.ref_xpath))
        status = "NO_XPATH_MATCH"
    except AttributeError:
        log.error("No match for filter: %s" % (site.ref_filter))
        status = "NO_FILTER_MATCH"
    except TypeError:
        log.error("Invalid URL template for site %s: %s"
                  % (site.name, site.url_template))
        status = "INVALID_URL_TEMPLATE"

    site.last_checked = datetime.now(utc)
    site.save()
    return status


@periodic_task(run_every=60)
def schedule(force=False):
    for site in Site.objects.all():
        if site.needs_check and not site.broken:
            Task.delay(check, site.id)
