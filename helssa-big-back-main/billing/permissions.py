"""
مجوزهای دسترسی سیستم مالی
Financial System Permissions
"""

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import View
from django.contrib.auth import get_user_model

User = get_user_model()


class IsAuthenticatedAndActive(permissions.BasePermission):
    """
    مجوز برای کاربران احراز هویت شده و فعال
    """
    
    def has_permission(self, request: Request, view: View) -> bool:
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_active
        )


class IsPatient(permissions.BasePermission):
    """
    مجوز برای بیماران
    """
    
    def has_permission(self, request: Request, view: View) -> bool:
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_active and
            request.user.user_type == 'patient'
        )


class IsDoctor(permissions.BasePermission):
    """
    مجوز برای پزشکان
    """
    
    def has_permission(self, request: Request, view: View) -> bool:
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_active and
            request.user.user_type == 'doctor'
        )


class IsDoctorOrPatient(permissions.BasePermission):
    """
    مجوز برای پزشکان یا بیماران
    """
    
    def has_permission(self, request: Request, view: View) -> bool:
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_active and
            request.user.user_type in ['doctor', 'patient']
        )


class IsAdminOrStaff(permissions.BasePermission):
    """
    مجوز برای ادمین یا کارمندان
    """
    
    def has_permission(self, request: Request, view: View) -> bool:
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_active and
            request.user.user_type in ['admin', 'staff']
        )


class HasWalletAccess(permissions.BasePermission):
    """
    مجوز دسترسی به کیف پول
    """
    
    def has_permission(self, request: Request, view: View) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        
        # بررسی وجود کیف پول
        if not hasattr(request.user, 'wallet'):
            return False
        
        # بررسی فعال بودن کیف پول
        return request.user.wallet.is_active


class HasActiveSubscription(permissions.BasePermission):
    """
    مجوز برای کاربران با اشتراک فعال
    """
    
    def has_permission(self, request: Request, view: View) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        
        from .models import Subscription, SubscriptionStatus
        
        # بررسی وجود اشتراک فعال
        active_subscription = Subscription.objects.filter(
            user=request.user,
            status__in=[SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE]
        ).exists()
        
        return active_subscription


class CanMakePayment(permissions.BasePermission):
    """
    مجوز انجام پرداخت
    """
    
    def has_permission(self, request: Request, view: View) -> bool:
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False
        
        # بررسی تایید هویت برای مبالغ بالا
        amount = request.data.get('amount', 0)
        if amount and float(amount) > 10000000 and not request.user.is_verified:
            return False
        
        return True


class CanAccessFinancialData(permissions.BasePermission):
    """
    مجوز دسترسی به اطلاعات مالی
    """
    
    def has_permission(self, request: Request, view: View) -> bool:
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_active and
            (request.user.user_type in ['doctor', 'patient'] or request.user.is_staff)
        )
    
    def has_object_permission(self, request: Request, view: View, obj) -> bool:
        # کاربر فقط می‌تواند به اطلاعات مالی خودش دسترسی داشته باشد
        # مگر اینکه ادمین باشد
        if request.user.is_staff or request.user.user_type == 'admin':
            return True
        
        # بررسی مالکیت
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'wallet') and hasattr(obj.wallet, 'user'):
            return obj.wallet.user == request.user
        
        return False


class CanManageSubscription(permissions.BasePermission):
    """
    مجوز مدیریت اشتراک
    """
    
    def has_permission(self, request: Request, view: View) -> bool:
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_active
        )
    
    def has_object_permission(self, request: Request, view: View, obj) -> bool:
        # کاربر فقط می‌تواند اشتراک خودش را مدیریت کند
        if request.user.is_staff or request.user.user_type == 'admin':
            return True
        
        return obj.user == request.user


class CanViewCommission(permissions.BasePermission):
    """
    مجوز مشاهده کمیسیون (فقط پزشکان)
    """
    
    def has_permission(self, request: Request, view: View) -> bool:
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_active and
            request.user.user_type == 'doctor'
        )
    
    def has_object_permission(self, request: Request, view: View, obj) -> bool:
        # پزشک فقط می‌تواند کمیسیون خودش را ببیند
        if request.user.is_staff or request.user.user_type == 'admin':
            return True
        
        return obj.doctor == request.user


class IsVerifiedUser(permissions.BasePermission):
    """
    مجوز برای کاربران تایید شده
    """
    
    def has_permission(self, request: Request, view: View) -> bool:
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_active and
            request.user.is_verified
        )


class RateLimitPermission(permissions.BasePermission):
    """
    مجوز محدودیت نرخ درخواست
    """
    
    def has_permission(self, request: Request, view: View) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        
        from django.core.cache import cache
        from django.utils import timezone
        
        # کلید کش بر اساس کاربر و IP
        cache_key = f"rate_limit:{request.user.id}:{self._get_client_ip(request)}"
        
        # دریافت تعداد درخواست‌های اخیر
        current_time = timezone.now()
        requests_count = cache.get(cache_key, 0)
        
        # محدودیت: 100 درخواست در ساعت
        if requests_count >= 100:
            return False
        
        # افزایش شمارنده
        cache.set(cache_key, requests_count + 1, 3600)  # 1 hour
        
        return True
    
    def _get_client_ip(self, request: Request) -> str:
        """دریافت IP کلاینت"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class BillingPermission(permissions.BasePermission):
    """
    مجوز کلی برای عملیات مالی
    ترکیبی از چندین مجوز
    """
    
    def has_permission(self, request: Request, view: View) -> bool:
        # بررسی احراز هویت و فعال بودن
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False
        
        # بررسی نوع کاربر
        if request.user.user_type not in ['patient', 'doctor', 'admin', 'staff']:
            return False
        
        # بررسی کیف پول
        if request.user.user_type in ['patient', 'doctor']:
            if not hasattr(request.user, 'wallet') or not request.user.wallet.is_active:
                return False
        
        return True


# Decorator های کمکی
def require_wallet(view_func):
    """Decorator برای نیاز به کیف پول"""
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'wallet') or not request.user.wallet.is_active:
            from rest_framework.response import Response
            from rest_framework import status
            return Response(
                {'error': 'کیف پول فعال یافت نشد'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return view_func(request, *args, **kwargs)
    return wrapper


def require_subscription(view_func):
    """Decorator برای نیاز به اشتراک فعال"""
    def wrapper(request, *args, **kwargs):
        from .models import Subscription, SubscriptionStatus
        
        active_subscription = Subscription.objects.filter(
            user=request.user,
            status__in=[SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE]
        ).exists()
        
        if not active_subscription:
            from rest_framework.response import Response
            from rest_framework import status
            return Response(
                {'error': 'اشتراک فعال یافت نشد'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return view_func(request, *args, **kwargs)
    return wrapper


def require_verification(view_func):
    """Decorator برای نیاز به تایید هویت"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_verified:
            from rest_framework.response import Response
            from rest_framework import status
            return Response(
                {'error': 'تایید هویت لازم است'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return view_func(request, *args, **kwargs)
    return wrapper