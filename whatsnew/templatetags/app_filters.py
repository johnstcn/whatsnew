from django import template
from django.contrib.humanize.templatetags.humanize import naturalday, naturaltime
from datetime import datetime
from pytz import utc


register = template.Library()


@register.filter(name="custom_natural_date")
def custom_natural_date(value):
    delta = datetime.now(utc) - value
    if delta.days == 0:
        return naturaltime(value)
    else:
        return naturalday(value)


@register.filter(name="get_int_key")
def get_int_key(d, key):
    return d.get(unicode(key))
