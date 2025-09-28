"""
URL patterns for ai_guardrails
"""

from django.urls import path
from . import views

app_name = 'ai_guardrails'

urlpatterns = [
    path('evaluate/', views.evaluate, name='evaluate'),
    path('policies/', views.policies, name='policies'),
    path('rules/', views.rules, name='rules'),
]
