"""
URL patterns for exports
"""

from django.urls import path
from . import views


app_name = 'exports'


urlpatterns = [
    path('main/', views.main_endpoint, name='main'),
]

