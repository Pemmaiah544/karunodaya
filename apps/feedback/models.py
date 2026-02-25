from django.db import models


class AppFeedback(models.Model):
    """
    General app helpfulness feedback from parents about how Karunodaya helps their children improve reading.
    """

    GOING_WELL_CHOICES = [
        ('assessments_accurate', 'Reading level assessments are accurate'),
        ('recommendations_good', 'Book recommendations match my child\'s level'),
        ('eager_reading', 'My child looks forward to reading sessions'),
        ('easy_to_use', 'App is easy to use'),
        ('language_variety', 'Good variety of languages/topics'),
    ]

    NEEDS_IMPROVEMENT_CHOICES = [
        ('more_languages', 'More books in regional languages'),
        ('better_recommendations', 'Better book recommendations for my child\'s level'),
        ('more_activities', 'More reading activities / exercises'),
        ('progress_tracking', 'Progress tracking / history'),
        ('parent_tips', 'Reading tips for parents'),
    ]

    parent = models.ForeignKey(
        'profiles.ParentProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='app_feedbacks'
    )
    rating = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 6)],
        help_text='1-5 star rating'
    )
    going_well = models.JSONField(
        default=list,
        blank=True,
        help_text='List of choice keys for what\'s working well'
    )
    needs_improvement = models.JSONField(
        default=list,
        blank=True,
        help_text='List of choice keys for what needs improvement'
    )
    comments = models.TextField(
        blank=True,
        max_length=500,
        help_text='Optional additional comments'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['rating']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"AppFeedback {self.rating}★ by {self.parent} ({self.created_at:%Y-%m-%d})"


class CycleFeedback(models.Model):
    """
    Per subscription cycle feedback about books and reading experience.
    """

    ENJOYED_CHOICES = [
        ('engaging_stories', 'Stories were engaging and age-appropriate'),
        ('good_difficulty', 'Good language difficulty level'),
        ('interesting_topics', 'Interesting topics (animals, adventure, etc.)'),
        ('good_illustrations', 'Beautiful illustrations'),
    ]

    NEEDS_IMPROVEMENT_CHOICES = [
        ('difficulty_level', 'Books were too easy / too hard'),
        ('not_interesting', 'Topics were not very interesting'),
        ('prefer_language', 'Would prefer more books in [language]'),
        ('poor_condition', 'Some books were in poor condition'),
    ]

    cycle = models.OneToOneField(
        'orders.SubscriptionCycle',
        on_delete=models.CASCADE,
        related_name='feedback'
    )
    parent = models.ForeignKey(
        'profiles.ParentProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='cycle_feedbacks'
    )
    child = models.ForeignKey(
        'profiles.Child',
        on_delete=models.SET_NULL,
        null=True,
        related_name='cycle_feedbacks'
    )
    rating = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 6)],
        help_text='1-5 star rating for books'
    )
    enjoyed = models.JSONField(
        default=list,
        blank=True,
        help_text='List of choice keys for what went well'
    )
    needs_improvement = models.JSONField(
        default=list,
        blank=True,
        help_text='List of choice keys for improvements'
    )
    comments = models.TextField(
        blank=True,
        max_length=300,
        help_text='Optional additional comments'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['parent', '-created_at']),
            models.Index(fields=['rating']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"CycleFeedback {self.rating}★ for {self.child} ({self.created_at:%Y-%m-%d})"
