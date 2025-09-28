"""
URL additions for ai_helsabrain
"""

from django.urls import path, include

urlpatterns += [
    path('api/ai_helsabrain/', include('ai_helsabrain.urls')),
]
