"""
سیستم مجوزهای اپلیکیشن بیمار
Patient App Permissions System
"""

from rest_framework import permissions
from django.contrib.auth import get_user_model
from django.core.cache import cache
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class BasePatientPermission(permissions.BasePermission):
    """
    کلاس پایه برای مجوزهای اپلیکیشن بیمار
    Base permission class for patient app
    """
    message = 'دسترسی غیرمجاز'
    
    def has_permission(self, request, view):
        """بررسی دسترسی سطح view"""
        if not request.user or not request.user.is_authenticated:
            self.message = 'احراز هویت الزامی است'
            return False
        
        if not request.user.is_active:
            self.message = 'حساب کاربری غیرفعال است'
            return False
            
        return True


class PatientOnlyPermission(BasePatientPermission):
    """
    دسترسی فقط برای بیماران
    Access only for patients
    
    طبق learning: استفاده از PatientOnlyPermission در endpoints مربوطه
    """
    message = 'دسترسی فقط برای بیماران مجاز است'
    
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
            
        if not hasattr(request.user, 'user_type'):
            self.message = 'نوع کاربر مشخص نیست'
            return False
            
        return request.user.user_type == 'patient'
    
    def has_object_permission(self, request, view, obj):
        """بررسی دسترسی سطح object برای بیمار"""
        if not self.has_permission(request, view):
            return False
            
        # بررسی مالکیت object توسط بیمار
        if hasattr(obj, 'patient'):
            # اگر object دارای فیلد patient است
            return obj.patient.user == request.user
        elif hasattr(obj, 'user'):
            # اگر object مستقیماً به user مربوط است
            return obj.user == request.user
            
        return False


class DoctorOnlyPermission(BasePatientPermission):
    """
    دسترسی فقط برای پزشکان
    Access only for doctors
    """
    message = 'دسترسی فقط برای پزشکان مجاز است'
    
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
            
        if not hasattr(request.user, 'user_type'):
            self.message = 'نوع کاربر مشخص نیست'
            return False
            
        return request.user.user_type == 'doctor'
    
    def has_object_permission(self, request, view, obj):
        """بررسی دسترسی سطح object برای پزشک"""
        if not self.has_permission(request, view):
            return False
            
        # پزشک می‌تواند به اطلاعات بیمارانی که به آنها دسترسی دارد دست یابد
        if hasattr(obj, 'patient'):
            # بررسی دسترسی پزشک به بیمار از طریق unified_access
            try:
                from unified_access.services import AccessControlService
                access_service = AccessControlService()
                return access_service.has_patient_access(request.user, obj.patient.user)
            except ImportError:
                # fallback: بررسی مستقیم doctor field
                if hasattr(obj, 'doctor'):
                    return obj.doctor == request.user
                return False
        elif hasattr(obj, 'doctor'):
            # اگر object مستقیماً به doctor مربوط است
            return obj.doctor == request.user
            
        return False


class PatientOwnerPermission(BasePatientPermission):
    """
    دسترسی فقط برای مالک بیمار
    Access only for patient owner
    """
    message = 'دسترسی فقط برای مالک مجاز است'
    
    def has_object_permission(self, request, view, obj):
        """بررسی مالکیت object"""
        if not self.has_permission(request, view):
            return False
            
        # بررسی فیلدهای مختلف مالکیت
        owner_fields = ['user', 'patient', 'created_by']
        
        for field in owner_fields:
            if hasattr(obj, field):
                owner = getattr(obj, field)
                
                # اگر فیلد به user مربوط است
                if owner == request.user:
                    return True
                    
                # اگر فیلد به patient مربوط است و user همان patient است
                if hasattr(owner, 'user') and owner.user == request.user:
                    return True
                    
        return False


class PatientOrDoctorPermission(BasePatientPermission):
    """
    دسترسی برای بیمار یا پزشک مربوطه
    Access for patient or related doctor
    """
    message = 'دسترسی برای بیمار یا پزشک مربوطه'
    
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
            
        user_type = getattr(request.user, 'user_type', None)
        return user_type in ['patient', 'doctor']
    
    def has_object_permission(self, request, view, obj):
        """بررسی دسترسی برای بیمار یا پزشک"""
        if not self.has_permission(request, view):
            return False
            
        user_type = request.user.user_type
        
        if user_type == 'patient':
            # بیمار فقط به اطلاعات خودش دسترسی دارد
            patient_permission = PatientOwnerPermission()
            return patient_permission.has_object_permission(request, view, obj)
            
        elif user_type == 'doctor':
            # پزشک به اطلاعات بیماران تحت نظرش دسترسی دارد
            doctor_permission = DoctorOnlyPermission()
            return doctor_permission.has_object_permission(request, view, obj)
            
        return False


class MedicalRecordPermission(BasePatientPermission):
    """
    مجوز ویژه برای سوابق پزشکی
    Special permission for medical records
    """
    message = 'دسترسی به سوابق پزشکی محدود است'
    
    def has_object_permission(self, request, view, obj):
        """بررسی دسترسی به سوابق پزشکی"""
        if not self.has_permission(request, view):
            return False
            
        user_type = request.user.user_type
        
        # بیمار فقط سوابق خودش را می‌بیند
        if user_type == 'patient':
            return obj.patient.user == request.user
            
        # پزشک سوابق بیماران تحت نظرش را می‌بیند
        elif user_type == 'doctor':
            try:
                from unified_access.services import AccessControlService
                access_service = AccessControlService()
                return access_service.has_patient_access(request.user, obj.patient.user)
            except ImportError:
                # fallback: بررسی مستقیم
                return hasattr(obj, 'doctor') and obj.doctor == request.user
                
        return False


class PrescriptionPermission(BasePatientPermission):
    """
    مجوز ویژه برای نسخه‌ها
    Special permission for prescriptions
    """
    message = 'دسترسی به نسخه‌ها محدود است'
    
    def has_object_permission(self, request, view, obj):
        """بررسی دسترسی به نسخه‌ها"""
        if not self.has_permission(request, view):
            return False
            
        user_type = request.user.user_type
        
        # بیمار فقط نسخه‌های خودش را می‌بیند
        if user_type == 'patient':
            return obj.patient.user == request.user
            
        # پزشک نسخه‌های تجویز شده توسط خودش یا بیماران تحت نظرش را می‌بیند
        elif user_type == 'doctor':
            # نسخه تجویز شده توسط همین پزشک
            if hasattr(obj, 'prescribed_by') and obj.prescribed_by == request.user:
                return True
                
            # بیمار تحت نظر این پزشک
            try:
                from unified_access.services import AccessControlService
                access_service = AccessControlService()
                return access_service.has_patient_access(request.user, obj.patient.user)
            except ImportError:
                return False
                
        return False


class ConsentPermission(BasePatientPermission):
    """
    مجوز ویژه برای رضایت‌نامه‌ها
    Special permission for medical consents
    """
    message = 'دسترسی به رضایت‌نامه‌ها محدود است'
    
    def has_object_permission(self, request, view, obj):
        """بررسی دسترسی به رضایت‌نامه‌ها"""
        if not self.has_permission(request, view):
            return False
            
        user_type = request.user.user_type
        
        # بیمار فقط رضایت‌نامه‌های خودش را می‌بیند
        if user_type == 'patient':
            return obj.patient.user == request.user
            
        # پزشک رضایت‌نامه‌های بیماران تحت نظرش را می‌بیند
        elif user_type == 'doctor':
            try:
                from unified_access.services import AccessControlService
                access_service = AccessControlService()
                return access_service.has_patient_access(request.user, obj.patient.user)
            except ImportError:
                return False
                
        return False


# Helper functions

def has_patient_access(user, patient):
    """
    بررسی دسترسی کاربر به بیمار
    Check if user has access to patient
    """
    if user.user_type == 'patient':
        return patient.user == user
    elif user.user_type == 'doctor':
        try:
            from unified_access.services import AccessControlService
            access_service = AccessControlService()
            return access_service.has_patient_access(user, patient.user)
        except ImportError:
            return False
    return False


def get_permission_for_model(model_name):
    """
    دریافت کلاس permission مناسب برای مدل
    Get appropriate permission class for model
    """
    permission_map = {
        'patientprofile': PatientOwnerPermission,
        'medicalrecord': MedicalRecordPermission,
        'prescriptionhistory': PrescriptionPermission,
        'medicalconsent': ConsentPermission,
    }
    
    return permission_map.get(model_name.lower(), PatientOrDoctorPermission)