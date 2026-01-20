from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import SubscriptionPlan, Order, SubscriptionCycle, OrderItem


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(ModelAdmin):
    list_display = ('name', 'books_per_month', 'price_per_month', 'age_group_min', 'age_group_max', 'is_active')
    list_filter = ('is_active', 'age_group_min')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)


class OrderItemInline(TabularInline):
    """Inline for OrderItem (purchase orders)."""
    model = OrderItem
    extra = 0
    readonly_fields = ('subtotal',)
    fields = ('book', 'quantity', 'price_per_unit', 'subtotal')


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ('id', 'parent', 'order_type', 'payment_method', 'status', 'total_amount', 'created_at')
    list_filter = ('order_type', 'payment_method', 'status', 'created_at')
    search_fields = ('parent__user__username', 'parent__phone_number')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['mark_as_dispatched', 'mark_as_delivered', 'confirm_cod_payment']
    inlines = [OrderItemInline]

    def mark_as_dispatched(self, request, queryset):
        """Mark selected orders as dispatched."""
        count = queryset.filter(status='PAID').update(status='DISPATCHED')
        self.message_user(request, f"{count} order(s) marked as dispatched.")
    mark_as_dispatched.short_description = "Mark as Dispatched"

    def mark_as_delivered(self, request, queryset):
        """Mark selected orders as delivered."""
        count = queryset.filter(status='DISPATCHED').update(status='DELIVERED')
        self.message_user(request, f"{count} order(s) marked as delivered.")
    mark_as_delivered.short_description = "Mark as Delivered"

    def confirm_cod_payment(self, request, queryset):
        """Confirm COD payment received and mark order as paid."""
        from apps.payments.models import Transaction
        count = 0
        for order in queryset:
            if order.payment_method == 'COD' and order.status == 'PENDING':
                # Update order status
                order.status = 'PAID'
                order.save()
                
                # Create transaction record for audit trail
                Transaction.objects.create(
                    order=order,
                    razorpay_order_id=f'COD-{order.id}',
                    amount=order.total_amount,
                    status='SUCCESS',
                    payment_method='COD',
                    provider_response={'payment_type': 'cash_on_delivery', 'confirmed_by': request.user.username}
                )
                count += 1
        
        self.message_user(request, f"{count} COD order(s) confirmed as paid.")
    confirm_cod_payment.short_description = "Confirm COD Payment Received"


@admin.register(SubscriptionCycle)
class SubscriptionCycleAdmin(ModelAdmin):
    list_display = ('child', 'plan', 'issue_date', 'expected_return_date', 'status', 'late_fee')
    list_filter = ('status', 'issue_date')
    search_fields = ('child__name', 'parent__user__username')
    readonly_fields = ('created_at', 'updated_at', 'books_count')
    filter_horizontal = ('physical_copies',)

    fieldsets = (
        ('Subscription Information', {
            'fields': ('parent', 'child', 'plan', 'order')
        }),
        ('Books', {
            'fields': ('physical_copies', 'books_count')
        }),
        ('Dates', {
            'fields': ('issue_date', 'expected_return_date', 'actual_return_date')
        }),
        ('Status & Fees', {
            'fields': ('status', 'late_fee')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Custom admin action for marking as returned will be added in Phase 4
    actions = ['mark_as_returned']

    def mark_as_returned(self, request, queryset):
        """Mark selected subscription cycles as returned."""
        from services.curation import return_subscription_books
        count = 0
        for cycle in queryset:
            if cycle.status in ['ACTIVE', 'OVERDUE']:
                success, message = return_subscription_books(
                    cycle,
                    condition_notes='Returned via admin action',
                    returned_by=request.user
                )
                if success:
                    count += 1

        self.message_user(request, f"{count} subscription cycle(s) marked as returned.")

    mark_as_returned.short_description = "Mark as Returned"
