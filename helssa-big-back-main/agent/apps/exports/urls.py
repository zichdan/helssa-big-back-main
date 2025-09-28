"""
Exports URLs shim
"""

from django.urls import path, include

urlpatterns = [
    path('', include('exports.app_code.urls')),
]

