"""
Test-only settings override — uses SQLite so tests can run without CREATEDB privilege.
Usage: python manage.py test --settings=karunodaya_project.test_settings
"""
from .settings import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Bypass migrations (some use PostgreSQL-specific SQL); create tables from models directly.
class DisableMigrations:
    def __contains__(self, item):
        return True
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Disable debug toolbar in tests
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'debug_toolbar']
MIDDLEWARE = [m for m in MIDDLEWARE if 'debug_toolbar' not in m]
