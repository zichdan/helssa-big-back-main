"""
URL routing پنل ادمین
AdminPortal URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .views import (
    AdminUserViewSet,
    SystemOperationViewSet,
    SupportTicketViewSet,
    SystemMetricsViewSet,
    AdminAuditLogViewSet,
    AdminSessionViewSet,
    search_content,
    bulk_operations,
    system_monitoring,
    generate_report,
    process_voice,
    analyze_content,
    dashboard_overview,
)

app_name = 'adminportal'

# ایجاد router برای ViewSets
router = DefaultRouter()
router.register(r'admin-users', AdminUserViewSet, basename='admin-users')
router.register(r'system-operations', SystemOperationViewSet, basename='system-operations')
router.register(r'support-tickets', SupportTicketViewSet, basename='support-tickets')
router.register(r'system-metrics', SystemMetricsViewSet, basename='system-metrics')
router.register(r'audit-logs', AdminAuditLogViewSet, basename='audit-logs')
router.register(r'admin-sessions', AdminSessionViewSet, basename='admin-sessions')

# URL patterns
urlpatterns = [
    # Authentication endpoints
    path('auth/', include([
        path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        path('verify/', TokenVerifyView.as_view(), name='token_verify'),
    ])),
    
    # API v1 endpoints
    path('api/v1/', include([
        # ViewSets از router
        path('', include(router.urls)),
        
        # Action endpoints
        path('search/', search_content, name='search_content'),
        path('bulk-operations/', bulk_operations, name='bulk_operations'),
        path('system-monitoring/', system_monitoring, name='system_monitoring'),
        path('generate-report/', generate_report, name='generate_report'),
        path('process-voice/', process_voice, name='process_voice'),
        path('analyze-content/', analyze_content, name='analyze_content'),
        path('dashboard/', dashboard_overview, name='dashboard_overview'),
        
        # Quick actions
        path('quick/', include([
            path('ticket-stats/', 
                 SupportTicketViewSet.as_view({'get': 'dashboard_stats'}),
                 name='quick_ticket_stats'),
            path('admin-stats/',
                 AdminUserViewSet.as_view({'get': 'statistics'}),
                 name='quick_admin_stats'),
        ])),
        
        # Specific resource actions
        path('admin-users/', include([
            path('<uuid:pk>/update-activity/',
                 AdminUserViewSet.as_view({'post': 'update_activity'}),
                 name='admin_user_update_activity'),
        ])),
        
        path('system-operations/', include([
            path('<uuid:pk>/start/',
                 SystemOperationViewSet.as_view({'post': 'start'}),
                 name='system_operation_start'),
            path('<uuid:pk>/complete/',
                 SystemOperationViewSet.as_view({'post': 'complete'}),
                 name='system_operation_complete'),
            path('<uuid:pk>/fail/',
                 SystemOperationViewSet.as_view({'post': 'fail'}),
                 name='system_operation_fail'),
        ])),
        
        path('support-tickets/', include([
            path('<uuid:pk>/assign-to-me/',
                 SupportTicketViewSet.as_view({'post': 'assign_to_me'}),
                 name='support_ticket_assign_to_me'),
            path('<uuid:pk>/resolve/',
                 SupportTicketViewSet.as_view({'post': 'resolve'}),
                 name='support_ticket_resolve'),
        ])),
        
        path('admin-sessions/', include([
            path('<uuid:pk>/end/',
                 AdminSessionViewSet.as_view({'post': 'end_session'}),
                 name='admin_session_end'),
        ])),
    ])),
    
    # Health check
    path('health/', include([
        path('', lambda request: JsonResponse({'status': 'ok', 'service': 'adminportal'}), 
             name='health_check'),
        path('detailed/', lambda request: JsonResponse({
            'status': 'ok',
            'service': 'adminportal',
            'version': '1.0.0',
            'timestamp': timezone.now().isoformat(),
            'components': {
                'database': 'ok',
                'cache': 'ok',
                'cores': 'ok'
            }
        }), name='health_detailed'),
    ])),
    
    # Documentation
    path('docs/', include([
        path('', lambda request: JsonResponse({
            'service': 'AdminPortal API',
            'version': '1.0.0',
            'description': 'Internal support and operator tools for Helssa platform',
            'endpoints': {
                'authentication': '/adminportal/auth/',
                'api': '/adminportal/api/v1/',
                'health': '/adminportal/health/',
                'docs': '/adminportal/docs/'
            }
        }), name='api_info'),
        
        path('endpoints/', lambda request: JsonResponse({
            'admin_users': '/adminportal/api/v1/admin-users/',
            'system_operations': '/adminportal/api/v1/system-operations/',
            'support_tickets': '/adminportal/api/v1/support-tickets/',
            'system_metrics': '/adminportal/api/v1/system-metrics/',
            'audit_logs': '/adminportal/api/v1/audit-logs/',
            'admin_sessions': '/adminportal/api/v1/admin-sessions/',
            'search': '/adminportal/api/v1/search/',
            'bulk_operations': '/adminportal/api/v1/bulk-operations/',
            'monitoring': '/adminportal/api/v1/system-monitoring/',
            'reports': '/adminportal/api/v1/generate-report/',
            'voice_processing': '/adminportal/api/v1/process-voice/',
            'content_analysis': '/adminportal/api/v1/analyze-content/',
            'dashboard': '/adminportal/api/v1/dashboard/'
        }), name='endpoints_list'),
    ])),
]

# Import های مورد نیاز برای lambda functions
from django.http import JsonResponse
from django.utils import timezone