"""
تنظیمات Django Admin برای اپلیکیشن Doctor
Django Admin Configuration for Doctor App
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    DoctorProfile,
    DoctorSchedule,
    DoctorShift,
    DoctorCertificate,
    DoctorRating,
    DoctorSettings
)


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    """مدیریت پروفایل پزشک در admin"""
    
    list_display = [
        'get_full_name', 'specialty', 'medical_system_code', 
        'is_verified', 'rating', 'total_reviews', 'created_at'
    ]
    list_filter = [
        'specialty', 'is_verified', 'allow_online_visits', 
        'auto_accept_appointments', 'created_at'
    ]
    search_fields = [
        'first_name', 'last_name', 'national_code', 
        'medical_system_code', 'phone_number'
    ]
    readonly_fields = [
        'id', 'rating', 'total_reviews', 'created_at', 
        'updated_at', 'get_profile_picture_preview'
    ]
    
    fieldsets = (
        ('اطلاعات کاربری', {
            'fields': ('user', 'id')
        }),
        ('اطلاعات شخصی', {
            'fields': (
                'first_name', 'last_name', 'national_code', 
                'medical_system_code', 'phone_number'
            )
        }),
        ('تخصص و تجربه', {
            'fields': (
                'specialty', 'sub_specialty', 'years_of_experience', 'biography'
            )
        }),
        ('اطلاعات مطب', {
            'fields': ('clinic_address', 'clinic_phone')
        }),
        ('تصویر پروفایل', {
            'fields': ('profile_picture', 'get_profile_picture_preview')
        }),
        ('تنظیمات ویزیت', {
            'fields': (
                'visit_duration', 'visit_price', 'auto_accept_appointments', 
                'allow_online_visits'
            )
        }),
        ('وضعیت تایید', {
            'fields': ('is_verified', 'verification_date')
        }),
        ('امتیاز و نظرات', {
            'fields': ('rating', 'total_reviews')
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_name(self, obj):
        """نمایش نام کامل"""
        return obj.get_full_name()
    get_full_name.short_description = 'نام کامل'
    
    def get_profile_picture_preview(self, obj):
        """نمایش پیش‌نمایش تصویر پروفایل"""
        if obj.profile_picture:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px;" />',
                obj.profile_picture.url
            )
        return "تصویری موجود نیست"
    get_profile_picture_preview.short_description = 'پیش‌نمایش تصویر'
    
    actions = ['verify_doctors', 'unverify_doctors']
    
    def verify_doctors(self, request, queryset):
        """تایید پزشکان انتخاب شده"""
        from django.utils import timezone
        updated = queryset.update(
            is_verified=True,
            verification_date=timezone.now()
        )
        self.message_user(
            request,
            f"{updated} پزشک تایید شدند."
        )
    verify_doctors.short_description = "تایید پزشکان انتخاب شده"
    
    def unverify_doctors(self, request, queryset):
        """لغو تایید پزشکان انتخاب شده"""
        updated = queryset.update(
            is_verified=False,
            verification_date=None
        )
        self.message_user(
            request,
            f"تایید {updated} پزشک لغو شد."
        )
    unverify_doctors.short_description = "لغو تایید پزشکان انتخاب شده"


@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    """مدیریت برنامه کاری پزشک در admin"""
    
    list_display = [
        'get_doctor_name', 'get_weekday_display', 'start_time', 
        'end_time', 'visit_type', 'max_patients', 'is_active'
    ]
    list_filter = [
        'weekday', 'visit_type', 'is_active', 'created_at'
    ]
    search_fields = [
        'doctor__doctor_profile__first_name',
        'doctor__doctor_profile__last_name',
        'doctor__username'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('پزشک', {
            'fields': ('doctor',)
        }),
        ('زمان‌بندی', {
            'fields': (
                'weekday', 'start_time', 'end_time', 
                'break_start', 'break_end'
            )
        }),
        ('تنظیمات ویزیت', {
            'fields': ('visit_type', 'max_patients')
        }),
        ('اطلاعات سیستم', {
            'fields': ('id', 'created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    def get_doctor_name(self, obj):
        """نمایش نام پزشک"""
        try:
            return obj.doctor.doctor_profile.get_full_name()
        except DoctorProfile.DoesNotExist:
            return obj.doctor.username
    get_doctor_name.short_description = 'پزشک'


@admin.register(DoctorShift)
class DoctorShiftAdmin(admin.ModelAdmin):
    """مدیریت شیفت‌های پزشک در admin"""
    
    list_display = [
        'get_doctor_name', 'date', 'start_time', 'end_time', 
        'shift_type', 'visit_type', 'is_active'
    ]
    list_filter = [
        'shift_type', 'visit_type', 'date', 'is_active'
    ]
    search_fields = [
        'doctor__doctor_profile__first_name',
        'doctor__doctor_profile__last_name',
        'doctor__username'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('پزشک', {
            'fields': ('doctor',)
        }),
        ('زمان‌بندی', {
            'fields': ('date', 'start_time', 'end_time')
        }),
        ('نوع شیفت', {
            'fields': ('shift_type', 'visit_type', 'max_patients')
        }),
        ('یادداشت‌ها', {
            'fields': ('notes',)
        }),
        ('اطلاعات سیستم', {
            'fields': ('id', 'created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    def get_doctor_name(self, obj):
        """نمایش نام پزشک"""
        try:
            return obj.doctor.doctor_profile.get_full_name()
        except:
            return obj.doctor.username
    get_doctor_name.short_description = 'پزشک'


@admin.register(DoctorCertificate)
class DoctorCertificateAdmin(admin.ModelAdmin):
    """مدیریت مدارک پزشک در admin"""
    
    list_display = [
        'get_doctor_name', 'certificate_type', 'title', 
        'issuer', 'issue_date', 'is_verified', 'is_expired'
    ]
    list_filter = [
        'certificate_type', 'is_verified', 'issue_date', 'is_active'
    ]
    search_fields = [
        'doctor__doctor_profile__first_name',
        'doctor__doctor_profile__last_name',
        'title', 'issuer', 'certificate_number'
    ]
    readonly_fields = [
        'id', 'is_expired', 'created_at', 'updated_at',
        'get_file_link'
    ]
    date_hierarchy = 'issue_date'
    
    fieldsets = (
        ('پزشک', {
            'fields': ('doctor',)
        }),
        ('اطلاعات مدرک', {
            'fields': (
                'certificate_type', 'title', 'issuer', 
                'certificate_number'
            )
        }),
        ('تاریخ‌ها', {
            'fields': ('issue_date', 'expiry_date', 'is_expired')
        }),
        ('فایل مدرک', {
            'fields': ('file', 'get_file_link')
        }),
        ('وضعیت تایید', {
            'fields': (
                'is_verified', 'verification_date', 
                'verification_notes'
            )
        }),
        ('اطلاعات سیستم', {
            'fields': ('id', 'created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    def get_doctor_name(self, obj):
        """نمایش نام پزشک"""
        try:
            return obj.doctor.doctor_profile.get_full_name()
        except:
            return obj.doctor.username
    get_doctor_name.short_description = 'پزشک'
    
    def get_file_link(self, obj):
        """لینک دانلود فایل"""
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">دانلود فایل</a>',
                obj.file.url
            )
        return "فایلی موجود نیست"
    get_file_link.short_description = 'دانلود فایل'
    
    actions = ['verify_certificates', 'unverify_certificates']
    
    def verify_certificates(self, request, queryset):
        """تایید مدارک انتخاب شده"""
        from django.utils import timezone
        updated = queryset.update(
            is_verified=True,
            verification_date=timezone.now()
        )
        self.message_user(
            request,
            f"{updated} مدرک تایید شدند."
        )
    verify_certificates.short_description = "تایید مدارک انتخاب شده"
    
    def unverify_certificates(self, request, queryset):
        """لغو تایید مدارک انتخاب شده"""
        updated = queryset.update(
            is_verified=False,
            verification_date=None
        )
        self.message_user(
            request,
            f"تایید {updated} مدرک لغو شد."
        )
    unverify_certificates.short_description = "لغو تایید مدارک انتخاب شده"


@admin.register(DoctorRating)
class DoctorRatingAdmin(admin.ModelAdmin):
    """مدیریت امتیازات پزشک در admin"""
    
    list_display = [
        'get_doctor_name', 'get_patient_name', 'rating', 
        'visit_date', 'is_approved', 'created_at'
    ]
    list_filter = [
        'rating', 'is_approved', 'visit_date', 'created_at', 'is_active'
    ]
    search_fields = [
        'doctor__doctor_profile__first_name',
        'doctor__doctor_profile__last_name',
        'patient__username'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'visit_date'
    
    fieldsets = (
        ('اطلاعات کلی', {
            'fields': ('doctor', 'patient')
        }),
        ('امتیاز و نظر', {
            'fields': ('rating', 'comment')
        }),
        ('اطلاعات ویزیت', {
            'fields': ('visit_date',)
        }),
        ('وضعیت تایید', {
            'fields': ('is_approved',)
        }),
        ('اطلاعات سیستم', {
            'fields': ('id', 'created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    def get_doctor_name(self, obj):
        """نمایش نام پزشک"""
        try:
            return obj.doctor.doctor_profile.get_full_name()
        except:
            return obj.doctor.username
    get_doctor_name.short_description = 'پزشک'
    
    def get_patient_name(self, obj):
        """نمایش نام بیمار (مخفی)"""
        return f"{obj.patient.username[:3]}***"
    get_patient_name.short_description = 'بیمار'
    
    actions = ['approve_ratings', 'unapprove_ratings']
    
    def approve_ratings(self, request, queryset):
        """تایید امتیازات انتخاب شده"""
        updated = queryset.update(is_approved=True)
        self.message_user(
            request,
            f"{updated} امتیاز تایید شدند."
        )
    approve_ratings.short_description = "تایید امتیازات انتخاب شده"
    
    def unapprove_ratings(self, request, queryset):
        """لغو تایید امتیازات انتخاب شده"""
        updated = queryset.update(is_approved=False)
        self.message_user(
            request,
            f"تایید {updated} امتیاز لغو شد."
        )
    unapprove_ratings.short_description = "لغو تایید امتیازات انتخاب شده"


@admin.register(DoctorSettings)
class DoctorSettingsAdmin(admin.ModelAdmin):
    """مدیریت تنظیمات پزشک در admin"""
    
    list_display = [
        'get_doctor_name', 'email_notifications', 'sms_notifications',
        'auto_generate_prescription', 'preferred_language', 'is_active'
    ]
    list_filter = [
        'email_notifications', 'sms_notifications', 'push_notifications',
        'auto_generate_prescription', 'auto_generate_certificate',
        'preferred_language', 'is_active'
    ]
    search_fields = [
        'doctor__doctor_profile__first_name',
        'doctor__doctor_profile__last_name',
        'doctor__username'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('پزشک', {
            'fields': ('doctor',)
        }),
        ('تنظیمات اعلان‌ها', {
            'fields': (
                'email_notifications', 'sms_notifications', 
                'push_notifications'
            )
        }),
        ('تنظیمات نوبت‌دهی', {
            'fields': (
                'allow_same_day_booking', 'booking_lead_time',
                'max_daily_appointments'
            )
        }),
        ('تنظیمات گزارش‌گیری', {
            'fields': (
                'auto_generate_prescription', 'auto_generate_certificate'
            )
        }),
        ('تنظیمات زبان', {
            'fields': ('preferred_language',)
        }),
        ('اطلاعات سیستم', {
            'fields': ('id', 'created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    def get_doctor_name(self, obj):
        """نمایش نام پزشک"""
        try:
            return obj.doctor.doctor_profile.get_full_name()
        except:
            return obj.doctor.username
    get_doctor_name.short_description = 'پزشک'


# تنظیمات کلی Admin
admin.site.site_header = "مدیریت سیستم هلسا - بخش پزشکان"
admin.site.site_title = "هلسا - پزشکان"
admin.site.index_title = "مدیریت اپلیکیشن Doctor"