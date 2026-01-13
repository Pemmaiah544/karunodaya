from django.db import models
from django.contrib.auth.models import User
from apps.catalog.models import Book


class PhysicalCopy(models.Model):
    """
    Physical copy of a book for subscription tracking.
    Each subscription book has a unique barcode/ID for tracking.
    """
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('ISSUED', 'Issued'),
        ('DAMAGED', 'Damaged'),
        ('LOST', 'Lost'),
    ]

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='physical_copies'
    )
    barcode = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique barcode/ID for this copy"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='AVAILABLE'
    )
    condition_notes = models.TextField(
        blank=True,
        help_text="Notes about the condition of this copy"
    )
    purchased_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Physical Copy"
        verbose_name_plural = "Physical Copies"
        ordering = ['book', 'barcode']
        indexes = [
            models.Index(fields=['barcode']),
            models.Index(fields=['status', 'book']),
        ]

    def __str__(self):
        return f"{self.book.title} - {self.barcode} ({self.get_status_display()})"

    @property
    def is_available(self):
        """Check if copy is available for issuing."""
        return self.status == 'AVAILABLE'


class InventoryLog(models.Model):
    """
    Audit trail for all inventory actions on physical copies.
    """
    ACTION_CHOICES = [
        ('ADDED', 'Added to Inventory'),
        ('ISSUED', 'Issued to Customer'),
        ('RETURNED', 'Returned by Customer'),
        ('DAMAGED', 'Marked as Damaged'),
        ('LOST', 'Marked as Lost'),
        ('REPAIRED', 'Repaired'),
    ]

    physical_copy = models.ForeignKey(
        PhysicalCopy,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='inventory_actions'
    )
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Inventory Log"
        verbose_name_plural = "Inventory Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['physical_copy', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.get_action_display()} - {self.physical_copy.barcode} at {self.timestamp}"
