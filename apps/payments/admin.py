from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(ModelAdmin):
    list_display = ('razorpay_order_id', 'order', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('razorpay_order_id', 'razorpay_payment_id', 'order__id')
    readonly_fields = ('created_at', 'updated_at', 'provider_response')

    fieldsets = (
        ('Order Information', {
            'fields': ('order', 'amount')
        }),
        ('Razorpay Details', {
            'fields': ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Debug Information', {
            'fields': ('provider_response',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_delete_permission(self, request, obj=None):
        # Transactions should not be deleted (audit trail)
        return False
