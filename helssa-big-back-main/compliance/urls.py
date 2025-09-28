from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SecurityLayerViewSet,
    SecurityLogViewSet,
    MFAViewSet,
    RoleViewSet,
    TemporaryAccessViewSet,
    AuditLogViewSet,
    HIPAAComplianceViewSet,
    SecurityIncidentViewSet,
    MedicalFileViewSet,
    SecurityDashboardView
)

app_name = 'compliance'

# ایجاد router
router = DefaultRouter()
router.register(r'security-layers', SecurityLayerViewSet, basename='security-layer')
router.register(r'security-logs', SecurityLogViewSet, basename='security-log')
router.register(r'mfa', MFAViewSet, basename='mfa')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'temporary-access', TemporaryAccessViewSet, basename='temporary-access')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')
router.register(r'hipaa-compliance', HIPAAComplianceViewSet, basename='hipaa-compliance')
router.register(r'security-incidents', SecurityIncidentViewSet, basename='security-incident')
router.register(r'medical-files', MedicalFileViewSet, basename='medical-file')

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Dashboard
    path('api/dashboard/', SecurityDashboardView.as_view(), name='security-dashboard'),
]