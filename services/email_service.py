"""
Email notification service for order updates.
Sends emails for order placement, dispatch, and delivery.
"""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def _send_order_push(order, event_type: str):
    """Best-effort push for an order event. Never raises."""
    try:
        from apps.notifications.firebase_service import FirebaseNotificationService
        if FirebaseNotificationService.is_ready():
            result = FirebaseNotificationService.send_order_push(order, event_type)
            logger.info(
                f"Order push ({event_type}) for Order #{order.id}: "
                f"success={result.get('success_count', 0)}, failed={result.get('failure_count', 0)}"
            )
        else:
            logger.debug(f"Firebase not initialised — skipping push for Order #{order.id}")
    except Exception as e:
        logger.warning(f"Push notification failed for Order #{order.id}: {e}")


def send_order_confirmation_email(order):
    """
    Send order confirmation email when order is placed.
    
    Args:
        order: Order instance
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        parent = order.parent
        user = parent.user
        
        # Get recipient email
        recipient_email = user.email
        if not recipient_email:
            logger.warning(f"No email found for user {user.username} - Order #{order.id}")
            return False
        
        # Email subject
        subject = f"Order Confirmation - Order #{order.id} | Karunodaya"
        
        # Render HTML email template
        html_content = render_to_string('emails/order_confirmation.html', {
            'order': order,
            'parent': parent,
            'user': user,
        })
        
        # Create plain text version
        text_content = strip_tags(html_content)
        
        # Send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Order confirmation email sent to {recipient_email} for Order #{order.id}")
        _send_order_push(order, 'confirmed')
        return True
        
    except Exception as e:
        logger.error(f"Failed to send order confirmation email for Order #{order.id}: {str(e)}")
        return False


def send_order_dispatched_email(order):
    """
    Send email when order is dispatched.
    
    Args:
        order: Order instance
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        parent = order.parent
        user = parent.user
        
        recipient_email = user.email
        if not recipient_email:
            logger.warning(f"No email found for user {user.username} - Order #{order.id}")
            return False
        
        subject = f"Order Dispatched - Order #{order.id} | Karunodaya"
        
        html_content = render_to_string('emails/order_dispatched.html', {
            'order': order,
            'parent': parent,
            'user': user,
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
        
        logger.info(f"Order dispatched email sent to {recipient_email} for Order #{order.id}")
        _send_order_push(order, 'dispatched')
        return True
        
    except Exception as e:
        logger.error(f"Failed to send order dispatched email for Order #{order.id}: {str(e)}")
        return False


def send_order_delivered_email(order):
    """
    Send email when order is delivered.
    
    Args:
        order: Order instance
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        parent = order.parent
        user = parent.user
        
        recipient_email = user.email
        if not recipient_email:
            logger.warning(f"No email found for user {user.username} - Order #{order.id}")
            return False
        
        subject = f"Order Delivered - Order #{order.id} | Karunodaya"
        
        html_content = render_to_string('emails/order_delivered.html', {
            'order': order,
            'parent': parent,
            'user': user,
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
        
        logger.info(f"Order delivered email sent to {recipient_email} for Order #{order.id}")
        _send_order_push(order, 'delivered')
        return True
        
    except Exception as e:
        logger.error(f"Failed to send order delivered email for Order #{order.id}: {str(e)}")
        return False


def send_order_out_for_delivery_email(order):
    """
    Send email when order is out for delivery.
    
    Args:
        order: Order instance
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        parent = order.parent
        user = parent.user
        
        recipient_email = user.email
        if not recipient_email:
            logger.warning(f"No email found for user {user.username} - Order #{order.id}")
            return False
        
        subject = f"Out for Delivery - Order #{order.id} | Karunodaya"
        
        html_content = render_to_string('emails/order_out_for_delivery.html', {
            'order': order,
            'parent': parent,
            'user': user,
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
        
        logger.info(f"Out for delivery email sent to {recipient_email} for Order #{order.id}")
        _send_order_push(order, 'out_for_delivery')
        return True
        
    except Exception as e:
        logger.error(f"Failed to send out for delivery email for Order #{order.id}: {str(e)}")
        return False


def send_feedback_notification_email(feedback, feedback_type='app'):
    """
    Send admin notification email for low-rating feedback.
    Only sends for ratings <= 2 stars.

    Args:
        feedback: AppFeedback or CycleFeedback instance
        feedback_type: 'app' or 'cycle'

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Get admin email
        admin_email = settings.ADMIN_EMAIL
        if not admin_email:
            logger.warning(f"No ADMIN_EMAIL configured for feedback notification")
            return False

        # Build subject based on feedback type
        if feedback_type == 'app':
            parent_name = feedback.parent.user.get_full_name() if feedback.parent else "Unknown"
            subject = f"⚠ Low Feedback ({feedback.rating}★) — {parent_name}"
        elif feedback_type == 'cycle':
            child_name = feedback.child.name if feedback.child else "Unknown"
            parent_name = feedback.parent.user.get_full_name() if feedback.parent else "Unknown"
            subject = f"⚠ Low Book Feedback ({feedback.rating}★) — {child_name} ({parent_name})"
        else:
            subject = f"⚠ Low Feedback ({feedback.rating}★)"

        # Render HTML email template
        html_content = render_to_string('emails/feedback_notification.html', {
            'feedback': feedback,
            'feedback_type': feedback_type,
        })

        # Create plain text version
        text_content = strip_tags(html_content)

        # Send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[admin_email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()

        logger.info(f"Feedback notification email sent to admin for {feedback_type} feedback #{feedback.id}")
        return True

    except Exception as e:
        logger.error(f"Failed to send feedback notification email: {str(e)}")
        return False
