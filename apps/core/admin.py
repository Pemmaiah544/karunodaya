import datetime
import json
import logging

from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.sites.models import Site
from django.utils.html import format_html
from django import forms
from django.utils.crypto import get_random_string
from django.urls import path
from django.shortcuts import render
from django.http import JsonResponse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from unfold.admin import ModelAdmin
from apps.core.admin_mixins import AdminPaginationMixin, SectionPermissionMixin
from .models import (
    TableConfiguration, TableColumn, TableFilter, TableAction,
    AdminRole, AdminProfile, ADMIN_SECTIONS, SECTION_ACTIONS,
)

logger = logging.getLogger(__name__)

SECTION_LABELS = {
    'catalog': 'Catalog',
    'inventory': 'Inventory',
    'orders': 'Orders',
    'payments': 'Payments',
    'profiles': 'Profiles',
    'portal': 'Portal',
    'users': 'Users',
    'config': 'Configuration',
}


# Configure default admin site
admin.site.site_header = "Karunodaya Admin"
admin.site.site_title = "Karunodaya"
admin.site.index_title = "Admin Dashboard"


# ── Super Admin: Role Management ─────────────────────────────────────────────

class AdminRoleForm(forms.ModelForm):
    class Meta:
        model = AdminRole
        fields = ['name', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        existing = self.instance.permissions if self.instance.pk else {}
        for section in ADMIN_SECTIONS:
            for action in SECTION_ACTIONS:
                field_name = f'{section}__{action}'
                checked = action in existing.get(section, [])
                self.fields[field_name] = forms.BooleanField(
                    required=False,
                    label=action.capitalize(),
                    initial=checked,
                )

    def save(self, commit=True):
        instance = super().save(commit=False)
        permissions = {}
        for section in ADMIN_SECTIONS:
            actions = [
                action for action in SECTION_ACTIONS
                if self.cleaned_data.get(f'{section}__{action}')
            ]
            if actions:
                permissions[section] = actions
        instance.permissions = permissions
        if commit:
            instance.save()
        return instance


@admin.register(AdminRole)
class AdminRoleAdmin(ModelAdmin):
    form = AdminRoleForm
    list_display = ['name', 'section_summary', 'created_at']
    search_fields = ['name']

    # Dynamically build fieldsets — one tab per section
    fieldsets = [
        ('Role Info', {'fields': ['name', 'description']}),
    ] + [
        (f'{section.capitalize()} Permissions', {
            'fields': [f'{section}__{action}' for action in SECTION_ACTIONS],
            'classes': ['tab'],
        })
        for section in ADMIN_SECTIONS
    ]

    def section_summary(self, obj):
        return ', '.join(obj.permissions.keys()) or '\u2014'
    section_summary.short_description = 'Accessible Sections'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    # Super Admin only
    def _is_super(self, request):
        try:
            return request.user.admin_profile.is_super_admin
        except Exception:
            return request.user.is_superuser

    def has_module_perms(self, request, app_label=None):
        return self._is_super(request)

    def has_view_permission(self, request, obj=None):
        return self._is_super(request)

    def has_add_permission(self, request):
        return self._is_super(request)

    def has_change_permission(self, request, obj=None):
        return self._is_super(request)

    def has_delete_permission(self, request, obj=None):
        return self._is_super(request)


# ── Super Admin: Admin User Management ────────────────────────────────────────

class AdminUserCreationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, label="First Name")
    last_name = forms.CharField(max_length=150, label="Last Name")
    email = forms.EmailField(label="Email Address")

    class Meta:
        model = AdminProfile
        fields = ['is_active', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add permission checkboxes for each section and action
        for section in ADMIN_SECTIONS:
            for action in SECTION_ACTIONS:
                field_name = f'{section}__{action}'
                self.fields[field_name] = forms.BooleanField(
                    required=False,
                    label=f"{action.capitalize()}",
                )

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if not profile.pk:  # new user only
            # Generate a random password
            password = get_random_string(16)
            user = User.objects.create_user(
                username=self.cleaned_data['email'],
                email=self.cleaned_data['email'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                password=password,
                is_staff=True,
                is_active=True,
            )
            profile.user = user

            # Collect selected permissions
            permissions = {}
            for section in ADMIN_SECTIONS:
                actions = [
                    action for action in SECTION_ACTIONS
                    if self.cleaned_data.get(f'{section}__{action}')
                ]
                if actions:
                    permissions[section] = actions

            # Create or get role based on permissions
            # Use email as basis for unique role name
            role_name = f"Admin ({user.email})"
            role, _ = AdminRole.objects.get_or_create(
                name=role_name,
                defaults={
                    'description': f"Custom role for {user.get_full_name()}",
                    'permissions': permissions,
                    'created_by': None  # Will be set in save_model
                }
            )

            # If role already existed, update permissions
            if permissions:
                role.permissions = permissions
                role.save()

            profile.role = role
            # Store password in profile notes temporarily (for display)
            profile.temp_password = password
        if commit:
            profile.save()
        return profile


@admin.register(AdminProfile)
class AdminProfileAdmin(ModelAdmin):
    list_display = ['user_email', 'user_full_name', 'role', 'is_active', 'created_at']
    list_filter = ['is_active', 'role']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_by', 'created_at']
    change_list_template = 'admin/core/adminprofile/change_list.html'

    # ── Custom URLs ────────────────────────────────────────────────────────────

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'create-admin/',
                self.admin_site.admin_view(self.create_admin_view),
                name='core_adminprofile_create',
            ),
            path(
                'add-admin/',
                self.admin_site.admin_view(self.add_admin_page),
                name='core_adminprofile_add_admin',
            ),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['admin_sections'] = ADMIN_SECTIONS
        extra_context['section_actions'] = SECTION_ACTIONS
        extra_context['admin_sections_json'] = json.dumps(ADMIN_SECTIONS)
        extra_context['section_actions_json'] = json.dumps(SECTION_ACTIONS)
        extra_context['admin_sections_with_labels'] = [
            (s, SECTION_LABELS.get(s, s.capitalize())) for s in ADMIN_SECTIONS
        ]
        return super().changelist_view(request, extra_context=extra_context)

    def add_admin_page(self, request):
        """Dedicated full-page desktop form for adding a new admin."""
        from django.http import HttpResponseForbidden
        if not self._is_super(request):
            return HttpResponseForbidden()
        context = {
            **self.admin_site.each_context(request),
            'title': 'Add New Admin',
            'admin_sections': ADMIN_SECTIONS,
            'section_actions': SECTION_ACTIONS,
            'admin_sections_json': json.dumps(ADMIN_SECTIONS),
            'section_actions_json': json.dumps(SECTION_ACTIONS),
            'admin_sections_with_labels': [
                (s, SECTION_LABELS.get(s, s.capitalize())) for s in ADMIN_SECTIONS
            ],
        }
        return render(request, 'admin/core/adminprofile/add_admin_page.html', context)

    def create_admin_view(self, request):
        """AJAX endpoint — creates a new admin user and returns JSON."""
        if not self._is_super(request):
            return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)

        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'Method not allowed.'}, status=405)

        first_name   = request.POST.get('first_name',   '').strip()
        last_name    = request.POST.get('last_name',    '').strip()
        email        = request.POST.get('email',        '').strip().lower()
        password     = request.POST.get('password',     '').strip()
        phone_number = request.POST.get('phone_number', '').strip()

        errors = {}
        if not first_name:
            errors['first_name'] = 'First name is required.'
        if not email:
            errors['email'] = 'Email is required.'
        elif '@' not in email or '.' not in email.split('@')[-1]:
            errors['email'] = 'Enter a valid email address.'
        elif User.objects.filter(email=email).exists():
            errors['email'] = 'A user with this email already exists.'
        if not phone_number:
            errors['phone_number'] = 'Phone number is required.'

        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        if not password:
            password = get_random_string(16)

        # Collect permissions from POST checkboxes
        permissions = {}
        for section in ADMIN_SECTIONS:
            actions = [
                action for action in SECTION_ACTIONS
                if request.POST.get(f'{section}__{action}') == 'on'
            ]
            if actions:
                permissions[section] = actions

        # Validate that at least one permission is selected
        if not permissions:
            return JsonResponse({
                'success': False,
                'errors': {'permissions': 'Please select at least one permission section.'}
            })

        # Checkbox sends 'on' when checked; absent from POST when unchecked
        is_active = request.POST.get('is_active') == 'on'

        notes = request.POST.get('notes', '').strip()

        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            is_staff=True,
            is_active=True,
        )
        role = AdminRole.objects.create(
            name=f"Admin ({email})",
            description=f"Custom role for {first_name} {last_name}",
            permissions=permissions,
            created_by=request.user,
        )
        admin_profile = AdminProfile.objects.create(
            user=user,
            role=role,
            is_super_admin=False,
            is_active=is_active,
            notes=notes,
            created_by=request.user,
        )

        # Log admin creation for debugging
        logger.info(
            "Admin user created: email=%s, is_active=%s, profile_id=%s, role_id=%s",
            email, is_active, admin_profile.id, role.id
        )

        # ── Send welcome email with credentials ────────────────────────────
        email_sent = False
        try:
            admin_url = request.build_absolute_uri('/admin/')
            granted_sections = [
                SECTION_LABELS.get(s, s.capitalize())
                for s in permissions.keys()
            ]
            context = {
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'password': password,
                'phone_number': phone_number,
                'created_by': request.user.get_full_name() or request.user.email,
                'admin_url': admin_url,
                'granted_sections': granted_sections,
                'year': datetime.date.today().year,
            }
            html_body = render_to_string('emails/admin_welcome.html', context)
            plain_body = (
                f"Hello {first_name},\n\n"
                f"Your Karunodaya admin account has been created.\n\n"
                f"Email:    {email}\n"
                f"Password: {password}\n"
                f"Phone:    {phone_number}\n\n"
                f"Login at: {admin_url}\n\n"
                f"Please change your password after your first login.\n\n"
                f"— Karunodaya Admin"
            )
            msg = EmailMultiAlternatives(
                subject="Your Karunodaya Admin Account Credentials",
                body=plain_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )
            msg.attach_alternative(html_body, "text/html")
            msg.send(fail_silently=False)
            email_sent = True
            logger.info("Welcome email sent successfully to %s", email)
        except Exception as exc:
            logger.warning("Admin welcome email failed for %s: %s", email, exc, exc_info=True)

        return JsonResponse({
            'success': True,
            'email_sent': email_sent,
            'data': {
                'email': email,
                'password': password,
                'name': f"{first_name} {last_name}",
            },
        })

    # ── Standard form for editing existing admins ──────────────────────────────

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            return AdminUserCreationForm
        return super().get_form(request, obj, **kwargs)

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            fieldsets = [
                ('Admin User Information', {
                    'fields': ['first_name', 'last_name', 'email', 'is_active', 'notes']
                }),
            ]
            for section in ADMIN_SECTIONS:
                fieldsets.append((
                    f'{section.capitalize()} Permissions',
                    {
                        'fields': [f'{section}__{action}' for action in SECTION_ACTIONS],
                        'classes': ['tab'],
                    }
                ))
            return fieldsets
        return [
            ('Admin Information', {'fields': ['user', 'role', 'is_active', 'notes']}),
            ('Metadata', {'fields': ['created_by', 'created_at'], 'classes': ['collapse']}),
        ]

    def get_fields(self, request, obj=None):
        if obj is None:
            fields = ['first_name', 'last_name', 'email', 'is_active', 'notes']
            for section in ADMIN_SECTIONS:
                for action in SECTION_ACTIONS:
                    fields.append(f'{section}__{action}')
            return fields
        return ['user', 'role', 'is_active', 'notes', 'created_by', 'created_at']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
            if obj.role and not obj.role.created_by:
                obj.role.created_by = request.user
                obj.role.save()
        super().save_model(request, obj, form, change)

    def response_add(self, request, obj, post_url_continue=None):
        """Show password after creation via the legacy Django form flow."""
        temp_password = getattr(obj, 'temp_password', None)
        if temp_password:
            from django.contrib import messages
            from django.http import HttpResponseRedirect
            from django.urls import reverse

            email = obj.user.email
            messages.success(
                request,
                f"✓ Admin user created!\nEmail: {email}\nPassword: {temp_password}",
                extra_tags='safe',
            )
            request.session['new_admin_email'] = email
            request.session['new_admin_password'] = temp_password
            return HttpResponseRedirect(reverse('admin:core_adminprofile_changelist'))

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'

    def user_full_name(self, obj):
        return obj.user.get_full_name()
    user_full_name.short_description = 'Name'

    # Super Admin only
    def _is_super(self, request):
        try:
            return request.user.admin_profile.is_super_admin
        except Exception:
            return request.user.is_superuser

    def has_module_perms(self, request, app_label=None):
        return self._is_super(request)

    def has_view_permission(self, request, obj=None):
        return self._is_super(request)

    def has_add_permission(self, request):
        return self._is_super(request)

    def has_change_permission(self, request, obj=None):
        return self._is_super(request)

    def has_delete_permission(self, request, obj=None):
        return self._is_super(request)


