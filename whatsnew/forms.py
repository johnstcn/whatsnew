import logging
import datetime

from pytz import utc

from django import forms
from django.conf import settings
from django.core.mail import send_mail
from django.core.urlresolvers import reverse

from .models import create_or_get_user_from_email

logger = logging.getLogger(__name__)


class SignUpForm(forms.Form):
    email = forms.EmailField()

    def send_signin_email(self):
        clean_email = self.cleaned_data.get('email')
        user = create_or_get_user_from_email(clean_email)

        if user.accesscode.code is None:
            now = datetime.datetime.now(utc)
            limit = getattr(settings, 'AUTH_RATE_LIMIT', datetime.timedelta(seconds=60))
            last_accessed_ago = (now - user.accesscode.updated)
            if last_accessed_ago > limit:
                user.accesscode.regenerate()
            else:
                raise forms.ValidationError(
                    "Sorry, you need to wait before doing that",
                    code='rate_limit_exceeded'
                )

        auth_url = reverse('authenticate', kwargs={'auth_code': user.accesscode.code})
        full_url = getattr(settings, 'BASE_URL') + auth_url

        send_mail(subject='login to freshcomics',
                  message='visit %s to sign in' % (full_url),
                  from_email='noreply@freshcomics.org',
                  recipient_list=[user.email])