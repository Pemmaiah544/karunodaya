from django.db import models
from django.core.validators import MinValueValidator


class Publisher(models.Model):
    """
    Book publisher/vendor information.
    """
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Publisher"
        verbose_name_plural = "Publishers"
        ordering = ['name']

    def __str__(self):
        return self.name


class Book(models.Model):
    """
    Book catalog with subscription and purchase eligibility.
    """
    DIFFICULTY_RATING_CHOICES = [
        ('BEGINNER', 'Beginner (Ages 3-6)'),
        ('INTERMEDIATE', 'Intermediate (Ages 7-10)'),
        ('ADVANCED', 'Advanced (Ages 11-14)'),
    ]

    GRADE_CHOICES = [
        ('PRE_K', 'Pre-K'),
        ('KINDERGARTEN', 'Kindergarten'),
        ('GRADE_1', 'Grade 1'),
        ('GRADE_2', 'Grade 2'),
        ('GRADE_3', 'Grade 3'),
        ('GRADE_4', 'Grade 4'),
        ('GRADE_5', 'Grade 5'),
        ('GRADE_6', 'Grade 6'),
        ('GRADE_7', 'Grade 7'),
        ('GRADE_8', 'Grade 8'),
    ]

    # Basic Information
    title = models.CharField(max_length=300)
    author = models.CharField(max_length=200)
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        related_name='books'
    )
    isbn = models.CharField(max_length=20, unique=True, blank=True, null=True)

    # Pricing
    mrp = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="MRP"
    )

    # Content
    description = models.TextField(blank=True)
    locality_tags = models.JSONField(
        default=list,
        blank=True,
        help_text='Cultural/regional tags for locality-aware curation e.g. ["Tamil Nadu", "Chennai", "Idli"]'
    )
    cover_image = models.ImageField(
        upload_to='book_covers/',
        blank=True,
        null=True
    )

    # Curation Fields
    difficulty_rating = models.CharField(
        max_length=20,
        choices=DIFFICULTY_RATING_CHOICES,
        help_text="Reading difficulty level"
    )
    recommended_grade_min = models.CharField(
        max_length=20,
        choices=GRADE_CHOICES,
        verbose_name="Minimum Grade"
    )
    recommended_grade_max = models.CharField(
        max_length=20,
        choices=GRADE_CHOICES,
        verbose_name="Maximum Grade"
    )

    # Eligibility Flags
    is_subscription_eligible = models.BooleanField(
        default=True,
        help_text="Can be included in subscription boxes"
    )
    is_purchase_eligible = models.BooleanField(
        default=True,
        help_text="Can be purchased from marketplace"
    )

    # Inventory for Purchases (not for subscriptions)
    stock_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Available stock for purchases (not subscription copies)"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        """Override save to ensure marketplace visibility for new books."""
        # For new books, ensure they have sensible defaults
        if not self.pk:  # Only for new books
            if self.stock_count == 0:
                self.stock_count = 10
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Book"
        verbose_name_plural = "Books"
        ordering = ['title']
        indexes = [
            models.Index(fields=['difficulty_rating', 'is_subscription_eligible']),
            models.Index(fields=['is_purchase_eligible', 'stock_count']),
        ]

    def __str__(self):
        return f"{self.title} by {self.author}"

    @property
    def available_for_subscription(self):
        """Check if book can be used in subscription boxes."""
        return self.is_subscription_eligible and self.is_active

    @property
    def available_for_purchase(self):
        """Check if book can be purchased."""
        return self.is_purchase_eligible and self.stock_count > 0 and self.is_active

    @property
    def low_stock(self):
        """Check if stock is low (less than 5)."""
        return self.stock_count < 5

    @property
    def critical_stock(self):
        """Check if stock is critical (less than 2)."""
        return self.stock_count < 2
