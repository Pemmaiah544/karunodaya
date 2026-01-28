from django.urls import path
from apps.core.views import (
    books_dashboard, 
    simple_table_example, 
    enhanced_books_dashboard, 
    enhanced_users_dashboard,
    table_config_list,
    table_config_detail
)

app_name = 'core'

urlpatterns = [
    # Legacy table examples
    path('dashboard/', books_dashboard, name='books_dashboard'),
    path('simple-table/', simple_table_example, name='simple_table'),
    
    # Enhanced database-driven tables
    path('enhanced/books/', enhanced_books_dashboard, name='enhanced_books'),
    path('enhanced/users/', enhanced_users_dashboard, name='enhanced_users'),
    
    # Table configuration management
    path('configs/', table_config_list, name='table_config_list'),
    path('configs/<slug:slug>/', table_config_detail, name='table_config_detail'),
]
