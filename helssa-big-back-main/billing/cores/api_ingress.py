"""
هسته ورودی API سیستم مالی
Financial System API Ingress Core
"""

import logging
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

User = get_user_model()


class BillingAPIIngressCore:
    """
    هسته ورودی API برای سیستم مالی
    مسئول اعتبارسنجی، امنیت و مدیریت درخواست‌های API
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    def validate_payment_request(
        self, 
        user: User, 
        amount: Decimal, 
        request_data: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        اعتبارسنجی درخواست پرداخت
        
        Args:
            user: کاربر درخواست‌دهنده
            amount: مبلغ پرداخت
            request_data: داده‌های درخواست
            
        Returns:
            Tuple[bool, Dict]: (موفقیت، نتیجه یا خطا)
        """
        try:
            # بررسی فعال بودن کاربر
            if not user.is_active:
                return False, {
                    'error': 'user_inactive',
                    'message': 'حساب کاربری غیرفعال است'
                }
            
            # بررسی مبلغ
            if amount <= 0:
                return False, {
                    'error': 'invalid_amount',
                    'message': 'مبلغ باید بیشتر از صفر باشد'
                }
                
            # بررسی حداقل مبلغ
            if amount < 1000:  # 1000 ریال
                return False, {
                    'error': 'amount_too_low',
                    'message': 'حداقل مبلغ پرداخت 1000 ریال است'
                }
                
            # بررسی حداکثر مبلغ
            if amount > 500000000:  # 500 میلیون ریال
                return False, {
                    'error': 'amount_too_high',
                    'message': 'حداکثر مبلغ پرداخت 500 میلیون ریال است'
                }
            
            # بررسی تایید هویت برای مبالغ بالا
            if amount > 10000000 and not user.is_verified:  # 10 میلیون ریال
                return False, {
                    'error': 'verification_required',
                    'message': 'برای پرداخت مبالغ بالای 10 میلیون ریال، تایید هویت الزامی است'
                }
                
            # بررسی فیلدهای ضروری
            required_fields = ['description']
            for field in required_fields:
                if field not in request_data:
                    return False, {
                        'error': 'missing_field',
                        'message': f'فیلد {field} الزامی است'
                    }
            
            return True, {'validated': True}
            
        except Exception as e:
            self.logger.error(f"خطا در اعتبارسنجی پرداخت: {str(e)}")
            return False, {
                'error': 'validation_error',
                'message': 'خطا در اعتبارسنجی درخواست'
            }
    
    def validate_wallet_operation(
        self, 
        user: User, 
        operation: str, 
        amount: Decimal
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        اعتبارسنجی عملیات کیف پول
        
        Args:
            user: کاربر
            operation: نوع عملیات (deposit, withdraw, transfer)
            amount: مبلغ
            
        Returns:
            Tuple[bool, Dict]: (موفقیت، نتیجه یا خطا)
        """
        try:
            # بررسی کیف پول کاربر
            if not hasattr(user, 'wallet'):
                return False, {
                    'error': 'wallet_not_found',
                    'message': 'کیف پول یافت نشد'
                }
                
            wallet = user.wallet
            
            # بررسی فعال بودن کیف پول
            if not wallet.is_active:
                return False, {
                    'error': 'wallet_inactive',
                    'message': 'کیف پول غیرفعال است'
                }
            
            # بررسی‌های خاص برای برداشت
            if operation == 'withdraw':
                if not wallet.can_withdraw(amount):
                    return False, {
                        'error': 'insufficient_balance',
                        'message': f'موجودی کافی نیست. موجودی فعلی: {wallet.available_balance:,} ریال'
                    }
                    
                # بررسی محدودیت‌های برداشت
                if amount > wallet.daily_withdrawal_limit:
                    return False, {
                        'error': 'daily_limit_exceeded',
                        'message': f'از محدودیت برداشت روزانه ({wallet.daily_withdrawal_limit:,} ریال) تجاوز می‌کند'
                    }
            
            return True, {'validated': True}
            
        except Exception as e:
            self.logger.error(f"خطا در اعتبارسنجی عملیات کیف پول: {str(e)}")
            return False, {
                'error': 'validation_error',
                'message': 'خطا در اعتبارسنجی عملیات'
            }
    
    def validate_subscription_request(
        self, 
        user: User, 
        plan_id: str, 
        billing_cycle: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        اعتبارسنجی درخواست اشتراک
        
        Args:
            user: کاربر
            plan_id: شناسه پلن
            billing_cycle: دوره صورت‌حساب
            
        Returns:
            Tuple[bool, Dict]: (موفقیت، نتیجه یا خطا)
        """
        try:
            from ..models import SubscriptionPlan, Subscription
            
            # بررسی وجود پلن
            try:
                plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
            except SubscriptionPlan.DoesNotExist:
                return False, {
                    'error': 'plan_not_found',
                    'message': 'پلن یافت نشد'
                }
            
            # بررسی مناسب بودن پلن برای کاربر
            if not plan.is_suitable_for_user(user.user_type):
                return False, {
                    'error': 'plan_not_suitable',
                    'message': 'این پلن برای نوع کاربری شما مناسب نیست'
                }
            
            # بررسی دوره صورت‌حساب
            if billing_cycle not in ['monthly', 'yearly']:
                return False, {
                    'error': 'invalid_billing_cycle',
                    'message': 'دوره صورت‌حساب نامعتبر است'
                }
            
            # بررسی اشتراک فعال
            active_subscription = Subscription.objects.filter(
                user=user,
                status__in=['trial', 'active']
            ).first()
            
            if active_subscription:
                return False, {
                    'error': 'active_subscription_exists',
                    'message': 'شما در حال حاضر اشتراک فعال دارید'
                }
            
            return True, {'plan': plan, 'validated': True}
            
        except Exception as e:
            self.logger.error(f"خطا در اعتبارسنجی اشتراک: {str(e)}")
            return False, {
                'error': 'validation_error',
                'message': 'خطا در اعتبارسنجی درخواست اشتراک'
            }
    
    def check_rate_limit(
        self, 
        user: User, 
        action: str, 
        ip_address: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        بررسی محدودیت نرخ درخواست
        
        Args:
            user: کاربر
            action: نوع عمل (payment, withdrawal, etc.)
            ip_address: آدرس IP
            
        Returns:
            Tuple[bool, Dict]: (مجاز، اطلاعات)
        """
        try:
            from django.core.cache import cache
            
            # تعریف محدودیت‌ها
            limits = {
                'payment': {'count': 10, 'window': 3600},  # 10 پرداخت در ساعت
                'withdrawal': {'count': 5, 'window': 3600},  # 5 برداشت در ساعت
                'subscription': {'count': 3, 'window': 86400},  # 3 اشتراک در روز
            }
            
            if action not in limits:
                return True, {'allowed': True}
            
            limit_config = limits[action]
            
            # کلیدهای کش
            user_key = f"rate_limit:{action}:user:{user.id}"
            ip_key = f"rate_limit:{action}:ip:{ip_address}"
            
            # بررسی محدودیت کاربر
            user_count = cache.get(user_key, 0)
            if user_count >= limit_config['count']:
                return False, {
                    'error': 'rate_limit_exceeded',
                    'message': f'از محدودیت {action} تجاوز کرده‌اید. لطفاً بعداً تلاش کنید'
                }
            
            # بررسی محدودیت IP
            ip_count = cache.get(ip_key, 0)
            if ip_count >= limit_config['count'] * 2:  # محدودیت IP دو برابر کاربر
                return False, {
                    'error': 'ip_rate_limit_exceeded',
                    'message': 'از این IP درخواست‌های زیادی ارسال شده. لطفاً بعداً تلاش کنید'
                }
            
            # افزایش شمارنده‌ها
            cache.set(user_key, user_count + 1, limit_config['window'])
            cache.set(ip_key, ip_count + 1, limit_config['window'])
            
            return True, {'allowed': True}
            
        except Exception as e:
            self.logger.error(f"خطا در بررسی rate limit: {str(e)}")
            # در صورت خطا، اجازه ادامه
            return True, {'allowed': True}
    
    def format_api_response(
        self, 
        success: bool, 
        data: Any = None, 
        error: str = None, 
        message: str = None,
        status_code: int = None
    ) -> Response:
        """
        فرمت‌بندی پاسخ API
        
        Args:
            success: موفقیت عملیات
            data: داده‌های پاسخ
            error: کد خطا
            message: پیام
            status_code: کد وضعیت HTTP
            
        Returns:
            Response: پاسخ فرمت شده
        """
        response_data = {
            'success': success,
            'timestamp': timezone.now().isoformat(),
        }
        
        if success:
            response_data['data'] = data
            if message:
                response_data['message'] = message
            return Response(response_data, status=status_code or status.HTTP_200_OK)
        else:
            response_data['error'] = error or 'unknown_error'
            response_data['message'] = message or 'خطای ناشناخته'
            return Response(response_data, status=status_code or status.HTTP_400_BAD_REQUEST)
    
    def log_api_request(
        self, 
        user: User, 
        action: str, 
        request_data: Dict[str, Any], 
        response_data: Dict[str, Any],
        ip_address: str = None
    ):
        """
        ثبت لاگ درخواست API
        
        Args:
            user: کاربر
            action: نوع عمل
            request_data: داده‌های درخواست
            response_data: داده‌های پاسخ
            ip_address: آدرس IP
        """
        try:
            log_data = {
                'user_id': str(user.id),
                'action': action,
                'ip_address': ip_address,
                'success': response_data.get('success', False),
                'timestamp': timezone.now().isoformat(),
            }
            
            # حذف اطلاعات حساس از لاگ
            safe_request_data = request_data.copy()
            sensitive_fields = ['password', 'token', 'card_number', 'cvv']
            for field in sensitive_fields:
                if field in safe_request_data:
                    safe_request_data[field] = '***'
            
            log_data['request'] = safe_request_data
            
            # ثبت خطا در صورت وجود
            if not response_data.get('success'):
                log_data['error'] = response_data.get('error')
                self.logger.warning(f"API Error: {action}", extra=log_data)
            else:
                self.logger.info(f"API Success: {action}", extra=log_data)
                
        except Exception as e:
            self.logger.error(f"خطا در ثبت لاگ API: {str(e)}")
    
    def get_client_ip(self, request) -> str:
        """
        دریافت آدرس IP کلاینت
        
        Args:
            request: درخواست HTTP
            
        Returns:
            str: آدرس IP
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip