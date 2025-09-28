"""
هسته ورودی API اپ Doctor
Doctor App API Ingress Core
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.contrib.auth import get_user_model
import logging
import time
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)
User = get_user_model()


class DoctorAPIIngressCore:
    """
    هسته مدیریت ورودی API برای اپ Doctor
    مسئول validation، authentication، rate limiting و logging اپ دکتر
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def validate_doctor_permissions(self, user, required_verification=True) -> Tuple[bool, str]:
        """
        بررسی مجوزهای پزشک
        
        Args:
            user: کاربر درخواست‌دهنده
            required_verification: نیاز به تایید پزشک
            
        Returns:
            (is_valid, error_message)
        """
        # بررسی احراز هویت
        if not user.is_authenticated:
            return False, "کاربر احراز هویت نشده است"
        
        # بررسی نوع کاربر (اگر مدل User این قابلیت را دارد)
        try:
            if hasattr(user, 'user_type') and user.user_type != 'doctor':
                return False, "کاربر باید پزشک باشد"
        except:
            pass
        
        # بررسی وجود پروفایل پزشک
        try:
            doctor_profile = user.doctor_profile
            if required_verification and not doctor_profile.is_verified:
                return False, "پروفایل پزشک تایید نشده است"
        except User.doctor_profile.RelatedObjectDoesNotExist:
            return False, "پروفایل پزشک یافت نشد"
        
        return True, ""
    
    def validate_patient_permissions(self, user) -> Tuple[bool, str]:
        """
        بررسی مجوزهای بیمار برای امتیازدهی
        
        Args:
            user: کاربر درخواست‌دهنده
            
        Returns:
            (is_valid, error_message)
        """
        if not user.is_authenticated:
            return False, "کاربر احراز هویت نشده است"
        
        try:
            if hasattr(user, 'user_type') and user.user_type != 'patient':
                return False, "کاربر باید بیمار باشد"
        except:
            pass
        
        return True, ""
    
    def check_doctor_rate_limit(self, user_id: int, action: str, 
                               limit: int = 100, window: int = 60) -> bool:
        """
        بررسی محدودیت تعداد درخواست برای عملیات پزشک
        
        Args:
            user_id: شناسه کاربر
            action: نوع عملیات (create_schedule, update_profile, etc.)
            limit: حداکثر تعداد درخواست
            window: بازه زمانی به ثانیه
            
        Returns:
            True if allowed, False if rate limited
        """
        cache_key = f"doctor_rate_limit:{user_id}:{action}"
        current_count = cache.get(cache_key, 0)
        
        if current_count >= limit:
            self.logger.warning(f"Doctor rate limit exceeded for user {user_id} on {action}")
            return False
        
        cache.set(cache_key, current_count + 1, window)
        return True
    
    def validate_schedule_data(self, data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        اعتبارسنجی داده‌های برنامه کاری
        
        Args:
            data: داده‌های برنامه کاری
            
        Returns:
            (is_valid, validated_data or errors)
        """
        from ..serializers import DoctorScheduleSerializer
        
        serializer = DoctorScheduleSerializer(data=data)
        if not serializer.is_valid():
            self.logger.warning(f"Schedule validation failed: {serializer.errors}")
            return False, serializer.errors
        
        return True, serializer.validated_data
    
    def validate_profile_data(self, data: Dict[str, Any], is_update=False) -> Tuple[bool, Dict[str, Any]]:
        """
        اعتبارسنجی داده‌های پروفایل پزشک
        
        Args:
            data: داده‌های پروفایل
            is_update: آیا ویرایش است یا ایجاد
            
        Returns:
            (is_valid, validated_data or errors)
        """
        from ..serializers import DoctorProfileSerializer, DoctorProfileCreateSerializer
        
        serializer_class = DoctorProfileSerializer if is_update else DoctorProfileCreateSerializer
        serializer = serializer_class(data=data)
        
        if not serializer.is_valid():
            self.logger.warning(f"Profile validation failed: {serializer.errors}")
            return False, serializer.errors
        
        return True, serializer.validated_data
    
    def log_doctor_action(self, request, action: str, target_id: str = None,
                         response_status: int = 200, execution_time: float = None):
        """
        ثبت لاگ عملیات پزشک
        
        Args:
            request: Django request object
            action: نوع عملیات
            target_id: شناسه هدف (اختیاری)
            response_status: HTTP status code
            execution_time: زمان اجرا
        """
        try:
            doctor_profile = request.user.doctor_profile
            doctor_name = doctor_profile.get_full_name()
        except:
            doctor_name = request.user.username
        
        log_data = {
            'action': action,
            'doctor_id': request.user.id,
            'doctor_name': doctor_name,
            'target_id': target_id,
            'ip': self.get_client_ip(request),
            'status': response_status,
            'execution_time': execution_time,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        
        if response_status >= 400:
            self.logger.error(f"Doctor API Error - {action}", extra=log_data)
        else:
            self.logger.info(f"Doctor API Action - {action}", extra=log_data)
    
    def get_client_ip(self, request) -> str:
        """دریافت IP واقعی کاربر"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def build_doctor_error_response(self, error_type: str, 
                                  details: Any = None, 
                                  persian_message: str = None) -> Dict[str, Any]:
        """
        ساخت پاسخ خطای اختصاصی برای اپ Doctor
        
        Args:
            error_type: نوع خطا
            details: جزئیات اضافی
            persian_message: پیام فارسی سفارشی
            
        Returns:
            دیکشنری پاسخ خطا
        """
        error_mapping = {
            'not_doctor': {
                'code': 'NOT_DOCTOR',
                'message': persian_message or 'کاربر باید پزشک باشد'
            },
            'not_verified': {
                'code': 'DOCTOR_NOT_VERIFIED',
                'message': persian_message or 'پروفایل پزشک تایید نشده است'
            },
            'profile_not_found': {
                'code': 'DOCTOR_PROFILE_NOT_FOUND',
                'message': persian_message or 'پروفایل پزشک یافت نشد'
            },
            'schedule_conflict': {
                'code': 'SCHEDULE_CONFLICT',
                'message': persian_message or 'تداخل در برنامه کاری'
            },
            'invalid_time': {
                'code': 'INVALID_TIME',
                'message': persian_message or 'زمان‌بندی نامعتبر'
            },
            'validation': {
                'code': 'VALIDATION_ERROR',
                'message': persian_message or 'داده‌های ورودی معتبر نیستند'
            },
            'rate_limit': {
                'code': 'RATE_LIMIT_EXCEEDED',
                'message': persian_message or 'تعداد درخواست‌ها بیش از حد مجاز'
            },
            'permission_denied': {
                'code': 'PERMISSION_DENIED',
                'message': persian_message or 'دسترسی مجاز نیست'
            },
            'internal': {
                'code': 'INTERNAL_ERROR',
                'message': persian_message or 'خطای داخلی سرور'
            }
        }
        
        error_info = error_mapping.get(error_type, error_mapping['internal'])
        response = {
            'success': False,
            'error': error_info['code'],
            'message': error_info['message']
        }
        
        if details:
            response['details'] = details
            
        return response
    
    def build_success_response(self, data: Any = None, 
                             message: str = "عملیات با موفقیت انجام شد") -> Dict[str, Any]:
        """
        ساخت پاسخ موفق استاندارد
        
        Args:
            data: داده‌های پاسخ
            message: پیام موفقیت
            
        Returns:
            دیکشنری پاسخ موفق
        """
        response = {
            'success': True,
            'message': message
        }
        
        if data is not None:
            response['data'] = data
            
        return response


