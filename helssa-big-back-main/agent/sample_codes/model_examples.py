"""
نمونه کدهای Model برای ایجنت‌ها
Sample Model Code Examples for Agents
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from app_standards.models.base_models import (
    BaseModel, PatientRelatedModel, DoctorRelatedModel,
    MedicalRecordModel, FileAttachmentModel, StatusModel,
    RatingModel, VersionedModel
)
from decimal import Decimal
import uuid

User = get_user_model()


# ====================================
# نمونه 1: Simple Model
# ====================================

class PatientProfile(PatientRelatedModel):
    """
    پروفایل بیمار
    """
    # اطلاعات شخصی
    national_code = models.CharField(
        max_length=10,
        unique=True,
        validators=[RegexValidator(r'^\d{10}$', 'کد ملی باید 10 رقم باشد')],
        verbose_name='کد ملی'
    )
    date_of_birth = models.DateField(
        verbose_name='تاریخ تولد'
    )
    gender = models.CharField(
        max_length=10,
        choices=[
            ('male', 'مرد'),
            ('female', 'زن'),
        ],
        verbose_name='جنسیت'
    )
    phone_number = models.CharField(
        max_length=11,
        validators=[RegexValidator(r'^09\d{9}$', 'شماره موبایل معتبر نیست')],
        verbose_name='شماره موبایل'
    )
    
    # اطلاعات پزشکی
    blood_type = models.CharField(
        max_length=5,
        choices=[
            ('A+', 'A+'), ('A-', 'A-'),
            ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'),
            ('O+', 'O+'), ('O-', 'O-'),
        ],
        blank=True,
        verbose_name='گروه خونی'
    )
    allergies = models.TextField(
        blank=True,
        verbose_name='آلرژی‌ها'
    )
    chronic_diseases = models.TextField(
        blank=True,
        verbose_name='بیماری‌های مزمن'
    )
    
    class Meta:
        verbose_name = 'پروفایل بیمار'
        verbose_name_plural = 'پروفایل بیماران'
    
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.national_code}"
    
    @property
    def age(self):
        """محاسبه سن"""
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


# ====================================
# نمونه 2: Complex Model with Relations
# ====================================

class MedicalVisit(StatusModel, MedicalRecordModel):
    """
    ویزیت پزشکی
    """
    STATUS_CHOICES = [
        ('scheduled', 'زمان‌بندی شده'),
        ('in_progress', 'در حال انجام'),
        ('completed', 'تکمیل شده'),
        ('cancelled', 'لغو شده'),
        ('no_show', 'عدم حضور'),
    ]
    
    # اطلاعات اصلی
    visit_date = models.DateTimeField(
        verbose_name='تاریخ ویزیت'
    )
    visit_type = models.CharField(
        max_length=20,
        choices=[
            ('in_person', 'حضوری'),
            ('online', 'آنلاین'),
            ('phone', 'تلفنی'),
        ],
        default='in_person',
        verbose_name='نوع ویزیت'
    )
    duration_minutes = models.IntegerField(
        default=15,
        validators=[MinValueValidator(5), MaxValueValidator(120)],
        verbose_name='مدت زمان (دقیقه)'
    )
    
    # شکایت و تشخیص
    chief_complaint = models.TextField(
        verbose_name='شکایت اصلی'
    )
    diagnosis = models.TextField(
        blank=True,
        verbose_name='تشخیص'
    )
    treatment_plan = models.TextField(
        blank=True,
        verbose_name='برنامه درمان'
    )
    
    # پرداخت
    fee = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name='هزینه ویزیت'
    )
    is_paid = models.BooleanField(
        default=False,
        verbose_name='پرداخت شده'
    )
    payment_reference = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='شماره مرجع پرداخت'
    )
    
    # فایل‌های پیوست
    attachments = models.ManyToManyField(
        'MedicalFile',
        blank=True,
        related_name='visits',
        verbose_name='فایل‌های پیوست'
    )
    
    # متادیتا
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='اطلاعات اضافی'
    )
    
    class Meta:
        verbose_name = 'ویزیت پزشکی'
        verbose_name_plural = 'ویزیت‌های پزشکی'
        ordering = ['-visit_date']
        indexes = [
            models.Index(fields=['patient', 'visit_date']),
            models.Index(fields=['doctor', 'visit_date']),
            models.Index(fields=['status', 'visit_date']),
        ]
    
    def __str__(self):
        return f"ویزیت {self.patient} با {self.doctor} - {self.visit_date}"
    
    def save(self, *args, **kwargs):
        # محاسبه خودکار مدت زمان برای ویزیت‌های تکمیل شده
        if self.status == 'completed' and not self.duration_minutes:
            if hasattr(self, 'started_at') and hasattr(self, 'ended_at'):
                duration = (self.ended_at - self.started_at).total_seconds() / 60
                self.duration_minutes = int(duration)
        
        super().save(*args, **kwargs)
    
    def can_cancel(self):
        """آیا ویزیت قابل لغو است؟"""
        return self.status in ['scheduled'] and self.visit_date > timezone.now()
    
    def cancel(self, reason=''):
        """لغو ویزیت"""
        if not self.can_cancel():
            raise ValueError('این ویزیت قابل لغو نیست')
        
        self.change_status('cancelled')
        self.metadata['cancellation_reason'] = reason
        self.metadata['cancelled_at'] = timezone.now().isoformat()
        self.save()


# ====================================
# نمونه 3: Model with Custom Manager
# ====================================

class PrescriptionManager(models.Manager):
    """Manager سفارشی برای نسخه‌ها"""
    
    def active(self):
        """نسخه‌های فعال"""
        return self.filter(is_active=True)
    
    def for_patient(self, patient):
        """نسخه‌های یک بیمار"""
        return self.filter(patient=patient, is_active=True)
    
    def recent(self, days=30):
        """نسخه‌های اخیر"""
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(created_at__gte=cutoff_date)
    
    def by_drug(self, drug_name):
        """نسخه‌های حاوی دارو خاص"""
        return self.filter(items__drug_name__icontains=drug_name).distinct()


class Prescription(StatusModel, MedicalRecordModel):
    """
    نسخه پزشکی
    """
    STATUS_CHOICES = [
        ('draft', 'پیش‌نویس'),
        ('issued', 'صادر شده'),
        ('dispensed', 'تحویل شده'),
        ('expired', 'منقضی شده'),
    ]
    
    # اطلاعات نسخه
    prescription_code = models.CharField(
        max_length=20,
        unique=True,
        default=uuid.uuid4,
        verbose_name='کد نسخه'
    )
    issue_date = models.DateTimeField(
        default=timezone.now,
        verbose_name='تاریخ صدور'
    )
    expiry_date = models.DateTimeField(
        verbose_name='تاریخ انقضا'
    )
    
    # ارتباط با ویزیت
    visit = models.ForeignKey(
        MedicalVisit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prescriptions',
        verbose_name='ویزیت مربوطه'
    )
    
    # اطلاعات اضافی
    notes = models.TextField(
        blank=True,
        verbose_name='یادداشت‌ها'
    )
    pharmacy = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='داروخانه'
    )
    
    # استفاده از Manager سفارشی
    objects = PrescriptionManager()
    
    class Meta:
        verbose_name = 'نسخه'
        verbose_name_plural = 'نسخه‌ها'
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"نسخه {self.prescription_code}"
    
    def save(self, *args, **kwargs):
        # تنظیم تاریخ انقضا (30 روز)
        if not self.expiry_date:
            from datetime import timedelta
            self.expiry_date = self.issue_date + timedelta(days=30)
        
        # بررسی انقضا
        if timezone.now() > self.expiry_date and self.status != 'expired':
            self.status = 'expired'
        
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """آیا نسخه منقضی شده؟"""
        return timezone.now() > self.expiry_date
    
    def get_total_items(self):
        """تعداد کل اقلام نسخه"""
        return self.items.count()


# ====================================
# نمونه 4: Related Model (1-to-Many)
# ====================================

class PrescriptionItem(BaseModel):
    """
    اقلام نسخه
    """
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='نسخه'
    )
    
    # اطلاعات دارو
    drug_name = models.CharField(
        max_length=200,
        verbose_name='نام دارو'
    )
    drug_type = models.CharField(
        max_length=50,
        choices=[
            ('tablet', 'قرص'),
            ('capsule', 'کپسول'),
            ('syrup', 'شربت'),
            ('injection', 'تزریقی'),
            ('ointment', 'پماد'),
            ('drops', 'قطره'),
        ],
        verbose_name='نوع دارو'
    )
    dosage = models.CharField(
        max_length=50,
        verbose_name='دوز'
    )
    
    # دستور مصرف
    frequency = models.CharField(
        max_length=100,
        verbose_name='تعداد دفعات مصرف'
    )
    duration = models.CharField(
        max_length=100,
        verbose_name='مدت مصرف'
    )
    instructions = models.TextField(
        blank=True,
        verbose_name='دستور مصرف'
    )
    
    # تعداد
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='تعداد'
    )
    
    class Meta:
        verbose_name = 'قلم نسخه'
        verbose_name_plural = 'اقلام نسخه'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.drug_name} - {self.dosage}"


# ====================================
# نمونه 5: Model with File Handling
# ====================================

class MedicalFile(FileAttachmentModel, PatientRelatedModel):
    """
    فایل‌های پزشکی بیمار
    """
    FILE_TYPES = [
        ('lab_result', 'نتیجه آزمایش'),
        ('radiology', 'رادیولوژی'),
        ('prescription', 'نسخه'),
        ('report', 'گزارش'),
        ('other', 'سایر'),
    ]
    
    file_type = models.CharField(
        max_length=20,
        choices=FILE_TYPES,
        default='other',
        verbose_name='نوع فایل'
    )
    
    # ارتباط با ویزیت
    related_visit = models.ForeignKey(
        MedicalVisit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='files',
        verbose_name='ویزیت مربوطه'
    )
    
    # تگ‌ها برای جستجو
    tags = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='برچسب‌ها',
        help_text='برچسب‌ها را با کاما جدا کنید'
    )
    
    # محرمانگی
    is_sensitive = models.BooleanField(
        default=False,
        verbose_name='محرمانه'
    )
    
    class Meta:
        verbose_name = 'فایل پزشکی'
        verbose_name_plural = 'فایل‌های پزشکی'
        ordering = ['-created_at']
        permissions = [
            ('view_sensitive_files', 'Can view sensitive files'),
        ]
    
    def __str__(self):
        return f"{self.get_file_type_display()} - {self.patient}"
    
    def save(self, *args, **kwargs):
        # استخراج نام فایل از مسیر
        if self.file and not self.file_name:
            import os
            self.file_name = os.path.basename(self.file.name)
        
        super().save(*args, **kwargs)
    
    def get_tags_list(self):
        """لیست تگ‌ها"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []


