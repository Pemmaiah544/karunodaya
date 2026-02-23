from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

UserModel = get_user_model()


class CaseInsensitiveModelBackend(ModelBackend):
    """
    Authentication backend that performs case-insensitive username lookup.

    Since admin users are created with username=email.lower(), but users may
    type their email with mixed case in the login form, we normalize the
    username to lowercase before querying the database.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is not None:
            username = username.strip().lower()
        return super().authenticate(request, username=username, password=password, **kwargs)
