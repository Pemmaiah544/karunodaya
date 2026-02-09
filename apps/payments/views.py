from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest
from django.conf import settings
from django.db import transaction as db_transaction
from django.contrib import messages
import razorpay
import hmac
import hashlib
import json

from apps.orders.models import Order, SubscriptionCycle
from apps.payments.models import Transaction
from services.curation import assign_subscription_books
from services.email_service import send_order_confirmation_email


# Initialize Razorpay client
razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


@login_required
def initiate_payment(request, order_id):
    """
    Initiate payment for an order.
    For COD orders: Redirect to COD confirmation page.
    For online orders: Create Razorpay order and Transaction record.
    """
    order = get_object_or_404(Order, id=order_id, parent=request.user.parent_profile)

    # Check if order is already paid
    if order.status in ['PAID', 'DISPATCHED', 'DELIVERED']:
        messages.warning(request, 'This order has already been paid.')
        return redirect('portal:order_detail', order_id=order.id)

    # Handle COD orders
    if order.payment_method == 'COD':
        return redirect('payments:cod_confirmation', order_id=order.id)

    # Handle online payment orders
    try:
        # Create Razorpay order
        razorpay_order = razorpay_client.order.create({
            'amount': int(order.total_amount * 100),  # Amount in paise
            'currency': 'INR',
            'payment_capture': 1,  # Auto capture
            'notes': {
                'order_id': str(order.id),
                'order_type': order.order_type,
                'user_id': str(request.user.id),
            }
        })

        # Create Transaction record
        transaction = Transaction.objects.create(
            order=order,
            razorpay_order_id=razorpay_order['id'],
            amount=order.total_amount,
            status='INITIATED',
            provider_response=razorpay_order
        )

        context = {
            'order': order,
            'transaction': transaction,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'amount': int(order.total_amount * 100),  # Amount in paise
            'currency': 'INR',
            'user_name': request.user.get_full_name() or request.user.username,
            'user_email': request.user.email,
            'user_phone': getattr(request.user.parent_profile, 'phone_number', ''),
        }

        return render(request, 'payments/payment_page.html', context)

    except Exception as e:
        messages.error(request, f'Failed to initiate payment: {str(e)}')
        return redirect('portal:order_detail', order_id=order.id)



@login_required
def payment_callback(request):
    """
    Handle Razorpay payment callback (success/failure).
    Verify signature and update order status.
    """
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request method')

    try:
        # Get payment details from POST data
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')

        if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
            messages.error(request, 'Invalid payment response received.')
            return redirect('portal:orders')

        # Get transaction
        transaction = get_object_or_404(
            Transaction,
            razorpay_order_id=razorpay_order_id
        )

        # Verify signature
        if verify_razorpay_signature(
            razorpay_order_id,
            razorpay_payment_id,
            razorpay_signature
        ):
            # Signature verified - payment is genuine
            with db_transaction.atomic():
                # Update transaction
                transaction.razorpay_payment_id = razorpay_payment_id
                transaction.razorpay_signature = razorpay_signature
                transaction.status = 'SUCCESS'
                transaction.save()

                # Update order
                order = transaction.order
                order.status = 'PAID'
                order.save()

                # If subscription order, assign books
                if order.order_type == 'SUBSCRIPTION':
                    try:
                        subscription_cycle = SubscriptionCycle.objects.get(order=order)
                        success, message, assigned_copies = assign_subscription_books(subscription_cycle)
                        if not success:
                            # Log the issue but don't fail the payment
                            print(f"Book assignment failed: {message}")
                    except SubscriptionCycle.DoesNotExist:
                        print(f"SubscriptionCycle not found for order {order.id}")

            # Send confirmation email
            send_order_confirmation_email(order)

            messages.success(request, 'Payment successful! Your order has been confirmed.')
            return redirect('portal:payment_success', transaction_id=transaction.id)
        else:
            # Signature verification failed
            transaction.status = 'FAILED'
            transaction.provider_response['error'] = 'Signature verification failed'
            transaction.save()

            messages.error(request, 'Payment verification failed. Please contact support.')
            return redirect('portal:payment_failure', transaction_id=transaction.id)

    except Exception as e:
        messages.error(request, f'Payment processing error: {str(e)}')
        return redirect('portal:orders')


