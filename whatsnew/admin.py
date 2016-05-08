from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.contrib.sessions.models import Session

from requests.exceptions import RequestException
import pprint
from lxml.etree import XPathEvalError

from .models import *
from .tasks import fetch, extract


class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = "__all__"

    def test(self):
        data = self.cleaned_data
        url = data.get("base_url", "")
        ref_xpath = data.get("ref_xpath", "")
        ref_filter = data.get("ref_filter", "")
        url_template = data.get("url_template", "")

        try:
            if not url:
                raise ValidationError("URL cannot be blank")
            navigation = data.get("navigation", "")
            page = fetch(url, navigation)
        except RequestException:
            raise ValidationError("Error fetching %s" % (url))
        except IndexError:
            raise ValidationError({"navigation": "No match for XPath %s"
                                  % (navigation)})
        except XPathEvalError:
            raise ValidationError({"navigation": "Invalid XPath: %s"
                                  % (navigation)})

        try:
            url, ref = extract(ref_xpath, ref_filter, url_template, page)
        except IndexError:
            raise ValidationError("No matches for XPath expression %s"
                                  % (ref_xpath))
        except AttributeError:
            raise ValidationError("Filter %s does not match %s"
                                  % (ref_filter, url))
        except TypeError:
            raise ValidationError("Invalid URL template: %s" % (url_template))
        except XPathEvalError:
            raise ValidationError("Invalid XPath: %s" % (ref_xpath))


class SiteUpdateAdmin(admin.TabularInline):
    model = SiteUpdate
    extra = 0


class TagInlineAdmin(admin.TabularInline):
    model = Tag.site.through
    extra = 1


class SiteAdmin(admin.ModelAdmin):
    list_display = ["name"]
    list_filter = ["broken", "last_checked", "site_tags"]
    ordering = ["name"]
    inlines = [TagInlineAdmin, SiteUpdateAdmin]
    form = SiteForm


class TagAdmin(admin.ModelAdmin):
    list_display = ["name"]

admin.site.register(Site, SiteAdmin)
admin.site.register(Tag, TagAdmin)


class SessionAdmin(admin.ModelAdmin):
    def _session_data(self, obj):
        return pprint.pformat(obj.get_decoded()).replace('\n', '<br>\n')
    _session_data.allow_tags=True
    list_display = ['session_key', '_session_data', 'expire_date']
    readonly_fields = ['_session_data']
    exclude = ['session_data']
    date_hierarchy='expire_date'

admin.site.register(Session, SessionAdmin)