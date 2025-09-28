"""
مجوزهای دسترسی برای اپلیکیشن Checklist
"""
from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    مجوز دسترسی: فقط مالک می‌تواند ویرایش کند، بقیه فقط خواندن
    """
    def has_object_permission(self, request, view, obj):
        # دسترسی خواندن برای همه
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # دسترسی نوشتن فقط برای مالک
        return obj.created_by == request.user


class IsHealthcareProvider(permissions.BasePermission):
    """
    مجوز دسترسی: فقط کادر درمان (پزشک، پرستار و...)
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # بررسی نقش کاربر
        if hasattr(request.user, 'role'):
            return request.user.role in ['doctor', 'nurse', 'specialist', 'therapist']
        
        # بررسی گروه کاربر
        return request.user.groups.filter(
            name__in=['doctors', 'nurses', 'healthcare_providers']
        ).exists()


class IsDoctor(permissions.BasePermission):
    """
    مجوز دسترسی: فقط پزشکان
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # بررسی نقش کاربر
        if hasattr(request.user, 'role'):
            return request.user.role == 'doctor'
        
        # بررسی گروه کاربر
        return request.user.groups.filter(name='doctors').exists()


class CanManageChecklists(permissions.BasePermission):
    """
    مجوز دسترسی: برای مدیریت چک‌لیست‌ها (ایجاد، ویرایش، حذف)
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # ادمین‌ها دسترسی کامل دارند
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # پزشکان می‌توانند چک‌لیست مدیریت کنند
        if hasattr(request.user, 'role') and request.user.role == 'doctor':
            return True
        
        # کاربران با مجوز خاص
        return request.user.has_perm('checklist.manage_checklists')


class CanEvaluateChecklists(permissions.BasePermission):
    """
    مجوز دسترسی: برای ارزیابی چک‌لیست‌ها
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # کادر درمان می‌توانند ارزیابی انجام دهند
        if hasattr(request.user, 'role'):
            return request.user.role in ['doctor', 'nurse', 'specialist']
        
        return request.user.has_perm('checklist.evaluate_checklists')


class IsEncounterParticipant(permissions.BasePermission):
    """
    مجوز دسترسی: فقط شرکت‌کنندگان ویزیت (پزشک یا بیمار)
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # دسترسی به encounter مرتبط
        encounter = None
        if hasattr(obj, 'encounter'):
            encounter = obj.encounter
        elif hasattr(obj, 'get_encounter'):
            encounter = obj.get_encounter()
        
        if not encounter:
            return False
        
        # بررسی شرکت‌کننده بودن
        if hasattr(encounter, 'doctor') and encounter.doctor == request.user:
            return True
        
        if hasattr(encounter, 'patient') and encounter.patient == request.user:
            # بیماران فقط دسترسی خواندن دارند
            return request.method in permissions.SAFE_METHODS
        
        return False


class CanDismissAlerts(permissions.BasePermission):
    """
    مجوز دسترسی: برای رد کردن هشدارها
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # پزشکان و ادمین‌ها می‌توانند هشدارها را رد کنند
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        if hasattr(request.user, 'role'):
            return request.user.role in ['doctor', 'nurse']
        
        return request.user.has_perm('checklist.dismiss_alerts')
    
    def has_object_permission(self, request, view, obj):
        # فقط پزشک ویزیت می‌تواند هشدارهای آن را رد کند
        if hasattr(obj, 'encounter') and hasattr(obj.encounter, 'doctor'):
            return obj.encounter.doctor == request.user
        
        return request.user.is_superuser or request.user.is_staff