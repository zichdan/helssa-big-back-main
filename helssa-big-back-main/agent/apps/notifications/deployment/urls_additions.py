"""
URL additions for notifications
"""

from django.urls import path, include

urlpatterns += [
    path('api/notifications/', include('agent.apps.notifications.app_code.urls')),
]

