"""
API endpoints for Firebase Cloud Messaging device token registration.
These endpoints are called by the Android APK to register/unregister for push notifications.
"""
import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import PushSubscription
from .firebase_service import FirebaseNotificationService

logger = logging.getLogger(__name__)


def _parse_body(request):
    """Parse JSON body from request."""
    try:
        return json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return {}


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def register_device_token(request):
    """
    Register an Android device token for push notifications.

    Expected POST data:
    {
        "device_token": "FCM_TOKEN_HERE",
        "platform": "android"  # or "ios", "web"
    }
    """
    data = _parse_body(request)
    device_token = data.get('device_token', '').strip()
    platform = data.get('platform', 'android').lower()

    if not device_token:
        return JsonResponse({'error': 'device_token is required'}, status=400)

    if platform not in ['android', 'ios', 'web']:
        return JsonResponse({'error': f'Invalid platform: {platform}'}, status=400)

    try:
        subscription, created = PushSubscription.objects.update_or_create(
            user=request.user,
            device_token=device_token,
            defaults={
                'platform': platform,
                'is_active': True,
                'last_used': timezone.now()
            }
        )

        logger.info(
            f"Device registered for {request.user.username}: "
            f"platform={platform}, created={created}"
        )

        return JsonResponse({
            'success': True,
            'message': 'Device registered for push notifications',
            'created': created,
            'subscription_id': subscription.id
        }, status=201 if created else 200)

    except Exception as e:
        logger.error(f"Error registering device token: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def unregister_device_token(request):
    """
    Unregister a device token (remove from push notifications).

    Expected POST data:
    {
        "device_token": "FCM_TOKEN_HERE"
    }
    """
    data = _parse_body(request)
    device_token = data.get('device_token', '').strip()

    if not device_token:
        return JsonResponse({'error': 'device_token is required'}, status=400)

    try:
        subscription = PushSubscription.objects.get(
            user=request.user,
            device_token=device_token
        )
        subscription.delete()

        logger.info(f"Device unregistered for {request.user.username}")

        return JsonResponse({
            'success': True,
            'message': 'Device unregistered from push notifications'
        })

    except PushSubscription.DoesNotExist:
        return JsonResponse({'error': 'Device token not found'}, status=404)
    except Exception as e:
        logger.error(f"Error unregistering device token: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def list_device_tokens(request):
    """
    List all registered device tokens for current user.
    """
    try:
        subscriptions = list(
            PushSubscription.objects.filter(
                user=request.user,
                is_active=True
            ).values('id', 'platform', 'created_at', 'last_used')
        )

        return JsonResponse({
            'success': True,
            'count': len(subscriptions),
            'devices': subscriptions
        })

    except Exception as e:
        logger.error(f"Error listing device tokens: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def send_test_notification(request):
    """
    Send a test push notification to all registered devices.
    For testing/debugging purposes.
    """
    try:
        subscriptions = PushSubscription.objects.filter(
            user=request.user,
            is_active=True
        )

        if not subscriptions.exists():
            return JsonResponse({'error': 'No registered devices found'}, status=400)

        device_tokens = [sub.device_token for sub in subscriptions]

        result = FirebaseNotificationService.send_to_multiple(
            device_tokens=device_tokens,
            title='Karunodaya Test Notification',
            body='This is a test notification from Karunodaya',
            data={
                'type': 'test',
                'message': 'Test notification sent successfully'
            }
        )

        logger.info(f"Test notification sent: {result}")

        return JsonResponse({
            'success': True,
            'message': 'Test notification sent',
            'result': result
        })

    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def send_notification_to_parent(request):
    """
    Internal API: Send notification to a parent and all their devices.
    Called by the notification scheduler.

    Expected POST data:
    {
        "parent_id": 123,
        "title": "Reading Reminder",
        "body": "Time to read!",
        "data": {
            "type": "reading_reminder",
            "children": ["Joe", "Jose"]
        }
    }
    """
    data = _parse_body(request)
    parent_id = data.get('parent_id')
    title = data.get('title')
    body = data.get('body')
    extra_data = data.get('data', {})

    if not all([parent_id, title, body]):
        return JsonResponse(
            {'error': 'parent_id, title, and body are required'},
            status=400
        )

    try:
        subscriptions = PushSubscription.objects.filter(
            user__parent_profile__id=parent_id,
            is_active=True
        )

        device_tokens = [sub.device_token for sub in subscriptions]

        if not device_tokens:
            logger.warning(f"No devices found for parent {parent_id}")
            return JsonResponse({
                'success': False,
                'message': 'No registered devices for this parent',
                'sent_count': 0
            })

        result = FirebaseNotificationService.send_to_multiple(
            device_tokens=device_tokens,
            title=title,
            body=body,
            data=extra_data
        )

        logger.info(f"Notification sent to parent {parent_id}: {result}")

        return JsonResponse({
            'success': True,
            'message': f"Notification sent to {result['success_count']} devices",
            'result': result
        })

    except Exception as e:
        logger.error(f"Error sending notification to parent: {e}")
        return JsonResponse({'error': str(e)}, status=500)
