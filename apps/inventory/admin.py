from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import PhysicalCopy, InventoryLog


class InventoryLogInline(TabularInline):
    model = InventoryLog
    extra = 0
    readonly_fields = ('action', 'performed_by', 'notes', 'timestamp')
    can_delete = False
    fields = ('action', 'performed_by', 'notes', 'timestamp')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(PhysicalCopy)
class PhysicalCopyAdmin(ModelAdmin):
    list_display = ('barcode_link', 'book', 'status', 'purchased_date', 'updated_at')
    list_filter = ('status', 'purchased_date')
    search_fields = ('barcode', 'book__title')
    list_per_page = 5

    readonly_fields = ('created_at', 'updated_at')
    inlines = [InventoryLogInline]
    actions = ['mark_as_damaged', 'mark_as_lost', 'mark_as_available']
    
    # Enhanced change list template - same as all other tables
    change_list_template = 'admin/catalog/enhanced_book_clean.html'

    def changelist_view(self, request, extra_context=None):
        # Store per_page parameter before modifying GET
        original_get = request.GET
        per_page_value = original_get.get('per_page')
        
        # Remove per_page from GET to avoid Django treating it as filter
        cleaned = original_get.copy()
        if 'per_page' in cleaned:
            del cleaned['per_page']
        
        request.GET = cleaned
        
        try:
            response = super().changelist_view(request, extra_context=extra_context)
            # Apply per_page to the ChangeList and re-fetch results
            if hasattr(response, 'context_data') and 'cl' in response.context_data:
                cl = response.context_data['cl']
                allowed = {"5": 5, "10": 10, "25": 25, "50": 50}
                if per_page_value in allowed:
                    cl.list_per_page = allowed[per_page_value]
                    cl.get_results(request)
                    response.context_data['per_page'] = str(cl.list_per_page)
                else:
                    response.context_data['per_page'] = str(self.list_per_page)
            return response
        finally:
            request.GET = original_get

    def barcode_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse('admin:inventory_physicalcopy_change', args=[obj.pk])
        return format_html(
            '<a href="{}" style="color: #4b5563 !important; font-weight: 600; font-size: 14px;">{}</a>',
            url,
            obj.barcode
        )
    barcode_link.short_description = 'Barcode'
    barcode_link.admin_order_field = 'barcode'

    fieldsets = (
        ('Book Information', {
            'fields': ('book', 'barcode')
        }),
        ('Status', {
            'fields': ('status', 'condition_notes')
        }),
        ('Dates', {
            'fields': ('purchased_date', 'created_at', 'updated_at')
        }),
    )

    def mark_as_damaged(self, request, queryset):
        """Mark selected copies as damaged."""
        from .models import InventoryLog
        count = 0
        for copy in queryset:
            if copy.status != 'DAMAGED':
                copy.status = 'DAMAGED'
                copy.save()
                InventoryLog.objects.create(
                    physical_copy=copy,
                    action='DAMAGED',
                    performed_by=request.user,
                    notes='Marked as damaged via admin action'
                )
                count += 1
        self.message_user(request, f"{count} copy(ies) marked as damaged.")
    mark_as_damaged.short_description = "Mark as Damaged"

    def mark_as_lost(self, request, queryset):
        """Mark selected copies as lost."""
        from .models import InventoryLog
        count = 0
        for copy in queryset:
            if copy.status != 'LOST':
                copy.status = 'LOST'
                copy.save()
                InventoryLog.objects.create(
                    physical_copy=copy,
                    action='LOST',
                    performed_by=request.user,
                    notes='Marked as lost via admin action'
                )
                count += 1
        self.message_user(request, f"{count} copy(ies) marked as lost.")
    mark_as_lost.short_description = "Mark as Lost"

    def mark_as_available(self, request, queryset):
        """Mark selected copies as available."""
        from .models import InventoryLog
        count = 0
        for copy in queryset.filter(status__in=['DAMAGED', 'ISSUED']):
            copy.status = 'AVAILABLE'
            copy.save()
            InventoryLog.objects.create(
                physical_copy=copy,
                action='REPAIRED',
                performed_by=request.user,
                notes='Marked as available via admin action'
            )
            count += 1
        self.message_user(request, f"{count} copy(ies) marked as available.")
    mark_as_available.short_description = "Mark as Available"


@admin.register(InventoryLog)
class InventoryLogAdmin(ModelAdmin):
    list_display = ('physical_copy_display', 'barcode', 'action', 'performed_by', 'timestamp', 'notes')
    list_filter = ('action', 'timestamp', 'performed_by')
    search_fields = (
        'physical_copy__barcode', 
        'physical_copy__book__title',
        'performed_by__first_name', 
        'performed_by__last_name', 
        'notes'
    )
    list_per_page = 5

    readonly_fields = ('timestamp',)
    
    def physical_copy_display(self, obj):
        """Display only the book title without barcode"""
        return obj.physical_copy.book.title if obj.physical_copy else '-'
    physical_copy_display.short_description = 'Physical Copy'
    physical_copy_display.admin_order_field = 'physical_copy__book__title'
    
    def barcode(self, obj):
        """Display barcode from the related physical copy"""
        return obj.physical_copy.barcode if obj.physical_copy else '-'
    barcode.short_description = 'Barcode'
    
    # Enhanced change list template - same as all other tables
    change_list_template = 'admin/catalog/enhanced_book_clean.html'

    def changelist_view(self, request, extra_context=None):
        # Store per_page parameter before modifying GET
        original_get = request.GET
        per_page_value = original_get.get('per_page')
        
        # Remove per_page from GET to avoid Django treating it as filter
        cleaned = original_get.copy()
        if 'per_page' in cleaned:
            del cleaned['per_page']
        
        request.GET = cleaned
        
        try:
            response = super().changelist_view(request, extra_context=extra_context)
            # Apply per_page to the ChangeList and re-fetch results
            if hasattr(response, 'context_data') and 'cl' in response.context_data:
                cl = response.context_data['cl']
                allowed = {"5": 5, "10": 10, "25": 25, "50": 50}
                if per_page_value in allowed:
                    cl.list_per_page = allowed[per_page_value]
                    cl.get_results(request)
                    response.context_data['per_page'] = str(cl.list_per_page)
                else:
                    response.context_data['per_page'] = str(self.list_per_page)
            return response
        finally:
            request.GET = original_get

    def physical_copy_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse('admin:inventory_inventorylog_change', args=[obj.pk])
        return format_html(
            '<a href="{}" style="color: #4b5563 !important; font-weight: 600; font-size: 14px;">{}</a>',
            url,
            str(obj.physical_copy.book.title)
        )
    physical_copy_link.short_description = 'Physical Copy'
    physical_copy_link.admin_order_field = 'physical_copy__book__title'

    def get_barcode(self, obj):
        return obj.physical_copy.barcode
    get_barcode.short_description = 'Bar-Code'
    get_barcode.admin_order_field = 'physical_copy__barcode'

    def has_delete_permission(self, request, obj=None):
        # Inventory logs should not be deleted (audit trail)
        return False
