from django.db import models
from django.core.validators import MinValueValidator
from apps.orders.models import Order


class Transaction(models.Model):
    """
    Payment transaction record for Razorpay integration.
    """
    STATUS_CHOICES = [
        ('INITIATED', 'Initiated'),
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    # Razorpay IDs
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    razorpay_signature = models.CharField(max_length=200, blank=True)

    # Amount
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='INITIATED'
    )

    # Payment Method (captured from Razorpay)
    payment_method = models.CharField(
        max_length=50,
        blank=True,
        help_text="Payment method used (card, netbanking, upi, etc.)"
    )

    # Provider Response (for debugging)
    provider_response = models.JSONField(
        default=dict,
        blank=True,
        help_text="Full response from Razorpay for debugging"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['razorpay_order_id']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Transaction {self.razorpay_order_id} - {self.get_status_display()}"

    @property
    def is_successful(self):
        """Check if transaction was successful."""
        return self.status == 'SUCCESS'
