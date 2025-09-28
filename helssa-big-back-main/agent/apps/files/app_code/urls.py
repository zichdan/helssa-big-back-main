"""
الگوی URL های اپلیکیشن فایل‌ها
URLs for Files application
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StoredFileViewSet


app_name = 'files'

router = DefaultRouter()
router.register(r'stored-files', StoredFileViewSet, basename='stored-file')

urlpatterns = [
    path('', include(router.urls)),
]