# ── Table Configuration Admins ────────────────────────────────────────────────

@admin.register(TableConfiguration)
class TableConfigurationAdmin(SectionPermissionMixin, AdminPaginationMixin, ModelAdmin):
    admin_section = 'config'
    list_display = ('name', 'model_name', 'items_per_page', 'enable_search', 'is_active')
    list_filter = ('enable_search', 'enable_sorting', 'enable_pagination', 'header_style', 'is_active')
    search_fields = ('name', 'description', 'model_name')
    readonly_fields = ('created_at', 'updated_at', 'slug')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'model_name')
        }),
        ('Table Settings', {
            'fields': ('items_per_page', 'enable_search', 'enable_sorting', 'enable_pagination', 'mobile_card_view')
        }),
        ('Visual Settings', {
            'fields': ('header_style', 'row_striping', 'hover_effects', 'compact_mode')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TableColumn)
class TableColumnAdmin(SectionPermissionMixin, AdminPaginationMixin, ModelAdmin):
    admin_section = 'config'
    list_display = ('table_config', 'display_name', 'field_name', 'column_type', 'sortable', 'order')
    list_filter = ('column_type', 'sortable', 'searchable', 'text_align')
    search_fields = ('display_name', 'field_name', 'table_config__name')

    fieldsets = (
        ('Column Information', {
            'fields': ('table_config', 'field_name', 'display_name', 'column_type')
        }),
        ('Display Options', {
            'fields': ('width', 'text_align', 'sortable', 'searchable', 'truncate', 'max_length')
        }),
        ('Custom Template', {
            'fields': ('custom_template',),
            'classes': ('collapse',)
        }),
        ('Order', {
            'fields': ('order',)
        }),
    )


@admin.register(TableFilter)
class TableFilterAdmin(SectionPermissionMixin, AdminPaginationMixin, ModelAdmin):
    admin_section = 'config'
    list_display = ('table_config', 'label', 'field_name', 'filter_type', 'order')
    list_filter = ('filter_type',)
    search_fields = ('label', 'field_name', 'table_config__name')

    fieldsets = (
        ('Filter Information', {
            'fields': ('table_config', 'field_name', 'filter_type', 'label', 'placeholder')
        }),
        ('Filter Options', {
            'fields': ('choices',),
            'classes': ('collapse',)
        }),
        ('Order', {
            'fields': ('order',)
        }),
    )


@admin.register(TableAction)
class TableActionAdmin(SectionPermissionMixin, AdminPaginationMixin, ModelAdmin):
    admin_section = 'config'
    list_display = ('table_config', 'label', 'action_type', 'button_class', 'order')
    list_filter = ('action_type', 'button_class')
    search_fields = ('label', 'name', 'table_config__name')

    fieldsets = (
        ('Action Information', {
            'fields': ('table_config', 'name', 'label', 'action_type')
        }),
        ('URL and Styling', {
            'fields': ('url_pattern', 'button_class', 'icon')
        }),
        ('Permissions', {
            'fields': ('required_permission',)
        }),
        ('Order', {
            'fields': ('order',)
        }),
    )


# Override default Site admin to use enhanced table styling
admin.site.unregister(Site)


@admin.register(Site)
class SiteAdmin(SectionPermissionMixin, AdminPaginationMixin, ModelAdmin):
    admin_section = 'config'
    list_display = ('domain_link', 'name')
    search_fields = ('domain', 'name')

    # Enhanced change list template
    change_list_template = 'admin/catalog/enhanced_book_clean.html'

    def domain_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse('admin:sites_site_change', args=[obj.pk])
        return format_html(
            '<a href="{}" style="color: #374151; font-weight: 400; font-size: 13px;">{}</a>',
            url,
            obj.domain
        )
    domain_link.short_description = 'Domain Name'
    domain_link.admin_order_field = 'domain'
