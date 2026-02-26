from django.db import models
from django.contrib.auth.models import User
from apps.profiles.models import ParentProfile


class NotificationLog(models.Model):
    """
    Audit log and deduplication guard for all scheduled notifications.
    One row per (parent, notification_type, scheduled_date, slot_key).
    The unique_together constraint prevents duplicate sends.
    """
    NOTIFICATION_TYPE_CHOICES = [
        ('WEEKDAY_REMINDER', 'Weekday Reading Reminder'),
        ('WEEKEND_REMINDER', 'Weekend Reading Reminder'),
    ]

    STATUS_CHOICES = [
        ('SENT', 'Sent Successfully'),
        ('FAILED', 'Failed'),
        ('SKIPPED', 'Skipped (no email)'),
    ]

    parent = models.ForeignKey(
        ParentProfile,
        on_delete=models.CASCADE,
        related_name='notification_logs'
    )
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES)

    # scheduled_date: the calendar date this notification belongs to
    scheduled_date = models.DateField()

    # slot_key: for weekend, one of '00', '03', '06', '09', '12', '15', '18', '21'
    #           for weekday, the parent's preferred time as 'HH:MM'
    slot_key = models.CharField(max_length=10)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    sent_at = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Notification Log"
        verbose_name_plural = "Notification Logs"
        # THE DEDUPLICATION CONSTRAINT: cannot send the same notification twice
        unique_together = [('parent', 'notification_type', 'scheduled_date', 'slot_key')]
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['scheduled_date', 'notification_type']),
            models.Index(fields=['parent', 'scheduled_date']),
        ]

    def __str__(self):
        return (
            f"{self.parent} | {self.notification_type} | "
            f"{self.scheduled_date} {self.slot_key} | {self.status}"
        )


class PushSubscription(models.Model):
    """
    Store Firebase Cloud Messaging device tokens for push notifications.
    One record per user per device.
    """
    PLATFORM_CHOICES = [
        ('android', 'Android APK'),
        ('ios', 'iOS App'),
        ('web', 'Web Browser'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='push_subscriptions'
    )
    device_token = models.CharField(max_length=500, unique=True)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='android')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Push Subscription"
        verbose_name_plural = "Push Subscriptions"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['platform']),
        ]

    def __str__(self):
        return f"{self.user.username} | {self.platform} | {self.created_at.date()}"
