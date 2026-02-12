from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('initiate/<int:order_id>/', views.initiate_payment, name='initiate_payment'),
    path('callback/', views.payment_callback, name='payment_callback'),
    path('success/<int:transaction_id>/', views.payment_success, name='payment_success'),
    path('failure/<int:transaction_id>/', views.payment_failure, name='payment_failure'),
    path('cod-confirmation/<int:order_id>/', views.cod_confirmation, name='cod_confirmation'),
    path('webhook/', views.razorpay_webhook, name='razorpay_webhook'),
]
