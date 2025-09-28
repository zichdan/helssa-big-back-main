"""
سیستم دسترسی‌ها و permissions پنل ادمین
AdminPortal Permissions System
"""

from rest_framework import permissions
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class AdminPermissions:
    """
    کلاس مدیریت دسترسی‌های ادمین
    """
    
    # دسترسی‌های اصلی سیستم
    CORE_PERMISSIONS = {
        # مدیریت کاربران
        'manage_users': 'مدیریت کاربران',
        'view_users': 'مشاهده کاربران',
        'create_users': 'ایجاد کاربران',
        'update_users': 'ویرایش کاربران',
        'delete_users': 'حذف کاربران',
        
        # مدیریت ادمین‌ها
        'manage_admins': 'مدیریت ادمین‌ها',
        'view_admins': 'مشاهده ادمین‌ها',
        'create_admins': 'ایجاد ادمین‌ها',
        'update_admins': 'ویرایش ادمین‌ها',
        'delete_admins': 'حذف ادمین‌ها',
        
        # مدیریت تیکت‌ها
        'manage_tickets': 'مدیریت تیکت‌ها',
        'view_tickets': 'مشاهده تیکت‌ها',
        'assign_tickets': 'تخصیص تیکت‌ها',
        'resolve_tickets': 'حل تیکت‌ها',
        'escalate_tickets': 'ارجاع تیکت‌ها',
        
        # مدیریت عملیات سیستمی
        'manage_operations': 'مدیریت عملیات سیستمی',
        'view_operations': 'مشاهده عملیات',
        'start_operations': 'شروع عملیات',
        'stop_operations': 'توقف عملیات',
        'monitor_operations': 'نظارت بر عملیات',
        
        # گزارش‌گیری
        'view_reports': 'مشاهده گزارش‌ها',
        'generate_reports': 'تولید گزارش‌ها',
        'export_reports': 'صادرات گزارش‌ها',
        'schedule_reports': 'زمان‌بندی گزارش‌ها',
        
        # مدیریت سیستم
        'system_admin': 'مدیریت سیستم',
        'view_system_metrics': 'مشاهده متریک‌های سیستم',
        'manage_system_settings': 'مدیریت تنظیمات سیستم',
        'access_audit_logs': 'دسترسی به لاگ‌های حسابرسی',
        
        # عملیات دسته‌ای
        'bulk_operations': 'عملیات دسته‌ای',
        'bulk_user_operations': 'عملیات دسته‌ای کاربران',
        'bulk_ticket_operations': 'عملیات دسته‌ای تیکت‌ها',
        
        # پردازش محتوا
        'content_analysis': 'تحلیل محتوا',
        'voice_processing': 'پردازش صوت',
        'text_processing': 'پردازش متن',
        
        # امنیت
        'security_admin': 'مدیریت امنیت',
        'view_security_logs': 'مشاهده لاگ‌های امنیتی',
        'manage_access_control': 'مدیریت کنترل دسترسی',
        'view_sessions': 'مشاهده نشست‌ها',
        'terminate_sessions': 'پایان نشست‌ها',
        
        # پشتیبان‌گیری و بازیابی
        'backup_data': 'پشتیبان‌گیری داده‌ها',
        'restore_data': 'بازیابی داده‌ها',
        'export_data': 'صادرات داده‌ها',
        'import_data': 'وارد کردن داده‌ها',
    }
    
    # نقش‌های پیش‌فرض و دسترسی‌هایشان
    ROLE_PERMISSIONS = {
        'super_admin': ['*'],  # تمام دسترسی‌ها
        
        'support_admin': [
            'view_users', 'manage_tickets', 'view_tickets', 'assign_tickets',
            'resolve_tickets', 'view_reports', 'generate_reports',
            'content_analysis', 'view_operations'
        ],
        
        'content_admin': [
            'view_users', 'view_tickets', 'content_analysis', 'text_processing',
            'voice_processing', 'view_reports', 'generate_reports'
        ],
        
        'financial_admin': [
            'view_users', 'view_reports', 'generate_reports', 'export_reports',
            'view_operations', 'bulk_operations'
        ],
        
        'technical_admin': [
            'view_users', 'manage_operations', 'view_operations', 'start_operations',
            'stop_operations', 'monitor_operations', 'system_admin',
            'view_system_metrics', 'access_audit_logs', 'view_sessions',
            'backup_data', 'restore_data'
        ],
        
        'security_admin': [
            'view_users', 'security_admin', 'view_security_logs',
            'manage_access_control', 'view_sessions', 'terminate_sessions',
            'access_audit_logs', 'view_system_metrics'
        ]
    }
    
    @classmethod
    def get_user_permissions(cls, admin_user):
        """
        دریافت تمام دسترسی‌های یک کاربر ادمین
        
        Args:
            admin_user: instance از AdminUser
            
        Returns:
            set: مجموعه دسترسی‌های کاربر
        """
        if not admin_user or not admin_user.is_active:
            return set()
        
        # دسترسی‌های بر اساس نقش
        role_permissions = set(cls.ROLE_PERMISSIONS.get(admin_user.role, []))
        
        # اگر super_admin است، تمام دسترسی‌ها
        if '*' in role_permissions:
            return set(cls.CORE_PERMISSIONS.keys())
        
        # دسترسی‌های اضافی شخصی
        custom_permissions = set(admin_user.permissions or [])
        
        # ترکیب دسترسی‌ها
        all_permissions = role_permissions.union(custom_permissions)
        
        # فیلتر دسترسی‌های معتبر
        valid_permissions = all_permissions.intersection(set(cls.CORE_PERMISSIONS.keys()))
        
        return valid_permissions
    
    @classmethod
    def has_permission(cls, admin_user, permission_name):
        """
        بررسی داشتن دسترسی خاص
        
        Args:
            admin_user: instance از AdminUser
            permission_name: نام دسترسی
            
        Returns:
            bool: True اگر دسترسی دارد
        """
        user_permissions = cls.get_user_permissions(admin_user)
        return permission_name in user_permissions
    
    @classmethod
    def check_multiple_permissions(cls, admin_user, permissions_list, require_all=True):
        """
        بررسی چندین دسترسی
        
        Args:
            admin_user: instance از AdminUser
            permissions_list: لیست دسترسی‌ها
            require_all: True اگر تمام دسترسی‌ها لازم باشد، False اگر یکی کافی باشد
            
        Returns:
            bool: نتیجه بررسی
        """
        user_permissions = cls.get_user_permissions(admin_user)
        
        if require_all:
            return all(perm in user_permissions for perm in permissions_list)
        else:
            return any(perm in user_permissions for perm in permissions_list)
    
    @classmethod
    def get_filtered_permissions(cls, admin_user, permission_category=None):
        """
        دریافت دسترسی‌های فیلتر شده
        
        Args:
            admin_user: instance از AdminUser
            permission_category: دسته‌بندی دسترسی (مثل 'manage_', 'view_')
            
        Returns:
            set: دسترسی‌های فیلتر شده
        """
        user_permissions = cls.get_user_permissions(admin_user)
        
        if not permission_category:
            return user_permissions
        
        return {perm for perm in user_permissions if perm.startswith(permission_category)}


