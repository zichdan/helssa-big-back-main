"""
هسته مدیریت ورودی API برای ماژول Privacy
API Ingress Core for Privacy Module
"""

import logging
from typing import Dict, Any, Optional, Tuple
from django.http import HttpRequest
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework import status
from ..services.redactor import default_redactor
from ..services.consent_manager import default_consent_manager

logger = logging.getLogger(__name__)


class PrivacyAPIIngressCore:
    """
    هسته مدیریت ورودی API برای عملیات حریم خصوصی
    """
    
    def __init__(self):
        self.redactor = default_redactor
        self.consent_manager = default_consent_manager
        self.logger = logger
    
    def validate_privacy_request(
        self,
        request: HttpRequest,
        serializer_class: serializers.Serializer,
        required_consent_type: Optional[str] = None,
        data_categories: Optional[list] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        اعتبارسنجی درخواست با در نظر گیری حریم خصوصی
        
        Args:
            request: درخواست HTTP
            serializer_class: کلاس serializer
            required_consent_type: نوع رضایت مورد نیاز
            data_categories: دسته‌بندی‌های داده مورد نیاز
            
        Returns:
            tuple: (آیا معتبر است، داده‌ها یا خطاها)
        """
        try:
            # اعتبارسنجی داده‌های ورودی
            serializer = serializer_class(data=request.data)
            if not serializer.is_valid():
                return False, {
                    'error': 'validation_failed',
                    'details': serializer.errors,
                    'message': 'داده‌های ورودی نامعتبر است'
                }
            
            # بررسی رضایت کاربر (در صورت لزوم)
            if required_consent_type and request.user.is_authenticated:
                has_consent = self.consent_manager.check_consent(
                    user_id=str(request.user.id),
                    consent_type=required_consent_type
                )
                
                if not has_consent:
                    return False, {
                        'error': 'consent_required',
                        'consent_type': required_consent_type,
                        'message': 'برای این عملیات رضایت کاربر مورد نیاز است'
                    }
            
            # بررسی دسته‌بندی‌های داده (در صورت لزوم)
            if data_categories and request.user.is_authenticated:
                validation_result = self.consent_manager.validate_consent_requirements(
                    user_id=str(request.user.id),
                    requested_data_types=data_categories,
                    purpose=f"API request to {request.path}"
                )
                
                if not validation_result.get('is_valid', False):
                    return False, {
                        'error': 'insufficient_consent',
                        'missing_consents': validation_result.get('missing_consents', []),
                        'message': 'رضایت کافی برای دسترسی به این داده‌ها وجود ندارد'
                    }
            
            return True, serializer.validated_data
            
        except Exception as e:
            self.logger.error(
                f"خطا در اعتبارسنجی درخواست: {str(e)}",
                extra={
                    'path': request.path,
                    'method': request.method,
                    'user_id': getattr(request.user, 'id', None)
                }
            )
            return False, {
                'error': 'internal_error',
                'message': 'خطای داخلی در اعتبارسنجی'
            }
    
    def sanitize_response_data(
        self,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        user_role: Optional[str] = None,
        request_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        پاکسازی و پنهان‌سازی داده‌های پاسخ
        
        Args:
            data: داده‌های پاسخ
            user_id: شناسه کاربر
            user_role: نقش کاربر
            request_context: زمینه درخواست
            
        Returns:
            Dict: داده‌های پاکسازی شده
        """
        try:
            # تعیین سطح دسترسی کاربر
            if user_role:
                # بررسی سطح دسترسی برای هر فیلد
                for key, value in data.items():
                    if isinstance(value, dict) and 'classification' in value:
                        classification = value.get('classification')
                        if not self.redactor.validate_redaction_level(classification, user_role):
                            # پنهان‌سازی داده
                            if isinstance(value.get('data'), str):
                                redacted_text, _ = self.redactor.redact_text(
                                    text=value['data'],
                                    user_id=user_id,
                                    context=request_context
                                )
                                value['data'] = redacted_text
            
            # پنهان‌سازی عمومی داده‌ها
            sanitized_data, redaction_info = self.redactor.redact_dict(
                data=data,
                user_id=user_id,
                context=request_context
            )
            
            # اضافه کردن اطلاعات پنهان‌سازی (در صورت نیاز)
            if redaction_info and user_role in ['admin', 'auditor']:
                sanitized_data['_privacy_info'] = {
                    'redacted_fields': len(redaction_info),
                    'redaction_summary': [
                        {
                            'pattern': item['pattern_name'],
                            'classification': item['classification']
                        }
                        for item in redaction_info
                    ]
                }
            
            return sanitized_data
            
        except Exception as e:
            self.logger.error(
                f"خطا در پاکسازی داده‌های پاسخ: {str(e)}",
                extra={'user_id': user_id, 'user_role': user_role}
            )
            return data  # بازگرداندن داده‌های اصلی در صورت خطا
    
    def build_privacy_error_response(
        self,
        error_type: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ) -> Response:
        """
        ساخت پاسخ خطای مرتبط با حریم خصوصی
        
        Args:
            error_type: نوع خطا
            details: جزئیات خطا
            status_code: کد وضعیت HTTP
            
        Returns:
            Response: پاسخ خطا
        """
        error_messages = {
            'consent_required': 'برای این عملیات رضایت کاربر مورد نیاز است',
            'insufficient_consent': 'رضایت کافی برای دسترسی به این داده‌ها وجود ندارد',
            'privacy_violation': 'نقض حریم خصوصی تشخیص داده شد',
            'data_classification_error': 'خطا در طبقه‌بندی داده‌ها',
            'redaction_failed': 'خطا در پنهان‌سازی داده‌ها',
            'validation_failed': 'اعتبارسنجی داده‌ها ناموفق بود',
        }
        
        from django.utils import timezone
        response_data = {
            'success': False,
            'error': error_type,
            'message': error_messages.get(error_type, 'خطای نامشخص'),
            'timestamp': timezone.now().isoformat()
        }
        
        if details:
            response_data.update(details)
        
        return Response(response_data, status=status_code)
    
    def log_privacy_access(
        self,
        request: HttpRequest,
        action: str,
        resource: str,
        success: bool,
        additional_context: Optional[Dict[str, Any]] = None
    ):
        """
        لاگ کردن دسترسی‌های مرتبط با حریم خصوصی
        
        Args:
            request: درخواست HTTP
            action: عملیات انجام شده
            resource: منبع مورد دسترسی
            success: آیا عملیات موفق بود؟
            additional_context: زمینه اضافی
        """
        try:
            context = {
                'path': request.path,
                'method': request.method,
                'user_id': getattr(request.user, 'id', None),
                'ip_address': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'action': action,
                'resource': resource,
                'success': success,
            }
            
            if additional_context:
                context.update(additional_context)
            
            if success:
                self.logger.info(f"دسترسی موفق به منبع حریم خصوصی", extra=context)
            else:
                self.logger.warning(f"دسترسی ناموفق به منبع حریم خصوصی", extra=context)
                
        except Exception as e:
            self.logger.error(f"خطا در لاگ کردن دسترسی: {str(e)}")


# نمونه‌ای از API ingress core برای استفاده در views
privacy_api_ingress = PrivacyAPIIngressCore()