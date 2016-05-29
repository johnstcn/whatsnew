from .models import AccessCode, User

class OneTimeLinkAuthBackend(object):
    supports_object_permissions = False
    supports_anonymous_user = False

    def authenticate(self, code):
        try:
            code = AccessCode.objects.get(code=code)
            code.code = None
            code.save()
            return code.user
        except AccessCode.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
