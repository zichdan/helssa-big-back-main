"""
URL patterns for notifications
"""

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('send/', views.send_notification, name='send'),
]

