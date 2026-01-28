from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(ModelAdmin):
    list_display = ('transaction_id_link', 'order', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = (
        'razorpay_order_id', 
        'razorpay_payment_id', 
        'order__id', 
        'order__parent__user__username',
        'order__parent__user__email'
    )
    readonly_fields = ('created_at', 'updated_at', 'provider_response')

    # Enhanced change list template
    change_list_template = 'admin/catalog/enhanced_book_clean.html'

    def transaction_id_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse('admin:payments_transaction_change', args=[obj.pk])
        display_id = obj.razorpay_order_id if obj.razorpay_order_id else f"TXN-{obj.id}"
        return format_html(
            '<a href="{}" style="color: #374151; font-weight: 400; font-size: 13px;">{}</a>',
            url,
            display_id
        )
    transaction_id_link.short_description = 'Transaction ID'
    transaction_id_link.admin_order_field = 'razorpay_order_id'

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
