"""
URLs for notifications API and views.
"""
from django.urls import path
from . import api_views

app_name = 'notifications'

urlpatterns = [
    # Device Token Registration
    path('api/register-device-token/', api_views.register_device_token, name='register_token'),
    path('api/unregister-device-token/', api_views.unregister_device_token, name='unregister_token'),
    path('api/list-devices/', api_views.list_device_tokens, name='list_devices'),
    path('api/test-notification/', api_views.send_test_notification, name='test_notification'),

    # Internal API (for scheduler)
    path('api/send-to-parent/', api_views.send_notification_to_parent, name='send_to_parent'),
]
