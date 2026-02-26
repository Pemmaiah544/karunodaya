from apps.profiles.models import Child
from django.utils import timezone

def reading_notifications(request):
    """
    Passes notification data for children who haven't completed their reading test
    AND reading reminder notifications sent today.
    """
    if not request.user.is_authenticated:
        return {}

    try:
        # Get children linked to this parent who haven't taken the test
        pending_test_children = Child.objects.filter(
            parent__user=request.user,
            reading_test_completed=False
        )

        # Get reading reminder notifications sent today
        from apps.notifications.models import NotificationLog
        today = timezone.localdate()
        reading_reminders_today = NotificationLog.objects.filter(
            parent__user=request.user,
            scheduled_date=today,
            status='SENT'
        ).count()

        # Combined notification count for badge
        total_notifications = pending_test_children.count() + reading_reminders_today

        # If user has seen notifications in this session, return 0 for the badge
        if request.session.get('notifications_seen'):
            return {
                'header_notification_count': 0,
                'pending_test_children_list': pending_test_children,
                'reading_reminders_today': reading_reminders_today,
                'total_notifications': total_notifications,
            }

        return {
            'header_notification_count': total_notifications,
            'pending_test_children_list': pending_test_children,
            'reading_reminders_today': reading_reminders_today,
            'total_notifications': total_notifications,
        }
    except Exception:
        return {}
