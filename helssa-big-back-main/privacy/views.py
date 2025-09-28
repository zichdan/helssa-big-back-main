"""
Views برای ماژول Privacy
"""

import logging
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import (
    DataClassification,
    DataField,
    DataAccessLog,
    ConsentRecord,
    DataRetentionPolicy
)
from .serializers import (
    DataClassificationSerializer,
    DataFieldSerializer,
    DataAccessLogSerializer,
    ConsentRecordSerializer,
    DataRetentionPolicySerializer,
    TextRedactionRequestSerializer,
    TextRedactionResponseSerializer,
    ConsentGrantRequestSerializer,
    ConsentWithdrawRequestSerializer,
    PrivacyAnalysisRequestSerializer,
    PrivacyAnalysisResponseSerializer
)
from .cores.api_ingress import privacy_api_ingress
from .cores.text_processor import privacy_text_processor
from .services.redactor import default_redactor
from .services.consent_manager import default_consent_manager

User = get_user_model()
logger = logging.getLogger(__name__)


class DataClassificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet برای مدیریت طبقه‌بندی داده‌ها
    """
    queryset = DataClassification.objects.all()
    serializer_class = DataClassificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """فیلتر کردن بر اساس دسترسی کاربر"""
        queryset = super().get_queryset()
        
        # فقط ادمین‌ها می‌توانند همه طبقه‌بندی‌ها را ببینند
        if not getattr(self.request.user, 'is_staff', False):
            queryset = queryset.filter(is_active=True)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """لاگ کردن ایجاد طبقه‌بندی جدید"""
        instance = serializer.save()
        
        privacy_api_ingress.log_privacy_access(
            request=self.request,
            action='create_classification',
            resource=f"classification:{instance.id}",
            success=True,
            additional_context={
                'classification_type': instance.classification_type,
                'name': instance.name
            }
        )


class DataFieldViewSet(viewsets.ModelViewSet):
    """
    ViewSet برای مدیریت فیلدهای داده
    """
    queryset = DataField.objects.all()
    serializer_class = DataFieldSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """فیلتر کردن بر اساس دسترسی و پارامترها"""
        queryset = super().get_queryset()
        
        # فیلتر بر اساس اپلیکیشن
        app_name = self.request.query_params.get('app_name')
        if app_name:
            queryset = queryset.filter(app_name=app_name)
        
        # فیلتر بر اساس مدل
        model_name = self.request.query_params.get('model_name')
        if model_name:
            queryset = queryset.filter(model_name=model_name)
        
        # فیلتر بر اساس طبقه‌بندی
        classification_type = self.request.query_params.get('classification_type')
        if classification_type:
            queryset = queryset.filter(classification__classification_type=classification_type)
        
        return queryset.select_related('classification').order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def bulk_update_patterns(self, request):
        """بروزرسانی دسته‌ای الگوهای پنهان‌سازی"""
        try:
            updates = request.data.get('updates', [])
            
            if not updates:
                return Response({
                    'success': False,
                    'message': 'هیچ بروزرسانی ارائه نشده است'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            updated_count = 0
            
            with transaction.atomic():
                for update in updates:
                    field_id = update.get('id')
                    pattern = update.get('redaction_pattern')
                    replacement = update.get('replacement_text')
                    
                    if field_id:
                        try:
                            field = DataField.objects.get(id=field_id)
                            if pattern is not None:
                                field.redaction_pattern = pattern
                            if replacement is not None:
                                field.replacement_text = replacement
                            field.save()
                            updated_count += 1
                        except DataField.DoesNotExist:
                            continue
            
            # پاک کردن کش
            default_redactor.clear_cache()
            
            return Response({
                'success': True,
                'message': f'{updated_count} فیلد بروزرسانی شد',
                'updated_count': updated_count
            })
            
        except Exception as e:
            logger.error(f"خطا در بروزرسانی دسته‌ای: {str(e)}")
            return Response({
                'success': False,
                'message': 'خطا در بروزرسانی'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)