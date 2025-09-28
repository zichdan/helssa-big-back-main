"""
مدل‌های پایگاه داده برای API Gateway
"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils import timezone


class UnifiedUser(AbstractUser):
    """
    مدل کاربر یکپارچه برای تمام نوع کاربران
    
    این مدل base کلاس برای تمام کاربران سیستم است
    """
    
    USER_TYPES = [
        ('patient', 'بیمار'),
        ('doctor', 'پزشک'),
        ('admin', 'مدیر'),
        ('staff', 'کارمند'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='شناسه یکتا'
    )
    
    phone_validator = RegexValidator(
        regex=r'^09\d{9}$',
        message='شماره موبایل باید به فرمت 09123456789 باشد'
    )
    
    username = models.CharField(
        max_length=11,
        unique=True,
        validators=[phone_validator],
        verbose_name='شماره موبایل'
    )
    
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPES,
        default='patient',
        verbose_name='نوع کاربر'
    )
    
    is_phone_verified = models.BooleanField(
        default=False,
        verbose_name='تأیید شماره موبایل'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ایجاد'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاریخ بروزرسانی'
    )
    
    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['user_type']),
            models.Index(fields=['is_phone_verified']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    def get_full_name(self):
        """دریافت نام کامل کاربر"""
        return f"{self.first_name} {self.last_name}".strip() or self.username


class APIRequest(models.Model):
    """
    مدل لاگ درخواست‌های API
    
    تمام درخواست‌های ورودی به API Gateway در این مدل ثبت می‌شوند
    """
    
    REQUEST_METHODS = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('processing', 'در حال پردازش'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق'),
        ('cancelled', 'لغو شده'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='شناسه درخواست'
    )
    
    user = models.ForeignKey(
        UnifiedUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='api_requests',
        verbose_name='کاربر'
    )
    
    method = models.CharField(
        max_length=10,
        choices=REQUEST_METHODS,
        verbose_name='روش درخواست'
    )
    
    path = models.CharField(
        max_length=500,
        verbose_name='مسیر درخواست'
    )
    
    ip_address = models.GenericIPAddressField(
        verbose_name='آدرس IP'
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    
    request_headers = models.JSONField(
        default=dict,
        verbose_name='Headers درخواست'
    )
    
    request_body = models.JSONField(
        default=dict,
        verbose_name='بدنه درخواست'
    )
    
    response_status = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='کد وضعیت پاسخ'
    )
    
    response_body = models.JSONField(
        default=dict,
        verbose_name='بدنه پاسخ'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='وضعیت'
    )
    
    processing_time = models.FloatField(
        null=True,
        blank=True,
        verbose_name='زمان پردازش (ثانیه)'
    )
    
    processor_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='نوع پردازش‌کننده'
    )
    
    error_message = models.TextField(
        blank=True,
        verbose_name='پیام خطا'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='زمان دریافت'
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان تکمیل'
    )
    
    class Meta:
        verbose_name = 'درخواست API'
        verbose_name_plural = 'درخواست‌های API'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['method', 'path']),
            models.Index(fields=['ip_address', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.method} {self.path} - {self.status}"
    
    def mark_completed(self, response_status: int, response_body: dict = None):
        """نشان‌گذاری درخواست به عنوان تکمیل شده"""
        self.status = 'completed'
        self.response_status = response_status
        self.response_body = response_body or {}
        self.completed_at = timezone.now()
        
        if self.created_at:
            self.processing_time = (self.completed_at - self.created_at).total_seconds()
        
        self.save()
    
    def mark_failed(self, error_message: str, response_status: int = 500):
        """نشان‌گذاری درخواست به عنوان ناموفق"""
        self.status = 'failed'
        self.error_message = error_message
        self.response_status = response_status
        self.completed_at = timezone.now()
        
        if self.created_at:
            self.processing_time = (self.completed_at - self.created_at).total_seconds()
        
        self.save()


class Workflow(models.Model):
    """
    مدل workflow برای ردگیری فرآیندهای پیچیده
    
    این مدل برای ذخیره و مدیریت workflow های چندمرحله‌ای استفاده می‌شود
    """
    
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('running', 'در حال اجرا'),
        ('paused', 'متوقف شده'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق'),
        ('cancelled', 'لغو شده'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='شناسه workflow'
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name='نام workflow'
    )
    
    user = models.ForeignKey(
        UnifiedUser,
        on_delete=models.CASCADE,
        related_name='workflows',
        verbose_name='کاربر'
    )
    
    api_request = models.ForeignKey(
        APIRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workflows',
        verbose_name='درخواست API'
    )
    
    config = models.JSONField(
        verbose_name='تنظیمات workflow'
    )
    
    context = models.JSONField(
        default=dict,
        verbose_name='context اجرا'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='وضعیت'
    )
    
    current_step = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='مرحله فعلی'
    )
    
    completed_steps = models.JSONField(
        default=list,
        verbose_name='مراحل تکمیل شده'
    )
    
    results = models.JSONField(
        default=dict,
        verbose_name='نتایج'
    )
    
    error_message = models.TextField(
        blank=True,
        verbose_name='پیام خطا'
    )
    
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان شروع'
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان تکمیل'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='زمان ایجاد'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='زمان بروزرسانی'
    )
    
    class Meta:
        verbose_name = 'فرآیند کاری'
        verbose_name_plural = 'فرآیندهای کاری'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['api_request']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.status}"
    
    def start(self):
        """شروع workflow"""
        self.status = 'running'
        self.started_at = timezone.now()
        self.save()
    
    def complete(self, results: dict = None):
        """تکمیل workflow"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if results:
            self.results = results
        self.save()
    
    def fail(self, error_message: str):
        """نشان‌گذاری workflow به عنوان ناموفق"""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save()
    
    def get_duration(self):
        """محاسبه مدت زمان اجرا"""
        if self.started_at:
            end_time = self.completed_at or timezone.now()
            return (end_time - self.started_at).total_seconds()
        return 0


class RateLimitTracker(models.Model):
    """
    مدل ردگیری محدودیت نرخ درخواست
    
    برای کنترل تعداد درخواست‌های هر کاربر استفاده می‌شود
    """
    
    user = models.ForeignKey(
        UnifiedUser,
        on_delete=models.CASCADE,
        related_name='rate_limits',
        verbose_name='کاربر'
    )
    
    ip_address = models.GenericIPAddressField(
        verbose_name='آدرس IP'
    )
    
    endpoint = models.CharField(
        max_length=500,
        verbose_name='نقطه پایانی'
    )
    
    request_count = models.IntegerField(
        default=1,
        verbose_name='تعداد درخواست'
    )
    
    window_start = models.DateTimeField(
        auto_now_add=True,
        verbose_name='شروع بازه زمانی'
    )
    
    last_request = models.DateTimeField(
        auto_now=True,
        verbose_name='آخرین درخواست'
    )
    
    class Meta:
        verbose_name = 'ردگیر محدودیت نرخ'
        verbose_name_plural = 'ردگیرهای محدودیت نرخ'
        unique_together = ['user', 'ip_address', 'endpoint', 'window_start']
        indexes = [
            models.Index(fields=['user', 'endpoint', 'window_start']),
            models.Index(fields=['ip_address', 'endpoint', 'window_start']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.endpoint} ({self.request_count})"