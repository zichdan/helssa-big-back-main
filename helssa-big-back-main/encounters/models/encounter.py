from django.db import models
from django.utils import timezone
import uuid
from datetime import timedelta


class Encounter(models.Model):
    """مدل ملاقات پزشکی"""
    
    ENCOUNTER_TYPES = [
        ('in_person', 'حضوری'),
        ('video', 'ویدیویی'),
        ('audio', 'صوتی'),
        ('chat', 'چت'),
        ('follow_up', 'پیگیری'),
    ]
    
    ENCOUNTER_STATUS = [
        ('scheduled', 'زمان‌بندی شده'),
        ('confirmed', 'تایید شده'),
        ('in_progress', 'در حال انجام'),
        ('completed', 'تکمیل شده'),
        ('cancelled', 'لغو شده'),
        ('no_show', 'عدم حضور'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    
    # شرکت‌کنندگان
    patient = models.ForeignKey(
        'unified_auth.UnifiedUser',
        on_delete=models.PROTECT,
        related_name='patient_encounters',
        verbose_name='بیمار'
    )
    doctor = models.ForeignKey(
        'unified_auth.UnifiedUser',
        on_delete=models.PROTECT,
        related_name='doctor_encounters',
        verbose_name='پزشک'
    )
    
    # مشخصات ویزیت
    type = models.CharField(
        max_length=20,
        choices=ENCOUNTER_TYPES,
        verbose_name='نوع ویزیت'
    )
    status = models.CharField(
        max_length=20,
        choices=ENCOUNTER_STATUS,
        default='scheduled',
        verbose_name='وضعیت'
    )
    chief_complaint = models.TextField(
        verbose_name='شکایت اصلی',
        help_text="شکایت اصلی بیمار"
    )
    
    # زمان‌بندی
    scheduled_at = models.DateTimeField(verbose_name='زمان برنامه‌ریزی شده')
    duration_minutes = models.IntegerField(
        default=30,
        verbose_name='مدت زمان (دقیقه)'
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان شروع'
    )
    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان پایان'
    )
    
    # لینک‌ها و دسترسی
    video_room_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='شناسه اتاق ویدیو',
        help_text="ID اتاق ویدیو"
    )
    patient_join_url = models.URLField(
        null=True,
        blank=True,
        verbose_name='لینک ورود بیمار'
    )
    doctor_join_url = models.URLField(
        null=True,
        blank=True,
        verbose_name='لینک ورود پزشک'
    )
    
    # ضبط
    is_recording_enabled = models.BooleanField(
        default=True,
        verbose_name='ضبط فعال است'
    )
    recording_consent = models.BooleanField(
        default=False,
        verbose_name='رضایت ضبط'
    )
    recording_url = models.URLField(
        null=True,
        blank=True,
        verbose_name='آدرس فایل ضبط شده'
    )
    
    # پرداخت
    fee_amount = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        verbose_name='هزینه ویزیت',
        help_text="هزینه ویزیت به ریال"
    )
    is_paid = models.BooleanField(
        default=False,
        verbose_name='پرداخت شده'
    )
    payment_transaction = models.ForeignKey(
        'unified_billing.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='تراکنش پرداخت'
    )
    
    # یادداشت‌ها
    patient_notes = models.TextField(
        null=True,
        blank=True,
        verbose_name='یادداشت بیمار',
        help_text="یادداشت‌های بیمار قبل از ویزیت"
    )
    doctor_notes = models.TextField(
        null=True,
        blank=True,
        verbose_name='یادداشت پزشک',
        help_text="یادداشت‌های پزشک"
    )
    
    # امنیت
    access_code = models.CharField(
        max_length=6,
        null=True,
        blank=True,
        verbose_name='کد دسترسی',
        help_text="کد دسترسی برای بیمار"
    )
    encryption_key = models.CharField(
        max_length=255,
        verbose_name='کلید رمزنگاری',
        help_text="کلید رمزنگاری فایل‌ها"
    )
    
    # metadata
    metadata = models.JSONField(
        default=dict,
        verbose_name='اطلاعات اضافی'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ایجاد'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاریخ به‌روزرسانی'
    )
    
    class Meta:
        db_table = 'encounters'
        verbose_name = 'ملاقات'
        verbose_name_plural = 'ملاقات‌ها'
        indexes = [
            models.Index(fields=['patient', 'status', 'scheduled_at']),
            models.Index(fields=['doctor', 'status', 'scheduled_at']),
            models.Index(fields=['scheduled_at']),
            models.Index(fields=['video_room_id']),
        ]
        ordering = ['-scheduled_at']
        
    def __str__(self):
        return f"ملاقات {self.patient} با دکتر {self.doctor} - {self.scheduled_at}"
        
    @property
    def actual_duration(self) -> timedelta:
        """مدت زمان واقعی ویزیت"""
        if self.started_at and self.ended_at:
            return self.ended_at - self.started_at
        return timedelta(minutes=self.duration_minutes)
        
    @property
    def is_upcoming(self) -> bool:
        """آیا ویزیت در آینده است"""
        return self.scheduled_at > timezone.now() and self.status == 'scheduled'
        
    @property
    def can_start(self) -> bool:
        """آیا می‌توان ویزیت را شروع کرد"""
        now = timezone.now()
        # اجازه شروع از 10 دقیقه قبل
        start_window = self.scheduled_at - timedelta(minutes=10)
        return now >= start_window and self.status == 'confirmed'
        
    @property
    def is_active(self) -> bool:
        """آیا ویزیت در حال انجام است"""
        return self.status == 'in_progress'
        
    def save(self, *args, **kwargs):
        """override save برای تولید کلید رمزنگاری"""
        if not self.encryption_key:
            from ..utils.encryption import generate_encryption_key
            self.encryption_key = generate_encryption_key()
            
        super().save(*args, **kwargs)