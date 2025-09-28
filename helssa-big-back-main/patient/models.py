"""
مدل‌های سیستم مدیریت بیماران
Patient Management System Models
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import date, timedelta
import uuid

User = get_user_model()


class PatientProfile(models.Model):
    """
    پروفایل بیمار
    Patient Profile Model
    """
    
    GENDER_CHOICES = [
        ('male', 'مرد'),
        ('female', 'زن'),
        ('other', 'سایر'),
    ]
    
    BLOOD_TYPE_CHOICES = [
        ('A+', 'A مثبت'),
        ('A-', 'A منفی'),
        ('B+', 'B مثبت'),
        ('B-', 'B منفی'),
        ('AB+', 'AB مثبت'),
        ('AB-', 'AB منفی'),
        ('O+', 'O مثبت'),
        ('O-', 'O منفی'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('single', 'مجرد'),
        ('married', 'متأهل'),
        ('divorced', 'مطلقه'),
        ('widowed', 'بیوه'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # ارتباط با کاربر
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='patient_profile',
        verbose_name='کاربر'
    )
    
    # اطلاعات هویتی
    national_code = models.CharField(
        max_length=10,
        unique=True,
        validators=[
            RegexValidator(
                r'^\d{10}$',
                'کد ملی باید 10 رقم باشد'
            )
        ],
        verbose_name='کد ملی',
        db_index=True
    )
    
    first_name = models.CharField(
        max_length=50,
        verbose_name='نام'
    )
    
    last_name = models.CharField(
        max_length=50,
        verbose_name='نام خانوادگی'
    )
    
    birth_date = models.DateField(
        verbose_name='تاریخ تولد'
    )
    
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        verbose_name='جنسیت'
    )
    
    # اطلاعات تماس
    emergency_contact_name = models.CharField(
        max_length=100,
        verbose_name='نام تماس اضطراری'
    )
    
    emergency_contact_phone = models.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                r'^09\d{9}$',
                'شماره موبایل باید با 09 شروع شود و 11 رقم باشد'
            )
        ],
        verbose_name='شماره تماس اضطراری'
    )
    
    emergency_contact_relation = models.CharField(
        max_length=50,
        verbose_name='نسبت با تماس اضطراری'
    )
    
    # آدرس
    address = models.TextField(
        verbose_name='آدرس محل سکونت'
    )
    
    city = models.CharField(
        max_length=50,
        verbose_name='شهر'
    )
    
    province = models.CharField(
        max_length=50,
        verbose_name='استان'
    )
    
    postal_code = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                r'^\d{10}$',
                'کد پستی باید 10 رقم باشد'
            )
        ],
        verbose_name='کد پستی'
    )
    
    # اطلاعات پزشکی پایه
    blood_type = models.CharField(
        max_length=3,
        choices=BLOOD_TYPE_CHOICES,
        blank=True,
        null=True,
        verbose_name='گروه خونی'
    )
    
    height = models.FloatField(
        validators=[
            MinValueValidator(50.0),
            MaxValueValidator(250.0)
        ],
        blank=True,
        null=True,
        verbose_name='قد (سانتی‌متر)',
        help_text='قد به سانتی‌متر'
    )
    
    weight = models.FloatField(
        validators=[
            MinValueValidator(10.0),
            MaxValueValidator(500.0)
        ],
        blank=True,
        null=True,
        verbose_name='وزن (کیلوگرم)',
        help_text='وزن به کیلوگرم'
    )
    
    marital_status = models.CharField(
        max_length=10,
        choices=MARITAL_STATUS_CHOICES,
        verbose_name='وضعیت تأهل'
    )
    
    # شماره پرونده پزشکی
    medical_record_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='شماره پرونده پزشکی',
        help_text='شماره منحصر به فرد پرونده پزشکی'
    )
    
    # وضعیت فعالیت
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    
    # تاریخ‌ها
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ایجاد'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاریخ آخرین بروزرسانی'
    )
    
    class Meta:
        verbose_name = 'پروفایل بیمار'
        verbose_name_plural = 'پروفایل‌های بیماران'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['national_code']),
            models.Index(fields=['medical_record_number']),
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} - {self.medical_record_number}"
    
    def get_full_name(self) -> str:
        """
        دریافت نام کامل بیمار
        Get patient's full name
        """
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self) -> int:
        """
        محاسبه سن بیمار
        Calculate patient's age
        """
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
    
    @property
    def bmi(self) -> float:
        """
        محاسبه شاخص توده بدنی (BMI)
        Calculate Body Mass Index
        """
        if self.height and self.weight:
            height_m = self.height / 100  # تبدیل سانتی‌متر به متر
            return round(self.weight / (height_m ** 2), 2)
        return None
    
    def save(self, *args, **kwargs):
        """
        ذخیره با تولید خودکار شماره پرونده در صورت عدم وجود
        Save with automatic medical record number generation if not exists
        """
        if not self.medical_record_number:
            self.medical_record_number = self._generate_medical_record_number()
        super().save(*args, **kwargs)
    
    def _generate_medical_record_number(self) -> str:
        """
        تولید شماره پرونده پزشکی منحصر به فرد
        Generate unique medical record number
        """
        from datetime import datetime
        year = datetime.now().year
        # گرفتن آخرین شماره پرونده در سال جاری
        last_record = PatientProfile.objects.filter(
            medical_record_number__startswith=f"P{year}"
        ).order_by('-medical_record_number').first()
        
        if last_record:
            last_number = int(last_record.medical_record_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
        
        return f"P{year}-{new_number:06d}"


class MedicalRecord(models.Model):
    """
    سابقه پزشکی بیمار
    Patient Medical History Record
    """
    
    RECORD_TYPE_CHOICES = [
        ('allergy', 'آلرژی'),
        ('medication', 'دارو'),
        ('surgery', 'جراحی'),
        ('illness', 'بیماری'),
        ('family_history', 'سابقه خانوادگی'),
        ('vaccination', 'واکسیناسیون'),
        ('other', 'سایر'),
    ]
    
    SEVERITY_CHOICES = [
        ('mild', 'خفیف'),
        ('moderate', 'متوسط'),
        ('severe', 'شدید'),
        ('critical', 'بحرانی'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='medical_records',
        verbose_name='بیمار'
    )
    
    record_type = models.CharField(
        max_length=20,
        choices=RECORD_TYPE_CHOICES,
        verbose_name='نوع رکورد'
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان'
    )
    
    description = models.TextField(
        verbose_name='توضیحات'
    )
    
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='mild',
        verbose_name='شدت'
    )
    
    start_date = models.DateField(
        verbose_name='تاریخ شروع',
        help_text='تاریخ شروع بیماری یا مصرف دارو'
    )
    
    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='تاریخ پایان',
        help_text='تاریخ پایان (در صورت وجود)'
    )
    
    is_ongoing = models.BooleanField(
        default=False,
        verbose_name='در حال ادامه',
        help_text='آیا این مورد هنوز ادامه دارد؟'
    )
    
    doctor_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='نام پزشک مربوطه'
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name='یادداشت‌های اضافی'
    )
    
    # metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_medical_records',
        verbose_name='ایجاد شده توسط'
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
        verbose_name = 'سابقه پزشکی'
        verbose_name_plural = 'سوابق پزشکی'
        ordering = ['-start_date', '-created_at']
        indexes = [
            models.Index(fields=['patient', 'record_type']),
            models.Index(fields=['start_date']),
            models.Index(fields=['is_ongoing']),
        ]
    
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.title}"


class PrescriptionHistory(models.Model):
    """
    تاریخچه نسخه‌های بیمار
    Patient Prescription History
    """
    
    STATUS_CHOICES = [
        ('active', 'فعال'),
        ('completed', 'تکمیل شده'),
        ('cancelled', 'لغو شده'),
        ('expired', 'منقضی شده'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='prescriptions',
        verbose_name='بیمار'
    )
    
    prescribed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'user_type': 'doctor'},
        related_name='prescribed_medications',
        verbose_name='تجویز شده توسط'
    )
    
    # اطلاعات نسخه
    prescription_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='شماره نسخه'
    )
    
    medication_name = models.CharField(
        max_length=200,
        verbose_name='نام دارو'
    )
    
    dosage = models.CharField(
        max_length=100,
        verbose_name='دوز مصرف'
    )
    
    frequency = models.CharField(
        max_length=100,
        verbose_name='دفعات مصرف',
        help_text='مثال: روزی 3 بار'
    )
    
    duration = models.CharField(
        max_length=50,
        verbose_name='مدت مصرف',
        help_text='مثال: 7 روز'
    )
    
    instructions = models.TextField(
        blank=True,
        verbose_name='دستورات مصرف',
        help_text='راهنمای تفصیلی مصرف دارو'
    )
    
    diagnosis = models.CharField(
        max_length=200,
        verbose_name='تشخیص',
        help_text='تشخیص یا دلیل تجویز'
    )
    
    # تاریخ‌ها
    prescribed_date = models.DateField(
        default=timezone.now,
        verbose_name='تاریخ تجویز'
    )
    
    start_date = models.DateField(
        verbose_name='تاریخ شروع مصرف'
    )
    
    end_date = models.DateField(
        verbose_name='تاریخ پایان مصرف'
    )
    
    # وضعیت
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='وضعیت'
    )
    
    is_repeat_allowed = models.BooleanField(
        default=False,
        verbose_name='قابل تکرار',
        help_text='آیا این نسخه قابل تکرار است؟'
    )
    
    repeat_count = models.PositiveIntegerField(
        default=0,
        verbose_name='تعداد تکرار'
    )
    
    max_repeats = models.PositiveIntegerField(
        default=1,
        verbose_name='حداکثر تکرار مجاز'
    )
    
    # یادداشت‌ها
    pharmacy_notes = models.TextField(
        blank=True,
        verbose_name='یادداشت داروخانه'
    )
    
    patient_notes = models.TextField(
        blank=True,
        verbose_name='یادداشت بیمار'
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
        verbose_name = 'تاریخچه نسخه'
        verbose_name_plural = 'تاریخچه نسخه‌ها'
        ordering = ['-prescribed_date', '-created_at']
        indexes = [
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['prescribed_date']),
            models.Index(fields=['prescription_number']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.prescription_number} - {self.medication_name}"
    
    @property
    def is_expired(self) -> bool:
        """
        بررسی انقضا نسخه
        Check if prescription is expired
        """
        return timezone.now().date() > self.end_date
    
    @property
    def days_remaining(self) -> int:
        """
        محاسبه روزهای باقی‌مانده
        Calculate remaining days
        """
        if self.is_expired:
            return 0
        return (self.end_date - timezone.now().date()).days
    
    def can_repeat(self) -> bool:
        """
        بررسی امکان تکرار نسخه
        Check if prescription can be repeated
        """
        return (
            self.is_repeat_allowed and
            self.repeat_count < self.max_repeats and
            not self.is_expired
        )
    
    def save(self, *args, **kwargs):
        """
        ذخیره با تولید خودکار شماره نسخه
        Save with automatic prescription number generation
        """
        if not self.prescription_number:
            self.prescription_number = self._generate_prescription_number()
        super().save(*args, **kwargs)
    
    def _generate_prescription_number(self) -> str:
        """
        تولید شماره نسخه منحصر به فرد
        Generate unique prescription number
        """
        from datetime import datetime
        year = datetime.now().year
        month = datetime.now().month
        
        # گرفتن آخرین شماره نسخه در ماه جاری
        last_prescription = PrescriptionHistory.objects.filter(
            prescription_number__startswith=f"RX{year}{month:02d}"
        ).order_by('-prescription_number').first()
        
        if last_prescription:
            last_number = int(last_prescription.prescription_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
        
        return f"RX{year}{month:02d}-{new_number:05d}"


class MedicalConsent(models.Model):
    """
    رضایت‌نامه‌های پزشکی بیمار
    Patient Medical Consent Forms
    """
    
    CONSENT_TYPE_CHOICES = [
        ('treatment', 'درمان'),
        ('surgery', 'جراحی'),
        ('data_sharing', 'اشتراک اطلاعات'),
        ('research', 'تحقیقات'),
        ('telemedicine', 'طب از راه دور'),
        ('recording', 'ضبط ملاقات'),
        ('emergency', 'اورژانس'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('granted', 'موافقت'),
        ('denied', 'عدم موافقت'),
        ('expired', 'منقضی شده'),
        ('revoked', 'لغو شده'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='consent_forms',
        verbose_name='بیمار'
    )
    
    consent_type = models.CharField(
        max_length=20,
        choices=CONSENT_TYPE_CHOICES,
        verbose_name='نوع رضایت‌نامه'
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان رضایت‌نامه'
    )
    
    description = models.TextField(
        verbose_name='شرح رضایت‌نامه'
    )
    
    consent_text = models.TextField(
        verbose_name='متن کامل رضایت‌نامه'
    )
    
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='وضعیت'
    )
    
    # تاریخ‌ها
    created_date = models.DateField(
        auto_now_add=True,
        verbose_name='تاریخ ایجاد'
    )
    
    consent_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='تاریخ رضایت',
        help_text='زمان دقیق ثبت رضایت بیمار'
    )
    
    expiry_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='تاریخ انقضا'
    )
    
    # امضای دیجیتال
    digital_signature = models.TextField(
        blank=True,
        verbose_name='امضای دیجیتال'
    )
    
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name='آدرس IP'
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    
    # اطلاعات اضافی
    witness_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='نام شاهد'
    )
    
    witness_signature = models.TextField(
        blank=True,
        verbose_name='امضای شاهد'
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name='یادداشت‌ها'
    )
    
    # audit trail
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='requested_consents',
        verbose_name='درخواست شده توسط'
    )
    
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_consents',
        verbose_name='پردازش شده توسط'
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
        verbose_name = 'رضایت‌نامه پزشکی'
        verbose_name_plural = 'رضایت‌نامه‌های پزشکی'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient', 'consent_type']),
            models.Index(fields=['status']),
            models.Index(fields=['expiry_date']),
        ]
    
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.title}"
    
    @property
    def is_valid(self) -> bool:
        """
        بررسی اعتبار رضایت‌نامه
        Check if consent is valid
        """
        if self.status != 'granted':
            return False
        
        if self.expiry_date and timezone.now().date() > self.expiry_date:
            return False
        
        return True
    
    @property
    def is_expired(self) -> bool:
        """
        بررسی انقضا رضایت‌نامه
        Check if consent is expired
        """
        return (
            self.expiry_date and
            timezone.now().date() > self.expiry_date
        )
    
    def grant_consent(self, digital_signature: str, ip_address: str, user_agent: str):
        """
        ثبت رضایت بیمار
        Grant patient consent
        """
        self.status = 'granted'
        self.consent_date = timezone.now()
        self.digital_signature = digital_signature
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.save()
    
    def revoke_consent(self):
        """
        لغو رضایت
        Revoke consent
        """
        self.status = 'revoked'
        self.save()