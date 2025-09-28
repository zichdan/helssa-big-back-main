from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.contrib.auth import get_user_model
from typing import Dict, List
import pyotp
from datetime import datetime, timedelta

from .models import (
    SecurityLayer, SecurityLog, MFAConfig, Role, TemporaryAccess,
    AuditLog, HIPAAComplianceReport, SecurityIncident, MedicalFile
)
from .serializers import (
    SecurityLayerSerializer, SecurityLogSerializer, MFAEnableSerializer,
    MFAVerifySerializer, RoleSerializer, TemporaryAccessSerializer,
    AuditLogSerializer, HIPAAComplianceReportSerializer,
    SecurityIncidentSerializer, SecurityIncidentUpdateSerializer,
    MedicalFileSerializer, SecurityDashboardSerializer, AuditReportSerializer
)
from .services import (
    SecurityLayerManager, MFAService, RBACService, HIPAACompliance,
    AuditSystem, IncidentResponseSystem, SecureFileStorage
)
from .permissions import IsAdminOrReadOnly, HasMFAEnabled, CanAccessPatientData

User = get_user_model()


class SecurityLayerViewSet(viewsets.ModelViewSet):
    """
    مدیریت لایه‌های امنیتی
    """
    queryset = SecurityLayer.objects.all()
    serializer_class = SecurityLayerSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    
    def get_queryset(self):
        """فیلتر بر اساس نوع لایه و وضعیت"""
        queryset = super().get_queryset()
        
        layer_type = self.request.query_params.get('layer_type')
        if layer_type:
            queryset = queryset.filter(layer_type=layer_type)
            
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset.order_by('priority')
    
    @action(detail=True, methods=['post'])
    def test_layer(self, request, pk=None):
        """تست عملکرد یک لایه امنیتی"""
        layer = self.get_object()
        
        # شبیه‌سازی درخواست تست
        test_request = {
            'ip': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'path': '/test',
            'method': 'GET'
        }
        
        # تست لایه
        layer_manager = SecurityLayerManager()
        result = layer_manager.test_single_layer(layer, test_request)
        
        return Response({
            'layer': layer.name,
            'test_passed': result['passed'],
            'details': result['details'],
            'recommendations': result.get('recommendations', [])
        })


class SecurityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    مشاهده لاگ‌های امنیتی
    """
    queryset = SecurityLog.objects.all()
    serializer_class = SecurityLogSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def get_queryset(self):
        """فیلتر پیشرفته لاگ‌ها"""
        queryset = super().get_queryset()
        
        # فیلتر بر اساس نوع رویداد
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
            
        # فیلتر بر اساس کاربر
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            
        # فیلتر بر اساس IP
        ip_address = self.request.query_params.get('ip_address')
        if ip_address:
            queryset = queryset.filter(ip_address=ip_address)
            
        # فیلتر بر اساس ریسک
        min_risk = self.request.query_params.get('min_risk_score')
        if min_risk:
            queryset = queryset.filter(risk_score__gte=int(min_risk))
            
        # فیلتر بر اساس تاریخ
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """آمار لاگ‌های امنیتی"""
        # بازه زمانی پیش‌فرض: 7 روز گذشته
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        logs = self.get_queryset().filter(created_at__gte=start_date)
        
        stats = {
            'total_events': logs.count(),
            'events_by_type': dict(logs.values_list('event_type').annotate(count=Count('id'))),
            'average_risk_score': logs.aggregate(avg_risk=Avg('risk_score'))['avg_risk'] or 0,
            'unique_ips': logs.values('ip_address').distinct().count(),
            'unique_users': logs.exclude(user__isnull=True).values('user').distinct().count(),
            'high_risk_events': logs.filter(risk_score__gte=70).count(),
            'timeline': self._generate_timeline(logs, days)
        }
        
        return Response(stats)
    
    def _generate_timeline(self, logs, days):
        """تولید timeline رویدادها"""
        timeline = []
        for i in range(days):
            date = timezone.now().date() - timedelta(days=i)
            day_logs = logs.filter(created_at__date=date)
            timeline.append({
                'date': date.isoformat(),
                'total': day_logs.count(),
                'high_risk': day_logs.filter(risk_score__gte=70).count()
            })
        return timeline[::-1]  # معکوس کردن برای نمایش از قدیم به جدید


class MFAViewSet(viewsets.ViewSet):
    """
    مدیریت احراز هویت چندعامله
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def enable(self, request):
        """فعال‌سازی MFA"""
        serializer = MFAEnableSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        
        return Response({
            'message': 'کد QR را اسکن کنید و سپس با توکن تایید کنید',
            'provisioning_uri': result['provisioning_uri'],
            'backup_codes': result['backup_codes']
        })
    
    @action(detail=False, methods=['post'])
    def verify(self, request):
        """تایید توکن MFA"""
        serializer = MFAVerifySerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        mfa_config = serializer.save()
        
        return Response({
            'message': 'MFA با موفقیت فعال شد',
            'is_active': mfa_config.is_active
        })
    
    @action(detail=False, methods=['post'])
    def disable(self, request):
        """غیرفعال‌سازی MFA"""
        # نیاز به تایید با رمز عبور یا توکن
        token = request.data.get('token')
        if not token:
            return Response(
                {'error': 'توکن MFA برای غیرفعال‌سازی الزامی است'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            mfa_config = request.user.mfa_config
            totp = pyotp.TOTP(mfa_config.secret)
            
            if not totp.verify(token, valid_window=1):
                return Response(
                    {'error': 'توکن نامعتبر'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            mfa_config.delete()
            
            return Response({'message': 'MFA غیرفعال شد'})
            
        except MFAConfig.DoesNotExist:
            return Response(
                {'error': 'MFA فعال نیست'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """وضعیت MFA کاربر"""
        has_mfa = hasattr(request.user, 'mfa_config')
        
        response_data = {
            'mfa_enabled': has_mfa,
            'mfa_active': has_mfa and request.user.mfa_config.is_active if has_mfa else False
        }
        
        if has_mfa:
            response_data['last_used'] = request.user.mfa_config.last_used
            
        return Response(response_data)


class RoleViewSet(viewsets.ModelViewSet):
    """
    مدیریت نقش‌ها
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    @action(detail=True, methods=['post'])
    def assign_to_user(self, request, pk=None):
        """اختصاص نقش به کاربر"""
        role = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id الزامی است'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            user = User.objects.get(id=user_id)
            # فرض بر وجود رابطه many-to-many
            user.roles.add(role)
            
            # ثبت در audit log
            AuditLog.objects.create(
                event_type='role_assigned',
                user_id=request.user.id,
                resource=f'user:{user_id}',
                action='assign_role',
                result='success',
                metadata={
                    'role': role.name,
                    'assigned_to': str(user_id),
                    'assigned_by': str(request.user.id)
                }
            )
            
            return Response({'message': f'نقش {role.get_name_display()} به کاربر اختصاص یافت'})
            
        except User.DoesNotExist:
            return Response(
                {'error': 'کاربر یافت نشد'},
                status=status.HTTP_404_NOT_FOUND
            )


class TemporaryAccessViewSet(viewsets.ModelViewSet):
    """
    مدیریت دسترسی‌های موقت
    """
    queryset = TemporaryAccess.objects.all()
    serializer_class = TemporaryAccessSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """فیلتر بر اساس نقش کاربر"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # ادمین: همه دسترسی‌ها
        if user.is_superuser:
            return queryset
            
        # پزشک: دسترسی‌های خودش
        if hasattr(user, 'roles') and user.roles.filter(name='doctor').exists():
            return queryset.filter(doctor=user)
            
        # بیمار: دسترسی‌های مربوط به خودش
        return queryset.filter(patient_id=user.id)
    
    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """لغو دسترسی موقت"""
        access = self.get_object()
        
        if access.revoked_at:
            return Response(
                {'error': 'این دسترسی قبلاً لغو شده است'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        access.revoked_at = timezone.now()
        access.is_active = False
        access.save()
        
        # ثبت در audit log
        AuditLog.objects.create(
            event_type='access_revoked',
            user_id=request.user.id,
            resource=f'temporary_access:{access.id}',
            action='revoke_access',
            result='success',
            metadata={
                'doctor_id': str(access.doctor.id),
                'patient_id': str(access.patient_id),
                'revoked_by': str(request.user.id)
            }
        )
        
        return Response({'message': 'دسترسی با موفقیت لغو شد'})


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    مشاهده لاگ‌های ممیزی
    """
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def get_queryset(self):
        """فیلترهای پیشرفته"""
        queryset = super().get_queryset()
        
        # فیلترهای مختلف
        filters = {
            'event_type': 'event_type',
            'user_id': 'user_id',
            'resource': 'resource__icontains',
            'action': 'action',
            'result': 'result'
        }
        
        for param, field in filters.items():
            value = self.request.query_params.get(param)
            if value:
                queryset = queryset.filter(**{field: value})
                
        # فیلتر تاریخ
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)
            
        return queryset
    
    @action(detail=False, methods=['post'])
    def generate_report(self, request):
        """تولید گزارش ممیزی"""
        serializer = AuditReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # استخراج پارامترها
        start_date = serializer.validated_data.get('start_date', timezone.now() - timedelta(days=30))
        end_date = serializer.validated_data.get('end_date', timezone.now())
        
        # تولید گزارش
        audit_system = AuditSystem()
        report = audit_system.generate_audit_report(start_date, end_date)
        
        return Response(report)


class HIPAAComplianceViewSet(viewsets.ModelViewSet):
    """
    مدیریت گزارش‌های HIPAA
    """
    queryset = HIPAAComplianceReport.objects.all()
    serializer_class = HIPAAComplianceReportSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    @action(detail=False, methods=['post'])
    def run_audit(self, request):
        """اجرای ممیزی HIPAA"""
        hipaa_compliance = HIPAACompliance()
        audit_result = hipaa_compliance.audit_compliance()
        
        # ذخیره گزارش
        report = HIPAAComplianceReport.objects.create(
            report_date=timezone.now().date(),
            compliant=audit_result['compliant'],
            score=audit_result['score'],
            findings=audit_result['findings'],
            recommendations=audit_result['recommendations'],
            administrative_score=audit_result.get('administrative_score', 0),
            physical_score=audit_result.get('physical_score', 0),
            technical_score=audit_result.get('technical_score', 0),
            generated_by=request.user
        )
        
        serializer = self.get_serializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """آخرین گزارش HIPAA"""
        latest_report = self.get_queryset().first()
        if not latest_report:
            return Response(
                {'error': 'گزارشی یافت نشد'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        serializer = self.get_serializer(latest_report)
        return Response(serializer.data)


class SecurityIncidentViewSet(viewsets.ModelViewSet):
    """
    مدیریت حوادث امنیتی
    """
    queryset = SecurityIncident.objects.all()
    serializer_class = SecurityIncidentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """فیلتر بر اساس وضعیت و شدت"""
        queryset = super().get_queryset()
        
        # فیلتر وضعیت
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        # فیلتر شدت
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
            
        # فقط حوادث فعال
        active_only = self.request.query_params.get('active_only')
        if active_only and active_only.lower() == 'true':
            queryset = queryset.exclude(status__in=['resolved', 'closed'])
            
        return queryset
    
    def get_serializer_class(self):
        """انتخاب سریالایزر بر اساس action"""
        if self.action in ['update', 'partial_update']:
            return SecurityIncidentUpdateSerializer
        return SecurityIncidentSerializer
    
    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """پاسخ به حادثه امنیتی"""
        incident = self.get_object()
        
        # بررسی وضعیت
        if incident.status in ['resolved', 'closed']:
            return Response(
                {'error': 'این حادثه قبلاً حل شده است'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # اجرای پاسخ خودکار
        incident_response = IncidentResponseSystem()
        response_result = incident_response.handle_security_incident(
            incident.incident_type,
            incident.severity,
            incident.details
        )
        
        # به‌روزرسانی وضعیت
        incident.status = 'investigating'
        incident.assigned_to = request.user
        incident.response_plan = response_result.get('response_plan', {})
        incident.save()
        
        return Response({
            'message': 'پاسخ به حادثه آغاز شد',
            'actions_taken': response_result.get('immediate_actions', []),
            'next_steps': response_result.get('next_steps', [])
        })


class MedicalFileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    مدیریت فایل‌های پزشکی رمزنگاری شده
    """
    queryset = MedicalFile.objects.all()
    serializer_class = MedicalFileSerializer
    permission_classes = [permissions.IsAuthenticated, CanAccessPatientData]
    
    def get_queryset(self):
        """فیلتر بر اساس دسترسی کاربر"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # ادمین: همه فایل‌ها
        if user.is_superuser:
            return queryset
            
        # بیمار: فایل‌های خودش
        patient_id = self.request.query_params.get('patient_id', user.id)
        if str(user.id) == str(patient_id):
            return queryset.filter(patient_id=patient_id)
            
        # پزشک: بررسی دسترسی
        rbac_service = RBACService()
        if rbac_service.check_permission(user.id, 'VIEW_PATIENT_RECORDS', {'patient_id': patient_id}):
            return queryset.filter(patient_id=patient_id)
            
        return queryset.none()
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """دانلود فایل رمزگشایی شده"""
        medical_file = self.get_object()
        
        # ثبت دسترسی
        medical_file.last_accessed = timezone.now()
        medical_file.access_count += 1
        medical_file.save()
        
        # ثبت در audit log
        AuditLog.objects.create(
            event_type='file_accessed',
            user_id=request.user.id,
            resource=f'medical_file:{medical_file.file_id}',
            action='download',
            result='success',
            metadata={
                'patient_id': str(medical_file.patient_id),
                'file_type': medical_file.file_type
            }
        )
        
        # بازیابی و رمزگشایی فایل
        secure_storage = SecureFileStorage()
        file_data = secure_storage.retrieve_and_decrypt(medical_file)
        
        return Response({
            'message': 'فایل آماده دانلود است',
            'download_url': file_data.get('download_url'),
            'expires_in': 300  # 5 دقیقه
        })


class SecurityDashboardView(APIView):
    """
    داشبورد امنیت
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def get(self, request):
        """نمایش داشبورد امنیت"""
        # بازه زمانی
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        # جمع‌آوری داده‌ها
        dashboard_data = {
            'period': {
                'start': start_date.isoformat(),
                'end': timezone.now().isoformat()
            },
            'security_score': self._calculate_security_score(),
            'active_incidents': SecurityIncident.objects.exclude(
                status__in=['resolved', 'closed']
            ).count(),
            'failed_auth_attempts': SecurityLog.objects.filter(
                event_type='authentication_failed',
                created_at__gte=start_date
            ).count(),
            'suspicious_activities': SecurityLog.objects.filter(
                risk_score__gte=70,
                created_at__gte=start_date
            ).count(),
            'compliance_status': self._get_compliance_status(),
            'recent_incidents': SecurityIncidentSerializer(
                SecurityIncident.objects.all()[:5],
                many=True
            ).data,
            'top_threats': self._get_top_threats(start_date),
            'recommendations': self._generate_recommendations()
        }
        
        serializer = SecurityDashboardSerializer(data=dashboard_data)
        serializer.is_valid(raise_exception=True)
        
        return Response(serializer.data)
    
    def _calculate_security_score(self):
        """محاسبه امتیاز امنیتی کلی"""
        # فرمول ساده برای نمونه
        latest_hipaa = HIPAAComplianceReport.objects.first()
        base_score = latest_hipaa.score if latest_hipaa else 70
        
        # کاهش امتیاز بر اساس حوادث فعال
        active_incidents = SecurityIncident.objects.exclude(
            status__in=['resolved', 'closed']
        ).count()
        
        score = base_score - (active_incidents * 5)
        return max(0, min(100, score))
    
    def _get_compliance_status(self):
        """وضعیت compliance"""
        latest_hipaa = HIPAAComplianceReport.objects.first()
        
        if not latest_hipaa:
            return {
                'hipaa_compliant': False,
                'last_audit': None,
                'score': 0
            }
            
        return {
            'hipaa_compliant': latest_hipaa.compliant,
            'last_audit': latest_hipaa.report_date.isoformat(),
            'score': latest_hipaa.score
        }
    
    def _get_top_threats(self, start_date):
        """شناسایی تهدیدات برتر"""
        threats = SecurityLog.objects.filter(
            created_at__gte=start_date,
            risk_score__gte=50
        ).values('event_type').annotate(
            count=Count('id'),
            avg_risk=Avg('risk_score')
        ).order_by('-count')[:5]
        
        return list(threats)
    
    def _generate_recommendations(self):
        """تولید پیشنهادات امنیتی"""
        recommendations = []
        
        # بررسی MFA
        users_without_mfa = User.objects.filter(
            mfa_config__isnull=True
        ).count()
        if users_without_mfa > 0:
            recommendations.append({
                'priority': 'high',
                'title': 'فعال‌سازی MFA',
                'description': f'{users_without_mfa} کاربر بدون MFA وجود دارد'
            })
            
        # بررسی حوادث حل نشده
        old_incidents = SecurityIncident.objects.filter(
            status__in=['detected', 'investigating'],
            detected_at__lte=timezone.now() - timedelta(days=3)
        ).count()
        if old_incidents > 0:
            recommendations.append({
                'priority': 'medium',
                'title': 'بررسی حوادث قدیمی',
                'description': f'{old_incidents} حادثه بیش از 3 روز در انتظار بررسی است'
            })
            
        return recommendations