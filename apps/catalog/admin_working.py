# Import the simple, working admin configuration
from .admin_simple import BookAdmin, PublisherAdmin

# Register the admin classes
from django.contrib import admin
admin.site.register(Publisher, PublisherAdmin)
admin.site.register(Book, BookAdmin)
