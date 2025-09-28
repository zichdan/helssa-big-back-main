"""
URL additions for exports
"""

from django.urls import path, include

urlpatterns += [
    path('api/exports/', include('exports.urls')),
]

