from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class ParentProfile(models.Model):
    """
    Extended profile for parent users.
    OneToOne relationship with Django's User model.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='parent_profile'
    )
    phone_number = models.CharField(max_length=15)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    plan_preference = models.CharField(
        max_length=20,
        choices=[
            ('subscription', 'Subscription Only'),
            ('purchase', 'Purchase Only'),
            ('both', 'Subscription + Purchase')
        ],
        blank=True,
        null=True,
        help_text="User's preferred plan type from onboarding"
    )
    onboarding_completed = models.BooleanField(
        default=False,
        help_text="Whether the user has completed the full onboarding process"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Parent Profile"
        verbose_name_plural = "Parent Profiles"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.phone_number}"

    @property
    def children_count(self):
        return self.children.count()


class Child(models.Model):
    """
    Child profile linked to parent.
    Used for book curation based on age, grade, and reading level.
    """
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

    DIFFICULTY_LEVEL_CHOICES = [
        ('BEGINNER', 'Beginner (Ages 3-6)'),
        ('INTERMEDIATE', 'Intermediate (Ages 7-10)'),
        ('ADVANCED', 'Advanced (Ages 11-14)'),
    ]

    parent = models.ForeignKey(
        ParentProfile,
        on_delete=models.CASCADE,
        related_name='children'
    )
    name = models.CharField(max_length=100)
    age = models.IntegerField(
        validators=[MinValueValidator(3), MaxValueValidator(14)],
        blank=True,
        null=True
    )
    grade = models.CharField(max_length=20, choices=GRADE_CHOICES, blank=True, null=True)
    reading_difficulty_level = models.CharField(
        max_length=20,
        choices=DIFFICULTY_LEVEL_CHOICES,
        help_text="Reading difficulty level for book curation",
        blank=True,
        null=True
    )
    date_of_birth = models.DateField(blank=True, null=True)
    interests = models.TextField(blank=True, null=True, help_text="Child's interests (e.g., animals, space, adventures)")
    reading_wpm = models.IntegerField(blank=True, null=True, help_text="Words per minute from fluency check")
    reading_test_completed = models.BooleanField(default=False, help_text="Whether the child has completed their first reading test")
    reading_accuracy = models.FloatField(blank=True, null=True, help_text="Accuracy percentage from fluency check")
    reading_strengths = models.TextField(blank=True, null=True, help_text="Strengths identified in reading")
    reading_gaps = models.TextField(blank=True, null=True, help_text="Areas for improvement identified in reading")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Child"
        verbose_name_plural = "Children"
        ordering = ['name']
        # Limit 5 children per parent (enforced at form level)

    def __str__(self):
        age_str = f"{self.age} years" if self.age else "age unknown"
        grade_str = self.get_grade_display() if self.grade else "grade unknown"
        return f"{self.name} ({age_str}, {grade_str})"

    def save(self, *args, **kwargs):
        # Validate max 5 children per parent
        if not self.pk:  # New child
            if self.parent.children.count() >= 5:
                raise ValueError("A parent can have a maximum of 5 children.")
        super().save(*args, **kwargs)
