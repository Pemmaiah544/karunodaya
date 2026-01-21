# Email Notification Setup Guide

## Overview
This guide explains how to configure and use the SMTP email notification system for Karunodaya order updates.

## Features Implemented
✅ Order confirmation emails (when order is PAID or CONFIRMED)
✅ Order dispatched emails (when order is DISPATCHED)
✅ Out for delivery emails (when order is OUT_FOR_DELIVERY)
✅ Order delivered emails (when order is DELIVERED)
✅ Automatic email sending on status changes in admin panel
✅ Email notifications for bulk actions

## Email Configuration

### 1. Gmail Setup (Recommended for Development)

#### Step 1: Enable 2-Step Verification
1. Go to your Google Account: https://myaccount.google.com/
2. Navigate to Security → 2-Step Verification
3. Enable 2-Step Verification if not already enabled

#### Step 2: Generate App Password
1. Go to: https://myaccount.google.com/apppasswords
2. Select app: "Mail"
3. Select device: "Other (Custom name)" → Enter "Karunodaya"
4. Click "Generate"
5. Copy the 16-character password (remove spaces)

#### Step 3: Update .env File
Create or update `/home/pemmu/projects/Karunodaya/karunodaya/.env`:

```bash
# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=Karunodaya <noreply@karunodaya.com>
ADMIN_EMAIL=admin@karunodaya.com
```

**Important:** Replace:
- `your-email@gmail.com` with your actual Gmail address
- `your-16-char-app-password` with the app password you generated

### 2. Alternative SMTP Providers

#### SendGrid
```bash
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
```

#### AWS SES
```bash
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-aws-smtp-username
EMAIL_HOST_PASSWORD=your-aws-smtp-password
```

#### Mailgun
```bash
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=postmaster@your-domain.mailgun.org
EMAIL_HOST_PASSWORD=your-mailgun-password
```

## Testing Email Configuration

### Method 1: Django Shell
```bash
cd /home/pemmu/projects/Karunodaya/karunodaya
source .venv/bin/activate
python manage.py shell
```

Then run:
```python
from django.core.mail import send_mail

send_mail(
    'Test Email from Karunodaya',
    'This is a test email to verify SMTP configuration.',
    'noreply@karunodaya.com',
    ['your-email@example.com'],
    fail_silently=False,
)
```

If successful, you'll see: `1` (meaning 1 email sent)

### Method 2: Test with Actual Order
1. Go to Django Admin: http://localhost:8000/admin/
2. Navigate to Orders
3. Select an order with a user that has an email address
4. Change status to "PAID" or "CONFIRMED"
5. Save the order
6. Check the admin message for email confirmation
7. Check the recipient's email inbox

## How It Works

### Automatic Email Triggers

#### 1. Order Confirmation Email
**Triggered when:**
- Order status changes from any status to `PAID` or `CONFIRMED`

**Email contains:**
- Order number
- Order type (Subscription/Purchase)
- Order date
- Payment method
- Total amount
- Delivery address

#### 2. Order Dispatched Email
**Triggered when:**
- Order status changes to `DISPATCHED`

**Email contains:**
- Order number
- Dispatch date/time
- Tracking number (if available)
- Courier partner (if available)
- Estimated delivery date (if available)

#### 3. Out for Delivery Email
**Triggered when:**
- Order status changes to `OUT_FOR_DELIVERY`

**Email contains:**
- Order number
- Delivery address
- Alert to be available for delivery

#### 4. Order Delivered Email
**Triggered when:**
- Order status changes to `DELIVERED` or `PAID` (after delivery)

**Email contains:**
- Order number
- Delivery date/time
- Total amount
- Thank you message

### Admin Panel Integration

#### Single Order Update
1. Open any order in admin
2. Change the status field
3. Click "Save"
4. Email is automatically sent
5. Admin message confirms email status

#### Bulk Actions
1. Select multiple orders in the order list
2. Choose action:
   - "📦 Mark as Dispatched"
   - "🚚 Mark as Out for Delivery"
   - "✅ Mark as Delivered"
3. Click "Go"
4. Emails are sent to all affected orders
5. Admin message shows count of emails sent

## Email Templates

Email templates are located in:
```
/home/pemmu/projects/Karunodaya/karunodaya/templates/emails/
├── order_confirmation.html
├── order_dispatched.html
├── order_out_for_delivery.html
└── order_delivered.html
```

### Customizing Email Templates
You can edit these HTML files to customize:
- Colors and branding
- Content and messaging
- Layout and structure

## Troubleshooting

### Issue: Emails not sending
**Solution:**
1. Check `.env` file has correct SMTP credentials
2. Verify EMAIL_HOST_USER has valid email
3. Check Gmail app password is correct (no spaces)
4. Ensure user in database has valid email address
5. Check Django logs for error messages

### Issue: Gmail blocking login
**Solution:**
1. Ensure 2-Step Verification is enabled
2. Use App Password, not regular password
3. Check "Less secure app access" is NOT needed (app passwords bypass this)

### Issue: Emails going to spam
**Solution:**
1. Use a verified domain email (not Gmail for production)
2. Set up SPF, DKIM, and DMARC records
3. Use a professional email service (SendGrid, AWS SES)

### Issue: User has no email address
**Solution:**
- Email will not be sent (logged as warning)
- Ensure users register with email addresses
- Add email field validation in registration

## Production Recommendations

### 1. Use Professional Email Service
- **SendGrid**: Free tier (100 emails/day)
- **AWS SES**: Pay as you go ($0.10 per 1000 emails)
- **Mailgun**: Free tier (5000 emails/month)

### 2. Set Up Email Queue
For high volume, use Celery for async email sending:
```python
# Future enhancement
from celery import shared_task

@shared_task
def send_order_email_async(order_id, email_type):
    # Send email in background
    pass
```

### 3. Monitor Email Delivery
- Track bounce rates
- Monitor spam complaints
- Log all email attempts
- Set up email delivery webhooks

### 4. Email Rate Limiting
- Implement rate limiting to avoid spam flags
- Batch emails for bulk operations
- Add delays between emails if needed

## Files Modified/Created

### Created Files:
1. `/services/email_service.py` - Email sending functions
2. `/templates/emails/order_confirmation.html` - Confirmation email template
3. `/templates/emails/order_dispatched.html` - Dispatch email template
4. `/templates/emails/order_out_for_delivery.html` - Out for delivery email template
5. `/templates/emails/order_delivered.html` - Delivery email template

### Modified Files:
1. `/karunodaya_project/settings.py` - Added email configuration
2. `/apps/orders/admin.py` - Added email triggers

## Next Steps

1. ✅ Configure `.env` with SMTP credentials
2. ✅ Test email sending with Django shell
3. ✅ Test with actual order status changes
4. ✅ Verify emails are received and formatted correctly
5. ⏳ (Optional) Set up professional email service for production
6. ⏳ (Optional) Implement email analytics/tracking
7. ⏳ (Optional) Add email templates for subscription renewals

## Support

For issues or questions:
- Check Django logs: `tail -f /path/to/django.log`
- Check email service logs
- Verify SMTP credentials are correct
- Test with Django shell first
