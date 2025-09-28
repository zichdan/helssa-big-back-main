"""
مدل‌های سیستم حفاظت از حریم خصوصی
Privacy Protection System Models
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import RegexValidator
import uuid
import json

User = get_user_model()


class DataClassification(models.Model):
    """
    طبقه‌بندی انواع داده‌ها بر اساس حساسیت
    """
    CLASSIFICATION_TYPES = [
        ('public', 'عمومی'),
        ('internal', 'داخلی'),
        ('confidential', 'محرمانه'),
        ('restricted', 'محدود'),
        ('phi', 'اطلاعات سلامت محافظت‌شده'),
        ('pii', 'اطلاعات شخصی قابل شناسایی'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    name = models.CharField(
        max_length=100,
        verbose_name='نام طبقه‌بندی'
    )
    
    classification_type = models.CharField(
        max_length=20,
        choices=CLASSIFICATION_TYPES,
        verbose_name='نوع طبقه‌بندی'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='توضیحات'
    )
    
    retention_period_days = models.PositiveIntegerField(
        default=365,
        verbose_name='مدت نگهداری (روز)',
        help_text='مدت نگهداری داده به روز'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ایجاد'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاریخ آخرین بروزرسانی'
    )
    
    class Meta:
        verbose_name = 'طبقه‌بندی داده'
        verbose_name_plural = 'طبقه‌بندی داده‌ها'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['classification_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.get_classification_type_display()}"


class DataField(models.Model):
    """
    فیلدهای داده‌ای که نیاز به حفاظت از حریم خصوصی دارند
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    field_name = models.CharField(
        max_length=100,
        verbose_name='نام فیلد',
        help_text='نام فیلد در دیتابیس یا API'
    )
    
    model_name = models.CharField(
        max_length=100,
        verbose_name='نام مدل',
        help_text='نام مدل Django که این فیلد متعلق به آن است'
    )
    
    app_name = models.CharField(
        max_length=50,
        verbose_name='نام اپلیکیشن',
        help_text='نام اپلیکیشن Django'
    )
    
    classification = models.ForeignKey(
        DataClassification,
        on_delete=models.PROTECT,
        verbose_name='طبقه‌بندی',
        related_name='fields'
    )
    
    redaction_pattern = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='الگوی حذف/پنهان‌سازی',
        help_text='regex pattern برای تشخیص و پنهان‌سازی داده'
    )
    
    replacement_text = models.CharField(
        max_length=50,
        default='[REDACTED]',
        verbose_name='متن جایگزین',
        help_text='متن جایگزین برای داده‌های پنهان شده'
    )
    
    is_encrypted = models.BooleanField(
        default=False,
        verbose_name='رمزگذاری شده',
        help_text='آیا این فیلد باید رمزگذاری شود؟'
    )
    
    encryption_algorithm = models.CharField(
        max_length=50,
        default='AES256',
        verbose_name='الگوریتم رمزگذاری',
        help_text='الگوریتم مورد استفاده برای رمزگذاری'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ایجاد'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاریخ آخرین بروزرسانی'
    )
    
    class Meta:
        verbose_name = 'فیلد داده'
        verbose_name_plural = 'فیلدهای داده'
        ordering = ['-created_at']
        unique_together = [['field_name', 'model_name', 'app_name']]
        indexes = [
            models.Index(fields=['model_name', 'app_name']),
            models.Index(fields=['classification']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.app_name}.{self.model_name}.{self.field_name}"


class DataAccessLog(models.Model):
    """
    لاگ دسترسی به داده‌های حساس
    """
    ACTION_TYPES = [
        ('read', 'خواندن'),
        ('write', 'نوشتن'),
        ('update', 'بروزرسانی'),
        ('delete', 'حذف'),
        ('export', 'خروجی گیری'),
        ('redact', 'پنهان‌سازی'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='کاربر',
        related_name='privacy_access_logs'
    )
    
    session_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='شناسه جلسه'
    )
    
    data_field = models.ForeignKey(
        DataField,
        on_delete=models.CASCADE,
        verbose_name='فیلد داده',
        related_name='access_logs'
    )
    
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_TYPES,
        verbose_name='نوع عملیات'
    )
    
    record_id = models.CharField(
        max_length=100,
        verbose_name='شناسه رکورد',
        help_text='شناسه رکورد مورد دسترسی'
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='آدرس IP'
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    
    purpose = models.CharField(
        max_length=200,
        verbose_name='هدف دسترسی',
        help_text='هدف از دسترسی به این داده'
    )
    
    was_redacted = models.BooleanField(
        default=False,
        verbose_name='پنهان‌سازی شده',
        help_text='آیا داده پنهان‌سازی شده بود؟'
    )
    
    original_value_hash = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='هش مقدار اصلی',
        help_text='هش SHA256 مقدار اصلی داده'
    )
    
    context_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='داده‌های زمینه‌ای',
        help_text='اطلاعات اضافی در مورد زمینه دسترسی'
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name='زمان دسترسی'
    )
    
    class Meta:
        verbose_name = 'لاگ دسترسی به داده'
        verbose_name_plural = 'لاگ‌های دسترسی به داده'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['data_field', 'timestamp']),
            models.Index(fields=['action_type', 'timestamp']),
            models.Index(fields=['was_redacted']),
        ]
    
    def __str__(self):
        user_str = self.user.username if self.user else "Anonymous"
        return f"{user_str} - {self.get_action_type_display()} - {self.data_field}"


