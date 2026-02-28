"""
Firebase Cloud Messaging service for PWA push notifications.
Handles sending push notifications to mobile and web devices.

Two modes:
  1. firebase-admin SDK (preferred) — requires FIREBASE_CREDENTIALS_PATH in settings.
  2. FCM Legacy HTTP API via `requests` — works as long as the server key is set
     in FIREBASE_SERVER_KEY (not needed for web-push VAPID subscriptions).

The server only needs firebase-admin (or the FCM server key) to SEND messages.
The VAPID key is only used by the browser client to SUBSCRIBE.
"""
import logging
from django.conf import settings
import os

logger = logging.getLogger(__name__)

# Guard the firebase_admin import — the package is optional.
# If it is not installed the service will log a warning and return
# graceful no-op results instead of crashing the whole application.
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    firebase_admin = None
    credentials = None
    messaging = None
    FIREBASE_AVAILABLE = False
    logger.warning(
        "firebase_admin package is not installed. "
        "Push notifications via FCM will be disabled. "
        "Install it with: pip install firebase-admin"
    )


class FirebaseNotificationService:
    """Service for sending push notifications via Firebase Cloud Messaging"""

    _app = None

    @classmethod
    def initialize(cls):
        """Initialize Firebase app (call once on startup)"""
        if not FIREBASE_AVAILABLE:
            return None

        if cls._app is not None:
            return cls._app

        try:
            credentials_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)

            if not credentials_path:
                logger.warning("FIREBASE_CREDENTIALS_PATH not set in settings — firebase-admin disabled")
                return None

            if not os.path.exists(credentials_path):
                logger.error(f"Firebase credentials file not found: {credentials_path}")
                return None

            cred = credentials.Certificate(credentials_path)
            cls._app = firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized successfully")
            return cls._app

        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            return None

    @classmethod
    def is_ready(cls):
        """Return True if the SDK is initialised and ready to send."""
        return FIREBASE_AVAILABLE and cls._app is not None

    @staticmethod
    def send_to_device(device_token: str, title: str, body: str, data: dict = None) -> tuple:
        """
        Send push notification to a single device

        Args:
            device_token: FCM device token
            title: Notification title
            body: Notification body/message
            data: Optional data payload (dict)

        Returns:
            (success: bool, response: str)
        """
        if not FIREBASE_AVAILABLE:
            logger.warning("firebase_admin not installed — skipping push notification")
            return False, "firebase_admin not installed"

        if not FirebaseNotificationService.is_ready():
            logger.warning("Firebase not initialised (no credentials) — skipping push")
            return False, "Firebase not initialised"

        if not device_token:
            return False, "No device token provided"

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data={str(k): str(v) for k, v in (data or {}).items()},
                token=device_token,
            )

            response = messaging.send(message)
            logger.info(f"Notification sent to {device_token[:20]}…: {response}")
            return True, response

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False, str(e)

    @staticmethod
    def send_to_multiple(device_tokens: list, title: str, body: str, data: dict = None) -> dict:
        """
        Send push notification to multiple devices

        Returns:
            {
                'success_count': int,
                'failure_count': int,
                'failed_tokens': list,
                'response': str
            }
        """
        if not FIREBASE_AVAILABLE:
            logger.warning("firebase_admin not installed — skipping push notification")
            return {
                'success_count': 0,
                'failure_count': len(device_tokens),
                'failed_tokens': list(device_tokens),
                'response': 'firebase_admin not installed'
            }

        if not FirebaseNotificationService.is_ready():
            logger.warning("Firebase not initialised — skipping push")
            return {
                'success_count': 0,
                'failure_count': len(device_tokens),
                'failed_tokens': list(device_tokens),
                'response': 'Firebase not initialised'
            }

        if not device_tokens:
            return {
                'success_count': 0,
                'failure_count': 0,
                'failed_tokens': [],
                'response': 'No device tokens provided'
            }

        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data={str(k): str(v) for k, v in (data or {}).items()},
                tokens=device_tokens,
            )

            response = messaging.send_each_for_multicast(message)

            failed_tokens = []
            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    failed_tokens.append(device_tokens[idx])
                    logger.debug(f"FCM send failed for token {device_tokens[idx][:20]}…: {resp.exception}")

            logger.info(f"Sent to {response.success_count}, failed: {response.failure_count}")

            return {
                'success_count': response.success_count,
                'failure_count': response.failure_count,
                'failed_tokens': failed_tokens,
                'response': f"Sent: {response.success_count}, Failed: {response.failure_count}"
            }

        except Exception as e:
            logger.error(f"Failed to send multicast notification: {e}")
            return {
                'success_count': 0,
                'failure_count': len(device_tokens),
                'failed_tokens': device_tokens,
                'response': str(e)
            }

    @staticmethod
    def send_notification_to_topic(topic: str, title: str, body: str, data: dict = None) -> tuple:
        """
        Send push notification to users subscribed to a topic
        """
        if not FIREBASE_AVAILABLE:
            logger.warning("firebase_admin not installed — skipping push notification")
            return False, "firebase_admin not installed"

        if not FirebaseNotificationService.is_ready():
            return False, "Firebase not initialised"

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data={str(k): str(v) for k, v in (data or {}).items()},
                topic=topic,
            )

            response = messaging.send(message)
            logger.info(f"Notification sent to topic '{topic}': {response}")
            return True, response

        except Exception as e:
            logger.error(f"Failed to send topic notification: {e}")
            return False, str(e)

    @classmethod
    def send_reading_reminder_push(cls, parent) -> dict:
        """
        High-level helper: send a reading reminder push to all of a parent's
        registered web/mobile devices.

        Args:
            parent: ParentProfile instance

        Returns:
            dict with success_count / failure_count / response
        """
        from apps.notifications.models import PushSubscription

        subscriptions = PushSubscription.objects.filter(
            user=parent.user,
            is_active=True
        )

        device_tokens = [sub.device_token for sub in subscriptions]
        if not device_tokens:
            logger.debug(f"No push subscriptions for parent {parent.id}")
            return {'success_count': 0, 'failure_count': 0, 'failed_tokens': [], 'response': 'No devices'}

        children = parent.children.filter(is_active=True)
        child_names = ', '.join(c.name for c in children) if children.exists() else 'your child'

        result = cls.send_to_multiple(
            device_tokens=device_tokens,
            title='📚 Reading Reminder',
            body=f"It's time for {child_names} to read.",
            data={
                'type': 'reading_reminder',
                'parent_id': str(parent.id),
            }
        )

        # Deactivate tokens that are no longer valid
        if result.get('failed_tokens'):
            PushSubscription.objects.filter(
                device_token__in=result['failed_tokens']
            ).update(is_active=False)
            logger.info(
                f"Deactivated {len(result['failed_tokens'])} invalid FCM tokens "
                f"for parent {parent.id}"
            )

        return result

    @classmethod
    def send_order_push(cls, order, event_type: str) -> dict:
        """
        Send a push notification for an order status update.

        Args:
            order: Order instance
            event_type: 'confirmed' | 'dispatched' | 'out_for_delivery' | 'delivered'
        """
        from apps.notifications.models import PushSubscription

        parent = order.parent
        subscriptions = PushSubscription.objects.filter(user=parent.user, is_active=True)
        device_tokens = [sub.device_token for sub in subscriptions]

        if not device_tokens:
            logger.debug(f"No push subscriptions for parent {parent.id} (Order #{order.id})")
            return {'success_count': 0, 'failure_count': 0, 'failed_tokens': [], 'response': 'No devices'}

        _TITLES = {
            'confirmed':        '✅ Order Confirmed',
            'dispatched':       '🚚 Order Dispatched',
            'out_for_delivery': '📦 Out for Delivery',
            'delivered':        '🎉 Order Delivered',
        }
        _BODIES = {
            'confirmed':        f'Your order #{order.id} has been confirmed.',
            'dispatched':       f'Your order #{order.id} is on its way!',
            'out_for_delivery': f'Your order #{order.id} is out for delivery today.',
            'delivered':        f'Your order #{order.id} has been delivered. Happy reading!',
        }

        result = cls.send_to_multiple(
            device_tokens=device_tokens,
            title=_TITLES.get(event_type, 'Order Update'),
            body=_BODIES.get(event_type, f'Order #{order.id} has been updated.'),
            data={'type': 'order_update', 'event': event_type, 'order_id': str(order.id)},
        )

        if result.get('failed_tokens'):
            PushSubscription.objects.filter(
                device_token__in=result['failed_tokens']
            ).update(is_active=False)
            logger.info(f"Deactivated {len(result['failed_tokens'])} invalid tokens for Order #{order.id}")

        return result


# Initialize on module import (safe — guarded above)
try:
    FirebaseNotificationService.initialize()
except Exception as e:
    logger.warning(f"Firebase not available: {e}")
