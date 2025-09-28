from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from typing import Dict, List, Optional
import json
import uuid

User = get_user_model()


class SecurityLayer(models.Model):
    """
    لایه‌های امنیتی سیستم
    """
    LAYER_TYPES = [
        ('network', 'Network Security'),
        ('application', 'Application Security'),
        ('data', 'Data Security'),
        ('audit', 'Audit Security'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='نام لایه')
    layer_type = models.CharField(max_length=20, choices=LAYER_TYPES, verbose_name='نوع لایه')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    priority = models.IntegerField(default=1, verbose_name='اولویت')
    config = models.JSONField(default=dict, verbose_name='تنظیمات')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')
    
    class Meta:
        verbose_name = 'لایه امنیتی'
        verbose_name_plural = 'لایه‌های امنیتی'
        ordering = ['priority', 'name']
        
    def __str__(self):
        return f"{self.name} ({self.get_layer_type_display()})"


class SecurityLog(models.Model):
    """
    لاگ‌های امنیتی سیستم
    """
    EVENT_TYPES = [
        ('security_violation', 'نقض امنیتی'),
        ('authentication_failed', 'احراز هویت ناموفق'),
        ('authorization_denied', 'عدم مجوز دسترسی'),
        ('data_breach_attempt', 'تلاش برای نفوذ به داده‌ها'),
        ('malware_detected', 'شناسایی بدافزار'),
        ('invalid_access_pattern', 'الگوی دسترسی غیرمجاز'),
        ('successful_auth', 'احراز هویت موفق'),
        ('permission_granted', 'اعطای مجوز'),
        ('permission_denied', 'رد مجوز'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, verbose_name='نوع رویداد')
    layer = models.CharField(max_length=50, verbose_name='لایه امنیتی')
    reason = models.TextField(verbose_name='دلیل')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='آدرس IP')
    user_agent = models.TextField(null=True, blank=True, verbose_name='User Agent')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='security_logs', verbose_name='کاربر')
    risk_score = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='امتیاز ریسک')
    metadata = models.JSONField(default=dict, verbose_name='اطلاعات اضافی')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان رخداد')
    
    class Meta:
        verbose_name = 'لاگ امنیتی'
        verbose_name_plural = 'لاگ‌های امنیتی'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at', 'event_type']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['ip_address', '-created_at']),
        ]
        
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.created_at}"


class MFAConfig(models.Model):
    """
    تنظیمات احراز هویت چندعامله
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mfa_config', verbose_name='کاربر')
    secret = models.CharField(max_length=255, verbose_name='کلید رمزنگاری شده')
    backup_codes = models.JSONField(default=list, verbose_name='کدهای پشتیبان')
    is_active = models.BooleanField(default=False, verbose_name='فعال')
    last_used = models.DateTimeField(null=True, blank=True, verbose_name='آخرین استفاده')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')
    
    class Meta:
        verbose_name = 'تنظیمات MFA'
        verbose_name_plural = 'تنظیمات MFA'
        
    def __str__(self):
        return f"MFA Config for {self.user}"


class Role(models.Model):
    """
    نقش‌های سیستم
    """
    ROLE_NAMES = [
        ('patient', 'بیمار'),
        ('doctor', 'پزشک'),
        ('admin', 'ادمین'),
        ('nurse', 'پرستار'),
        ('staff', 'کارمند'),
    ]
    
    name = models.CharField(max_length=50, choices=ROLE_NAMES, unique=True, verbose_name='نام نقش')
    permissions = models.JSONField(default=list, verbose_name='مجوزها')
    description = models.TextField(blank=True, verbose_name='توضیحات')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')
    
    class Meta:
        verbose_name = 'نقش'
        verbose_name_plural = 'نقش‌ها'
        
    def __str__(self):
        return self.get_name_display()


class TemporaryAccess(models.Model):
    """
    دسترسی‌های موقت
    """
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='temporary_accesses', verbose_name='پزشک')
    patient_id = models.UUIDField(verbose_name='شناسه بیمار')
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='granted_accesses', verbose_name='اعطا شده توسط')
    reason = models.TextField(verbose_name='دلیل دسترسی')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    granted_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان اعطا')
    expires_at = models.DateTimeField(verbose_name='زمان انقضا')
    revoked_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان لغو')
    
    class Meta:
        verbose_name = 'دسترسی موقت'
        verbose_name_plural = 'دسترسی‌های موقت'
        ordering = ['-granted_at']
        
    def __str__(self):
        return f"Access for Dr. {self.doctor} to Patient {self.patient_id}"
        
    def is_valid(self):
        """بررسی اعتبار دسترسی"""
        if not self.is_active or self.revoked_at:
            return False
        return timezone.now() < self.expires_at


class AuditLog(models.Model):
    """
    لاگ‌های ممیزی (Audit)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='زمان')
    event_type = models.CharField(max_length=100, verbose_name='نوع رویداد')
    user_id = models.UUIDField(null=True, blank=True, verbose_name='شناسه کاربر')
    resource = models.CharField(max_length=255, null=True, blank=True, verbose_name='منبع')
    action = models.CharField(max_length=100, verbose_name='عملیات')
    result = models.CharField(max_length=50, verbose_name='نتیجه')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='آدرس IP')
    user_agent = models.TextField(null=True, blank=True, verbose_name='User Agent')
    session_id = models.CharField(max_length=255, null=True, blank=True, verbose_name='شناسه نشست')
    metadata = models.JSONField(default=dict, verbose_name='اطلاعات اضافی')
    
    class Meta:
        verbose_name = 'لاگ ممیزی'
        verbose_name_plural = 'لاگ‌های ممیزی'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'event_type']),
            models.Index(fields=['user_id', '-timestamp']),
            models.Index(fields=['resource', '-timestamp']),
        ]
        
    def __str__(self):
        return f"{self.event_type} - {self.timestamp}"


