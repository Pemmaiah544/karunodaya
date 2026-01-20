from django.db import models
from django.core.validators import MinValueValidator
from apps.profiles.models import ParentProfile, Child
from apps.inventory.models import PhysicalCopy
from apps.catalog.models import Book


class SubscriptionPlan(models.Model):
    """
    Fixed monthly subscription plans.
    """
    name = models.CharField(max_length=100)
    books_per_month = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Number of books per month"
    )
    price_per_month = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    age_group_min = models.IntegerField(
        validators=[MinValueValidator(3)],
        help_text="Minimum age (3-14)"
    )
    age_group_max = models.IntegerField(
        validators=[MinValueValidator(3)],
        help_text="Maximum age (3-14)"
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"
        ordering = ['age_group_min', 'price_per_month']

    def __str__(self):
        return f"{self.name} - {self.books_per_month} books/₹{self.price_per_month}"


class Order(models.Model):
    """
    Order for both subscription and purchase.
    """
    ORDER_TYPE_CHOICES = [
        ('SUBSCRIPTION', 'Subscription'),
        ('PURCHASE', 'Purchase'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('DISPATCHED', 'Dispatched'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('ONLINE', 'Online Payment'),
        ('COD', 'Cash on Delivery'),
    ]

    parent = models.ForeignKey(
        ParentProfile,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='ONLINE',
        help_text='Payment method: Online or Cash on Delivery'
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['parent', 'status']),
        ]

    def __str__(self):
        return f"Order #{self.id} - {self.parent.user.username} - {self.get_order_type_display()}"


class SubscriptionCycle(models.Model):
    """
    Tracks active subscription cycles with issued books.
    """
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('RETURNED', 'Returned'),
        ('OVERDUE', 'Overdue'),
        ('LOST', 'Lost/Damaged'),
    ]

    parent = models.ForeignKey(
        ParentProfile,
        on_delete=models.CASCADE,
        related_name='subscription_cycles'
    )
    child = models.ForeignKey(
        Child,
        on_delete=models.CASCADE,
        related_name='subscription_cycles'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cycles'
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscription_cycles'
    )
    physical_copies = models.ManyToManyField(
        PhysicalCopy,
        related_name='subscription_cycles',
        help_text="Books issued in this cycle"
    )

    # Dates
    issue_date = models.DateField()
    expected_return_date = models.DateField(
        help_text="30 days from issue date"
    )
    actual_return_date = models.DateField(null=True, blank=True)

    # Status and fees
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )
    late_fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="₹50/day after grace period"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Subscription Cycle"
        verbose_name_plural = "Subscription Cycles"
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['status', '-issue_date']),
            models.Index(fields=['child', '-issue_date']),
        ]

    def __str__(self):
        return f"{self.child.name} - Cycle {self.issue_date} ({self.get_status_display()})"

    @property
    def is_overdue(self):
        """Check if cycle is overdue."""
        from datetime import date
        if self.status == 'ACTIVE' and date.today() > self.expected_return_date:
            return True
        return False

    @property
    def books_count(self):
        """Number of books in this cycle."""
        return self.physical_copies.count()


class OrderItem(models.Model):
    """
    Individual items in a purchase order.
    Tracks books and quantities for purchase orders.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Number of copies"
    )
    price_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Price per book at time of order"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        ordering = ['order', 'book']
        indexes = [
            models.Index(fields=['order']),
        ]

    def __str__(self):
        return f"Order #{self.order.id} - {self.book.title} x{self.quantity}"

    @property
    def subtotal(self):
        """Calculate subtotal for this item."""
        return self.quantity * self.price_per_unit
