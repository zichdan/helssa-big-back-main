# urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FileUploadViewSet

router = DefaultRouter()
router.register(r'files', FileUploadViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
