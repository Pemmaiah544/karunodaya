import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.feedback.models import AppFeedback, CycleFeedback

logger = logging.getLogger(__name__)


@receiver(post_save, sender=AppFeedback)
def on_app_feedback_saved(sender, instance, created, **kwargs):
    """Send notification email for low-rating app feedback."""
    if created and instance.rating <= 2:
        try:
            from services.email_service import send_feedback_notification_email
            send_feedback_notification_email(instance, feedback_type='app')
        except Exception as e:
            logger.error(f"Failed to send feedback notification email: {e}")


@receiver(post_save, sender=CycleFeedback)
def on_cycle_feedback_saved(sender, instance, created, **kwargs):
    """Send notification email for low-rating cycle feedback."""
    if created and instance.rating <= 2:
        try:
            from services.email_service import send_feedback_notification_email
            send_feedback_notification_email(instance, feedback_type='cycle')
        except Exception as e:
            logger.error(f"Failed to send feedback notification email: {e}")
