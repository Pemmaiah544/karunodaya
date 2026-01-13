from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Publisher, Book


@admin.register(Publisher)
class PublisherAdmin(ModelAdmin):
    list_display = ('name', 'email', 'phone', 'created_at')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Book)
class BookAdmin(ModelAdmin):
    list_display = (
        'title', 'author', 'publisher', 'difficulty_rating',
        'is_subscription_eligible', 'is_purchase_eligible',
        'stock_count', 'is_active'
    )
    list_filter = (
        'difficulty_rating', 'is_subscription_eligible',
        'is_purchase_eligible', 'is_active', 'publisher'
    )
    search_fields = ('title', 'author', 'isbn')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('stock_count', 'is_active')

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'author', 'publisher', 'isbn', 'mrp', 'cover_image')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Curation Settings', {
            'fields': ('difficulty_rating', 'recommended_grade_min', 'recommended_grade_max')
        }),
        ('Eligibility', {
            'fields': ('is_subscription_eligible', 'is_purchase_eligible', 'stock_count')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
