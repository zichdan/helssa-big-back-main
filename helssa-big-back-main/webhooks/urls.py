"""
URL های اپ webhooks
"""

from django.urls import path
from .views import webhook_handler

app_name = 'webhooks'

urlpatterns = [
    path('receive/', webhook_handler, name='receive'),
]