class IsAdminUser(permissions.BasePermission):
    """
    دسترسی پایه برای کاربران ادمین
    """
    message = 'شما دسترسی ادمین ندارید'
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'admin_profile') and
            request.user.admin_profile.is_active
        )


class HasAdminPermission(permissions.BasePermission):
    """
    بررسی دسترسی خاص ادمین
    """
    required_permission = None
    message = 'شما دسترسی لازم برای این عملیات را ندارید'
    
    def __init__(self, permission_name=None):
        if permission_name:
            self.required_permission = permission_name
    
    def has_permission(self, request, view):
        # ابتدا بررسی ادمین بودن
        if not (request.user and 
                request.user.is_authenticated and 
                hasattr(request.user, 'admin_profile') and
                request.user.admin_profile.is_active):
            return False
        
        # اگر دسترسی خاصی نیاز نیست
        if not self.required_permission:
            return True
        
        # بررسی دسترسی خاص
        return AdminPermissions.has_permission(
            request.user.admin_profile, 
            self.required_permission
        )


class HasAnyAdminPermission(permissions.BasePermission):
    """
    بررسی داشتن حداقل یکی از دسترسی‌ها
    """
    required_permissions = []
    message = 'شما هیچ‌کدام از دسترسی‌های لازم را ندارید'
    
    def __init__(self, permissions_list=None):
        if permissions_list:
            self.required_permissions = permissions_list
    
    def has_permission(self, request, view):
        # ابتدا بررسی ادمین بودن
        if not (request.user and 
                request.user.is_authenticated and 
                hasattr(request.user, 'admin_profile') and
                request.user.admin_profile.is_active):
            return False
        
        # اگر لیست دسترسی‌ها خالی است
        if not self.required_permissions:
            return True
        
        # بررسی داشتن حداقل یک دسترسی
        return AdminPermissions.check_multiple_permissions(
            request.user.admin_profile,
            self.required_permissions,
            require_all=False
        )


