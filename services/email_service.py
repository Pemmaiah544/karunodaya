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
        return True
        
    except Exception as e:
        logger.error(f"Failed to send out for delivery email for Order #{order.id}: {str(e)}")
        return False
