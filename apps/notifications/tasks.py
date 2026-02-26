"""
Django-Q2 task functions for sending reading reminder notifications.
These are called by the Q2 scheduler based on the Schedule model.
"""
from django.conf import settings
from django.utils import timezone
from zoneinfo import ZoneInfo
from datetime import datetime
from django.db import IntegrityError

from apps.profiles.models import ParentProfile, ParentProfileExtra
from apps.notifications.models import NotificationLog
from services.notification_service import send_reading_reminder_email
import logging

logger = logging.getLogger(__name__)


def _get_weekend_slots():
    """Derive slot hours from settings — no hardcoded list."""
    interval = settings.WEEKEND_NOTIFICATION_INTERVAL_HOURS  # e.g. 3
    return list(range(0, 24, interval))  # [0, 3, 6, 9, 12, 15, 18, 21]


def _is_within_window(local_now, target_hour, target_minute):
    """Check if local_now is within settings.NOTIFICATION_WINDOW_MINUTES of target time."""
    window = settings.NOTIFICATION_WINDOW_MINUTES
    target = local_now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    return abs((local_now - target).total_seconds()) <= window * 60


def _try_send(parent, notification_type, scheduled_date, slot_key):
    """
    Attempt to send one notification. Uses database unique constraint
    as the atomic deduplication mechanism.
    Returns: 'sent', 'skipped', 'failed', or 'duplicate'
    """
    user = parent.user
    if not user.email:
        logger.debug(f"No email for parent {parent.id}, skipping")
        return 'skipped'

    try:
        # Attempt to create log entry FIRST (this is the deduplication lock)
        # If a duplicate key exists, IntegrityError is raised before the email
        log = NotificationLog(
            parent=parent,
            notification_type=notification_type,
            scheduled_date=scheduled_date,
            slot_key=slot_key,
            status='SENT',
        )
        log.save()
    except IntegrityError:
        # Already sent for this slot — normal case if tasks overlap
        logger.debug(f"Notification already sent to parent {parent.id} for {scheduled_date} {slot_key}")
        return 'duplicate'

    # Log entry created — now actually send the email
    try:
        success = send_reading_reminder_email(parent, notification_type)
        if not success:
            # Update log to FAILED (row already exists, safe to update)
            NotificationLog.objects.filter(pk=log.pk).update(
                status='FAILED',
                error_message='send_reading_reminder_email returned False'
            )
            return 'failed'
        return 'sent'
    except Exception as e:
        NotificationLog.objects.filter(pk=log.pk).update(
            status='FAILED',
            error_message=str(e)[:500]
        )
        logger.error(f"Failed to send notification to parent {parent.id}: {e}")
        return 'failed'


def _get_local_now(tz_name):
    """Convert UTC now to a specific timezone."""
    try:
        local_tz = ZoneInfo(tz_name)
    except Exception:
        local_tz = ZoneInfo('Asia/Kolkata')  # Fallback
    return timezone.now().astimezone(local_tz)


def send_weekend_notifications():
    """
    Called by django-q2 on a cron schedule (every 3 hours, Sat/Sun).
    Sends reading reminders to ALL parents with notifications_enabled=True.
    """
    now_utc = timezone.now()
    sent = 0
    skipped = 0
    failed = 0

    # For weekend broadcasts, we use default timezone from settings (IST)
    default_tz = settings.DEFAULT_NOTIFICATION_TIMEZONE
    ist_now = _get_local_now(default_tz)

    # Only fire on weekends (Saturday=5, Sunday=6)
    if ist_now.weekday() < 5:
        logger.debug(f"Not a weekend, skipping weekend notifications")
        return {'sent': 0, 'skipped': 0, 'failed': 0}

    # Find which 3-hour slot we're in (if any)
    current_slot_hour = None
    for slot_hour in _get_weekend_slots():
        slot_time_hour = slot_hour
        slot_time_minute = 0
        if _is_within_window(ist_now, slot_time_hour, slot_time_minute):
            current_slot_hour = slot_hour
            break

    if current_slot_hour is None:
        logger.debug(f"Not near any weekend slot boundary, skipping")
        return {'sent': 0, 'skipped': 0, 'failed': 0}

    scheduled_date = ist_now.date()
    slot_key = f"{current_slot_hour:02d}:00"

    # Fetch ALL parents with email and notifications enabled
    parents = ParentProfile.objects.select_related('user').filter(
        user__email__isnull=False,
    ).exclude(user__email='')

    # Filter for only those with notifications enabled
    parents_to_notify = []
    for parent in parents:
        try:
            if parent.extra_profile.notifications_enabled:
                parents_to_notify.append(parent)
        except ParentProfileExtra.DoesNotExist:
            # If no extra profile, skip (not yet onboarded for notifications)
            pass

    for parent in parents_to_notify:
        result = _try_send(
            parent,
            'WEEKEND_REMINDER',
            scheduled_date,
            slot_key
        )
        if result == 'sent':
            sent += 1
        elif result in ('skipped', 'duplicate'):
            skipped += 1
        elif result == 'failed':
            failed += 1

    logger.info(
        f"Weekend notifications: sent={sent}, skipped={skipped}, failed={failed}"
    )
    return {'sent': sent, 'skipped': skipped, 'failed': failed}


def send_weekday_notifications():
    """
    Called by django-q2 every minute on weekdays.
    Sends to parents whose notification_time matches current time in their timezone.
    """
    now_utc = timezone.now()
    sent = 0
    skipped = 0
    failed = 0

    # Process weekday notifications
    extras = ParentProfileExtra.objects.select_related(
        'parent__user'
    ).filter(
        notification_time__isnull=False,
        notifications_enabled=True,
    )

    for extra in extras:
        local_now = _get_local_now(extra.timezone or 'Asia/Kolkata')

        # Only fire on weekdays (Monday=0 ... Friday=4)
        if local_now.weekday() > 4:
            continue

        # Is now within the window of the parent's preferred time?
        if not _is_within_window(local_now, extra.notification_time.hour, extra.notification_time.minute):
            continue

        scheduled_date = local_now.date()
        slot_key = extra.notification_time.strftime('%H:%M')

        result = _try_send(
            extra.parent,
            'WEEKDAY_REMINDER',
            scheduled_date,
            slot_key
        )
        if result == 'sent':
            sent += 1
        elif result in ('skipped', 'duplicate'):
            skipped += 1
        elif result == 'failed':
            failed += 1

    logger.info(
        f"Weekday notifications: sent={sent}, skipped={skipped}, failed={failed}"
    )
    return {'sent': sent, 'skipped': skipped, 'failed': failed}