# دکوراتور برای بررسی مجوز پزشک
def doctor_required(verified_required=True):
    """
    دکوراتور برای بررسی اینکه کاربر پزشک است
    
    Args:
        verified_required: آیا پزشک باید تایید شده باشد
    """
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            ingress = DoctorAPIIngressCore()
            
            is_valid, error_msg = ingress.validate_doctor_permissions(
                request.user, 
                verified_required
            )
            
            if not is_valid:
                return Response(
                    ingress.build_doctor_error_response('not_doctor', message=error_msg),
                    status=status.HTTP_403_FORBIDDEN
                )
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


# دکوراتور برای rate limiting اختصاصی پزشک
def doctor_rate_limit(action: str, limit: int = 100, window: int = 60):
    """
    دکوراتور برای اعمال rate limiting برای عملیات پزشک
    
    Args:
        action: نوع عملیات
        limit: حداکثر تعداد درخواست
        window: بازه زمانی
    """
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            ingress = DoctorAPIIngressCore()
            start_time = time.time()
            
            try:
                # بررسی rate limit
                if not ingress.check_doctor_rate_limit(
                    request.user.id, action, limit, window
                ):
                    return Response(
                        ingress.build_doctor_error_response('rate_limit'),
                        status=status.HTTP_429_TOO_MANY_REQUESTS
                    )
                
                # اجرای تابع اصلی
                response = func(request, *args, **kwargs)
                
                # ثبت لاگ
                execution_time = time.time() - start_time
                ingress.log_doctor_action(
                    request, action, None, 
                    response.status_code, execution_time
                )
                
                return response
                
            except Exception as e:
                execution_time = time.time() - start_time
                ingress.log_doctor_action(
                    request, action, None, 500, execution_time
                )
                logger.exception(f"Error in doctor {action}")
                return Response(
                    ingress.build_doctor_error_response('internal'),
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        return wrapper
    return decorator