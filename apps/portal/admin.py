from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Complaint


@admin.register(Complaint)
class ComplaintAdmin(ModelAdmin):
    list_display = ['subject', 'parent', 'category', 'status', 'created_at']
    list_filter = ['status', 'category', 'created_at']
    search_fields = ['subject', 'description', 'parent__user__username', 'order__id']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('parent', 'order', 'category', 'status')
        }),
        ('Complaint Details', {
            'fields': ('subject', 'description')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
