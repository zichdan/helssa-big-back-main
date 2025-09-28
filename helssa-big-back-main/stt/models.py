"""
مدل‌های مربوط به تبدیل گفتار به متن
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from app_standards.models.base_models import BaseModel
import uuid

User = get_user_model()


class STTTask(BaseModel):
    """
    وظیفه تبدیل گفتار به متن
    
    ذخیره اطلاعات مربوط به درخواست‌های تبدیل گفتار به متن
    """
    
    # شناسه یکتا
    task_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name='شناسه وظیفه'
    )
    
    # کاربر درخواست دهنده
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='stt_tasks',
        verbose_name='کاربر'
    )
    
    # نوع کاربر (دکتر یا بیمار)
    user_type = models.CharField(
        max_length=20,
        choices=[
            ('doctor', 'دکتر'),
            ('patient', 'بیمار'),
        ],
        verbose_name='نوع کاربر'
    )
    
    # فایل صوتی
    audio_file = models.FileField(
        upload_to='stt/audio/%Y/%m/%d/',
        verbose_name='فایل صوتی'
    )
    
    # اطلاعات فایل
    file_size = models.PositiveIntegerField(
        verbose_name='حجم فایل (بایت)',
        validators=[MaxValueValidator(52428800)]  # حداکثر 50MB
    )
    
    duration = models.FloatField(
        verbose_name='مدت زمان (ثانیه)',
        null=True,
        blank=True,
        validators=[MinValueValidator(0.1), MaxValueValidator(600)]  # حداکثر 10 دقیقه
    )
    
    # نتیجه تبدیل
    transcription = models.TextField(
        verbose_name='متن تبدیل شده',
        blank=True,
        default=''
    )
    
    # زبان
    language = models.CharField(
        max_length=10,
        default='fa',
        choices=[
            ('fa', 'فارسی'),
            ('en', 'انگلیسی'),
            ('auto', 'تشخیص خودکار'),
        ],
        verbose_name='زبان'
    )
    
    # وضعیت
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('processing', 'در حال پردازش'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق'),
        ('cancelled', 'لغو شده'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='وضعیت'
    )
    
    # کیفیت
    confidence_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        verbose_name='امتیاز اطمینان'
    )
    
    # مدل استفاده شده
    model_used = models.CharField(
        max_length=50,
        default='base',
        choices=[
            ('tiny', 'Tiny'),
            ('base', 'Base'),
            ('small', 'Small'),
            ('medium', 'Medium'),
            ('large', 'Large'),
        ],
        verbose_name='مدل Whisper'
    )
    
    # خطا
    error_message = models.TextField(
        blank=True,
        default='',
        verbose_name='پیام خطا'
    )
    
    # زمان‌ها
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان شروع پردازش'
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان اتمام پردازش'
    )
    
    # متادیتا
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='اطلاعات اضافی'
    )
    
    class Meta:
        verbose_name = 'وظیفه تبدیل گفتار به متن'
        verbose_name_plural = 'وظایف تبدیل گفتار به متن'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['task_id']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"STT Task {self.task_id} - {self.user} - {self.status}"
    
    @property
    def processing_time(self):
        """محاسبه زمان پردازش"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def can_cancel(self):
        """آیا می‌توان وظیفه را لغو کرد؟"""
        return self.status in ['pending', 'processing']


class STTQualityControl(BaseModel):
    """
    کنترل کیفیت تبدیل گفتار به متن
    
    ذخیره نتایج بررسی کیفیت و اصلاحات انجام شده
    """
    
    # وظیفه مرتبط
    task = models.OneToOneField(
        STTTask,
        on_delete=models.CASCADE,
        related_name='quality_control',
        verbose_name='وظیفه STT'
    )
    
    # کیفیت صدا
    audio_quality_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        verbose_name='امتیاز کیفیت صدا'
    )
    
    # نویز پس‌زمینه
    background_noise_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'کم'),
            ('medium', 'متوسط'),
            ('high', 'زیاد'),
        ],
        verbose_name='سطح نویز پس‌زمینه'
    )
    
    # وضوح گفتار
    speech_clarity = models.CharField(
        max_length=20,
        choices=[
            ('clear', 'واضح'),
            ('moderate', 'متوسط'),
            ('unclear', 'نامفهوم'),
        ],
        verbose_name='وضوح گفتار'
    )
    
    # اصطلاحات پزشکی شناسایی شده
    medical_terms_detected = models.JSONField(
        default=list,
        blank=True,
        verbose_name='اصطلاحات پزشکی'
    )
    
    # اصلاحات پیشنهادی
    suggested_corrections = models.JSONField(
        default=list,
        blank=True,
        verbose_name='اصلاحات پیشنهادی'
    )
    
    # متن نهایی بعد از کنترل کیفیت
    corrected_transcription = models.TextField(
        blank=True,
        default='',
        verbose_name='متن اصلاح شده'
    )
    
    # آیا نیاز به بررسی انسانی دارد؟
    needs_human_review = models.BooleanField(
        default=False,
        verbose_name='نیاز به بررسی انسانی'
    )
    
    # دلیل نیاز به بررسی
    review_reason = models.TextField(
        blank=True,
        default='',
        verbose_name='دلیل نیاز به بررسی'
    )
    
    # بررسی کننده
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stt_reviews',
        verbose_name='بررسی کننده'
    )
    
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان بررسی'
    )
    
    class Meta:
        verbose_name = 'کنترل کیفیت STT'
        verbose_name_plural = 'کنترل‌های کیفیت STT'
        ordering = ['-created_at']


class STTUsageStats(BaseModel):
    """
    آمار استفاده از سرویس تبدیل گفتار به متن
    
    ذخیره آمار روزانه استفاده کاربران
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='stt_usage_stats',
        verbose_name='کاربر'
    )
    
    date = models.DateField(
        verbose_name='تاریخ'
    )
    
    # تعداد درخواست‌ها
    total_requests = models.PositiveIntegerField(
        default=0,
        verbose_name='تعداد کل درخواست‌ها'
    )
    
    successful_requests = models.PositiveIntegerField(
        default=0,
        verbose_name='درخواست‌های موفق'
    )
    
    failed_requests = models.PositiveIntegerField(
        default=0,
        verbose_name='درخواست‌های ناموفق'
    )
    
    # مدت زمان
    total_audio_duration = models.FloatField(
        default=0,
        verbose_name='مجموع مدت صوت (ثانیه)'
    )
    
    total_processing_time = models.FloatField(
        default=0,
        verbose_name='مجموع زمان پردازش (ثانیه)'
    )
    
    # کیفیت
    average_confidence_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        verbose_name='میانگین امتیاز اطمینان'
    )
    
    class Meta:
        verbose_name = 'آمار استفاده STT'
        verbose_name_plural = 'آمارهای استفاده STT'
        ordering = ['-date']
        unique_together = [['user', 'date']]
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"STT Stats - {self.user} - {self.date}"