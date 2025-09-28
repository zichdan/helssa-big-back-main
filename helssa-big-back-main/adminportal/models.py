"""
مدل‌های پنل ادمین
AdminPortal Models for Internal Support and Operator Tools
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

# Import BaseModel from app standards
# بعداً باید در settings.py به agent/app_standards اضافه شود
try:
    from agent.app_standards.models.base_models import BaseModel, StatusModel, AuditLogModel
except ImportError:
    # Fallback if not available
    from django.db import models
    
    class BaseModel(models.Model):
        """مدل پایه موقت"""
        id = models.UUIDField(
            primary_key=True,
            default=uuid.uuid4,
            editable=False,
            verbose_name='شناسه یکتا'
        )
        created_at = models.DateTimeField(
            auto_now_add=True,
            verbose_name='تاریخ ایجاد'
        )
        updated_at = models.DateTimeField(
            auto_now=True,
            verbose_name='تاریخ آخرین تغییر'
        )
        is_active = models.BooleanField(
            default=True,
            verbose_name='فعال'
        )
        
        class Meta:
            abstract = True

User = get_user_model()


class AdminUser(BaseModel):
    """
    مدل کاربران ادمین
    ایجاد و مدیریت کاربران ادمین سیستم
    """
    ROLE_CHOICES = [
        ('super_admin', 'ادمین کل'),
        ('support_admin', 'ادمین پشتیبانی'),
        ('content_admin', 'ادمین محتوا'),
        ('financial_admin', 'ادمین مالی'),
        ('technical_admin', 'ادمین فنی'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='admin_profile',
        verbose_name='کاربر'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='support_admin',
        verbose_name='نقش'
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='بخش'
    )
    permissions = models.JSONField(
        default=list,
        verbose_name='دسترسی‌های خاص',
        help_text='لیست دسترسی‌های اضافی'
    )
    last_activity = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='آخرین فعالیت'
    )
    
    class Meta:
        verbose_name = 'کاربر ادمین'
        verbose_name_plural = 'کاربران ادمین'
        indexes = [
            models.Index(fields=['role', '-last_activity']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_role_display()}"
    
    def update_last_activity(self):
        """بروزرسانی زمان آخرین فعالیت"""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])


class SystemOperation(BaseModel):
    """
    عملیات سیستمی
    ثبت و پیگیری عملیات مهم سیستم
    """
    OPERATION_CHOICES = [
        ('user_management', 'مدیریت کاربران'),
        ('data_export', 'صادرات داده'),
        ('system_maintenance', 'نگهداری سیستم'),
        ('backup_restore', 'پشتیبان‌گیری/بازیابی'),
        ('security_check', 'بررسی امنیتی'),
        ('performance_analysis', 'تحلیل عملکرد'),
        ('content_moderation', 'نظارت محتوا'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('in_progress', 'در حال اجرا'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق'),
        ('cancelled', 'لغو شده'),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان'
    )
    operation_type = models.CharField(
        max_length=30,
        choices=OPERATION_CHOICES,
        verbose_name='نوع عملیات'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='وضعیت'
    )
    description = models.TextField(
        blank=True,
        verbose_name='توضیحات'
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان شروع'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان پایان'
    )
    result = models.JSONField(
        default=dict,
        verbose_name='نتیجه',
        help_text='جزئیات نتیجه عملیات'
    )
    operator = models.ForeignKey(
        AdminUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='operations',
        verbose_name='اپراتور'
    )
    priority = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='اولویت',
        help_text='1=کم، 5=بحرانی'
    )
    
    class Meta:
        verbose_name = 'عملیات سیستمی'
        verbose_name_plural = 'عملیات سیستمی'
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['status', '-priority']),
            models.Index(fields=['operation_type', '-created_at']),
            models.Index(fields=['operator', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    def start_operation(self, operator=None):
        """شروع عملیات"""
        self.status = 'in_progress'
        self.started_at = timezone.now()
        if operator:
            self.operator = operator
        self.save(update_fields=['status', 'started_at', 'operator', 'updated_at'])
    
    def complete_operation(self, result_data=None):
        """تکمیل عملیات"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if result_data:
            self.result = result_data
        self.save(update_fields=['status', 'completed_at', 'result', 'updated_at'])
    
    def fail_operation(self, error_data=None):
        """ناموفق بودن عملیات"""
        self.status = 'failed'
        self.completed_at = timezone.now()
        if error_data:
            self.result = {'error': error_data}
        self.save(update_fields=['status', 'completed_at', 'result', 'updated_at'])


