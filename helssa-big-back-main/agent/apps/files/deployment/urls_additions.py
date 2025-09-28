"""
URL additions for files (to be merged by platform tooling)
"""

from django.urls import path, include

urlpatterns += [
    path('api/files/', include('files.app_code.urls')),
]