# ====================================
# نمونه 6: Model with Versioning
# ====================================

class ClinicalNote(VersionedModel, MedicalRecordModel):
    """
    یادداشت‌های بالینی با قابلیت versioning
    """
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان'
    )
    content = models.TextField(
        verbose_name='محتوا'
    )
    note_type = models.CharField(
        max_length=30,
        choices=[
            ('progress', 'یادداشت پیشرفت'),
            ('consultation', 'مشاوره'),
            ('discharge', 'ترخیص'),
            ('admission', 'پذیرش'),
        ],
        verbose_name='نوع یادداشت'
    )
    
    # امضای دیجیتال
    is_signed = models.BooleanField(
        default=False,
        verbose_name='امضا شده'
    )
    signed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان امضا'
    )
    
    class Meta:
        verbose_name = 'یادداشت بالینی'
        verbose_name_plural = 'یادداشت‌های بالینی'
    
    def sign(self, user):
        """امضای یادداشت"""
        if self.is_signed:
            raise ValueError('این یادداشت قبلاً امضا شده است')
        
        self.is_signed = True
        self.signed_at = timezone.now()
        self.save()
        
        # ایجاد نسخه جدید پس از امضا
        return self.create_new_version()


# ====================================
# نمونه 7: Model with Ratings
# ====================================

