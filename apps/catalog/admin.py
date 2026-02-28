from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from apps.core.admin_mixins import AdminPaginationMixin, SectionPermissionMixin
from .models import Publisher, Book
from .forms import BookAdminForm


@admin.register(Publisher)
class PublisherAdmin(SectionPermissionMixin, AdminPaginationMixin, ModelAdmin):
    admin_section = 'catalog'
    list_display = ('name_link', 'email', 'phone', 'created_at')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 15
    change_list_template = 'admin/catalog/publisher/change_list.html'
    


    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'add-publisher/',
                self.admin_site.admin_view(self.add_publisher_page),
                name='catalog_publisher_add_custom',
            ),
            path(
                'create-publisher/',
                self.admin_site.admin_view(self.create_publisher_view),
                name='catalog_publisher_create_custom',
            ),
            path(
                '<path:object_id>/update-publisher/',
                self.admin_site.admin_view(self.update_publisher_view),
                name='catalog_publisher_update_custom',
            ),
        ]
        return custom_urls + urls

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Override change_view to use our custom publisher detail template."""
        extra_context = extra_context or {}
        publisher = self.get_object(request, object_id)
        if not publisher:
            return super().change_view(request, object_id, form_url, extra_context)
            
        extra_context['publisher'] = publisher
        extra_context['title'] = f'Publisher: {publisher.name}'
        extra_context['admin_section'] = 'catalog'
        
        # Prepare display phone (strip +91 prefix for the input field)
        display_phone = publisher.phone or ""
        if display_phone.startswith('+91 '):
            display_phone = display_phone[4:]
        elif display_phone.startswith('+91'):
            display_phone = display_phone[3:]
        extra_context['display_phone'] = display_phone
        
        return render(request, 'admin/catalog/publisher/change_form.html', {
            **self.admin_site.each_context(request),
            **extra_context,
            'opts': self.model._meta,
            'original': publisher,
            'object_id': object_id,
        })

    def add_publisher_page(self, request):
        """Dedicated full-page desktop form for adding a new publisher."""
        context = {
            **self.admin_site.each_context(request),
            'title': 'Add New Publisher',
            'admin_section': 'catalog',
        }
        return render(request, 'admin/catalog/publisher/add_publisher.html', context)

    def create_publisher_view(self, request):
        """AJAX endpoint — creates a new publisher and returns JSON."""
        from django.http import JsonResponse
        import json

        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'Method not allowed.'}, status=405)

        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()

        errors = {}
        if not name:
            errors['name'] = 'Publisher name is required.'
        if not email:
            errors['email'] = 'Email address is required.'
        elif '@' not in email or '.' not in email.split('@')[-1]:
            errors['email'] = 'Enter a valid email address.'
        if not phone:
            errors['phone'] = 'Phone number is required.'
        if not address:
            errors['address'] = 'Office address is required.'

        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        try:
            publisher = Publisher.objects.create(
                name=name,
                email=email,
                phone=phone,
                address=address
            )
            return JsonResponse({
                'success': True,
                'data': {
                    'id': publisher.id,
                    'name': publisher.name,
                },
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    def update_publisher_view(self, request, object_id):
        """AJAX endpoint — updates an existing publisher and returns JSON."""
        from django.http import JsonResponse
        import json

        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'Method not allowed.'}, status=405)

        publisher = self.get_object(request, object_id)
        if not publisher:
            return JsonResponse({'success': False, 'error': 'Publisher not found.'}, status=404)

        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()

        errors = {}
        if not name:
            errors['name'] = 'Publisher name is required.'
        if not email:
            errors['email'] = 'Email address is required.'
        elif '@' not in email or '.' not in email.split('@')[-1]:
            errors['email'] = 'Enter a valid email address.'
        if not phone:
            errors['phone'] = 'Phone number is required.'
        if not address:
            errors['address'] = 'Office address is required.'

        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        try:
            publisher.name = name
            publisher.email = email
            publisher.phone = phone
            publisher.address = address
            publisher.save()
            
            return JsonResponse({
                'success': True,
                'data': {
                    'id': publisher.id,
                    'name': publisher.name,
                    'updated_at': publisher.updated_at.strftime("%b %d, %Y %H:%M")
                },
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

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
class BookAdmin(SectionPermissionMixin, AdminPaginationMixin, ModelAdmin):
    admin_section = 'catalog'
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
