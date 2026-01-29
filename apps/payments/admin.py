from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(ModelAdmin):
    list_display = ('transaction_id_link', 'get_order_number', 'get_parent_name', 'get_order_type', 'amount', 'status', 'created_at')
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
            '<a href="{}" style="color: #4b5563 !important; font-weight: 600; font-size: 14px;">{}</a>',
            url,
            display_id
        )
    transaction_id_link.short_description = 'Transaction ID'
    transaction_id_link.admin_order_field = 'razorpay_order_id'

    def get_order_number(self, obj):
        """Display order number as a link."""
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.order:
            url = reverse('admin:orders_order_change', args=[obj.order.pk])
            return format_html(
                '<a href="{}" style="color: #4b5563;">#{}</a>',
                url,
                obj.order.id
            )
        return '-'
    get_order_number.short_description = 'Order No'
    get_order_number.admin_order_field = 'order__id'

    def get_parent_name(self, obj):
        """Display parent name."""
        if obj.order and obj.order.parent:
            user = obj.order.parent.user
            if user.first_name:
                return f"{user.first_name} {user.last_name}".strip()
            return user.username
        return '-'
    get_parent_name.short_description = 'Parent Name'
    get_parent_name.admin_order_field = 'order__parent__user__first_name'

    def get_order_type(self, obj):
        """Display order type with color coding."""
        from django.utils.html import format_html
        if obj.order:
            if obj.order.order_type == 'SUBSCRIPTION':
                return format_html(
                    '<span style="color: #fb923c; font-weight: 500;">📦 Subscription</span>'
                )
            else:
                return format_html(
                    '<span style="color: #4b5563; font-weight: 500;">🛒 Purchase</span>'
                )
        return '-'
    get_order_type.short_description = 'Order Type'
    get_order_type.admin_order_field = 'order__order_type'

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
