"""
مدل‌های اپلیکیشن Doctor
Doctor Application Models
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import time, timedelta
import uuid

# استفاده از UnifiedUser
User = get_user_model()


class BaseModel(models.Model):
    """مدل پایه ساده"""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        abstract = True


class DoctorProfile(BaseModel):
    """
    پروفایل پزشک
    شامل اطلاعات کامل پزشک، تخصص، مجوزها و تنظیمات
    """
    
    # رابطه با کاربر (یک به یک)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='doctor_profile',
        verbose_name='کاربر'
    )
    
    # اطلاعات شخصی
    first_name = models.CharField(
        max_length=50,
        verbose_name='نام'
    )
    last_name = models.CharField(
        max_length=50,
        verbose_name='نام خانوادگی'
    )
    
    # اطلاعات شناسایی
    national_code = models.CharField(
        max_length=10,
        unique=True,
        validators=[RegexValidator(r'^\d{10}$', 'کد ملی باید 10 رقم باشد')],
        verbose_name='کد ملی'
    )
    medical_system_code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='کد نظام پزشکی'
    )
    
    # تخصص و رشته
    SPECIALTY_CHOICES = [
        ('general', 'پزشک عمومی'),
        ('internal', 'داخلی'),
        ('pediatrics', 'کودکان'),
        ('cardiology', 'قلب'),
        ('neurology', 'مغز و اعصاب'),
        ('psychiatry', 'روانپزشکی'),
        ('dermatology', 'پوست'),
        ('orthopedics', 'ارتوپدی'),
        ('ophthalmology', 'چشم'),
        ('ent', 'گوش، حلق و بینی'),
        ('gynecology', 'زنان'),
        ('urology', 'اورولوژی'),
        ('emergency', 'اورژانس'),
        ('anesthesiology', 'بیهوشی'),
        ('radiology', 'رادیولوژی'),
        ('pathology', 'آسیب‌شناسی'),
        ('surgery', 'جراحی عمومی'),
        ('other', 'سایر')
    ]
    specialty = models.CharField(
        max_length=20,
        choices=SPECIALTY_CHOICES,
        default='general',
        verbose_name='تخصص'
    )
    
    sub_specialty = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='فوق تخصص'
    )
    
    # اطلاعات تماس
    phone_number = models.CharField(
        max_length=11,
        validators=[RegexValidator(r'^09\d{9}$', 'شماره موبایل باید با 09 شروع شود')],
        verbose_name='شماره موبایل'
    )
    
    # آدرس مطب
    clinic_address = models.TextField(
        blank=True,
        verbose_name='آدرس مطب'
    )
    clinic_phone = models.CharField(
        max_length=11,
        blank=True,
        verbose_name='تلفن مطب'
    )
    
    # بیوگرافی و تجربیات
    biography = models.TextField(
        blank=True,
        verbose_name='بیوگرافی'
    )
    years_of_experience = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        default=0,
        verbose_name='سال‌های تجربه'
    )
    
    # تصویر پروفایل
    profile_picture = models.ImageField(
        upload_to='doctor_profiles/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='تصویر پروفایل'
    )
    
    # تنظیمات ویزیت
    visit_duration = models.IntegerField(
        default=30,
        validators=[MinValueValidator(15), MaxValueValidator(120)],
        verbose_name='مدت ویزیت (دقیقه)'
    )
    visit_price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        verbose_name='هزینه ویزیت (تومان)'
    )
    
    # تایید و وضعیت
    is_verified = models.BooleanField(
        default=False,
        verbose_name='تایید شده'
    )
    verification_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاریخ تایید'
    )
    
    # امتیاز و نظرات
    rating = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        verbose_name='امتیاز'
    )
    total_reviews = models.IntegerField(
        default=0,
        verbose_name='تعداد نظرات'
    )
    
    # تنظیمات پیشرفته
    auto_accept_appointments = models.BooleanField(
        default=False,
        verbose_name='تایید خودکار نوبت‌ها'
    )
    allow_online_visits = models.BooleanField(
        default=True,
        verbose_name='ویزیت آنلاین'
    )
    
    class Meta:
        verbose_name = 'پروفایل پزشک'
        verbose_name_plural = 'پروفایل‌های پزشکان'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['specialty', 'is_verified']),
            models.Index(fields=['national_code']),
            models.Index(fields=['medical_system_code']),
            models.Index(fields=['rating']),
        ]
    
    def __str__(self):
        return f"دکتر {self.first_name} {self.last_name} - {self.get_specialty_display()}"
    
    def get_full_name(self):
        """نام کامل پزشک"""
        return f"{self.first_name} {self.last_name}"
    
    def update_rating(self):
        """بروزرسانی امتیاز میانگین"""
        from django.db.models import Avg
        ratings = DoctorRating.objects.filter(doctor=self.user, is_active=True)
        avg_rating = ratings.aggregate(avg=Avg('rating'))['avg'] or 0.0
        self.rating = round(avg_rating, 1)
        self.total_reviews = ratings.count()
        self.save(update_fields=['rating', 'total_reviews'])


class DoctorSchedule(BaseModel):
    """
    برنامه هفتگی پزشک
    """
    
    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='doctor_schedules',
        verbose_name='پزشک'
    )
    
    WEEKDAY_CHOICES = [
        (0, 'شنبه'),
        (1, 'یکشنبه'),
        (2, 'دوشنبه'),
        (3, 'سه‌شنبه'),
        (4, 'چهارشنبه'),
        (5, 'پنج‌شنبه'),
        (6, 'جمعه'),
    ]
    
    weekday = models.IntegerField(
        choices=WEEKDAY_CHOICES,
        verbose_name='روز هفته'
    )
    
    start_time = models.TimeField(
        verbose_name='ساعت شروع'
    )
    end_time = models.TimeField(
        verbose_name='ساعت پایان'
    )
    
    # نوع ویزیت
    VISIT_TYPE_CHOICES = [
        ('in_person', 'حضوری'),
        ('online', 'آنلاین'),
        ('both', 'هر دو'),
    ]
    visit_type = models.CharField(
        max_length=10,
        choices=VISIT_TYPE_CHOICES,
        default='both',
        verbose_name='نوع ویزیت'
    )
    
    max_patients = models.IntegerField(
        default=20,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        verbose_name='حداکثر بیمار'
    )
    
    break_start = models.TimeField(
        null=True,
        blank=True,
        verbose_name='شروع استراحت'
    )
    break_end = models.TimeField(
        null=True,
        blank=True,
        verbose_name='پایان استراحت'
    )
    
    class Meta:
        verbose_name = 'برنامه کاری پزشک'
        verbose_name_plural = 'برنامه‌های کاری پزشکان'
        unique_together = ['doctor', 'weekday']
        ordering = ['weekday', 'start_time']
        indexes = [
            models.Index(fields=['doctor', 'weekday']),
        ]
    
    def __str__(self):
        return f"{self.doctor.username} - {self.get_weekday_display()}"


class DoctorShift(BaseModel):
    """
    شیفت‌های خاص پزشک (برای روزهای غیر عادی)
    """
    
    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='doctor_shifts',
        verbose_name='پزشک'
    )
    
    date = models.DateField(
        verbose_name='تاریخ'
    )
    
    start_time = models.TimeField(
        verbose_name='ساعت شروع'
    )
    end_time = models.TimeField(
        verbose_name='ساعت پایان'
    )
    
    # نوع شیفت
    SHIFT_TYPE_CHOICES = [
        ('normal', 'عادی'),
        ('emergency', 'اورژانس'),
        ('special', 'ویژه'),
        ('off', 'مرخصی'),
    ]
    shift_type = models.CharField(
        max_length=10,
        choices=SHIFT_TYPE_CHOICES,
        default='normal',
        verbose_name='نوع شیفت'
    )
    
    visit_type = models.CharField(
        max_length=10,
        choices=DoctorSchedule.VISIT_TYPE_CHOICES,
        default='both',
        verbose_name='نوع ویزیت'
    )
    
    max_patients = models.IntegerField(
        default=20,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        verbose_name='حداکثر بیمار'
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name='یادداشت‌ها'
    )
    
    class Meta:
        verbose_name = 'شیفت پزشک'
        verbose_name_plural = 'شیفت‌های پزشکان'
        unique_together = ['doctor', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['doctor', 'date']),
            models.Index(fields=['date', 'shift_type']),
        ]
    
    def __str__(self):
        return f"{self.doctor.username} - {self.date}"


class DoctorCertificate(BaseModel):
    """
    مدارک و گواهی‌نامه‌های پزشک
    """
    
    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='doctor_certificates',
        verbose_name='پزشک'
    )
    
    CERTIFICATE_TYPE_CHOICES = [
        ('medical_license', 'پروانه پزشکی'),
        ('specialty_board', 'بورد تخصصی'),
        ('fellowship', 'فلوشیپ'),
        ('university_degree', 'مدرک دانشگاهی'),
        ('workshop_certificate', 'گواهی کارگاه'),
        ('conference_certificate', 'گواهی کنفرانس'),
        ('other', 'سایر'),
    ]
    
    certificate_type = models.CharField(
        max_length=30,
        choices=CERTIFICATE_TYPE_CHOICES,
        verbose_name='نوع مدرک'
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان مدرک'
    )
    
    issuer = models.CharField(
        max_length=200,
        verbose_name='مرجع صادرکننده'
    )
    
    issue_date = models.DateField(
        verbose_name='تاریخ صدور'
    )
    
    expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاریخ انقضا'
    )
    
    certificate_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='شماره گواهی'
    )
    
    is_verified = models.BooleanField(
        default=False,
        verbose_name='تایید شده'
    )
    
    verification_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاریخ تایید'
    )
    
    verification_notes = models.TextField(
        blank=True,
        verbose_name='یادداشت‌های تایید'
    )
    
    # فایل مدرک
    file = models.FileField(
        upload_to='doctor_certificates/%Y/%m/',
        verbose_name='فایل مدرک'
    )
    
    class Meta:
        verbose_name = 'مدرک پزشک'
        verbose_name_plural = 'مدارک پزشکان'
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['doctor', 'certificate_type']),
            models.Index(fields=['is_verified']),
        ]
    
    def __str__(self):
        return f"{self.doctor.username} - {self.title}"
    
    @property
    def is_expired(self):
        """بررسی انقضای مدرک"""
        if not self.expiry_date:
            return False
        return self.expiry_date < timezone.now().date()


class DoctorRating(BaseModel):
    """
    امتیازدهی به پزشک توسط بیمار
    """
    
    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='doctor_ratings',
        verbose_name='پزشک'
    )
    
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='given_doctor_ratings',
        verbose_name='بیمار'
    )
    
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='امتیاز'
    )
    
    comment = models.TextField(
        blank=True,
        verbose_name='نظر'
    )
    
    # اطلاعات ویزیت مربوطه
    visit_date = models.DateTimeField(
        verbose_name='تاریخ ویزیت'
    )
    
    # تایید و انتشار
    is_approved = models.BooleanField(
        default=True,
        verbose_name='تایید شده'
    )
    
    class Meta:
        verbose_name = 'امتیاز پزشک'
        verbose_name_plural = 'امتیازات پزشکان'
        unique_together = ['doctor', 'patient', 'visit_date']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['doctor', '-created_at']),
            models.Index(fields=['rating']),
        ]
    
    def __str__(self):
        return f"امتیاز {self.rating} به {self.doctor.username}"
    
    def save(self, *args, **kwargs):
        """بروزرسانی امتیاز پزشک هنگام ذخیره"""
        super().save(*args, **kwargs)
        if self.is_approved and self.is_active:
            # اگر doctor_profile وجود دارد، امتیاز را بروزرسانی کن
            try:
                self.doctor.doctor_profile.update_rating()
            except User.doctor_profile.RelatedObjectDoesNotExist:
                pass


class DoctorSettings(BaseModel):
    """
    تنظیمات شخصی پزشک
    """
    
    doctor = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='doctor_settings',
        verbose_name='پزشک'
    )
    
    # تنظیمات اعلان‌ها
    email_notifications = models.BooleanField(
        default=True,
        verbose_name='اعلان‌های ایمیل'
    )
    
    sms_notifications = models.BooleanField(
        default=True,
        verbose_name='اعلان‌های پیامک'
    )
    
    push_notifications = models.BooleanField(
        default=True,
        verbose_name='اعلان‌های push'
    )
    
    # تنظیمات نوبت‌دهی
    allow_same_day_booking = models.BooleanField(
        default=False,
        verbose_name='نوبت‌دهی در همان روز'
    )
    
    booking_lead_time = models.IntegerField(
        default=120,
        validators=[MinValueValidator(30), MaxValueValidator(1440)],
        help_text='زمان قبل از ویزیت برای نوبت‌دهی (دقیقه)',
        verbose_name='زمان قبل‌ویزیت'
    )
    
    max_daily_appointments = models.IntegerField(
        default=30,
        validators=[MinValueValidator(5), MaxValueValidator(100)],
        verbose_name='حداکثر نوبت روزانه'
    )
    
    # تنظیمات گزارش‌گیری
    auto_generate_prescription = models.BooleanField(
        default=True,
        verbose_name='تولید خودکار نسخه PDF'
    )
    
    auto_generate_certificate = models.BooleanField(
        default=True,
        verbose_name='تولید خودکار گواهی PDF'
    )
    
    # تنظیمات زبان
    LANGUAGE_CHOICES = [
        ('fa', 'فارسی'),
        ('en', 'English'),
    ]
    
    preferred_language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default='fa',
        verbose_name='زبان ترجیحی'
    )
    
    class Meta:
        verbose_name = 'تنظیمات پزشک'
        verbose_name_plural = 'تنظیمات پزشکان'
    
    def __str__(self):
        return f"تنظیمات {self.doctor.username}"