from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FHIRResourceViewSet,
    FHIRMappingViewSet,
    FHIRBundleViewSet,
    FHIRExportLogViewSet,
    FHIRTransformView,
    FHIRImportView,
    FHIRSearchView
)

# ایجاد router
router = DefaultRouter()
router.register(r'resources', FHIRResourceViewSet, basename='fhir-resource')
router.register(r'mappings', FHIRMappingViewSet, basename='fhir-mapping')
router.register(r'bundles', FHIRBundleViewSet, basename='fhir-bundle')
router.register(r'logs', FHIRExportLogViewSet, basename='fhir-log')

app_name = 'fhir_adapter'

urlpatterns = [
    # ViewSet URLs
    path('', include(router.urls)),
    
    # Custom API endpoints
    path('transform/', FHIRTransformView.as_view(), name='fhir-transform'),
    path('import/', FHIRImportView.as_view(), name='fhir-import'),
    path('search/', FHIRSearchView.as_view(), name='fhir-search'),
]