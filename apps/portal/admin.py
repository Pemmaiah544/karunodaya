from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Complaint


@admin.register(Complaint)
class ComplaintAdmin(ModelAdmin):
    list_display = ['subject_link', 'parent', 'category', 'status', 'created_at']
    list_filter = ['status', 'category', 'created_at']
    search_fields = ['subject', 'description', 'parent__user__username', 'order__id']
    readonly_fields = ['created_at', 'updated_at']
    
    # Enhanced change list template
    change_list_template = 'admin/catalog/enhanced_book_clean.html'

    def subject_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse('admin:portal_complaint_change', args=[obj.pk])
        return format_html(
            '<a href="{}" style="color: #374151; font-weight: 400; font-size: 13px;">{}</a>',
            url,
            obj.subject
        )
    subject_link.short_description = 'Subject'
    subject_link.admin_order_field = 'subject'
    
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
