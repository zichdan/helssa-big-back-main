"""
مدل‌های اپلیکیشن Checklist

این اپ برای مدیریت چک‌لیست‌های پویا در طول ویزیت‌ها و ایجاد هشدارهای real-time استفاده می‌شود.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class BaseModel(models.Model):
    """
    مدل پایه برای همه مدل‌ها
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name='ایجادکننده'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        verbose_name='به‌روزرسانی‌کننده'
    )

    class Meta:
        abstract = True


class ChecklistCatalog(BaseModel):
    """
    کاتالوگ آیتم‌های چک‌لیست
    هر آیتم یک مورد قابل بررسی در طول ویزیت است
    """
    CATEGORY_CHOICES = [
        ('history', 'تاریخچه پزشکی'),
        ('physical_exam', 'معاینه فیزیکی'),
        ('diagnosis', 'تشخیص'),
        ('treatment', 'درمان'),
        ('education', 'آموزش بیمار'),
        ('follow_up', 'پیگیری'),
        ('red_flags', 'علائم خطر'),
        ('other', 'سایر')
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'پایین'),
        ('medium', 'متوسط'),
        ('high', 'بالا'),
        ('critical', 'بحرانی')
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان'
    )
    description = models.TextField(
        blank=True,
        verbose_name='توضیحات'
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='other',
        verbose_name='دسته‌بندی'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='اولویت'
    )
    keywords = ArrayField(
        models.CharField(max_length=100),
        blank=True,
        default=list,
        verbose_name='کلمات کلیدی',
        help_text='کلماتی که برای تشخیص این آیتم در متن استفاده می‌شوند'
    )
    question_template = models.TextField(
        blank=True,
        verbose_name='قالب سوال',
        help_text='سوالی که در صورت عدم پوشش این آیتم از پزشک پرسیده می‌شود'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    specialty = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='تخصص مرتبط'
    )
    conditions = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='شرایط اعمال',
        help_text='شرایطی که باید برقرار باشد تا این آیتم بررسی شود'
    )
    
    class Meta:
        verbose_name = 'آیتم کاتالوگ چک‌لیست'
        verbose_name_plural = 'آیتم‌های کاتالوگ چک‌لیست'
        ordering = ['-priority', 'category', 'title']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['priority', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"


class ChecklistTemplate(BaseModel):
    """
    قالب چک‌لیست برای استفاده در موارد خاص
    """
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='نام قالب'
    )
    description = models.TextField(
        blank=True,
        verbose_name='توضیحات'
    )
    catalog_items = models.ManyToManyField(
        ChecklistCatalog,
        related_name='templates',
        verbose_name='آیتم‌های کاتالوگ'
    )
    specialty = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='تخصص'
    )
    chief_complaint = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='شکایت اصلی مرتبط'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    
    class Meta:
        verbose_name = 'قالب چک‌لیست'
        verbose_name_plural = 'قالب‌های چک‌لیست'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ChecklistEval(BaseModel):
    """
    ارزیابی چک‌لیست برای یک encounter
    """
    STATUS_CHOICES = [
        ('covered', 'پوشش داده شده'),
        ('partial', 'پوشش جزئی'),
        ('missing', 'پوشش داده نشده'),
        ('unclear', 'نامشخص'),
        ('not_applicable', 'قابل اعمال نیست')
    ]
    
    encounter = models.ForeignKey(
        'encounters.Encounter',  # فرض بر وجود اپ encounters
        on_delete=models.CASCADE,
        related_name='checklist_evaluations',
        verbose_name='ویزیت'
    )
    catalog_item = models.ForeignKey(
        ChecklistCatalog,
        on_delete=models.CASCADE,
        related_name='evaluations',
        verbose_name='آیتم کاتالوگ'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='unclear',
        verbose_name='وضعیت'
    )
    confidence_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name='امتیاز اطمینان'
    )
    evidence_text = models.TextField(
        blank=True,
        verbose_name='متن شاهد',
        help_text='بخشی از متن که این آیتم را پوشش می‌دهد'
    )
    anchor_positions = models.JSONField(
        default=list,
        blank=True,
        verbose_name='موقعیت‌های متن',
        help_text='موقعیت‌های شروع و پایان متن شاهد'
    )
    generated_question = models.TextField(
        blank=True,
        verbose_name='سوال تولید شده'
    )
    doctor_response = models.TextField(
        blank=True,
        verbose_name='پاسخ پزشک'
    )
    is_acknowledged = models.BooleanField(
        default=False,
        verbose_name='تایید شده'
    )
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان تایید'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='یادداشت‌ها'
    )
    
    class Meta:
        verbose_name = 'ارزیابی چک‌لیست'
        verbose_name_plural = 'ارزیابی‌های چک‌لیست'
        unique_together = ['encounter', 'catalog_item']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['encounter', 'status']),
            models.Index(fields=['status', 'confidence_score']),
        ]
    
    def __str__(self):
        return f"{self.catalog_item.title} - {self.encounter} ({self.get_status_display()})"


class ChecklistAlert(BaseModel):
    """
    هشدارهای real-time برای آیتم‌های چک‌لیست
    """
    ALERT_TYPE_CHOICES = [
        ('missing_critical', 'آیتم بحرانی پوشش داده نشده'),
        ('low_confidence', 'اطمینان پایین'),
        ('red_flag', 'علامت خطر'),
        ('incomplete', 'چک‌لیست ناقص'),
        ('reminder', 'یادآوری')
    ]
    
    encounter = models.ForeignKey(
        'encounters.Encounter',
        on_delete=models.CASCADE,
        related_name='checklist_alerts',
        verbose_name='ویزیت'
    )
    evaluation = models.ForeignKey(
        ChecklistEval,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts',
        verbose_name='ارزیابی مرتبط'
    )
    alert_type = models.CharField(
        max_length=20,
        choices=ALERT_TYPE_CHOICES,
        verbose_name='نوع هشدار'
    )
    message = models.TextField(
        verbose_name='پیام هشدار'
    )
    is_dismissed = models.BooleanField(
        default=False,
        verbose_name='رد شده'
    )
    dismissed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان رد کردن'
    )
    dismissed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dismissed_alerts',
        verbose_name='رد شده توسط'
    )
    
    class Meta:
        verbose_name = 'هشدار چک‌لیست'
        verbose_name_plural = 'هشدارهای چک‌لیست'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['encounter', 'is_dismissed']),
            models.Index(fields=['alert_type', 'is_dismissed']),
        ]
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.encounter}"