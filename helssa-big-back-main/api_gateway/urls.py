"""
URL routing برای API Gateway
"""
from django.urls import path
from . import views

app_name = 'api_gateway'

# URL patterns ساده برای تست
urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),
    path('test/', views.test_endpoint, name='test_endpoint'),
]