class HIPAAComplianceReport(models.Model):
    """
    گزارش‌های رعایت HIPAA
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_date = models.DateField(verbose_name='تاریخ گزارش')
    compliant = models.BooleanField(default=True, verbose_name='رعایت شده')
    score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='امتیاز')
    findings = models.JSONField(default=list, verbose_name='یافته‌ها')
    recommendations = models.JSONField(default=list, verbose_name='پیشنهادات')
    administrative_score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='امتیاز اداری')
    physical_score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='امتیاز فیزیکی')
    technical_score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='امتیاز فنی')
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='تولید شده توسط')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان تولید')
    
    class Meta:
        verbose_name = 'گزارش HIPAA'
        verbose_name_plural = 'گزارش‌های HIPAA'
        ordering = ['-report_date']
        
    def __str__(self):
        return f"HIPAA Report {self.report_date} - Score: {self.score}%"


class SecurityIncident(models.Model):
    """
    حوادث امنیتی
    """
    INCIDENT_TYPES = [
        ('data_breach', 'نقض داده'),
        ('unauthorized_access', 'دسترسی غیرمجاز'),
        ('ddos_attack', 'حمله DDoS'),
        ('malware', 'بدافزار'),
        ('phishing', 'فیشینگ'),
        ('other', 'سایر'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'پایین'),
        ('medium', 'متوسط'),
        ('high', 'بالا'),
        ('critical', 'بحرانی'),
    ]
    
    STATUS_CHOICES = [
        ('detected', 'شناسایی شده'),
        ('investigating', 'در حال بررسی'),
        ('contained', 'مهار شده'),
        ('resolved', 'حل شده'),
        ('closed', 'بسته شده'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    incident_type = models.CharField(max_length=50, choices=INCIDENT_TYPES, verbose_name='نوع حادثه')
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, verbose_name='شدت')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='detected', verbose_name='وضعیت')
    details = models.JSONField(verbose_name='جزئیات')
    detected_at = models.DateTimeField(verbose_name='زمان شناسایی')
    contained_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان مهار')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان حل')
    response_plan = models.JSONField(default=dict, verbose_name='طرح پاسخ')
    affected_systems = models.JSONField(default=list, verbose_name='سیستم‌های آسیب‌دیده')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_incidents', verbose_name='مسئول رسیدگی')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ثبت')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین به‌روزرسانی')
    
    class Meta:
        verbose_name = 'حادثه امنیتی'
        verbose_name_plural = 'حوادث امنیتی'
        ordering = ['-detected_at']
        
    def __str__(self):
        return f"{self.get_incident_type_display()} - {self.get_severity_display()} - {self.detected_at}"


class MedicalFile(models.Model):
    """
    فایل‌های پزشکی رمزنگاری شده
    """
    file_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient_id = models.UUIDField(verbose_name='شناسه بیمار')
    storage_path = models.CharField(max_length=500, verbose_name='مسیر ذخیره‌سازی')
    file_type = models.CharField(max_length=50, verbose_name='نوع فایل')
    file_size = models.BigIntegerField(verbose_name='حجم فایل')
    encryption_key_id = models.CharField(max_length=255, verbose_name='شناسه کلید رمزنگاری')
    upload_metadata = models.JSONField(default=dict, verbose_name='اطلاعات آپلود')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='آپلود شده توسط')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان آپلود')
    last_accessed = models.DateTimeField(null=True, blank=True, verbose_name='آخرین دسترسی')
    access_count = models.IntegerField(default=0, verbose_name='تعداد دسترسی')
    
    class Meta:
        verbose_name = 'فایل پزشکی'
        verbose_name_plural = 'فایل‌های پزشکی'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['patient_id', '-uploaded_at']),
        ]
        
    def __str__(self):
        return f"Medical File {self.file_id} - {self.file_type}"