class DoctorRating(RatingModel):
    """
    امتیازدهی به پزشک
    """
    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'doctor'},
        related_name='ratings_received',
        verbose_name='پزشک'
    )
    visit = models.OneToOneField(
        MedicalVisit,
        on_delete=models.CASCADE,
        related_name='rating',
        verbose_name='ویزیت'
    )
    
    # معیارهای امتیازدهی
    professionalism = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='حرفه‌ای بودن'
    )
    communication = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='ارتباط'
    )
    punctuality = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='وقت‌شناسی'
    )
    
    class Meta:
        verbose_name = 'امتیاز پزشک'
        verbose_name_plural = 'امتیازات پزشکان'
        unique_together = [['rated_by', 'visit']]
    
    def calculate_average(self):
        """محاسبه میانگین امتیاز"""
        scores = [self.professionalism, self.communication, self.punctuality]
        return sum(scores) / len(scores)
    
    def save(self, *args, **kwargs):
        # محاسبه امتیاز کلی
        self.rating = round(self.calculate_average())
        super().save(*args, **kwargs)


# ====================================
# نمونه 8: Abstract Model
# ====================================

class AbstractMedicalTest(BaseModel):
    """
    مدل abstract برای آزمایش‌های پزشکی
    """
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'patient'},
        verbose_name='بیمار'
    )
    ordered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'user_type': 'doctor'},
        related_name='%(class)s_ordered',
        verbose_name='دستور دهنده'
    )
    
    test_date = models.DateTimeField(
        verbose_name='تاریخ آزمایش'
    )
    result_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاریخ نتیجه'
    )
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('ordered', 'دستور داده شده'),
            ('in_progress', 'در حال انجام'),
            ('completed', 'تکمیل شده'),
            ('cancelled', 'لغو شده'),
        ],
        default='ordered',
        verbose_name='وضعیت'
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name='یادداشت‌ها'
    )
    
    class Meta:
        abstract = True
        ordering = ['-test_date']
    
    def is_ready(self):
        """آیا نتیجه آماده است؟"""
        return self.status == 'completed' and self.result_date is not None


# استفاده از Abstract Model
class BloodTest(AbstractMedicalTest):
    """آزمایش خون"""
    # فیلدهای اختصاصی آزمایش خون
    hemoglobin = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name='هموگلوبین'
    )
    white_blood_cells = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='گلبول سفید'
    )
    # سایر فیلدها...
    
    class Meta:
        verbose_name = 'آزمایش خون'
        verbose_name_plural = 'آزمایش‌های خون'


class UrineTest(AbstractMedicalTest):
    """آزمایش ادرار"""
    # فیلدهای اختصاصی آزمایش ادرار
    specific_gravity = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name='وزن مخصوص'
    )
    ph_level = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name='pH'
    )
    # سایر فیلدها...
    
    class Meta:
        verbose_name = 'آزمایش ادرار'
        verbose_name_plural = 'آزمایش‌های ادرار'