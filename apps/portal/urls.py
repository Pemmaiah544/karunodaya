from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'portal'

urlpatterns = [
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),

    # Onboarding
    path('onboarding/', views.OnboardingView.as_view(), name='onboarding'),
    path('onboarding/step2/', views.onboarding_step2, name='onboarding_step2'),
    path('onboarding/step3/', views.onboarding_step3, name='onboarding_step3'),
    path('onboarding/complete/', views.onboarding_complete, name='onboarding_complete'),

    # Main Portal
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard_alt'),
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
    path('profile/child/add/', views.AddChildView.as_view(), name='add_child'),
    path('profile/child/<int:child_id>/edit/', views.EditChildView.as_view(), name='edit_child'),
]
