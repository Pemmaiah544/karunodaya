from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from django.conf import settings
from . import views
from .forms import PortalAuthenticationForm, UniqueEmailPasswordResetForm

app_name = 'portal'

urlpatterns = [
    # Authentication
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=PortalAuthenticationForm
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    
    # Password Reset - Using custom view for dev tunnel support
    path('password-reset/', 
         views.CustomPasswordResetView.as_view(
             form_class=UniqueEmailPasswordResetForm,
             email_template_name='registration/password_reset_email.txt',
             html_email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt',
             success_url=reverse_lazy('portal:password_reset_done'),
             from_email=settings.DEFAULT_FROM_EMAIL
         ),
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             success_url=reverse_lazy('portal:password_reset_complete')
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
         name='password_reset_complete'),

    # Onboarding
    path('onboarding/', views.OnboardingView.as_view(), name='onboarding'),
    path('onboarding/step2/', views.onboarding_step2, name='onboarding_step2'),
    path('onboarding/step3/', views.onboarding_step3, name='onboarding_step3'),
    path('onboarding/complete/', views.onboarding_complete, name='onboarding_complete'),

    # Main Portal
    path('', views.HomeView.as_view(), name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('curated-box/<int:child_id>/', views.CuratedBoxView.as_view(), name='curated_box'),

    # Marketplace
    path('marketplace/', views.MarketplaceView.as_view(), name='marketplace'),
    path('marketplace/search/', views.marketplace_search, name='marketplace_search'),
    path('book/<int:book_id>/', views.BookDetailView.as_view(), name='book_detail'),

    # Orders
    path('orders/', views.OrdersView.as_view(), name='orders'),
    path('order/<int:order_id>/', views.OrderDetailView.as_view(), name='order_detail'),

    # Profile
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/update-name/', views.update_profile_name, name='update_profile_name'),
    path('profile/child/add/', views.AddChildView.as_view(), name='add_child'),
    path('profile/child/<int:child_id>/edit/', views.EditChildView.as_view(), name='edit_child'),

    # Subscriptions
    path('subscribe/', views.SubscribeView.as_view(), name='subscribe'),
    path('subscribe/<int:child_id>/', views.SubscribeView.as_view(), name='subscribe_child'),

    # Returns
    path('my-books/', views.MyBooksView.as_view(), name='my_books'),
    path('return/<int:cycle_id>/', views.initiate_return, name='initiate_return'),

    # Shopping Cart
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/<int:book_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:book_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:book_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('checkout/', views.checkout, name='checkout'),
    path('support/', views.SupportView.as_view(), name='support'),
]
