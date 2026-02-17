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


class ReadingPassage(models.Model):
    LANGUAGE_CHOICES = [
        ('EN', 'English'),
        ('HI', 'Hindi'),
        ('KN', 'Kannada'),
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

    THEME_CHOICES = [
        ('adventure', 'Adventure'),
        ('animals', 'Animals'),
        ('space', 'Space'),
        ('fairy_tales', 'Fairy Tales'),
    ]

    title = models.CharField(max_length=200)
    text = models.TextField(help_text="The reading passage text")
    word_count = models.PositiveIntegerField(editable=False, default=0)
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='EN')
    grade = models.CharField(max_length=20, choices=GRADE_CHOICES)
    theme = models.CharField(max_length=20, choices=THEME_CHOICES)
    is_active = models.BooleanField(default=True, help_text="Inactive passages won't appear in fluency checks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Reading Passage"
        verbose_name_plural = "Reading Passages"
        ordering = ['language', 'grade', 'theme', 'title']

    def __str__(self):
        return f"{self.title} ({self.get_language_display()} / {self.get_grade_display()} / {self.get_theme_display()})"

    def save(self, *args, **kwargs):
        self.word_count = len(self.text.split())
        super().save(*args, **kwargs)
