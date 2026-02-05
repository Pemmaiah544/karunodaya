from apps.profiles.models import Child

def reading_notifications(request):
    """
    Passes notification data for children who haven't completed their reading test.
    """
    if not request.user.is_authenticated:
        return {}
    
    try:
        # Get children linked to this parent who haven't taken the test
        pending_test_children = Child.objects.filter(
            parent__user=request.user,
            reading_test_completed=False
        )
        
        # If user has seen notifications in this session, return 0 for the badge
        if request.session.get('notifications_seen'):
            return {
                'header_notification_count': 0,
                'pending_test_children_list': pending_test_children,
            }
            
        return {
            'header_notification_count': pending_test_children.count(),
            'pending_test_children_list': pending_test_children,
        }
    except Exception:
        return {}