@login_required
def cod_confirmation(request, order_id):
    """
    Display COD order confirmation page.
    Marks order as CONFIRMED (not PAID - payment collected on delivery).
    For subscriptions, assign books immediately.
    """
    order = get_object_or_404(Order, id=order_id, parent=request.user.parent_profile)

    # Mark COD order as CONFIRMED (payment will be collected on delivery)
    if order.payment_method == 'COD' and order.status == 'PENDING':
        order.status = 'CONFIRMED'
        order.save()
        
        # Create transaction record for audit trail
        Transaction.objects.create(
            order=order,
            razorpay_order_id=f'COD-{order.id}',
            amount=order.total_amount,
            status='PENDING',  # Payment pending until delivery
            payment_method='COD',
            provider_response={
                'payment_type': 'cash_on_delivery',
                'note': 'Payment to be collected on delivery'
            }
        )
        
        # Send confirmation email
        send_order_confirmation_email(order)

    # Assign books for subscription COD orders
    if order.order_type == 'SUBSCRIPTION':
        try:
            subscription_cycle = SubscriptionCycle.objects.get(order=order)
            # Assign books immediately for COD subscriptions
            success, message, assigned_copies = assign_subscription_books(subscription_cycle)
            if not success:
                messages.warning(request, f'Order confirmed but book assignment issue: {message}')
        except SubscriptionCycle.DoesNotExist:
            messages.warning(request, 'Subscription cycle not found.')

    context = {
        'order': order,
        'is_subscription': order.order_type == 'SUBSCRIPTION',
    }

    # Get order items for purchase orders
    if order.order_type == 'PURCHASE':
        context['order_items'] = order.items.all()

    return render(request, 'payments/cod_confirmation.html', context)



@login_required
def payment_success(request, transaction_id):
    """Display payment success page."""
    transaction = get_object_or_404(
        Transaction,
        id=transaction_id,
        order__parent=request.user.parent_profile
    )

    return render(request, 'payments/payment_success.html', {
        'transaction': transaction,
        'order': transaction.order,
    })


@login_required
def payment_failure(request, transaction_id):
    """Display payment failure page."""
    transaction = get_object_or_404(
        Transaction,
        id=transaction_id,
        order__parent=request.user.parent_profile
    )

    return render(request, 'payments/payment_failure.html', {
        'transaction': transaction,
        'order': transaction.order,
    })


@csrf_exempt
def razorpay_webhook(request):
    """
    Handle Razorpay webhook events.
    This endpoint receives notifications about payment status changes.
    """
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request method')

    try:
        # Verify webhook signature
        webhook_signature = request.headers.get('X-Razorpay-Signature')
        webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET

        if not webhook_signature or not webhook_secret:
            return HttpResponseBadRequest('Invalid webhook signature')

        # Verify the webhook signature
        body = request.body.decode('utf-8')
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        if webhook_signature != expected_signature:
            return HttpResponseBadRequest('Signature verification failed')

        # Parse webhook payload
        payload = json.loads(body)
        event = payload.get('event')
        payment_entity = payload.get('payload', {}).get('payment', {}).get('entity', {})

        # Handle different events
        if event == 'payment.captured':
            handle_payment_captured(payment_entity)
        elif event == 'payment.failed':
            handle_payment_failed(payment_entity)

        return JsonResponse({'status': 'success'})

    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def verify_razorpay_signature(order_id, payment_id, signature):
    """
    Verify Razorpay payment signature to ensure authenticity.
    """
    try:
        # Create signature string
        message = f"{order_id}|{payment_id}"

        # Generate expected signature
        expected_signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Compare signatures
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        print(f"Signature verification error: {str(e)}")
        return False


def handle_payment_captured(payment_entity):
    """
    Handle payment.captured webhook event.
    Update transaction and order status.
    """
    try:
        order_id = payment_entity.get('order_id')
        payment_id = payment_entity.get('id')

        if not order_id:
            return

        transaction = Transaction.objects.filter(
            razorpay_order_id=order_id
        ).first()

        if transaction and transaction.status != 'SUCCESS':
            with db_transaction.atomic():
                transaction.razorpay_payment_id = payment_id
                transaction.status = 'SUCCESS'
                transaction.provider_response = payment_entity
                transaction.save()

                order = transaction.order
                if order.status == 'PENDING':
                    order.status = 'PAID'
                    order.save()

                    # If subscription, assign books
                    if order.order_type == 'SUBSCRIPTION':
                        try:
                            subscription_cycle = SubscriptionCycle.objects.get(order=order)
                            success, message, assigned_copies = assign_subscription_books(subscription_cycle)
                        except SubscriptionCycle.DoesNotExist:
                            pass
    except Exception as e:
        print(f"Error handling payment captured: {str(e)}")


def handle_payment_failed(payment_entity):
    """
    Handle payment.failed webhook event.
    Update transaction status.
    """
    try:
        order_id = payment_entity.get('order_id')

        if not order_id:
            return

        transaction = Transaction.objects.filter(
            razorpay_order_id=order_id
        ).first()

        if transaction and transaction.status != 'SUCCESS':
            transaction.status = 'FAILED'
            transaction.provider_response = payment_entity
            transaction.save()
    except Exception as e:
        print(f"Error handling payment failed: {str(e)}")
