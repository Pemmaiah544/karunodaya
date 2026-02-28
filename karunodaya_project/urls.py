"""
URL configuration for karunodaya_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
import os


def firebase_sw(request):
    """
    Serve the Firebase service worker from the root path so its scope covers
    the entire origin. A SW at /static/... can only control /static/ requests.
    """
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'js', 'firebase-messaging-sw.js')
    try:
        with open(sw_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        content = '// firebase-messaging-sw.js not found'
    response = HttpResponse(content, content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache'
    return response


urlpatterns = [
    path('firebase-messaging-sw.js', firebase_sw, name='firebase_sw'),
    path('admin/', admin.site.urls),
    path('payments/', include('apps.payments.urls')),
    path('feedback/', include('apps.feedback.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('', include('apps.portal.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Debug toolbar
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]
