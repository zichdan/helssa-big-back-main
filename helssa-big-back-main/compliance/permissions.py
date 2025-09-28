from rest_framework import permissions
from typing import Any
from django.contrib.auth import get_user_model

User = get_user_model()


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    دسترسی کامل برای ادمین، فقط خواندن برای سایرین
    """
    
    def has_permission(self, request, view):
        # همه می‌توانند بخوانند
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # فقط ادمین می‌تواند تغییر دهد
        return request.user and request.user.is_staff


class HasMFAEnabled(permissions.BasePermission):
    """
    بررسی فعال بودن MFA برای کاربر
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        # بررسی وجود و فعال بودن MFA
        return (
            hasattr(request.user, 'mfa_config') and 
            request.user.mfa_config.is_active
        )


class CanAccessPatientData(permissions.BasePermission):
    """
    بررسی دسترسی به داده‌های بیمار
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
        
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # ادمین دسترسی کامل دارد
        if user.is_superuser:
            return True
            
        # بیمار به داده‌های خودش دسترسی دارد
        if hasattr(obj, 'patient_id') and str(obj.patient_id) == str(user.id):
            return True
            
        # TODO: بررسی دسترسی پزشک با استفاده از TemporaryAccess
        # نیاز به پیاده‌سازی کامل پس از ایجاد unified_auth
        
        return False


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    دسترسی برای مالک یا ادمین
    """
    
    def has_object_permission(self, request, view, obj):
        # ادمین دسترسی کامل دارد
        if request.user.is_superuser:
            return True
            
        # بررسی مالکیت
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
            
        return False


class HasRole(permissions.BasePermission):
    """
    بررسی داشتن نقش خاص
    """
    
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles
        
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        # TODO: بررسی نقش کاربر
        # نیاز به رابطه many-to-many بین User و Role
        
        return True  # موقتاً true برمی‌گردانیم


class IsMedicalStaff(permissions.BasePermission):
    """
    دسترسی برای کادر پزشکی (پزشک، پرستار، کارمند)
    """
    
    medical_roles = ['doctor', 'nurse', 'staff']
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        # ادمین دسترسی دارد
        if request.user.is_superuser:
            return True
            
        # TODO: بررسی نقش کاربر در medical_roles
        # نیاز به پیاده‌سازی کامل
        
        return False