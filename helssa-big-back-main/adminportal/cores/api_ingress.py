"""
هسته ورودی و خروجی API پنل ادمین
AdminPortal API Ingress Core
"""

import logging
from typing import Dict, Any, Tuple, Optional
from django.http import HttpRequest
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import json


class APIIngressCore:
    """
    هسته مدیریت ورودی و خروجی API برای پنل ادمین
    مسئول validation، rate limiting، logging و security
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.rate_limit_cache_prefix = 'admin_rate_limit'
        self.security_cache_prefix = 'admin_security'
    
    def validate_admin_request(self, request: HttpRequest, required_permissions: list = None) -> Tuple[bool, Dict]:
        """
        اعتبارسنجی درخواست ادمین
        
        Args:
            request: درخواست HTTP
            required_permissions: لیست دسترسی‌های مورد نیاز
            
        Returns:
            Tuple[bool, Dict]: (موفقیت، جزئیات)
        """
        try:
            # بررسی احراز هویت
            if not request.user.is_authenticated:
                return False, {
                    'error': 'authentication_required',
                    'message': 'احراز هویت الزامی است'
                }
            
            # بررسی وجود پروفایل ادمین
            if not hasattr(request.user, 'admin_profile'):
                return False, {
                    'error': 'admin_access_denied',
                    'message': 'دسترسی ادمین ندارید'
                }
            
            admin_profile = request.user.admin_profile
            
            # بررسی فعال بودن ادمین
            if not admin_profile.is_active:
                return False, {
                    'error': 'admin_inactive',
                    'message': 'حساب ادمین غیرفعال است'
                }
            
            # بررسی دسترسی‌های مورد نیاز
            if required_permissions:
                has_access = self._check_admin_permissions(admin_profile, required_permissions)
                if not has_access:
                    return False, {
                        'error': 'insufficient_permissions',
                        'message': 'دسترسی کافی ندارید'
                    }
            
            # بروزرسانی آخرین فعالیت
            admin_profile.update_last_activity()
            
            self.logger.info(
                f"Admin request validated: {admin_profile.user.username} - "
                f"{request.method} {request.path}"
            )
            
            return True, {
                'admin_user': admin_profile,
                'permissions': admin_profile.permissions
            }
            
        except Exception as e:
            self.logger.error(f"Admin request validation error: {str(e)}")
            return False, {
                'error': 'validation_error',
                'message': 'خطا در اعتبارسنجی درخواست'
            }
    
    def check_rate_limit(self, request: HttpRequest, limit: int = 100, window: int = 3600) -> Tuple[bool, Dict]:
        """
        بررسی محدودیت نرخ درخواست برای ادمین
        
        Args:
            request: درخواست HTTP
            limit: حد مجاز درخواست
            window: پنجره زمانی (ثانیه)
            
        Returns:
            Tuple[bool, Dict]: (مجاز است، اطلاعات)
        """
        try:
            # شناسه کاربر ادمین
            admin_id = request.user.admin_profile.id if hasattr(request.user, 'admin_profile') else 'anonymous'
            cache_key = f"{self.rate_limit_cache_prefix}:{admin_id}"
            
            # دریافت تعداد درخواست‌های فعلی
            current_requests = cache.get(cache_key, 0)
            
            if current_requests >= limit:
                self.logger.warning(
                    f"Rate limit exceeded for admin {admin_id}: {current_requests}/{limit}"
                )
                return False, {
                    'error': 'rate_limit_exceeded',
                    'limit': limit,
                    'current': current_requests,
                    'window': window,
                    'message': f'حد مجاز {limit} درخواست در {window} ثانیه اخیر'
                }
            
            # افزایش شمارنده
            cache.set(cache_key, current_requests + 1, timeout=window)
            
            return True, {
                'limit': limit,
                'current': current_requests + 1,
                'remaining': limit - current_requests - 1
            }
            
        except Exception as e:
            self.logger.error(f"Rate limit check error: {str(e)}")
            # در صورت خطا، اجازه ادامه
            return True, {'warning': 'rate_limit_check_failed'}
    
    def log_admin_action(self, request: HttpRequest, action: str, resource: str, details: Dict = None):
        """
        ثبت عملیات ادمین
        
        Args:
            request: درخواست HTTP
            action: نوع عملیات
            resource: منبع مورد عملیات
            details: جزئیات اضافی
        """
        try:
            from ..models import AdminAuditLog
            
            admin_profile = getattr(request.user, 'admin_profile', None)
            
            audit_data = {
                'admin_user': admin_profile,
                'resource_type': resource,
                'action_performed': action,
                'reason': details.get('reason', '') if details else '',
                'old_values': details.get('old_values', {}) if details else {},
                'new_values': details.get('new_values', {}) if details else {},
                'created_by': request.user
            }
            
            # ثبت در دیتابیس
            AdminAuditLog.objects.create(**audit_data)
            
            # ثبت در لاگ
            self.logger.info(
                f"Admin action logged: {request.user.username} performed {action} on {resource}"
            )
            
        except Exception as e:
            self.logger.error(f"Admin action logging error: {str(e)}")
    
    def check_security_constraints(self, request: HttpRequest) -> Tuple[bool, Dict]:
        """
        بررسی محدودیت‌های امنیتی
        
        Args:
            request: درخواست HTTP
            
        Returns:
            Tuple[bool, Dict]: (مجاز است، جزئیات)
        """
        try:
            # بررسی IP محدود شده
            client_ip = self._get_client_ip(request)
            if self._is_ip_blocked(client_ip):
                return False, {
                    'error': 'ip_blocked',
                    'message': 'IP شما مسدود شده است'
                }
            
            # بررسی زمان مجاز دسترسی (اختیاری)
            if not self._is_access_time_allowed():
                return False, {
                    'error': 'access_time_restricted',
                    'message': 'دسترسی در این ساعت مجاز نیست'
                }
            
            # بررسی تلاش‌های ناموفق اخیر
            failed_attempts = self._get_recent_failed_attempts(client_ip)
            if failed_attempts > 5:
                return False, {
                    'error': 'too_many_failed_attempts',
                    'message': 'تعداد زیادی تلاش ناموفق'
                }
            
            return True, {'ip': client_ip}
            
        except Exception as e:
            self.logger.error(f"Security constraints check error: {str(e)}")
            return True, {'warning': 'security_check_failed'}
    
    def format_api_response(self, success: bool, data: Any = None, error: str = None, 
                          message: str = None, status_code: int = 200) -> Dict:
        """
        فرمت استاندارد پاسخ API
        
        Args:
            success: موفقیت عملیات
            data: داده‌های پاسخ
            error: کد خطا
            message: پیام
            status_code: کد وضعیت HTTP
            
        Returns:
            Dict: پاسخ فرمت شده
        """
        response = {
            'success': success,
            'timestamp': timezone.now().isoformat(),
            'status_code': status_code
        }
        
        if success:
            response['data'] = data
            if message:
                response['message'] = message
        else:
            response['error'] = {
                'code': error or 'unknown_error',
                'message': message or 'خطای نامشخص'
            }
        
        return response
    
    def _check_admin_permissions(self, admin_profile, required_permissions: list) -> bool:
        """بررسی دسترسی‌های ادمین"""
        try:
            # دسترسی‌های کلی بر اساس نقش
            role_permissions = {
                'super_admin': ['*'],  # تمام دسترسی‌ها
                'support_admin': ['view_users', 'manage_tickets', 'view_metrics'],
                'content_admin': ['manage_content', 'moderate_content'],
                'financial_admin': ['view_billing', 'manage_payments'],
                'technical_admin': ['view_system', 'manage_operations'],
            }
            
            admin_role_perms = role_permissions.get(admin_profile.role, [])
            
            # اگر ادمین کل است
            if '*' in admin_role_perms:
                return True
            
            # بررسی دسترسی‌های نقش
            for perm in required_permissions:
                if perm not in admin_role_perms and perm not in admin_profile.permissions:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Permission check error: {str(e)}")
            return False
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """استخراج IP کلاینت"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _is_ip_blocked(self, ip: str) -> bool:
        """بررسی مسدود بودن IP"""
        cache_key = f"{self.security_cache_prefix}:blocked_ip:{ip}"
        return cache.get(cache_key, False)
    
    def _is_access_time_allowed(self) -> bool:
        """بررسی زمان مجاز دسترسی"""
        # فعلاً همیشه true برمی‌گرداند
        # می‌توان محدودیت‌های زمانی اضافه کرد
        return True
    
    def _get_recent_failed_attempts(self, ip: str) -> int:
        """دریافت تعداد تلاش‌های ناموفق اخیر"""
        cache_key = f"{self.security_cache_prefix}:failed_attempts:{ip}"
        return cache.get(cache_key, 0)
    
    def record_failed_attempt(self, request: HttpRequest):
        """ثبت تلاش ناموفق"""
        ip = self._get_client_ip(request)
        cache_key = f"{self.security_cache_prefix}:failed_attempts:{ip}"
        attempts = cache.get(cache_key, 0)
        cache.set(cache_key, attempts + 1, timeout=3600)  # 1 ساعت