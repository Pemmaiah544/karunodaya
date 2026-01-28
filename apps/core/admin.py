from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from .models import TableConfiguration, TableColumn, TableFilter, TableAction


@admin.register(TableConfiguration)
class TableConfigurationAdmin(ModelAdmin):
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
class TableColumnAdmin(ModelAdmin):
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
class TableFilterAdmin(ModelAdmin):
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
class TableActionAdmin(ModelAdmin):
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
