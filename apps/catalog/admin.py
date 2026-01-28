from django.contrib import admin
from django.utils.html import format_html
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
        'title', 'author', 'cover_image_thumbnail', 'publisher', 'difficulty_rating',
        'is_subscription_eligible', 'is_purchase_eligible',
        'stock_count', 'is_active', 'marketplace_status'
    )
    list_filter = (
        'difficulty_rating', 'is_subscription_eligible',
        'is_purchase_eligible', 'is_active', 'publisher'
    )
    search_fields = ('title', 'author', 'isbn')
    readonly_fields = ('created_at', 'updated_at', 'cover_image_thumbnail')
    list_editable = ('stock_count', 'is_active', 'is_purchase_eligible')

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
    marketplace_status.short_description = 'Marketplace Status'

    def save_model(self, request, obj, form, change):
        """Override save to ensure new books are marketplace-ready by default."""
        if not change:  # Only for new books
            # Ensure new books have sensible defaults for marketplace visibility
            if obj.stock_count == 0:
                obj.stock_count = 10  # Default stock for new books
            # Keep existing is_purchase_eligible and is_active values as they may be intentionally set
        super().save_model(request, obj, form, change)

    actions = ['make_marketplace_visible', 'make_marketplace_hidden']

    def make_marketplace_visible(self, request, queryset):
        """Make selected books visible in marketplace."""
        updated = queryset.update(
            is_purchase_eligible=True,
            is_active=True,
            stock_count=models.F('stock_count') + 10  # Add 10 to stock if it's 0
        )
        self.message_user(request, f'{updated} books are now visible in marketplace.')

    def make_marketplace_hidden(self, request, queryset):
        """Make selected books hidden from marketplace."""
        updated = queryset.update(is_purchase_eligible=False)
        self.message_user(request, f'{updated} books are now hidden from marketplace.')

    def cover_image_thumbnail(self, obj):
        """Display cover image thumbnail in admin list view."""
        if obj.cover_image:
            return format_html(
                '<img src="{}" width="50" height="70" style="object-fit: cover; border-radius: 4px;" />',
                obj.cover_image.url
            )
        return "No Image"
    cover_image_thumbnail.short_description = 'Cover'
