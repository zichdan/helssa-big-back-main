from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView


class IsPatientOrDoctor(permissions.BasePermission):
    """دسترسی فقط برای بیمار یا پزشک ملاقات"""
    
    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        # obj باید Encounter باشد
        if hasattr(obj, 'patient_id') and hasattr(obj, 'doctor_id'):
            return str(request.user.id) in [
                str(obj.patient_id),
                str(obj.doctor_id)
            ]
        return False


class IsDoctorOfEncounter(permissions.BasePermission):
    """دسترسی فقط برای پزشک ملاقات"""
    
    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        if hasattr(obj, 'doctor_id'):
            return str(request.user.id) == str(obj.doctor_id)
        # اگر obj یک مدل وابسته است (مثل SOAPReport)
        if hasattr(obj, 'encounter'):
            return str(request.user.id) == str(obj.encounter.doctor_id)
        return False


class IsPatientOfEncounter(permissions.BasePermission):
    """دسترسی فقط برای بیمار ملاقات"""
    
    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        if hasattr(obj, 'patient_id'):
            return str(request.user.id) == str(obj.patient_id)
        # اگر obj یک مدل وابسته است
        if hasattr(obj, 'encounter'):
            return str(request.user.id) == str(obj.encounter.patient_id)
        return False


class CanStartEncounter(permissions.BasePermission):
    """بررسی امکان شروع ملاقات"""
    
    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        # فقط بیمار یا پزشک می‌توانند ملاقات را شروع کنند
        if str(request.user.id) not in [str(obj.patient_id), str(obj.doctor_id)]:
            return False
            
        # بررسی وضعیت و زمان
        return obj.can_start


class CanModifySOAPReport(permissions.BasePermission):
    """دسترسی تغییر گزارش SOAP"""
    
    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        # فقط پزشک می‌تواند تغییر دهد
        if str(request.user.id) != str(obj.encounter.doctor_id):
            return False
            
        # اگر تایید شده، نمی‌توان تغییر داد
        if obj.doctor_approved and request.method in ['PUT', 'PATCH', 'DELETE']:
            return False
            
        return True


class CanViewPrescription(permissions.BasePermission):
    """دسترسی مشاهده نسخه"""
    
    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        # بیمار و پزشک می‌توانند ببینند
        allowed_users = [
            str(obj.encounter.patient_id),
            str(obj.encounter.doctor_id)
        ]
        
        # داروخانه با کد دسترسی
        if hasattr(request, 'pharmacy_access') and request.pharmacy_access:
            allowed_users.append(request.pharmacy_access.pharmacy_id)
            
        return str(request.user.id) in allowed_users


class CanUploadFile(permissions.BasePermission):
    """دسترسی آپلود فایل"""
    
    def has_permission(self, request: Request, view: APIView) -> bool:
        # باید authenticated باشد
        return request.user and request.user.is_authenticated
        
    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        # obj اینجا Encounter است
        # بیمار و پزشک می‌توانند آپلود کنند
        return str(request.user.id) in [
            str(obj.patient_id),
            str(obj.doctor_id)
        ]


class IsOwnerOrReadOnly(permissions.BasePermission):
    """مالک می‌تواند تغییر دهد، بقیه فقط مشاهده"""
    
    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        # خواندن برای همه
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # نوشتن فقط برای مالک
        if hasattr(obj, 'uploaded_by_id'):
            return str(obj.uploaded_by_id) == str(request.user.id)
            
        return False