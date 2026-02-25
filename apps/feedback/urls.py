from django.urls import path
from apps.feedback import views

app_name = 'feedback'

urlpatterns = [
    path('', views.app_feedback, name='app_feedback'),
    path('cycle/<int:cycle_id>/', views.cycle_feedback, name='cycle_feedback'),
]
