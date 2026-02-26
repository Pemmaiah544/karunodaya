"""
Firebase Cloud Messaging service for PWA push notifications.
Handles sending push notifications to mobile and web devices.
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
                logger.warning("FIREBASE_CREDENTIALS_PATH not set in settings")
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

        if not device_token:
            return False, "No device token provided"

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=device_token,
            )

            response = messaging.send(message)
            logger.info(f"Notification sent to {device_token}: {response}")
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
                data=data or {},
                tokens=device_tokens,
            )

            response = messaging.send_multicast(message)

            failed_tokens = []
            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    failed_tokens.append(device_tokens[idx])

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

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                topic=topic,
            )

            response = messaging.send(message)
            logger.info(f"Notification sent to topic '{topic}': {response}")
            return True, response

        except Exception as e:
            logger.error(f"Failed to send topic notification: {e}")
            return False, str(e)


# Initialize on module import (safe — guarded above)
try:
    FirebaseNotificationService.initialize()
except Exception as e:
    logger.warning(f"Firebase not available: {e}")