class ConsentRecord(models.Model):
    """
    رکورد رضایت‌های کاربر برای استفاده از داده‌ها
    """
    CONSENT_TYPES = [
        ('data_collection', 'جمع‌آوری داده'),
        ('data_processing', 'پردازش داده'),
        ('data_sharing', 'اشتراک‌گذاری داده'),
        ('marketing', 'بازاریابی'),
        ('analytics', 'تحلیل داده'),
        ('research', 'تحقیق'),
    ]
    
    CONSENT_STATUS = [
        ('granted', 'اعطا شده'),
        ('denied', 'رد شده'),
        ('withdrawn', 'پس گرفته شده'),
        ('expired', 'منقضی شده'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='کاربر',
        related_name='consent_records'
    )
    
    consent_type = models.CharField(
        max_length=30,
        choices=CONSENT_TYPES,
        verbose_name='نوع رضایت'
    )
    
    status = models.CharField(
        max_length=20,
        choices=CONSENT_STATUS,
        default='granted',
        verbose_name='وضعیت'
    )
    
    purpose = models.TextField(
        verbose_name='هدف استفاده',
        help_text='توضیحی از هدف استفاده از داده'
    )
    
    data_categories = models.ManyToManyField(
        DataClassification,
        verbose_name='دسته‌بندی داده‌ها',
        related_name='consent_records',
        help_text='انواع داده‌هایی که این رضایت شامل آن‌ها می‌شود'
    )
    
    granted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='زمان اعطای رضایت'
    )
    
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان انقضا',
        help_text='زمان انقضای رضایت (در صورت وجود)'
    )
    
    withdrawn_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان پس‌گیری'
    )
    
    withdrawal_reason = models.TextField(
        blank=True,
        verbose_name='دلیل پس‌گیری'
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='آدرس IP هنگام اعطا'
    )
    
    user_agent = models.TextField(
        blank=True,
        default='',
        verbose_name='User Agent هنگام اعطا'
    )
    
    legal_basis = models.CharField(
        max_length=200,
        verbose_name='مبنای قانونی',
        help_text='مبنای قانونی برای پردازش داده'
    )
    
    version = models.CharField(
        max_length=20,
        default='1.0',
        verbose_name='نسخه سیاست حریم خصوصی'
    )
    
    class Meta:
        verbose_name = 'رکورد رضایت'
        verbose_name_plural = 'رکوردهای رضایت'
        ordering = ['-granted_at']
        unique_together = [['user', 'consent_type', 'version']]
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['consent_type', 'status']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_consent_type_display()} - {self.get_status_display()}"
    
    @property
    def is_active(self) -> bool:
        """
        بررسی اینکه آیا رضایت فعال است یا خیر
        """
        if self.status != 'granted':
            return False
        
        if self.expires_at and timezone.now() > self.expires_at:
            return False
            
        return True


class DataRetentionPolicy(models.Model):
    """
    سیاست‌های نگهداری داده
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    name = models.CharField(
        max_length=100,
        verbose_name='نام سیاست'
    )
    
    classification = models.ForeignKey(
        DataClassification,
        on_delete=models.CASCADE,
        verbose_name='طبقه‌بندی داده',
        related_name='retention_policies'
    )
    
    retention_period_days = models.PositiveIntegerField(
        verbose_name='مدت نگهداری (روز)'
    )
    
    auto_delete = models.BooleanField(
        default=False,
        verbose_name='حذف خودکار',
        help_text='آیا داده‌ها بعد از انقضا خودکار حذف شوند؟'
    )
    
    archive_before_delete = models.BooleanField(
        default=True,
        verbose_name='آرشیو قبل از حذف',
        help_text='آیا داده‌ها قبل از حذف آرشیو شوند؟'
    )
    
    notification_days_before = models.PositiveIntegerField(
        default=30,
        verbose_name='اطلاع‌رسانی (روز قبل)',
        help_text='چند روز قبل از انقضا اطلاع‌رسانی شود'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='توضیحات'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ایجاد'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاریخ آخرین بروزرسانی'
    )
    
    class Meta:
        verbose_name = 'سیاست نگهداری داده'
        verbose_name_plural = 'سیاست‌های نگهداری داده'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['classification']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.retention_period_days} روز"