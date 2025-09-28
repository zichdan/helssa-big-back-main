"""
Views اضافی برای ماژول Privacy
"""

import logging
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import DataAccessLog, ConsentRecord
from .serializers import (
    DataAccessLogSerializer,
    ConsentRecordSerializer,
    TextRedactionRequestSerializer,
    TextRedactionResponseSerializer,
    ConsentGrantRequestSerializer,
    ConsentWithdrawRequestSerializer,
    PrivacyAnalysisRequestSerializer,
    PrivacyAnalysisResponseSerializer
)
from .cores.api_ingress import privacy_api_ingress
from .cores.text_processor import privacy_text_processor
from .services.consent_manager import default_consent_manager

User = get_user_model()
logger = logging.getLogger(__name__)


class DataAccessLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet فقط خواندنی برای لاگ‌های دسترسی
    """
    queryset = DataAccessLog.objects.all()
    serializer_class = DataAccessLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """فیلتر کردن بر اساس دسترسی کاربر"""
        queryset = super().get_queryset()
        
        # کاربران عادی فقط لاگ‌های خودشان را می‌بینند
        if not getattr(self.request.user, 'is_staff', False):
            queryset = queryset.filter(user=self.request.user)
        
        # فیلتر بر اساس زمان
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)
        
        # فیلتر بر اساس نوع عملیات
        action_type = self.request.query_params.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        
        return queryset.select_related('user', 'data_field').order_by('-timestamp')


class ConsentRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet برای مدیریت رضایت‌ها
    """
    queryset = ConsentRecord.objects.all()
    serializer_class = ConsentRecordSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """فیلتر کردن بر اساس کاربر"""
        queryset = super().get_queryset()
        
        # کاربران عادی فقط رضایت‌های خودشان را می‌بینند
        if not getattr(self.request.user, 'is_staff', False):
            queryset = queryset.filter(user=self.request.user)
        
        return queryset.prefetch_related('data_categories').order_by('-granted_at')
    
    @action(detail=False, methods=['post'])
    def grant_consent(self, request):
        """اعطای رضایت جدید"""
        serializer = ConsentGrantRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return privacy_api_ingress.build_privacy_error_response(
                'validation_failed',
                {'errors': serializer.errors}
            )
        
        try:
            consent = default_consent_manager.grant_consent(
                user_id=str(request.user.id),
                consent_type=serializer.validated_data['consent_type'],
                purpose=serializer.validated_data['purpose'],
                data_categories=serializer.validated_data['data_categories'],
                legal_basis=serializer.validated_data['legal_basis'],
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                expires_in_days=serializer.validated_data.get('expires_in_days'),
                version=serializer.validated_data.get('version', '1.0')
            )
            
            response_serializer = ConsentRecordSerializer(consent)
            
            return Response({
                'success': True,
                'message': 'رضایت با موفقیت ثبت شد',
                'consent': response_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"خطا در اعطای رضایت: {str(e)}")
            return privacy_api_ingress.build_privacy_error_response(
                'consent_grant_failed',
                {'error': str(e)},
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def withdraw_consent(self, request):
        """پس‌گیری رضایت"""
        serializer = ConsentWithdrawRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return privacy_api_ingress.build_privacy_error_response(
                'validation_failed',
                {'errors': serializer.errors}
            )
        
        success = default_consent_manager.withdraw_consent(
            user_id=str(request.user.id),
            consent_type=serializer.validated_data['consent_type'],
            reason=serializer.validated_data['reason'],
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        if success:
            return Response({
                'success': True,
                'message': 'رضایت با موفقیت پس‌گرفته شد'
            })
        else:
            return privacy_api_ingress.build_privacy_error_response(
                'consent_withdraw_failed',
                {'message': 'رضایت فعال برای پس‌گیری یافت نشد'},
                status.HTTP_404_NOT_FOUND
            )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def redact_text(request):
    """
    پنهان‌سازی متن
    
    POST /privacy/redact-text/
    
    Request Body:
        - text: متن برای پنهان‌سازی
        - redaction_level: سطح پنهان‌سازی (none, standard, strict)
        - context: اطلاعات زمینه‌ای
        - log_access: آیا دسترسی لاگ شود؟
        
    Returns:
        200: متن پنهان‌سازی شده
        400: خطای اعتبارسنجی
    """
    try:
        # اعتبارسنجی ورودی
        is_valid, data = privacy_api_ingress.validate_privacy_request(
            request=request,
            serializer_class=TextRedactionRequestSerializer,
            required_consent_type='data_processing'
        )
        
        if not is_valid:
            return privacy_api_ingress.build_privacy_error_response(
                data.get('error', 'validation_failed'),
                data
            )
        
        # پردازش متن
        if data['redaction_level'] == 'strict':
            result = privacy_text_processor.process_medical_text(
                text=data['text'],
                context=data.get('context'),
                redaction_level=data['redaction_level']
            )
        else:
            result = privacy_text_processor.process_general_text(
                text=data['text'],
                user_id=str(request.user.id),
                context=data.get('context')
            )
        
        # لاگ کردن دسترسی (اگر فعال باشد)
        if data.get('log_access', True):
            privacy_api_ingress.log_privacy_access(
                request=request,
                action='text_redaction',
                resource='text_data',
                success=True,
                additional_context={
                    'redaction_level': data['redaction_level'],
                    'text_length': len(data['text']),
                    'redacted_items': len(result.redacted_items)
                }
            )
        
        # پاسخ
        response_serializer = TextRedactionResponseSerializer({
            'original_text': result.original_text,
            'processed_text': result.processed_text,
            'redacted_items': result.redacted_items,
            'privacy_score': result.privacy_score,
            'contains_sensitive_data': result.contains_sensitive_data,
            'processing_metadata': result.processing_metadata
        })
        
        return Response({
            'success': True,
            'data': response_serializer.data
        })
        
    except Exception as e:
        logger.error(f"خطا در پنهان‌سازی متن: {str(e)}")
        return privacy_api_ingress.build_privacy_error_response(
            'redaction_failed',
            {'error': str(e)},
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_privacy_risks(request):
    """
    تحلیل ریسک‌های حریم خصوصی در متن
    
    POST /privacy/analyze-risks/
    
    Request Body:
        - text: متن مورد تحلیل
        - include_suggestions: شامل پیشنهادات بهبود
        
    Returns:
        200: گزارش تحلیل ریسک
        400: خطای اعتبارسنجی
    """
    try:
        # اعتبارسنجی ورودی
        serializer = PrivacyAnalysisRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return privacy_api_ingress.build_privacy_error_response(
                'validation_failed',
                {'errors': serializer.errors}
            )
        
        # تحلیل ریسک
        analysis = privacy_text_processor.analyze_text_privacy_risks(
            text=serializer.validated_data['text'],
            include_suggestions=serializer.validated_data['include_suggestions']
        )
        
        # لاگ کردن دسترسی
        privacy_api_ingress.log_privacy_access(
            request=request,
            action='privacy_analysis',
            resource='text_data',
            success=True,
            additional_context={
                'risk_score': analysis.get('risk_score', 0),
                'risk_level': analysis.get('risk_level', 'unknown'),
                'text_length': len(serializer.validated_data['text'])
            }
        )
        
        # پاسخ
        response_serializer = PrivacyAnalysisResponseSerializer(analysis)
        
        return Response({
            'success': True,
            'analysis': response_serializer.data
        })
        
    except Exception as e:
        logger.error(f"خطا در تحلیل ریسک‌های حریم خصوصی: {str(e)}")
        return privacy_api_ingress.build_privacy_error_response(
            'analysis_failed',
            {'error': str(e)},
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_consents(request):
    """
    دریافت تمام رضایت‌های کاربر
    
    GET /privacy/my-consents/
    
    Returns:
        200: لیست رضایت‌های کاربر
    """
    try:
        consents = default_consent_manager.get_user_consents(str(request.user.id))
        
        return Response({
            'success': True,
            'consents': consents,
            'total': len(consents)
        })
        
    except Exception as e:
        logger.error(f"خطا در دریافت رضایت‌های کاربر: {str(e)}")
        return privacy_api_ingress.build_privacy_error_response(
            'consent_fetch_failed',
            {'error': str(e)},
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_privacy_statistics(request):
    """
    دریافت آمار حریم خصوصی (فقط برای ادمین‌ها)
    
    GET /privacy/statistics/
    
    Returns:
        200: آمار حریم خصوصی
        403: عدم دسترسی
    """
    if not getattr(request.user, 'is_staff', False):
        return Response({
            'success': False,
            'message': 'دسترسی محدود شده'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # آمار رضایت‌ها
        consent_stats = default_consent_manager.get_consent_statistics()
        
        # آمار طبقه‌بندی‌ها
        from django.db.models import Count
        from .models import DataClassification, DataField
        
        classification_stats = DataClassification.objects.values('classification_type').annotate(
            count=Count('id')
        )
        
        # آمار فیلدهای داده
        field_stats = DataField.objects.values('classification__classification_type').annotate(
            count=Count('id')
        )
        
        # آمار لاگ‌های اخیر
        recent_logs = DataAccessLog.objects.filter(
            timestamp__gte=timezone.now() - timezone.timedelta(days=30)
        ).values('action_type').annotate(count=Count('id'))
        
        return Response({
            'success': True,
            'statistics': {
                'consents': consent_stats,
                'classifications': list(classification_stats),
                'data_fields': list(field_stats),
                'recent_access_logs': list(recent_logs),
                'generated_at': timezone.now()
            }
        })
        
    except Exception as e:
        logger.error(f"خطا در تولید آمار: {str(e)}")
        return privacy_api_ingress.build_privacy_error_response(
            'statistics_failed',
            {'error': str(e)},
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )