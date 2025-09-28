"""
URL patterns برای اپلیکیشن Checklist
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ChecklistCatalogViewSet,
    ChecklistTemplateViewSet,
    ChecklistEvalViewSet,
    ChecklistAlertViewSet
)

# ایجاد router
router = DefaultRouter()

# ثبت ViewSetها
router.register(r'catalogs', ChecklistCatalogViewSet, basename='checklist-catalog')
router.register(r'templates', ChecklistTemplateViewSet, basename='checklist-template')
router.register(r'evaluations', ChecklistEvalViewSet, basename='checklist-evaluation')
router.register(r'alerts', ChecklistAlertViewSet, basename='checklist-alert')

app_name = 'checklist'

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
]