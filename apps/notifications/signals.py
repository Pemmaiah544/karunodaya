"""
Signal handlers for the notifications app.
Fires when a parent updates their notification preferences.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.profiles.models import ParentProfileExtra
from apps.notifications.models import NotificationLog
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ParentProfileExtra)
def on_notification_preference_changed(sender, instance, created, **kwargs):
    """
    When a parent saves their ParentProfileExtra (including notification_time),
    remove any pending (not yet sent) NotificationLog entries for today and
    future dates. This ensures the new time is picked up immediately.

    Only clears FAILED logs for today onwards — SENT logs are never touched
    (they serve as the permanent deduplication guard).
    """
    try:
        # Only act if notification_time or timezone changed
        # (signal doesn't give us diff, so we clear failed future logs cheaply)
        today = timezone.localdate()

        # Remove FAILED log entries from today forward for this parent
        # so the scheduler retries at the new time slot
        deleted_count, _ = NotificationLog.objects.filter(
            parent=instance.parent,
            scheduled_date__gte=today,
            status='FAILED',
        ).delete()

        if deleted_count:
            logger.info(
                f"Cleared {deleted_count} failed notification logs for parent "
                f"{instance.parent.id} after preference update"
            )

    except Exception as e:
        logger.error(f"Error in on_notification_preference_changed signal: {e}")
        # Never crash on signal errors
