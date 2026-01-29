from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import SubscriptionPlan, Order, SubscriptionCycle, OrderItem
from services.email_service import (
    send_order_confirmation_email,
    send_order_dispatched_email,
    send_order_delivered_email,
    send_order_out_for_delivery_email
)


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(ModelAdmin):
    list_display = ('plan_name_link', 'books_per_month', 'price_per_month', 'age_group_min', 'age_group_max', 'is_active')
    list_filter = ('is_active', 'age_group_min')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)

    # Enhanced change list template
    change_list_template = 'admin/catalog/enhanced_book_clean.html'

    def plan_name_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse('admin:orders_subscriptionplan_change', args=[obj.pk])
        return format_html(
            '<a href="{}" style="color: #4b5563 !important; font-weight: 600; font-size: 14px;">{}</a>',
            url,
            obj.name
        )
    plan_name_link.short_description = 'Name'
    plan_name_link.admin_order_field = 'name'


class OrderItemInline(TabularInline):
    """Inline for OrderItem (purchase orders)."""
    model = OrderItem
    extra = 0
    readonly_fields = ('subtotal',)
    fields = ('book', 'quantity', 'price_per_unit', 'subtotal')


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ('order_id_link', 'get_parent_name', 'get_phone_number', 'order_type', 'status', 'total_amount', 'tracking_number', 'created_at')
    list_editable = ('status', 'tracking_number')
    list_filter = ('order_type', 'status', 'payment_method', 'created_at')
    search_fields = ('id', 'parent__user__username', 'parent__user__email', 'tracking_number')
    readonly_fields = ('created_at', 'updated_at')
    
    # Enhanced change list template
    change_list_template = 'admin/catalog/enhanced_book_clean.html'

    def order_id_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse('admin:orders_order_change', args=[obj.pk])
        # Use simple black color with important to ensure visibility
        return format_html(
            '<a href="{}" style="color: #1f2937 !important; font-weight: 500; font-size: 13px; display: inline-block;">#{}</a>',
            url,
            obj.id
        )
    order_id_link.short_description = 'Order ID'
    order_id_link.admin_order_field = 'id'

    def get_parent_name(self, obj):
        return f"{obj.parent.user.first_name} {obj.parent.user.last_name}" if obj.parent.user.first_name else obj.parent.user.username
    get_parent_name.short_description = 'Parent'

    def get_phone_number(self, obj):
        return obj.parent.phone_number
    get_phone_number.short_description = 'Phone Number'
    
    fieldsets = (
        ('Order Information', {
            'fields': ('parent', 'order_type', 'status', 'payment_method', 'total_amount')
        }),
        ('Delivery Address', {
            'fields': ('delivery_name', 'delivery_phone', 'delivery_address', 
                      'delivery_city', 'delivery_state', 'delivery_pincode'),
            'classes': ('collapse',)
        }),
        ('Tracking Information', {
            'fields': ('tracking_number', 'courier_partner', 'estimated_delivery_date',
                      'dispatched_at', 'delivered_at'),
            'description': 'Fill tracking details when marking order as DISPATCHED',
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['mark_as_dispatched', 'mark_as_out_for_delivery', 'mark_as_delivered', 'confirm_cod_payment']
    inlines = [OrderItemInline]
    
    def save_model(self, request, obj, form, change):
        """Auto-update timestamps when status changes and send email notifications."""
        from django.utils import timezone
        
        if change:  # Existing order
            old_obj = Order.objects.get(pk=obj.pk)
            
            # Auto-set dispatched_at when status changes to DISPATCHED
            if obj.status == 'DISPATCHED' and old_obj.status != 'DISPATCHED':
                if not obj.dispatched_at:
                    obj.dispatched_at = timezone.now()
                    self.message_user(request, f"✓ Dispatched timestamp auto-set to {obj.dispatched_at.strftime('%d %b %Y, %I:%M %p')}", level='SUCCESS')
            
            # Auto-set delivered_at when status changes to DELIVERED
            if obj.status == 'DELIVERED' and old_obj.status != 'DELIVERED':
                if not obj.delivered_at:
                    obj.delivered_at = timezone.now()
                    self.message_user(request, f"✓ Delivered timestamp auto-set to {obj.delivered_at.strftime('%d %b %Y, %I:%M %p')}", level='SUCCESS')
                
                # Auto-mark COD as PAID when delivered
                if obj.payment_method == 'COD' and obj.status == 'DELIVERED':
                    obj.status = 'PAID'
                    self.message_user(request, "✓ COD order auto-marked as PAID after delivery", level='SUCCESS')
        
        super().save_model(request, obj, form, change)
        
        # Send email notifications after save
        if change:
            old_obj = Order.objects.get(pk=obj.pk)
            
            # Send confirmation email when order is PAID or CONFIRMED
            if obj.status in ['PAID', 'CONFIRMED'] and old_obj.status not in ['PAID', 'CONFIRMED']:
                if send_order_confirmation_email(obj):
                    self.message_user(request, f"📧 Order confirmation email sent to {obj.parent.user.email}", level='SUCCESS')
                else:
                    self.message_user(request, "⚠️ Failed to send order confirmation email", level='WARNING')
            
            # Send dispatched email when status changes to DISPATCHED
            if obj.status == 'DISPATCHED' and old_obj.status != 'DISPATCHED':
                if send_order_dispatched_email(obj):
                    self.message_user(request, f"📧 Order dispatched email sent to {obj.parent.user.email}", level='SUCCESS')
                else:
                    self.message_user(request, "⚠️ Failed to send order dispatched email", level='WARNING')
            
            # Send out for delivery email when status changes to OUT_FOR_DELIVERY
            if obj.status == 'OUT_FOR_DELIVERY' and old_obj.status != 'OUT_FOR_DELIVERY':
                if send_order_out_for_delivery_email(obj):
                    self.message_user(request, f"📧 Out for delivery email sent to {obj.parent.user.email}", level='SUCCESS')
                else:
                    self.message_user(request, "⚠️ Failed to send out for delivery email", level='WARNING')
            
            # Send delivered email when status changes to DELIVERED or PAID (after delivery)
            if obj.status in ['DELIVERED', 'PAID'] and old_obj.status in ['DISPATCHED', 'OUT_FOR_DELIVERY', 'DELIVERED']:
                if obj.delivered_at and old_obj.status != 'PAID':  # Only send once
                    if send_order_delivered_email(obj):
                        self.message_user(request, f"📧 Order delivered email sent to {obj.parent.user.email}", level='SUCCESS')
                    else:
                        self.message_user(request, "⚠️ Failed to send order delivered email", level='WARNING')

    def mark_as_dispatched(self, request, queryset):
        """Mark selected orders as dispatched with timestamp."""
        from django.utils import timezone
        count = 0
        email_count = 0
        for order in queryset:
            if order.status in ['PAID', 'CONFIRMED']:
                order.status = 'DISPATCHED'
                if not order.dispatched_at:
                    order.dispatched_at = timezone.now()
                order.save()
                count += 1
                
                # Send dispatch email
                if send_order_dispatched_email(order):
                    email_count += 1
        
        self.message_user(request, f"✓ {count} order(s) marked as DISPATCHED. Don't forget to add tracking number!", level='WARNING')
        if email_count > 0:
            self.message_user(request, f"📧 {email_count} dispatch email(s) sent successfully", level='SUCCESS')
    mark_as_dispatched.short_description = "📦 Mark as Dispatched"
    
    def mark_as_out_for_delivery(self, request, queryset):
        """Mark selected orders as out for delivery."""
        from django.utils import timezone
        count = 0
        email_count = 0
        for order in queryset:
            if order.status == 'DISPATCHED':
                order.status = 'OUT_FOR_DELIVERY'
                order.save()
                count += 1
                
                # Send out for delivery email
                if send_order_out_for_delivery_email(order):
                    email_count += 1
        
        self.message_user(request, f"✓ {count} order(s) marked as OUT FOR DELIVERY", level='SUCCESS')
        if email_count > 0:
            self.message_user(request, f"📧 {email_count} out for delivery email(s) sent successfully", level='SUCCESS')
    mark_as_out_for_delivery.short_description = "🚚 Mark as Out for Delivery"

    def mark_as_delivered(self, request, queryset):
        """Mark selected orders as delivered with timestamp."""
        from django.utils import timezone
        count = 0
        email_count = 0
        for order in queryset:
            if order.status in ['DISPATCHED', 'OUT_FOR_DELIVERY']:
                order.status = 'DELIVERED'
                if not order.delivered_at:
                    order.delivered_at = timezone.now()
                
                # Auto-mark COD as PAID
                if order.payment_method == 'COD':
                    order.status = 'PAID'
                
                order.save()
                count += 1
                
                # Send delivered email
                if send_order_delivered_email(order):
                    email_count += 1
        
        self.message_user(request, f"✓ {count} order(s) marked as DELIVERED", level='SUCCESS')
        if email_count > 0:
            self.message_user(request, f"📧 {email_count} delivery confirmation email(s) sent successfully", level='SUCCESS')
    mark_as_delivered.short_description = "✅ Mark as Delivered"

    def confirm_cod_payment(self, request, queryset):
        """Confirm COD payment received and mark order as paid."""
        from apps.payments.models import Transaction
        count = 0
        for order in queryset:
            if order.payment_method == 'COD' and order.status == 'CONFIRMED':
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
        
        self.message_user(request, f"✓ {count} COD order(s) confirmed as PAID", level='SUCCESS')
    confirm_cod_payment.short_description = "💰 Confirm COD Payment"


@admin.register(SubscriptionCycle)
class SubscriptionCycleAdmin(ModelAdmin):
    list_display = ('child_name_link', 'plan', 'issue_date', 'expected_return_date', 'status', 'late_fee')
    list_filter = ('status', 'issue_date')
    search_fields = ('child__name', 'parent__user__username')
    readonly_fields = ('created_at', 'updated_at', 'books_count')
    filter_horizontal = ('physical_copies',)

    # Enhanced change list template
    change_list_template = 'admin/catalog/enhanced_book_clean.html'

    def child_name_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse('admin:orders_subscriptioncycle_change', args=[obj.pk])
        return format_html(
            '<a href="{}" style="color: #4b5563 !important; font-weight: 600; font-size: 14px;">{}</a>',
            url,
            obj.child.name
        )
    child_name_link.short_description = 'Child'
    child_name_link.admin_order_field = 'child__name'

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
