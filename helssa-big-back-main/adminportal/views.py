"""
ویوهای پنل ادمین
AdminPortal Views
"""

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
import logging

from .models import (
    AdminUser, SystemOperation, SupportTicket, 
    SystemMetrics, AdminAuditLog, AdminSession
)
from .serializers import (
    AdminUserSerializer, AdminUserCreateUpdateSerializer,
    SystemOperationSerializer, SystemOperationCreateSerializer,
    SupportTicketSerializer, SupportTicketUpdateSerializer,
    SystemMetricsSerializer, AdminAuditLogSerializer,
    AdminSessionSerializer, SearchQuerySerializer,
    BulkOperationSerializer, SystemMonitoringSerializer,
    ReportGenerationSerializer, VoiceProcessingSerializer,
    ContentAnalysisSerializer
)
from .cores import CentralOrchestrator

logger = logging.getLogger(__name__)


class IsAdminUser(permissions.BasePermission):
    """
    دسترسی فقط برای کاربران ادمین
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'admin_profile') and
            request.user.admin_profile.is_active
        )


class AdminUserViewSet(ModelViewSet):
    """
    ViewSet برای مدیریت کاربران ادمین
    """
    queryset = AdminUser.objects.all()
    permission_classes = [IsAdminUser]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AdminUserCreateUpdateSerializer
        return AdminUserSerializer
    
    def get_queryset(self):
        queryset = AdminUser.objects.select_related('user').all()
        
        # فیلتر بر اساس نقش
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        # فیلتر بر اساس وضعیت
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # فیلتر بر اساس بخش
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department__icontains=department)
        
        return queryset.order_by('-last_activity', '-created_at')
    
    @action(detail=True, methods=['post'])
    def update_activity(self, request, pk=None):
        """بروزرسانی آخرین فعالیت"""
        admin_user = self.get_object()
        admin_user.update_last_activity()
        
        return Response({
            'success': True,
            'message': 'آخرین فعالیت بروزرسانی شد',
            'last_activity': admin_user.last_activity
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """آمار کاربران ادمین"""
        total_count = AdminUser.objects.count()
        active_count = AdminUser.objects.filter(is_active=True).count()
        role_stats = AdminUser.objects.values('role').annotate(count=Count('role'))
        
        # آخرین فعالیت‌ها
        recent_activities = AdminUser.objects.filter(
            last_activity__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()
        
        return Response({
            'total_admins': total_count,
            'active_admins': active_count,
            'inactive_admins': total_count - active_count,
            'recent_activities': recent_activities,
            'role_distribution': list(role_stats)
        })


class SystemOperationViewSet(ModelViewSet):
    """
    ViewSet برای مدیریت عملیات سیستمی
    """
    queryset = SystemOperation.objects.all()
    permission_classes = [IsAdminUser]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SystemOperationCreateSerializer
        return SystemOperationSerializer
    
    def get_queryset(self):
        queryset = SystemOperation.objects.select_related('operator').all()
        
        # فیلتر بر اساس وضعیت
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # فیلتر بر اساس نوع عملیات
        operation_type = self.request.query_params.get('operation_type')
        if operation_type:
            queryset = queryset.filter(operation_type=operation_type)
        
        # فیلتر بر اساس اولویت
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        return queryset.order_by('-priority', '-created_at')
    
    def perform_create(self, serializer):
        """ایجاد عملیات جدید"""
        # تخصیص خودکار اپراتور
        if hasattr(self.request.user, 'admin_profile'):
            serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """شروع عملیات"""
        operation = self.get_object()
        
        if operation.status != 'pending':
            return Response({
                'success': False,
                'error': 'operation_not_pending',
                'message': 'عملیات در وضعیت انتظار نیست'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        operator = request.user.admin_profile if hasattr(request.user, 'admin_profile') else None
        operation.start_operation(operator)
        
        return Response({
            'success': True,
            'message': 'عملیات شروع شد',
            'operation': SystemOperationSerializer(operation).data
        })
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """تکمیل عملیات"""
        operation = self.get_object()
        
        if operation.status != 'in_progress':
            return Response({
                'success': False,
                'error': 'operation_not_in_progress',
                'message': 'عملیات در حال اجرا نیست'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result_data = request.data.get('result', {})
        operation.complete_operation(result_data)
        
        return Response({
            'success': True,
            'message': 'عملیات تکمیل شد',
            'operation': SystemOperationSerializer(operation).data
        })
    
    @action(detail=True, methods=['post'])
    def fail(self, request, pk=None):
        """ناموفق بودن عملیات"""
        operation = self.get_object()
        
        error_data = request.data.get('error', 'عملیات ناموفق')
        operation.fail_operation(error_data)
        
        return Response({
            'success': True,
            'message': 'عملیات به عنوان ناموفق ثبت شد',
            'operation': SystemOperationSerializer(operation).data
        })


class SupportTicketViewSet(ModelViewSet):
    """
    ViewSet برای مدیریت تیکت‌های پشتیبانی
    """
    queryset = SupportTicket.objects.all()
    permission_classes = [IsAdminUser]
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return SupportTicketUpdateSerializer
        return SupportTicketSerializer
    
    def get_queryset(self):
        queryset = SupportTicket.objects.select_related(
            'user', 'assigned_to__user'
        ).all()
        
        # فیلتر بر اساس وضعیت
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # فیلتر بر اساس اولویت
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # فیلتر بر اساس دسته‌بندی
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # فیلتر تیکت‌های تخصیص یافته به من
        assigned_to_me = self.request.query_params.get('assigned_to_me')
        if assigned_to_me == 'true' and hasattr(self.request.user, 'admin_profile'):
            queryset = queryset.filter(assigned_to=self.request.user.admin_profile)
        
        return queryset.order_by('-priority', '-created_at')
    
    @action(detail=True, methods=['post'])
    def assign_to_me(self, request, pk=None):
        """تخصیص تیکت به خودم"""
        ticket = self.get_object()
        
        if not hasattr(request.user, 'admin_profile'):
            return Response({
                'success': False,
                'error': 'no_admin_profile',
                'message': 'شما پروفایل ادمین ندارید'
            }, status=status.HTTP_403_FORBIDDEN)
        
        ticket.assign_to_admin(request.user.admin_profile)
        
        return Response({
            'success': True,
            'message': 'تیکت به شما تخصیص یافت',
            'ticket': SupportTicketSerializer(ticket).data
        })
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """حل تیکت"""
        ticket = self.get_object()
        resolution = request.data.get('resolution', '')
        
        if not resolution:
            return Response({
                'success': False,
                'error': 'resolution_required',
                'message': 'متن راه‌حل الزامی است'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        admin_user = request.user.admin_profile if hasattr(request.user, 'admin_profile') else None
        ticket.resolve_ticket(resolution, admin_user)
        
        return Response({
            'success': True,
            'message': 'تیکت حل شد',
            'ticket': SupportTicketSerializer(ticket).data
        })
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """آمار داشبورد تیکت‌ها"""
        total_tickets = SupportTicket.objects.count()
        open_tickets = SupportTicket.objects.filter(status='open').count()
        in_progress_tickets = SupportTicket.objects.filter(status='in_progress').count()
        resolved_tickets = SupportTicket.objects.filter(status='resolved').count()
        
        # تیکت‌های اولویت بالا
        high_priority = SupportTicket.objects.filter(priority__in=['high', 'urgent']).count()
        
        # تیکت‌های تخصیص نیافته
        unassigned = SupportTicket.objects.filter(assigned_to__isnull=True).count()
        
        # تیکت‌های امروز
        today_tickets = SupportTicket.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        
        return Response({
            'total_tickets': total_tickets,
            'open_tickets': open_tickets,
            'in_progress_tickets': in_progress_tickets,
            'resolved_tickets': resolved_tickets,
            'high_priority_tickets': high_priority,
            'unassigned_tickets': unassigned,
            'today_tickets': today_tickets
        })


class SystemMetricsViewSet(ModelViewSet):
    """
    ViewSet برای مدیریت متریک‌های سیستم
    """
    queryset = SystemMetrics.objects.all()
    serializer_class = SystemMetricsSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = SystemMetrics.objects.all()
        
        # فیلتر بر اساس نوع متریک
        metric_type = self.request.query_params.get('metric_type')
        if metric_type:
            queryset = queryset.filter(metric_type=metric_type)
        
        # فیلتر بر اساس نام متریک
        metric_name = self.request.query_params.get('metric_name')
        if metric_name:
            queryset = queryset.filter(metric_name__icontains=metric_name)
        
        # فیلتر زمانی
        time_range = self.request.query_params.get('time_range')
        if time_range:
            now = timezone.now()
            if time_range == '1h':
                queryset = queryset.filter(timestamp__gte=now - timezone.timedelta(hours=1))
            elif time_range == '24h':
                queryset = queryset.filter(timestamp__gte=now - timezone.timedelta(hours=24))
            elif time_range == '7d':
                queryset = queryset.filter(timestamp__gte=now - timezone.timedelta(days=7))
        
        return queryset.order_by('-timestamp')


class AdminAuditLogViewSet(ModelViewSet):
    """
    ViewSet برای مدیریت لاگ‌های حسابرسی
    """
    queryset = AdminAuditLog.objects.all()
    serializer_class = AdminAuditLogSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ['get', 'head', 'options']  # فقط خواندنی
    
    def get_queryset(self):
        queryset = AdminAuditLog.objects.select_related('admin_user__user').all()
        
        # فیلتر بر اساس کاربر ادمین
        admin_user = self.request.query_params.get('admin_user')
        if admin_user:
            queryset = queryset.filter(admin_user_id=admin_user)
        
        # فیلتر بر اساس نوع عملیات
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action_performed__icontains=action)
        
        # فیلتر بر اساس نوع منبع
        resource_type = self.request.query_params.get('resource_type')
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        
        return queryset.order_by('-created_at')


class AdminSessionViewSet(ModelViewSet):
    """
    ViewSet برای مدیریت نشست‌های ادمین
    """
    queryset = AdminSession.objects.all()
    serializer_class = AdminSessionSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ['get', 'post', 'head', 'options']
    
    def get_queryset(self):
        queryset = AdminSession.objects.select_related('admin_user__user').all()
        
        # فیلتر نشست‌های فعال
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # فیلتر بر اساس کاربر ادمین
        admin_user = self.request.query_params.get('admin_user')
        if admin_user:
            queryset = queryset.filter(admin_user_id=admin_user)
        
        return queryset.order_by('-started_at')
    
    @action(detail=True, methods=['post'])
    def end_session(self, request, pk=None):
        """پایان نشست"""
        session = self.get_object()
        
        if not session.is_active:
            return Response({
                'success': False,
                'error': 'session_already_ended',
                'message': 'نشست قبلاً پایان یافته'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        session.end_session()
        
        return Response({
            'success': True,
            'message': 'نشست پایان یافت',
            'session': AdminSessionSerializer(session).data
        })


# API Views اضافی
@api_view(['POST'])
@permission_classes([IsAdminUser])
def search_content(request):
    """جستجوی محتوا"""
    try:
        orchestrator = CentralOrchestrator()
        
        serializer = SearchQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'validation_error',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # اجرای جستجو
        result = orchestrator.handle_admin_request(
            request, 
            'search_users', 
            serializer.validated_data
        )
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"Search content error: {str(e)}")
        return Response({
            'success': False,
            'error': 'search_failed',
            'message': f'خطا در جستجو: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def bulk_operations(request):
    """عملیات دسته‌ای"""
    try:
        orchestrator = CentralOrchestrator()
        
        serializer = BulkOperationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'validation_error',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # تبدیل به فرمت مورد نیاز
        items = [{'id': item_id} for item_id in serializer.validated_data['item_ids']]
        
        result = orchestrator.process_bulk_operation(
            serializer.validated_data['operation_type'],
            items,
            request.user.admin_profile if hasattr(request.user, 'admin_profile') else None,
            serializer.validated_data.get('options', {})
        )
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"Bulk operations error: {str(e)}")
        return Response({
            'success': False,
            'error': 'bulk_operation_failed',
            'message': f'خطا در عملیات دسته‌ای: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def system_monitoring(request):
    """مانیتورینگ سیستم"""
    try:
        orchestrator = CentralOrchestrator()
        
        serializer = SystemMonitoringSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'validation_error',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = orchestrator.coordinate_system_monitoring(
            serializer.validated_data['scope']
        )
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"System monitoring error: {str(e)}")
        return Response({
            'success': False,
            'error': 'monitoring_failed',
            'message': f'خطا در مانیتورینگ: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def generate_report(request):
    """تولید گزارش"""
    try:
        orchestrator = CentralOrchestrator()
        
        serializer = ReportGenerationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'validation_error',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = orchestrator.handle_admin_request(
            request,
            'generate_report',
            serializer.validated_data
        )
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"Report generation error: {str(e)}")
        return Response({
            'success': False,
            'error': 'report_generation_failed',
            'message': f'خطا در تولید گزارش: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def process_voice(request):
    """پردازش صوت"""
    try:
        orchestrator = CentralOrchestrator()
        
        serializer = VoiceProcessingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'validation_error',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # تبدیل base64 به bytes
        import base64
        audio_data = base64.b64decode(serializer.validated_data['audio_data'])
        
        payload = {
            'audio_data': audio_data,
            'type': serializer.validated_data['processing_type'],
            'context': serializer.validated_data.get('context')
        }
        
        result = orchestrator.handle_admin_request(
            request,
            'process_voice',
            payload
        )
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"Voice processing error: {str(e)}")
        return Response({
            'success': False,
            'error': 'voice_processing_failed',
            'message': f'خطا در پردازش صوت: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def analyze_content(request):
    """تحلیل محتوا"""
    try:
        orchestrator = CentralOrchestrator()
        
        serializer = ContentAnalysisSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'validation_error',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = orchestrator.handle_admin_request(
            request,
            'analyze_content',
            serializer.validated_data
        )
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"Content analysis error: {str(e)}")
        return Response({
            'success': False,
            'error': 'content_analysis_failed',
            'message': f'خطا در تحلیل محتوا: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def dashboard_overview(request):
    """نمای کلی داشبورد"""
    try:
        # آمار کلی
        total_admin_users = AdminUser.objects.count()
        active_sessions = AdminSession.objects.filter(is_active=True).count()
        pending_operations = SystemOperation.objects.filter(status='pending').count()
        open_tickets = SupportTicket.objects.filter(status='open').count()
        
        # فعالیت‌های اخیر
        recent_operations = SystemOperation.objects.order_by('-created_at')[:5]
        recent_tickets = SupportTicket.objects.order_by('-created_at')[:5]
        
        return Response({
            'success': True,
            'overview': {
                'total_admin_users': total_admin_users,
                'active_sessions': active_sessions,
                'pending_operations': pending_operations,
                'open_tickets': open_tickets
            },
            'recent_activities': {
                'operations': SystemOperationSerializer(recent_operations, many=True).data,
                'tickets': SupportTicketSerializer(recent_tickets, many=True).data
            }
        })
        
    except Exception as e:
        logger.error(f"Dashboard overview error: {str(e)}")
        return Response({
            'success': False,
            'error': 'dashboard_error',
            'message': f'خطا در دریافت اطلاعات داشبورد: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)