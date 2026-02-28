from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
import json


# ── Super Admin RBAC ──────────────────────────────────────────────────────────

ADMIN_SECTIONS = [
    'catalog', 'inventory', 'orders',
    'payments', 'profiles', 'portal', 'users', 'config',
]

SECTION_ACTIONS = ['view', 'add', 'change', 'delete']


class AdminRole(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=dict)
    # Structure: { "catalog": ["view", "add"], "orders": ["view", "change"] }
    # Sections absent from the map = no access at all
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='created_roles'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def can_access(self, section: str) -> bool:
        """Returns True if this role has any permissions in the given section."""
        return section in self.permissions and bool(self.permissions[section])

    def can_do(self, section: str, action: str) -> bool:
        """Returns True if this role can perform the action in the given section."""
        return action in self.permissions.get(section, [])

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Admin Role"
        verbose_name_plural = "Admin Roles"


class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    is_super_admin = models.BooleanField(default=False)
    role = models.ForeignKey(
        AdminRole, null=True, blank=True, on_delete=models.SET_NULL
    )
    # role is null only for Super Admins — regular admins must have a role
    created_by = models.ForeignKey(
        User, null=True, blank=True, related_name='created_admins', on_delete=models.SET_NULL
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        tag = 'Super Admin' if self.is_super_admin else str(self.role)
        return f"{self.user.email} ({tag})"

    class Meta:
        verbose_name = "Admin User"
        verbose_name_plural = "Admin Users"


# ── Table Configuration ───────────────────────────────────────────────────────

class TableConfiguration(models.Model):
    """Store table configurations for reuse across the admin interface"""
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    model_name = models.CharField(max_length=100, help_text="Django model name (e.g., 'catalog.Book')")
    
    # Table settings
    items_per_page = models.PositiveIntegerField(default=10)
    enable_search = models.BooleanField(default=True)
    enable_sorting = models.BooleanField(default=True)
    enable_pagination = models.BooleanField(default=True)
    mobile_card_view = models.BooleanField(default=True)
    
    # Visual settings
    table_class = models.CharField(max_length=100, default='data-table')
    header_style = models.CharField(
        max_length=20,
        choices=[
            ('gradient', 'Gradient Header'),
            ('solid', 'Solid Color'),
            ('minimal', 'Minimal'),
        ],
        default='gradient'
    )
    
    # Row styling
    row_striping = models.BooleanField(default=True)
    hover_effects = models.BooleanField(default=True)
    compact_mode = models.BooleanField(default=False)
    
    # Created/updated info
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tables')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Table Configuration"
        verbose_name_plural = "Table Configurations"
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class TableColumn(models.Model):
    """Column configurations for tables"""
    
    table_config = models.ForeignKey(TableConfiguration, on_delete=models.CASCADE, related_name='columns')
    
    # Column identification
    field_name = models.CharField(max_length=100, help_text="Field name (e.g., 'title', 'publisher.name')")
    display_name = models.CharField(max_length=100, help_text="Header text")
    
    # Column properties
    column_type = models.CharField(
        max_length=20,
        choices=[
            ('text', 'Text'),
            ('number', 'Number'),
            ('currency', 'Currency'),
            ('date', 'Date'),
            ('datetime', 'Date & Time'),
            ('boolean', 'Boolean'),
            ('image', 'Image'),
            ('url', 'URL'),
            ('email', 'Email'),
            ('custom', 'Custom Template'),
        ],
        default='text'
    )
    
    # Display options
    width = models.CharField(max_length=20, blank=True, help_text="CSS width (e.g., '150px', '20%')")
    text_align = models.CharField(
        max_length=10,
        choices=[
            ('left', 'Left'),
            ('center', 'Center'),
            ('right', 'Right'),
        ],
        default='left'
    )
    
    # Formatting options
    sortable = models.BooleanField(default=True)
    searchable = models.BooleanField(default=True)
    truncate = models.BooleanField(default=False)
    max_length = models.PositiveIntegerField(null=True, blank=True, help_text="For truncation")
    
    # Custom template
    custom_template = models.TextField(blank=True, help_text="Custom Django template for rendering")
    
    # Display order
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Table Column"
        verbose_name_plural = "Table Columns"
        ordering = ['table_config', 'order']
        unique_together = ['table_config', 'field_name']
    
    def __str__(self):
        return f"{self.table_config.name} - {self.display_name}"


class TableFilter(models.Model):
    """Filter configurations for tables"""
    
    table_config = models.ForeignKey(TableConfiguration, on_delete=models.CASCADE, related_name='filters')
    
    # Filter identification
    field_name = models.CharField(max_length=100)
    filter_type = models.CharField(
        max_length=20,
        choices=[
            ('text', 'Text Search'),
            ('select', 'Dropdown'),
            ('date_range', 'Date Range'),
            ('number_range', 'Number Range'),
            ('boolean', 'Yes/No'),
            ('multiselect', 'Multi Select'),
        ],
        default='text'
    )
    
    # Filter properties
    label = models.CharField(max_length=100)
    placeholder = models.CharField(max_length=100, blank=True)
    
    # Options for select/multiselect filters
    choices = models.JSONField(default=dict, blank=True, help_text="JSON object with choices")
    
    # Display order
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Table Filter"
        verbose_name_plural = "Table Filters"
        ordering = ['table_config', 'order']
    
    def __str__(self):
        return f"{self.table_config.name} - {self.label}"


class TableAction(models.Model):
    """Action buttons for table rows"""
    
    table_config = models.ForeignKey(TableConfiguration, on_delete=models.CASCADE, related_name='actions')
    
    # Action identification
    name = models.CharField(max_length=100)
    label = models.CharField(max_length=100)
    
    # Action properties
    action_type = models.CharField(
        max_length=20,
        choices=[
            ('view', 'View'),
            ('edit', 'Edit'),
            ('delete', 'Delete'),
            ('custom', 'Custom'),
        ],
        default='view'
    )
    
    # URL/template
    url_pattern = models.CharField(
        max_length=200,
        help_text="URL pattern, use {id} for object ID (e.g., '/admin/catalog/book/{id}/change/')"
    )
    
    # Button styling
    button_class = models.CharField(
        max_length=50,
        choices=[
            ('primary', 'Primary'),
            ('secondary', 'Secondary'),
            ('success', 'Success'),
            ('warning', 'Warning'),
            ('danger', 'Danger'),
            ('info', 'Info'),
            ('light', 'Light'),
            ('dark', 'Dark'),
        ],
        default='primary'
    )
    
    # Icon
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class (e.g., 'fas fa-edit')")
    
    # Permissions
    required_permission = models.CharField(max_length=100, blank=True, help_text="Permission required to show this action")
    
    # Display order
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Table Action"
        verbose_name_plural = "Table Actions"
        ordering = ['table_config', 'order']
    
    def __str__(self):
        return f"{self.table_config.name} - {self.label}"