class HasAllAdminPermissions(permissions.BasePermission):
    """
    بررسی داشتن تمام دسترسی‌های مورد نیاز
    """
    required_permissions = []
    message = 'شما تمام دسترسی‌های لازم را ندارید'
    
    def __init__(self, permissions_list=None):
        if permissions_list:
            self.required_permissions = permissions_list
    
    def has_permission(self, request, view):
        # ابتدا بررسی ادمین بودن
        if not (request.user and 
                request.user.is_authenticated and 
                hasattr(request.user, 'admin_profile') and
                request.user.admin_profile.is_active):
            return False
        
        # اگر لیست دسترسی‌ها خالی است
        if not self.required_permissions:
            return True
        
        # بررسی داشتن تمام دسترسی‌ها
        return AdminPermissions.check_multiple_permissions(
            request.user.admin_profile,
            self.required_permissions,
            require_all=True
        )


class IsSuperAdmin(permissions.BasePermission):
    """
    دسترسی فقط برای super admin
    """
    message = 'فقط ادمین کل اجازه این عملیات را دارد'
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'admin_profile') and
            request.user.admin_profile.is_active and
            request.user.admin_profile.role == 'super_admin'
        )


class CanManageResource(permissions.BasePermission):
    """
    بررسی دسترسی مدیریت منبع خاص
    """
    resource_type = None
    message = 'شما دسترسی مدیریت این منبع را ندارید'
    
    def __init__(self, resource_type=None):
        if resource_type:
            self.resource_type = resource_type
    
    def has_permission(self, request, view):
        # ابتدا بررسی ادمین بودن
        if not (request.user and 
                request.user.is_authenticated and 
                hasattr(request.user, 'admin_profile') and
                request.user.admin_profile.is_active):
            return False
        
        if not self.resource_type:
            return True
        
        # تعیین دسترسی بر اساس نوع منبع و عملیات
        method = request.method.lower()
        
        if method == 'get':
            permission = f'view_{self.resource_type}'
        elif method == 'post':
            permission = f'create_{self.resource_type}' if 'create' in view.action else f'manage_{self.resource_type}'
        elif method in ['put', 'patch']:
            permission = f'update_{self.resource_type}'
        elif method == 'delete':
            permission = f'delete_{self.resource_type}'
        else:
            permission = f'manage_{self.resource_type}'
        
        return AdminPermissions.has_permission(
            request.user.admin_profile,
            permission
        )


class PermissionCacheManager:
    """
    مدیریت cache دسترسی‌ها برای بهبود عملکرد
    """
    CACHE_PREFIX = 'admin_permissions'
    CACHE_TIMEOUT = 300  # 5 دقیقه
    
    @classmethod
    def get_cache_key(cls, admin_user_id):
        """تولید کلید cache"""
        return f"{cls.CACHE_PREFIX}:{admin_user_id}"
    
    @classmethod
    def get_cached_permissions(cls, admin_user):
        """دریافت دسترسی‌ها از cache"""
        cache_key = cls.get_cache_key(admin_user.id)
        return cache.get(cache_key)
    
    @classmethod
    def cache_permissions(cls, admin_user, permissions):
        """ذخیره دسترسی‌ها در cache"""
        cache_key = cls.get_cache_key(admin_user.id)
        cache.set(cache_key, permissions, cls.CACHE_TIMEOUT)
    
    @classmethod
    def clear_user_cache(cls, admin_user_id):
        """پاک کردن cache کاربر"""
        cache_key = cls.get_cache_key(admin_user_id)
        cache.delete(cache_key)
    
    @classmethod
    def clear_all_cache(cls):
        """پاک کردن تمام cache دسترسی‌ها"""
        # این متد باید با احتیاط استفاده شود
        pass


def permission_required(permission_name):
    """
    دکوراتور برای بررسی دسترسی در توابع
    
    Usage:
        @permission_required('manage_users')
        def my_view(request):
            ...
    """
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            if not (request.user and 
                    request.user.is_authenticated and 
                    hasattr(request.user, 'admin_profile')):
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'error': 'authentication_required',
                    'message': 'احراز هویت الزامی است'
                }, status=401)
            
            if not AdminPermissions.has_permission(
                request.user.admin_profile, 
                permission_name
            ):
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'error': 'permission_denied',
                    'message': 'دسترسی کافی ندارید'
                }, status=403)
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def any_permission_required(*permission_names):
    """
    دکوراتور برای بررسی داشتن حداقل یکی از دسترسی‌ها
    """
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            if not (request.user and 
                    request.user.is_authenticated and 
                    hasattr(request.user, 'admin_profile')):
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'error': 'authentication_required',
                    'message': 'احراز هویت الزامی است'
                }, status=401)
            
            if not AdminPermissions.check_multiple_permissions(
                request.user.admin_profile,
                list(permission_names),
                require_all=False
            ):
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'error': 'permission_denied',
                    'message': 'دسترسی کافی ندارید'
                }, status=403)
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator