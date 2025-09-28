"""
پنل ادمین سیستم مدیریت بیماران
Patient Management System Admin Panel
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
import logging

from .models import PatientProfile, MedicalRecord, PrescriptionHistory, MedicalConsent
from .permissions import has_patient_access

logger = logging.getLogger(__name__)

User = get_user_model()


class BasePatientAdmin(admin.ModelAdmin):
    """
    کلاس پایه ادمین با permission checks
    Base admin class with permission checks
    """
    
    def has_view_permission(self, request, obj=None):
        """بررسی مجوز مشاهده"""
        if not super().has_view_permission(request, obj):
            return False
            
        # ادمین‌ها همیشه دسترسی دارند
        if request.user.is_superuser or request.user.user_type == 'admin':
            return True
            
        # اگر object خاص است، بررسی دسترسی
        if obj and hasattr(obj, 'patient'):
            if request.user.user_type == 'doctor':
                return has_patient_access(request.user, obj.patient)
            elif request.user.user_type == 'patient':
                return obj.patient.user == request.user
                
        return False
    
    def has_change_permission(self, request, obj=None):
        """بررسی مجوز تغییر"""
        if not super().has_change_permission(request, obj):
            return False
            
        # ادمین‌ها همیشه دسترسی دارند
        if request.user.is_superuser or request.user.user_type == 'admin':
            return True
            
        # پزشکان فقط می‌توانند سوابق و نسخه‌هایی که خودشان ایجاد کرده‌اند را تغییر دهند
        if obj and request.user.user_type == 'doctor':
            if hasattr(obj, 'doctor') and obj.doctor == request.user:
                return True
            return has_patient_access(request.user, obj.patient) if hasattr(obj, 'patient') else False
            
        # بیماران فقط اطلاعات خودشان را می‌توانند تغییر دهند
        if obj and request.user.user_type == 'patient':
            if hasattr(obj, 'patient'):
                return obj.patient.user == request.user
            elif hasattr(obj, 'user'):
                return obj.user == request.user
                
        return False
    
    def has_delete_permission(self, request, obj=None):
        """بررسی مجوز حذف"""
        # فقط ادمین‌ها می‌توانند حذف کنند
        return request.user.is_superuser or request.user.user_type == 'admin'
    
    def get_queryset(self, request):
        """فیلتر کردن queryset بر اساس دسترسی کاربر"""
        qs = super().get_queryset(request)
        
        # ادمین‌ها همه چیز را می‌بینند
        if request.user.is_superuser or request.user.user_type == 'admin':
            return qs
            
        # پزشکان فقط بیماران تحت نظر خود را می‌بینند
        elif request.user.user_type == 'doctor':
            # این باید با unified_access پیاده‌سازی شود
            # در حالت فعلی فقط رکوردهایی که خودشان ایجاد کرده‌اند
            if hasattr(qs.model, 'doctor'):
                return qs.filter(doctor=request.user)
            elif hasattr(qs.model, 'prescribed_by'):
                return qs.filter(prescribed_by=request.user)
            return qs.none()
            
        # بیماران فقط اطلاعات خودشان را می‌بینند
        elif request.user.user_type == 'patient':
            try:
                patient_profile = PatientProfile.objects.get(user=request.user)
                if hasattr(qs.model, 'patient'):
                    return qs.filter(patient=patient_profile)
                elif qs.model == PatientProfile:
                    return qs.filter(user=request.user)
            except PatientProfile.DoesNotExist:
                pass
            return qs.none()
            
        return qs.none()


@admin.register(PatientProfile)
class PatientProfileAdmin(BasePatientAdmin):
    """
    پنل ادمین پروفایل بیماران
    Patient Profile Admin Panel
    """
    
    list_display = [
        'medical_record_number',
        'get_full_name',
        'national_code',
        'age',
        'gender',
        'user_phone',
        'is_active',
        'created_at'
    ]
    
    list_filter = [
        'gender',
        'blood_type',
        'marital_status',
        'is_active',
        'created_at',
        'city',
        'province'
    ]
    
    search_fields = [
        'first_name',
        'last_name',
        'national_code',
        'medical_record_number',
        'user__username'
    ]
    
    readonly_fields = [
        'id',
        'medical_record_number',
        'age',
        'bmi',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': (
                'id',
                'user',
                'medical_record_number',
                'is_active'
            )
        }),
        ('اطلاعات هویتی', {
            'fields': (
                'national_code',
                'first_name',
                'last_name',
                'birth_date',
                'age',
                'gender'
            )
        }),
        ('اطلاعات تماس', {
            'fields': (
                'emergency_contact_name',
                'emergency_contact_phone',
                'emergency_contact_relation'
            )
        }),
        ('آدرس', {
            'fields': (
                'address',
                'city',
                'province',
                'postal_code'
            )
        }),
        ('اطلاعات پزشکی', {
            'fields': (
                'blood_type',
                'height',
                'weight',
                'bmi',
                'marital_status'
            )
        }),
        ('تاریخ‌ها', {
            'fields': (
                'created_at',
                'updated_at'
            )
        })
    )
    
    actions = ['activate_patients', 'deactivate_patients']
    
    def get_full_name(self, obj):
        """نمایش نام کامل"""
        return obj.get_full_name()
    get_full_name.short_description = 'نام کامل'
    
    def user_phone(self, obj):
        """نمایش شماره تلفن"""
        return obj.user.username if obj.user else '-'
    user_phone.short_description = 'شماره تلفن'
    
    def activate_patients(self, request, queryset):
        """فعال کردن بیماران انتخابی"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} بیمار فعال شد.')
    activate_patients.short_description = 'فعال کردن بیماران انتخابی'
    
    def deactivate_patients(self, request, queryset):
        """غیرفعال کردن بیماران انتخابی"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} بیمار غیرفعال شد.')
    deactivate_patients.short_description = 'غیرفعال کردن بیماران انتخابی'


@admin.register(MedicalRecord)
class MedicalRecordAdmin(BasePatientAdmin):
    """
    پنل ادمین سوابق پزشکی
    Medical Records Admin Panel
    """
    
    list_display = [
        'title',
        'patient_name',
        'record_type',
        'severity',
        'start_date',
        'is_ongoing',
        'created_at'
    ]
    
    list_filter = [
        'record_type',
        'severity',
        'is_ongoing',
        'start_date',
        'created_at'
    ]
    
    search_fields = [
        'title',
        'description',
        'patient__first_name',
        'patient__last_name',
        'patient__national_code',
        'doctor_name'
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'duration_days'
    ]
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': (
                'id',
                'patient',
                'created_by'
            )
        }),
        ('جزئیات سابقه', {
            'fields': (
                'record_type',
                'title',
                'description',
                'severity'
            )
        }),
        ('تاریخ‌ها', {
            'fields': (
                'start_date',
                'end_date',
                'is_ongoing',
                'duration_days'
            )
        }),
        ('اطلاعات اضافی', {
            'fields': (
                'doctor_name',
                'notes'
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    raw_id_fields = ['patient', 'created_by']
    
    def patient_name(self, obj):
        """نمایش نام بیمار"""
        return obj.patient.get_full_name()
    patient_name.short_description = 'نام بیمار'
    
    def duration_days(self, obj):
        """محاسبه مدت زمان"""
        if obj.end_date:
            return (obj.end_date - obj.start_date).days
        elif obj.is_ongoing:
            from datetime import date
            return (date.today() - obj.start_date).days
        return 0
    duration_days.short_description = 'مدت (روز)'


@admin.register(PrescriptionHistory)
class PrescriptionHistoryAdmin(BasePatientAdmin):
    """
    پنل ادمین تاریخچه نسخه‌ها
    Prescription History Admin Panel
    """
    
    list_display = [
        'prescription_number',
        'patient_name',
        'medication_name',
        'prescribed_by_name',
        'status',
        'prescribed_date',
        'is_expired',
        'can_repeat'
    ]
    
    list_filter = [
        'status',
        'prescribed_date',
        'is_repeat_allowed',
        'prescribed_by'
    ]
    
    search_fields = [
        'prescription_number',
        'medication_name',
        'patient__first_name',
        'patient__last_name',
        'patient__national_code',
        'diagnosis'
    ]
    
    readonly_fields = [
        'id',
        'prescription_number',
        'is_expired',
        'days_remaining',
        'can_repeat_now',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': (
                'id',
                'prescription_number',
                'patient',
                'prescribed_by'
            )
        }),
        ('اطلاعات دارو', {
            'fields': (
                'medication_name',
                'dosage',
                'frequency',
                'duration',
                'instructions'
            )
        }),
        ('تشخیص و درمان', {
            'fields': (
                'diagnosis',
            )
        }),
        ('تاریخ‌ها و وضعیت', {
            'fields': (
                'prescribed_date',
                'start_date',
                'end_date',
                'status',
                'is_expired',
                'days_remaining'
            )
        }),
        ('تکرار نسخه', {
            'fields': (
                'is_repeat_allowed',
                'repeat_count',
                'max_repeats',
                'can_repeat_now'
            )
        }),
        ('یادداشت‌ها', {
            'fields': (
                'pharmacy_notes',
                'patient_notes'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    raw_id_fields = ['patient', 'prescribed_by']
    actions = ['cancel_prescriptions', 'activate_prescriptions']
    
    def patient_name(self, obj):
        """نمایش نام بیمار"""
        return obj.patient.get_full_name()
    patient_name.short_description = 'نام بیمار'
    
    def prescribed_by_name(self, obj):
        """نمایش نام پزشک"""
        return obj.prescribed_by.get_full_name() if obj.prescribed_by else '-'
    prescribed_by_name.short_description = 'پزشک تجویزکننده'
    
    def can_repeat_now(self, obj):
        """نمایش امکان تکرار"""
        return obj.can_repeat()
    can_repeat_now.short_description = 'قابل تکرار'
    can_repeat_now.boolean = True
    
    def cancel_prescriptions(self, request, queryset):
        """لغو نسخه‌های انتخابی"""
        updated = queryset.filter(status='active').update(status='cancelled')
        self.message_user(request, f'{updated} نسخه لغو شد.')
    cancel_prescriptions.short_description = 'لغو نسخه‌های انتخابی'
    
    def activate_prescriptions(self, request, queryset):
        """فعال کردن نسخه‌های انتخابی"""
        updated = queryset.filter(status='cancelled').update(status='active')
        self.message_user(request, f'{updated} نسخه فعال شد.')
    activate_prescriptions.short_description = 'فعال کردن نسخه‌های انتخابی'


@admin.register(MedicalConsent)
class MedicalConsentAdmin(BasePatientAdmin):
    """
    پنل ادمین رضایت‌نامه‌های پزشکی
    Medical Consent Admin Panel
    """
    
    list_display = [
        'title',
        'patient_name',
        'consent_type',
        'status',
        'created_date',
        'consent_date',
        'is_valid',
        'is_expired'
    ]
    
    list_filter = [
        'consent_type',
        'status',
        'created_date',
        'expiry_date'
    ]
    
    search_fields = [
        'title',
        'description',
        'patient__first_name',
        'patient__last_name',
        'patient__national_code'
    ]
    
    readonly_fields = [
        'id',
        'is_valid',
        'is_expired',
        'consent_date',
        'digital_signature',
        'ip_address',
        'user_agent',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': (
                'id',
                'patient',
                'requested_by',
                'processed_by'
            )
        }),
        ('جزئیات رضایت‌نامه', {
            'fields': (
                'consent_type',
                'title',
                'description',
                'consent_text'
            )
        }),
        ('وضعیت و تاریخ‌ها', {
            'fields': (
                'status',
                'created_date',
                'consent_date',
                'expiry_date',
                'is_valid',
                'is_expired'
            )
        }),
        ('امضای دیجیتال', {
            'fields': (
                'digital_signature',
                'ip_address',
                'user_agent'
            ),
            'classes': ('collapse',)
        }),
        ('اطلاعات اضافی', {
            'fields': (
                'witness_name',
                'witness_signature',
                'notes'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    raw_id_fields = ['patient', 'requested_by', 'processed_by']
    actions = ['revoke_consents']
    
    def patient_name(self, obj):
        """نمایش نام بیمار"""
        return obj.patient.get_full_name()
    patient_name.short_description = 'نام بیمار'
    
    def revoke_consents(self, request, queryset):
        """لغو رضایت‌نامه‌های انتخابی"""
        updated = 0
        for consent in queryset.filter(status='granted'):
            consent.revoke_consent()
            updated += 1
        self.message_user(request, f'{updated} رضایت‌نامه لغو شد.')
    revoke_consents.short_description = 'لغو رضایت‌نامه‌های انتخابی'


# تنظیمات سایت ادمین
admin.site.site_header = "پنل مدیریت سیستم بیماران HELSSA"
admin.site.site_title = "مدیریت بیماران"
admin.site.index_title = "خوش آمدید به پنل مدیریت سیستم بیماران"