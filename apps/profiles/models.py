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
    is_active = models.BooleanField(default=True, help_text="Whether this child's profile is currently active")
    has_tried_other_languages = models.BooleanField(default=False, help_text="Whether the child has tried or dismissed the multilingual banner")
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


class ChildProfileExtra(models.Model):
    """
    Extended child profile data collected after onboarding.
    OneToOne extension of Child — use get_or_create pattern.
    Captures language background, reading behaviour, and digital habits.
    """
    MEDIUM_CHOICES = [
        ('ENGLISH', 'English Medium'),
        ('HINDI', 'Hindi Medium'),
        ('KANNADA', 'Kannada Medium'),
        ('MARATHI', 'Marathi Medium'),
        ('TAMIL', 'Tamil Medium'),
        ('TELUGU', 'Telugu Medium'),
        ('BENGALI', 'Bengali Medium'),
        ('GUJARATI', 'Gujarati Medium'),
        ('PUNJABI', 'Punjabi Medium'),
        ('OTHER', 'Other'),
    ]

    LANGUAGE_CHOICES = [
        ('ENGLISH', 'English'),
        ('HINDI', 'Hindi'),
        ('KANNADA', 'Kannada'),
        ('MARATHI', 'Marathi'),
        ('TAMIL', 'Tamil'),
        ('TELUGU', 'Telugu'),
        ('BENGALI', 'Bengali'),
        ('GUJARATI', 'Gujarati'),
        ('PUNJABI', 'Punjabi'),
        ('OTHER', 'Other'),
    ]

    COMPREHENSION_CHOICES = [
        ('BASIC', 'Basic – understands simple sentences'),
        ('DEVELOPING', 'Developing – follows short stories'),
        ('PROFICIENT', 'Proficient – understands complex texts'),
        ('ADVANCED', 'Advanced – critical comprehension'),
    ]

    SPEED_CHOICES = [
        ('SLOW', 'Slow – reads carefully, word by word'),
        ('AVERAGE', 'Average – normal pace'),
        ('FAST', 'Fast – reads quickly'),
        ('VARIES', 'Varies – depends on material'),
    ]

    child = models.OneToOneField(
        Child,
        on_delete=models.CASCADE,
        related_name='extra_profile'
    )

    # Basic
    medium = models.CharField(
        max_length=20,
        choices=MEDIUM_CHOICES,
        blank=True,
        null=True,
        help_text="Language of instruction at school"
    )

    # Language background
    primary_language = models.CharField(
        max_length=20,
        choices=LANGUAGE_CHOICES,
        blank=True,
        null=True,
        help_text="Child's primary reading/home language"
    )
    other_languages = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Other languages the child knows (comma-separated)"
    )
    comprehension_level = models.CharField(
        max_length=20,
        choices=COMPREHENSION_CHOICES,
        blank=True,
        null=True
    )

    # Reading behaviour
    reads_aloud = models.BooleanField(
        default=False,
        help_text="Child typically reads aloud rather than silently"
    )
    skips_words = models.BooleanField(
        default=False,
        help_text="Child tends to skip unfamiliar words"
    )
    reading_speed_perception = models.CharField(
        max_length=10,
        choices=SPEED_CHOICES,
        blank=True,
        null=True,
        help_text="Parent's perception of child's reading speed"
    )

    # Digital habits
    avg_screen_time_hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(24)],
        help_text="Average daily screen time in hours"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Child Profile Extra"
        verbose_name_plural = "Child Profile Extras"

    def __str__(self):
        return f"Extra profile – {self.child.name}"


class ParentProfileExtra(models.Model):
    """
    Extended parent profile data collected after onboarding.
    Captures reading support habits and routine.
    """
    FREQUENCY_CHOICES = [
        ('DAILY', 'Daily'),
        ('SEVERAL_WEEK', 'Several times a week'),
        ('ONCE_WEEK', 'Once a week'),
        ('RARELY', 'Rarely'),
        ('NEVER', 'Never'),
    ]

    TIME_CHOICES = [
        ('MORNING', 'Morning'),
        ('AFTERNOON', 'Afternoon'),
        ('EVENING', 'Evening'),
        ('BEDTIME', 'Bedtime'),
        ('WEEKEND', 'Weekends only'),
    ]

    parent = models.OneToOneField(
        ParentProfile,
        on_delete=models.CASCADE,
        related_name='extra_profile'
    )

    # Support
    reading_frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        blank=True,
        null=True,
        help_text="How often parent reads with child"
    )
    provides_assistance = models.BooleanField(
        default=False,
        help_text="Parent actively assists child during reading sessions"
    )
    books_at_home = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MaxValueValidator(500)],
        help_text="Approximate number of books at home"
    )

    # Routine
    preferred_reading_time = models.CharField(
        max_length=20,
        choices=TIME_CHOICES,
        blank=True,
        null=True
    )
    reading_duration_minutes = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MaxValueValidator(180)],
        help_text="Typical reading session duration in minutes"
    )

    profile_completed = models.BooleanField(
        default=False,
        help_text="Whether the parent has completed the enhanced profile form"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Parent Profile Extra"
        verbose_name_plural = "Parent Profile Extras"

    def __str__(self):
        return f"Extra profile – {self.parent.user.get_full_name() or self.parent.user.username}"


class ReadingAssessment(models.Model):
    """
    Historical record of each fluency check attempt.
    FK to Child (not OneToOne) — accumulates over time.
    """
    child = models.ForeignKey(
        Child,
        on_delete=models.CASCADE,
        related_name='reading_assessments'
    )
    passage = models.ForeignKey(
        'portal.ReadingPassage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assessments',
        help_text="DB passage used (null when static passage was used)"
    )
    wpm = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(500)],
        help_text="Words per minute"
    )
    accuracy = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Accuracy percentage"
    )
    level = models.CharField(
        max_length=20,
        choices=Child.DIFFICULTY_LEVEL_CHOICES,
        help_text="Reading level assigned at time of assessment"
    )
    strengths = models.TextField(blank=True, null=True)
    gaps = models.TextField(blank=True, null=True)
    language = models.CharField(
        max_length=5,
        choices=[('EN', 'English'), ('HI', 'Hindi'), ('KN', 'Kannada')],
        default='EN'
    )
    assessed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Reading Assessment"
        verbose_name_plural = "Reading Assessments"
        ordering = ['-assessed_at']

    def __str__(self):
        return f"{self.child.name} – {self.wpm} WPM – {self.assessed_at.strftime('%d %b %Y')}"
