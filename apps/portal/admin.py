from django.contrib import admin
from unfold.admin import ModelAdmin
from apps.core.admin_mixins import AdminPaginationMixin
from .models import Complaint, ReadingPassage


@admin.register(Complaint)
class ComplaintAdmin(AdminPaginationMixin, ModelAdmin):
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
            '<a href="{}" style="color: #4b5563 !important; font-weight: 600; font-size: 14px;">{}</a>',
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


@admin.register(ReadingPassage)
class ReadingPassageAdmin(AdminPaginationMixin, ModelAdmin):
    list_display = ['title', 'language', 'grade', 'theme', 'word_count', 'is_active']
    list_filter = ['language', 'grade', 'theme', 'is_active']
    search_fields = ['title', 'text']
    readonly_fields = ['word_count', 'created_at', 'updated_at']
    list_editable = ['is_active']

    change_list_template = 'admin/catalog/enhanced_book_clean.html'

    fieldsets = (
        (None, {
            'fields': ('title', 'language', 'grade', 'theme', 'is_active')
        }),
        ('Passage Content', {
            'fields': ('text', 'word_count')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
