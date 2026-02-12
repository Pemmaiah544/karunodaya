#!/usr/bin/env python
"""
Test script for email notification system.
Run this to verify SMTP configuration is working.

Usage:
    python test_email.py
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'karunodaya_project.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from apps.orders.models import Order


def test_smtp_connection():
    """Test basic SMTP connection."""
    print("=" * 60)
    print("Testing SMTP Email Configuration")
    print("=" * 60)
    print(f"\nEmail Backend: {settings.EMAIL_BACKEND}")
    print(f"SMTP Host: {settings.EMAIL_HOST}")
    print(f"SMTP Port: {settings.EMAIL_PORT}")
    print(f"Use TLS: {settings.EMAIL_USE_TLS}")
    print(f"From Email: {settings.DEFAULT_FROM_EMAIL}")
    print(f"Host User: {settings.EMAIL_HOST_USER}")
    print(f"Password Set: {'Yes' if settings.EMAIL_HOST_PASSWORD else 'No'}")
    
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        print("\n❌ ERROR: Email credentials not configured!")
        print("Please update your .env file with EMAIL_HOST_USER and EMAIL_HOST_PASSWORD")
        return False
    
    print("\n" + "-" * 60)
    print("Sending test email...")
    print("-" * 60)
    
    try:
        result = send_mail(
            subject='Test Email from Karunodaya',
            message='This is a test email to verify SMTP configuration is working correctly.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],  # Send to yourself
            fail_silently=False,
        )
        
        if result == 1:
            print(f"\n✅ SUCCESS! Test email sent to {settings.EMAIL_HOST_USER}")
            print("Check your inbox to confirm receipt.")
            return True
        else:
            print("\n❌ FAILED: Email was not sent")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nCommon issues:")
        print("1. Check your Gmail App Password (16 characters, no spaces)")
        print("2. Ensure 2-Step Verification is enabled on your Google Account")
        print("3. Verify EMAIL_HOST_USER is a valid Gmail address")
        print("4. Check your internet connection")
        return False


def test_order_email():
    """Test order notification email with real order data."""
    print("\n" + "=" * 60)
    print("Testing Order Notification Email")
    print("=" * 60)
    
    # Get the first order with a user that has an email
    orders = Order.objects.filter(parent__user__email__isnull=False).exclude(parent__user__email='')
    
    if not orders.exists():
        print("\n⚠️  WARNING: No orders found with user email addresses")
        print("Create an order with a user that has an email to test order notifications")
        return False
    
    order = orders.first()
    print(f"\nUsing Order #{order.id}")
    print(f"User: {order.parent.user.username}")
    print(f"Email: {order.parent.user.email}")
    print(f"Status: {order.get_status_display()}")
    
    print("\n" + "-" * 60)
    print("Sending order confirmation email...")
    print("-" * 60)
    
    try:
        from services.email_service import send_order_confirmation_email
        
        if send_order_confirmation_email(order):
            print(f"\n✅ SUCCESS! Order confirmation email sent to {order.parent.user.email}")
            print("Check the inbox to verify the email content and formatting.")
            return True
        else:
            print("\n❌ FAILED: Order email was not sent")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all email tests."""
    print("\n🚀 Karunodaya Email Notification Test Suite\n")
    
    # Test 1: SMTP Connection
    smtp_ok = test_smtp_connection()
    
    if not smtp_ok:
        print("\n" + "=" * 60)
        print("⚠️  Fix SMTP configuration before testing order emails")
        print("=" * 60)
        sys.exit(1)
    
    # Test 2: Order Email
    order_ok = test_order_email()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"SMTP Connection: {'✅ PASS' if smtp_ok else '❌ FAIL'}")
    print(f"Order Email: {'✅ PASS' if order_ok else '⚠️  SKIP'}")
    
    if smtp_ok and order_ok:
        print("\n🎉 All tests passed! Email system is working correctly.")
    elif smtp_ok:
        print("\n✅ SMTP is configured correctly.")
        print("⚠️  Create orders with user emails to test order notifications.")
    else:
        print("\n❌ Please fix the issues above and try again.")
    
    print("=" * 60 + "\n")


if __name__ == '__main__':
    main()
