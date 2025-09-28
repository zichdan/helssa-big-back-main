"""
هسته API Ingress - دریافت و validation درخواست‌ها
"""
import logging
from typing import Dict, Tuple, Any, Optional
from django.conf import settings
from rest_framework import status
from rest_framework.request import Request


logger = logging.getLogger(__name__)


class APIIngressCore:
    """
    هسته دریافت و پردازش اولیه درخواست‌های API
    
    این کلاس مسئول دریافت، validation و routing اولیه درخواست‌ها است
    """
    
    def __init__(self):
        """مقداردهی اولیه هسته API Ingress"""
        self.logger = logging.getLogger(__name__)
        self.max_request_size = getattr(settings, 'MAX_REQUEST_SIZE', 10 * 1024 * 1024)  # 10MB
        
    def validate_request(self, request: Request) -> Tuple[bool, Dict[str, Any]]:
        """
        اعتبارسنجی اولیه درخواست
        
        Args:
            request: درخواست HTTP ورودی
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (معتبر بودن، جزئیات/خطا)
        """
        try:
            # بررسی اندازه درخواست
            if hasattr(request, 'body') and len(request.body) > self.max_request_size:
                return False, {
                    'error': 'Request too large',
                    'message': 'درخواست بیش از حد مجاز بزرگ است',
                    'max_size': self.max_request_size
                }
            
            # بررسی Content-Type
            content_type = request.content_type
            allowed_types = ['application/json', 'multipart/form-data', 'application/x-www-form-urlencoded']
            
            if content_type and not any(allowed_type in content_type for allowed_type in allowed_types):
                return False, {
                    'error': 'Unsupported content type',
                    'message': 'نوع محتوای درخواست پشتیبانی نمی‌شود',
                    'content_type': content_type
                }
            
            # بررسی Headers ضروری
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            if not user_agent:
                self.logger.warning('Request without User-Agent header')
            
            self.logger.info(
                'Request validated successfully',
                extra={
                    'method': request.method,
                    'path': request.path,
                    'content_type': content_type,
                    'user_agent': user_agent[:100] if user_agent else None
                }
            )
            
            return True, {
                'method': request.method,
                'path': request.path,
                'content_type': content_type,
                'size': len(request.body) if hasattr(request, 'body') else 0
            }
            
        except Exception as e:
            self.logger.error(f"Request validation error: {str(e)}")
            return False, {
                'error': 'Validation failed',
                'message': 'خطا در اعتبارسنجی درخواست',
                'details': str(e)
            }
    
    def extract_metadata(self, request: Request) -> Dict[str, Any]:
        """
        استخراج metadata از درخواست
        
        Args:
            request: درخواست HTTP ورودی
            
        Returns:
            Dict[str, Any]: metadata استخراج شده
        """
        try:
            metadata = {
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'method': request.method,
                'path': request.path,
                'query_params': dict(request.GET),
                'timestamp': self._get_timestamp(),
                'content_length': request.META.get('CONTENT_LENGTH', 0)
            }
            
            # اضافه کردن اطلاعات کاربر در صورت وجود
            if hasattr(request, 'user') and request.user.is_authenticated:
                metadata['user_id'] = str(request.user.id)
                metadata['user_type'] = getattr(request.user, 'user_type', 'unknown')
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Metadata extraction error: {str(e)}")
            return {}
    
    def route_request(self, request: Request, metadata: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        تشخیص نوع درخواست و routing مناسب
        
        Args:
            request: درخواست HTTP ورودی
            metadata: metadata استخراج شده
            
        Returns:
            Tuple[str, Dict[str, Any]]: (نوع processor، تنظیمات routing)
        """
        try:
            path = request.path.lower()
            method = request.method.upper()
            
            # تشخیص نوع محتوا بر اساس path
            if '/text/' in path or '/nlp/' in path:
                return 'text_processor', {
                    'priority': 'normal',
                    'timeout': 30,
                    'retry_count': 2
                }
            elif '/speech/' in path or '/stt/' in path or '/tts/' in path:
                return 'speech_processor', {
                    'priority': 'high',
                    'timeout': 60,
                    'retry_count': 1
                }
            elif '/orchestrate/' in path or '/workflow/' in path:
                return 'orchestrator', {
                    'priority': 'high',
                    'timeout': 120,
                    'retry_count': 3
                }
            else:
                # Default routing
                return 'text_processor', {
                    'priority': 'normal',
                    'timeout': 30,
                    'retry_count': 2
                }
                
        except Exception as e:
            self.logger.error(f"Request routing error: {str(e)}")
            return 'text_processor', {
                'priority': 'low',
                'timeout': 15,
                'retry_count': 1
            }
    
    def _get_client_ip(self, request: Request) -> str:
        """استخراج IP واقعی کلاینت"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or 'unknown'
    
    def _get_timestamp(self) -> str:
        """دریافت timestamp فعلی"""
        from datetime import datetime
        return datetime.now().isoformat()