from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import NotificationLog


@admin.register(NotificationLog)
class NotificationLogAdmin(ModelAdmin):
    list_display = ['parent', 'notification_type', 'scheduled_date', 'slot_key', 'status', 'sent_at']
    list_filter = ['notification_type', 'status', 'scheduled_date']
    search_fields = ['parent__user__username', 'parent__user__email']
    readonly_fields = ['parent', 'notification_type', 'scheduled_date', 'slot_key', 'sent_at', 'status', 'error_message']
    ordering = ['-sent_at']
    date_hierarchy = 'scheduled_date'
