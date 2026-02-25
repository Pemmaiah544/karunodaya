from django.apps import AppConfig


class PortalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.portal'

    def ready(self):
        """Register signal handlers when app is ready"""
        import apps.portal.signals  # noqa: F401
