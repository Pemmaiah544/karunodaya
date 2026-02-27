"""
Notification email service for reading reminders.
Follows the same pattern as services/email_service.py.
"""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from django.utils import timezone
from django.db import IntegrityError
import logging

logger = logging.getLogger(__name__)


def send_reading_reminder_email(parent, notification_type):
    """
    Send a reading reminder email to a parent.

    Args:
        parent: ParentProfile instance
        notification_type: 'WEEKDAY_REMINDER' or 'WEEKEND_REMINDER'

    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        user = parent.user
        recipient_email = user.email
        if not recipient_email:
            logger.warning(f"No email for parent {parent.id}")
            return False

        children = parent.children.filter(is_active=True)
        if not children.exists():
            logger.debug(f"Parent {parent.id} has no active children, skipping")
            return False

        is_weekend = notification_type == 'WEEKEND_REMINDER'
        subject = (
            "It's weekend reading time! Open a book with your child"
            if is_weekend
            else "Time for your child's daily reading session"
        )

        html_content = render_to_string('emails/reading_reminder.html', {
            'parent': parent,
            'user': user,
            'children': children,
            'is_weekend': is_weekend,
            'notification_type': notification_type,
        })
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()

        logger.info(
            f"Reading reminder ({notification_type}) sent to {recipient_email} "
            f"for parent {parent.id}"
        )

        # ── Also send a push notification (best-effort) ──────────────────
        _send_push_reminder(parent)

        return True

    except Exception as e:
        logger.error(f"Failed to send reading reminder to parent {parent.id}: {e}")
        return False


def _send_push_reminder(parent):
    """
    Fire a push notification to all of the parent's registered devices.
    This is best-effort: any failure is logged but never raises.
    """
    try:
        from apps.notifications.firebase_service import FirebaseNotificationService
        if FirebaseNotificationService.is_ready():
            result = FirebaseNotificationService.send_reading_reminder_push(parent)
            logger.info(
                f"Push reminder sent for parent {parent.id}: "
                f"success={result.get('success_count', 0)}, "
                f"failed={result.get('failure_count', 0)}"
            )
        else:
            logger.debug(
                f"Firebase not initialised — skipping push for parent {parent.id}"
            )
    except Exception as e:
        logger.warning(f"Push notification failed for parent {parent.id}: {e}")




def send_reading_reminder_with_log(parent, notification_type, slot_key=None):
    """
    Send a reading reminder email AND create an in-app notification log entry.

    This is used for manual/direct notification sends (not from scheduled tasks).
    The scheduled tasks use their own log creation with deduplication.

    Args:
        parent: ParentProfile instance
        notification_type: 'WEEKDAY_REMINDER' or 'WEEKEND_REMINDER'
        slot_key: Optional slot identifier (e.g., '07:30' or '09:00').
                  If not provided, uses current time.

    Returns:
        tuple: (email_sent: bool, log_created: bool)
    """
    from apps.notifications.models import NotificationLog

    email_sent = False
    log_created = False

    try:
        # Send email first
        email_sent = send_reading_reminder_email(parent, notification_type)

        # Create log entry for in-app notification (even if email failed)
        if slot_key is None:
            # Default slot_key: current time (HH:MM format)
            slot_key = timezone.localtime().strftime('%H:%M')

        try:
            log = NotificationLog.objects.create(
                parent=parent,
                notification_type=notification_type,
                scheduled_date=timezone.localdate(),
                slot_key=slot_key,
                status='SENT' if email_sent else 'FAILED',
                error_message=None if email_sent else 'Email send failed'
            )
            log_created = True
            logger.info(
                f"Created notification log for parent {parent.id} - "
                f"{notification_type} (email_sent={email_sent})"
            )
        except IntegrityError:
            # Log already exists for this slot - this is expected for duplicate attempts
            logger.debug(
                f"Notification log already exists for parent {parent.id} - "
                f"{notification_type} on {timezone.localdate()}"
            )
            log_created = False

        return email_sent, log_created

    except Exception as e:
        logger.error(f"Error in send_reading_reminder_with_log: {e}")
        return False, False
