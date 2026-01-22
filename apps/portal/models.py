from django.db import models
from apps.profiles.models import ParentProfile
from apps.orders.models import Order


class Complaint(models.Model):
    """
    Model for logging issues and complaints by parents.
    """
    CATEGORY_CHOICES = [
        ('DELIVERY_DELAY', 'Delivery Delay'),
        ('MISSING_BOOK', 'Missing Book'),
        ('DAMAGED_BOOK', 'Damaged Book'),
        ('PAYMENT_ISSUE', 'Payment Issue'),
        ('TECHNICAL_GLITCH', 'Technical Glitch'),
        ('OTHER', 'Other'),
    ]

    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ]

    parent = models.ForeignKey(
        ParentProfile,
        on_delete=models.CASCADE,
        related_name='complaints'
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='complaints',
        help_text="Optional: Reference to a specific order"
    )
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='OPEN'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Complaint"
        verbose_name_plural = "Complaints"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} - {self.parent.user.username} ({self.get_status_display()})"