class SupportTicket(BaseModel):
    """
    تیکت‌های پشتیبانی
    مدیریت درخواست‌های پشتیبانی کاربران
    """
    PRIORITY_CHOICES = [
        ('low', 'کم'),
        ('normal', 'عادی'),
        ('high', 'بالا'),
        ('urgent', 'فوری'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'باز'),
        ('in_progress', 'در حال بررسی'),
        ('waiting_user', 'در انتظار کاربر'),
        ('resolved', 'حل شده'),
        ('closed', 'بسته شده'),
    ]
    
    CATEGORY_CHOICES = [
        ('technical', 'فنی'),
        ('billing', 'مالی'),
        ('account', 'حساب کاربری'),
        ('medical', 'پزشکی'),
        ('general', 'عمومی'),
    ]
    
    ticket_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='شماره تیکت'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='support_tickets',
        verbose_name='کاربر'
    )
    subject = models.CharField(
        max_length=200,
        verbose_name='موضوع'
    )
    description = models.TextField(
        verbose_name='توضیحات'
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='general',
        verbose_name='دسته‌بندی'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal',
        verbose_name='اولویت'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        verbose_name='وضعیت'
    )
    assigned_to = models.ForeignKey(
        AdminUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets',
        verbose_name='تخصیص یافته به'
    )
    resolution = models.TextField(
        blank=True,
        verbose_name='راه‌حل'
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان حل'
    )
    
    class Meta:
        verbose_name = 'تیکت پشتیبانی'
        verbose_name_plural = 'تیکت‌های پشتیبانی'
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"#{self.ticket_number} - {self.subject}"
    
    def save(self, *args, **kwargs):
        if not self.ticket_number:
            # تولید شماره تیکت خودکار
            last_ticket = SupportTicket.objects.order_by('-id').first()
            if last_ticket and last_ticket.ticket_number:
                last_num = int(last_ticket.ticket_number.split('-')[1])
                self.ticket_number = f"TK-{last_num + 1:06d}"
            else:
                self.ticket_number = "TK-000001"
        super().save(*args, **kwargs)
    
    def assign_to_admin(self, admin_user):
        """تخصیص تیکت به ادمین"""
        self.assigned_to = admin_user
        self.status = 'in_progress'
        self.save(update_fields=['assigned_to', 'status', 'updated_at'])
    
    def resolve_ticket(self, resolution, admin_user=None):
        """حل تیکت"""
        self.resolution = resolution
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        if admin_user:
            self.assigned_to = admin_user
        self.save(update_fields=['resolution', 'status', 'resolved_at', 'assigned_to', 'updated_at'])


class SystemMetrics(BaseModel):
    """
    متریک‌های سیستم
    ذخیره و پیگیری شاخص‌های عملکرد سیستم
    """
    METRIC_TYPES = [
        ('performance', 'عملکرد'),
        ('usage', 'استفاده'),
        ('error', 'خطا'),
        ('security', 'امنیت'),
        ('business', 'کسب‌وکار'),
    ]
    
    metric_name = models.CharField(
        max_length=100,
        verbose_name='نام متریک'
    )
    metric_type = models.CharField(
        max_length=20,
        choices=METRIC_TYPES,
        verbose_name='نوع متریک'
    )
    value = models.FloatField(
        verbose_name='مقدار'
    )
    unit = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='واحد'
    )
    metadata = models.JSONField(
        default=dict,
        verbose_name='متادیتا',
        help_text='اطلاعات اضافی متریک'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name='زمان ثبت'
    )
    
    class Meta:
        verbose_name = 'متریک سیستم'
        verbose_name_plural = 'متریک‌های سیستم'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['metric_name', '-timestamp']),
            models.Index(fields=['metric_type', '-timestamp']),
        ]
        unique_together = ['metric_name', 'timestamp']
    
    def __str__(self):
        return f"{self.metric_name}: {self.value} {self.unit}"


class AdminAuditLog(AuditLogModel if 'AuditLogModel' in locals() else BaseModel):
    """
    لاگ حسابرسی ادمین
    ثبت تمام عملیات انجام شده توسط ادمین‌ها
    """
    admin_user = models.ForeignKey(
        AdminUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        verbose_name='کاربر ادمین'
    )
    resource_type = models.CharField(
        max_length=100,
        verbose_name='نوع منبع'
    )
    resource_id = models.CharField(
        max_length=255,
        verbose_name='شناسه منبع'
    )
    action_performed = models.CharField(
        max_length=100,
        verbose_name='عملیات انجام شده'
    )
    old_values = models.JSONField(
        default=dict,
        verbose_name='مقادیر قبلی'
    )
    new_values = models.JSONField(
        default=dict,
        verbose_name='مقادیر جدید'
    )
    reason = models.TextField(
        blank=True,
        verbose_name='دلیل تغییر'
    )
    
    class Meta:
        verbose_name = 'لاگ حسابرسی ادمین'
        verbose_name_plural = 'لاگ‌های حسابرسی ادمین'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['admin_user', '-created_at']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['action_performed', '-created_at']),
        ]
    
    def __str__(self):
        admin_name = self.admin_user.user.get_full_name() if self.admin_user else 'نامشخص'
        return f"{admin_name} - {self.action_performed} - {self.resource_type}"


class AdminSession(BaseModel):
    """
    نشست‌های ادمین
    مدیریت و پیگیری نشست‌های کاربران ادمین
    """
    admin_user = models.ForeignKey(
        AdminUser,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name='کاربر ادمین'
    )
    session_key = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='کلید نشست'
    )
    ip_address = models.GenericIPAddressField(
        verbose_name='آدرس IP'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    location = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='موقعیت جغرافیایی'
    )
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='شروع نشست'
    )
    last_activity = models.DateTimeField(
        auto_now=True,
        verbose_name='آخرین فعالیت'
    )
    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='پایان نشست'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    
    class Meta:
        verbose_name = 'نشست ادمین'
        verbose_name_plural = 'نشست‌های ادمین'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['admin_user', '-started_at']),
            models.Index(fields=['is_active', '-last_activity']),
        ]
    
    def __str__(self):
        admin_name = self.admin_user.user.get_full_name() if self.admin_user else 'نامشخص'
        return f"{admin_name} - {self.ip_address} - {self.started_at}"
    
    def end_session(self):
        """پایان نشست"""
        self.ended_at = timezone.now()
        self.is_active = False
        self.save(update_fields=['ended_at', 'is_active'])
    
    @property
    def duration(self):
        """مدت زمان نشست"""
        end_time = self.ended_at or timezone.now()
        return end_time - self.started_at