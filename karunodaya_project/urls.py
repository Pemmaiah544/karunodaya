"""
URL configuration for karunodaya_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('payments/', include('apps.payments.urls')),
    path('feedback/', include('apps.feedback.urls')),
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
