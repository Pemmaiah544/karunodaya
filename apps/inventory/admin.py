from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import PhysicalCopy, InventoryLog


class InventoryLogInline(admin.TabularInline):
    model = InventoryLog
    extra = 0
    readonly_fields = ('action', 'performed_by', 'notes', 'timestamp')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(PhysicalCopy)
class PhysicalCopyAdmin(ModelAdmin):
    list_display = ('barcode', 'book', 'status', 'purchased_date', 'updated_at')
    list_filter = ('status', 'purchased_date')
    search_fields = ('barcode', 'book__title')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [InventoryLogInline]
    actions = ['mark_as_damaged', 'mark_as_lost', 'mark_as_available']

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
    list_display = ('physical_copy', 'action', 'performed_by', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('physical_copy__barcode', 'notes')
    readonly_fields = ('timestamp',)

    def has_delete_permission(self, request, obj=None):
        # Inventory logs should not be deleted (audit trail)
        return False
