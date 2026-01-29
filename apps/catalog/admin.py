from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from .models import Publisher, Book
from .forms import BookAdminForm


@admin.register(Publisher)
class PublisherAdmin(ModelAdmin):
    list_display = ('name_link', 'email', 'phone', 'created_at')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 15
    
    # Enhanced change list template
    change_list_template = 'admin/catalog/enhanced_book_clean.html'

    def name_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse('admin:catalog_publisher_change', args=[obj.pk])
        return format_html(
            '<a href="{}" style="color: #4b5563 !important; font-weight: 400; font-size: 13px;">{}</a>',
            url,
            obj.name
        )
    name_link.short_description = 'Name'
    name_link.admin_order_field = 'name'


@admin.register(Book)
class BookAdmin(ModelAdmin):
    form = BookAdminForm
    list_display = (
        'title_link', 'author', 'cover_image_thumbnail', 'publisher', 'difficulty_rating',
        'is_subscription_eligible', 'is_purchase_eligible',
        'stock_count', 'is_active', 'marketplace_status'
    )
    list_filter = (
        'difficulty_rating', 'is_subscription_eligible',
        'is_purchase_eligible', 'is_active', 'publisher'
    )
    search_fields = ('title', 'author', 'isbn')
    list_editable = ('stock_count', 'is_active', 'is_purchase_eligible')
    list_per_page = 15

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
    )

    # Enhanced change list template
    change_list_template = 'admin/catalog/enhanced_book_clean.html'

    def title_link(self, obj):
        """Display book title as a clickable link with custom styling."""
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse('admin:catalog_book_change', args=[obj.pk])
        return format_html(
            '<a href="{}" style="color: #000000 !important; font-weight: 600; font-size: 14px;">{}</a>',
            url,
            obj.title
        )
    title_link.short_description = 'Title'
    title_link.admin_order_field = 'title'

    def marketplace_status(self, obj):
        """Display marketplace eligibility status with color coding."""
        if obj.is_purchase_eligible and obj.is_active and obj.stock_count > 0:
            return '✅ Visible'
        else:
            reasons = []
            if not obj.is_purchase_eligible:
                reasons.append('Not purchase eligible')
            if not obj.is_active:
                reasons.append('Inactive')
            if obj.stock_count <= 0:
                reasons.append('No stock')
            return f'❌ Hidden: {", ".join(reasons)}'
    marketplace_status.short_description = 'Marketplace'

    def cover_image_thumbnail(self, obj):
        """Display cover image thumbnail in admin list view."""
        if obj.cover_image:
            return format_html(
                '<img src="{}" width="50" height="70" style="object-fit: cover; border-radius: 4px;" />',
                obj.cover_image.url
            )
        return "No Image"
    cover_image_thumbnail.short_description = 'Cover'

    def save_model(self, request, obj, form, change):
        """Override save to ensure marketplace visibility for new books."""
        if not change:  # Only for new books
            if obj.stock_count == 0:
                obj.stock_count = 10
        super().save_model(request, obj, form, change)
