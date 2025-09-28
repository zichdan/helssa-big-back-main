"""
سرویس پایه برای سیستم مالی
Base Service for Financial System
"""

import logging
from typing import Tuple, Dict, Any, Optional
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.cache import cache

User = get_user_model()


class BaseService:
    """
    کلاس پایه برای تمام سرویس‌های مالی
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    def success_response(self, data: Any = None, message: str = None) -> Tuple[bool, Dict[str, Any]]:
        """
        پاسخ موفقیت
        
        Args:
            data: داده‌های پاسخ
            message: پیام موفقیت
            
        Returns:
            Tuple[bool, Dict]: (True, داده‌های پاسخ)
        """
        response = {'success': True}
        
        if data is not None:
            response['data'] = data
            
        if message:
            response['message'] = message
            
        return True, response
    
    def error_response(
        self, 
        error_code: str, 
        message: str, 
        details: Any = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        پاسخ خطا
        
        Args:
            error_code: کد خطا
            message: پیام خطا
            details: جزئیات خطا
            
        Returns:
            Tuple[bool, Dict]: (False, اطلاعات خطا)
        """
        response = {
            'success': False,
            'error': error_code,
            'message': message
        }
        
        if details is not None:
            response['details'] = details
            
        return False, response
    
    def validate_user(self, user: User) -> Tuple[bool, Dict[str, Any]]:
        """
        اعتبارسنجی کاربر
        
        Args:
            user: کاربر
            
        Returns:
            Tuple[bool, Dict]: نتیجه اعتبارسنجی
        """
        if not user:
            return self.error_response('user_not_found', 'کاربر یافت نشد')
            
        if not user.is_active:
            return self.error_response('user_inactive', 'حساب کاربری غیرفعال است')
            
        return self.success_response()
    
    def validate_wallet(self, user: User) -> Tuple[bool, Dict[str, Any]]:
        """
        اعتبارسنجی کیف پول کاربر
        
        Args:
            user: کاربر
            
        Returns:
            Tuple[bool, Dict]: نتیجه اعتبارسنجی
        """
        if not hasattr(user, 'wallet'):
            return self.error_response('wallet_not_found', 'کیف پول یافت نشد')
            
        wallet = user.wallet
        
        if not wallet.is_active:
            return self.error_response('wallet_inactive', 'کیف پول غیرفعال است')
            
        return self.success_response({'wallet': wallet})
    
    def log_operation(
        self, 
        operation: str, 
        user: User, 
        data: Dict[str, Any],
        success: bool = True,
        error: str = None
    ):
        """
        ثبت لاگ عملیات
        
        Args:
            operation: نام عملیات
            user: کاربر
            data: داده‌های عملیات
            success: موفقیت عملیات
            error: پیام خطا در صورت وجود
        """
        try:
            log_data = {
                'operation': operation,
                'user_id': str(user.id) if user else None,
                'user_type': user.user_type if user else None,
                'success': success,
                'data': data
            }
            
            if error:
                log_data['error'] = error
                self.logger.error(f"Operation failed: {operation}", extra=log_data)
            else:
                self.logger.info(f"Operation success: {operation}", extra=log_data)
                
        except Exception as e:
            self.logger.error(f"خطا در ثبت لاگ: {str(e)}")
    
    def get_cache_key(self, prefix: str, *args) -> str:
        """
        تولید کلید کش
        
        Args:
            prefix: پیشوند
            args: آرگومان‌های اضافی
            
        Returns:
            str: کلید کش
        """
        key_parts = [prefix] + [str(arg) for arg in args]
        return ':'.join(key_parts)
    
    def cache_get(self, key: str, default=None):
        """
        دریافت از کش
        
        Args:
            key: کلید
            default: مقدار پیش‌فرض
            
        Returns:
            مقدار کش شده یا default
        """
        try:
            return cache.get(key, default)
        except Exception as e:
            self.logger.warning(f"خطا در دریافت از کش: {str(e)}")
            return default
    
    def cache_set(self, key: str, value, timeout: int = 3600):
        """
        ذخیره در کش
        
        Args:
            key: کلید
            value: مقدار
            timeout: مدت زمان انقضا (ثانیه)
        """
        try:
            cache.set(key, value, timeout)
        except Exception as e:
            self.logger.warning(f"خطا در ذخیره در کش: {str(e)}")
    
    def cache_delete(self, key: str):
        """
        حذف از کش
        
        Args:
            key: کلید
        """
        try:
            cache.delete(key)
        except Exception as e:
            self.logger.warning(f"خطا در حذف از کش: {str(e)}")
    
    def atomic_operation(self, func, *args, **kwargs):
        """
        اجرای عملیات در تراکنش
        
        Args:
            func: تابع برای اجرا
            args: آرگومان‌های تابع
            kwargs: کلیدواژه‌های تابع
            
        Returns:
            نتیجه تابع
        """
        try:
            with transaction.atomic():
                return func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"خطا در عملیات atomic: {str(e)}")
            raise
    
    def validate_amount(self, amount, min_amount=1000, max_amount=500000000) -> Tuple[bool, Dict[str, Any]]:
        """
        اعتبارسنجی مبلغ
        
        Args:
            amount: مبلغ
            min_amount: حداقل مبلغ (پیش‌فرض: 1000 ریال)
            max_amount: حداکثر مبلغ (پیش‌فرض: 500 میلیون ریال)
            
        Returns:
            Tuple[bool, Dict]: نتیجه اعتبارسنجی
        """
        try:
            from decimal import Decimal
            amount = Decimal(str(amount))
            
            if amount <= 0:
                return self.error_response(
                    'invalid_amount', 
                    'مبلغ باید بیشتر از صفر باشد'
                )
            
            if amount < min_amount:
                return self.error_response(
                    'amount_too_low',
                    f'حداقل مبلغ {min_amount:,} ریال است'
                )
            
            if amount > max_amount:
                return self.error_response(
                    'amount_too_high',
                    f'حداکثر مبلغ {max_amount:,} ریال است'
                )
            
            return self.success_response({'validated_amount': amount})
            
        except (ValueError, TypeError):
            return self.error_response('invalid_amount_format', 'فرمت مبلغ نامعتبر است')
    
    def check_rate_limit(
        self, 
        user: User, 
        operation: str, 
        limit: int = 10, 
        window: int = 3600
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        بررسی محدودیت نرخ عملیات
        
        Args:
            user: کاربر
            operation: نوع عملیات
            limit: حد مجاز (پیش‌فرض: 10)
            window: پنجره زمانی (پیش‌فرض: 3600 ثانیه)
            
        Returns:
            Tuple[bool, Dict]: نتیجه بررسی
        """
        cache_key = self.get_cache_key('rate_limit', operation, str(user.id))
        current_count = self.cache_get(cache_key, 0)
        
        if current_count >= limit:
            return self.error_response(
                'rate_limit_exceeded',
                f'از محدودیت {operation} تجاوز کرده‌اید. لطفاً بعداً تلاش کنید'
            )
        
        # افزایش شمارنده
        self.cache_set(cache_key, current_count + 1, window)
        
        return self.success_response({
            'rate_limit_ok': True,
            'remaining': limit - current_count - 1
        })
    
    def generate_reference_number(self, prefix: str = 'REF') -> str:
        """
        تولید شماره مرجع یکتا
        
        Args:
            prefix: پیشوند (پیش‌فرض: REF)
            
        Returns:
            str: شماره مرجع
        """
        import random
        import string
        from datetime import datetime
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_part = ''.join(random.choices(string.digits, k=6))
        
        return f"{prefix}{timestamp}{random_part}"
    
    def sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        پاک‌سازی داده‌های حساس
        
        Args:
            data: داده‌های ورودی
            
        Returns:
            Dict: داده‌های پاک‌سازی شده
        """
        sensitive_fields = ['password', 'token', 'card_number', 'cvv', 'api_key']
        sanitized = data.copy()
        
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = '***'
                
        return sanitized