from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils import timezone
import uuid


class FHIRResource(models.Model):
    """
    مدل پایه برای ذخیره منابع FHIR
    
    این مدل پایه برای نگهداری انواع مختلف منابع FHIR استفاده می‌شود
    """
    RESOURCE_TYPES = [
        ('Patient', 'Patient'),
        ('Practitioner', 'Practitioner'),
        ('Encounter', 'Encounter'),
        ('Condition', 'Condition'),
        ('Observation', 'Observation'),
        ('Procedure', 'Procedure'),
        ('MedicationRequest', 'MedicationRequest'),
        ('DiagnosticReport', 'DiagnosticReport'),
        ('CarePlan', 'CarePlan'),
        ('ImagingStudy', 'ImagingStudy'),
    ]
    
    resource_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="شناسه یکتای منبع FHIR"
    )
    
    resource_type = models.CharField(
        max_length=50,
        choices=RESOURCE_TYPES,
        help_text="نوع منبع FHIR"
    )
    
    # محتوای JSON منبع FHIR
    resource_content = models.JSONField(
        help_text="محتوای کامل منبع FHIR به صورت JSON"
    )
    
    # متادیتا
    version = models.IntegerField(
        default=1,
        help_text="نسخه منبع"
    )
    
    last_updated = models.DateTimeField(
        auto_now=True,
        help_text="آخرین زمان به‌روزرسانی"
    )
    
    created = models.DateTimeField(
        auto_now_add=True,
        help_text="زمان ایجاد"
    )
    
    # ارتباط با مدل‌های داخلی
    internal_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="شناسه داخلی سیستم برای ارتباط با مدل‌های دیگر"
    )
    
    internal_model = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="نام مدل داخلی مرتبط"
    )
    
    class Meta:
        verbose_name = "FHIR Resource"
        verbose_name_plural = "FHIR Resources"
        indexes = [
            models.Index(fields=['resource_type']),
            models.Index(fields=['internal_id', 'internal_model']),
            models.Index(fields=['last_updated']),
        ]
        ordering = ['-last_updated']
    
    def __str__(self):
        return f"{self.resource_type}/{self.resource_id}"


class FHIRMapping(models.Model):
    """
    مدل برای نگهداری نقشه‌برداری بین فیلدهای داخلی و FHIR
    
    این مدل برای تعریف نحوه تبدیل داده‌های داخلی به FHIR استفاده می‌شود
    """
    mapping_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # مدل داخلی
    source_model = models.CharField(
        max_length=100,
        help_text="نام مدل Django منبع"
    )
    
    # منبع FHIR هدف
    target_resource_type = models.CharField(
        max_length=50,
        choices=FHIRResource.RESOURCE_TYPES,
        help_text="نوع منبع FHIR هدف"
    )
    
    # نقشه‌برداری فیلدها
    field_mappings = models.JSONField(
        help_text="نقشه‌برداری فیلدها به صورت JSON"
    )
    
    # تنظیمات تبدیل
    transformation_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="قوانین تبدیل و پردازش داده‌ها"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="وضعیت فعال بودن نقشه‌برداری"
    )
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "FHIR Mapping"
        verbose_name_plural = "FHIR Mappings"
        unique_together = [['source_model', 'target_resource_type']]
        ordering = ['source_model', 'target_resource_type']
    
    def __str__(self):
        return f"{self.source_model} -> {self.target_resource_type}"


class FHIRBundle(models.Model):
    """
    مدل برای ذخیره Bundle های FHIR
    
    Bundle ها برای گروه‌بندی چندین منبع FHIR استفاده می‌شوند
    """
    BUNDLE_TYPES = [
        ('document', 'Document'),
        ('message', 'Message'),
        ('transaction', 'Transaction'),
        ('transaction-response', 'Transaction Response'),
        ('batch', 'Batch'),
        ('batch-response', 'Batch Response'),
        ('history', 'History'),
        ('searchset', 'Search Results'),
        ('collection', 'Collection'),
    ]
    
    bundle_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    bundle_type = models.CharField(
        max_length=30,
        choices=BUNDLE_TYPES,
        help_text="نوع Bundle"
    )
    
    # منابع موجود در Bundle
    resources = models.ManyToManyField(
        FHIRResource,
        related_name='bundles',
        help_text="منابع FHIR موجود در این Bundle"
    )
    
    # محتوای کامل Bundle
    bundle_content = models.JSONField(
        help_text="محتوای کامل Bundle به صورت JSON"
    )
    
    total = models.IntegerField(
        default=0,
        help_text="تعداد کل منابع در Bundle"
    )
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "FHIR Bundle"
        verbose_name_plural = "FHIR Bundles"
        ordering = ['-created']
    
    def __str__(self):
        return f"Bundle/{self.bundle_id} ({self.bundle_type})"


class FHIRExportLog(models.Model):
    """
    مدل برای ثبت تاریخچه صادرات و واردات FHIR
    """
    OPERATION_TYPES = [
        ('export', 'Export'),
        ('import', 'Import'),
        ('transform', 'Transform'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'در حال انجام'),
        ('success', 'موفق'),
        ('failed', 'ناموفق'),
        ('partial', 'جزئی'),
    ]
    
    log_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    operation_type = models.CharField(
        max_length=10,
        choices=OPERATION_TYPES,
        help_text="نوع عملیات"
    )
    
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="وضعیت عملیات"
    )
    
    source_model = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="مدل منبع"
    )
    
    target_resource_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="نوع منبع FHIR هدف"
    )
    
    # جزئیات عملیات
    details = models.JSONField(
        default=dict,
        help_text="جزئیات عملیات"
    )
    
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="پیام خطا در صورت وجود"
    )
    
    # تعداد رکوردها
    records_processed = models.IntegerField(
        default=0,
        help_text="تعداد رکوردهای پردازش شده"
    )
    
    records_failed = models.IntegerField(
        default=0,
        help_text="تعداد رکوردهای ناموفق"
    )
    
    # زمان‌ها
    started_at = models.DateTimeField(
        default=timezone.now,
        help_text="زمان شروع"
    )
    
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="زمان اتمام"
    )
    
    # کاربر انجام دهنده
    performed_by = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="کاربر انجام دهنده عملیات"
    )
    
    class Meta:
        verbose_name = "FHIR Export Log"
        verbose_name_plural = "FHIR Export Logs"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.operation_type} - {self.status} ({self.started_at})"
    
    @property
    def duration(self):
        """محاسبه مدت زمان عملیات"""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None