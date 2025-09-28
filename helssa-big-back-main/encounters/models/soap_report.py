from django.db import models
from django.utils import timezone
import uuid


class SOAPReport(models.Model):
    """مدل گزارش SOAP"""
    
    GENERATION_METHODS = [
        ('ai', 'تولید با AI'),
        ('manual', 'دستی'),
        ('hybrid', 'ترکیبی'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    encounter = models.OneToOneField(
        'Encounter',
        on_delete=models.CASCADE,
        related_name='soap_report',
        verbose_name='ملاقات'
    )
    
    # بخش‌های SOAP
    subjective = models.TextField(
        verbose_name='Subjective - شرح حال',
        help_text="Subjective - شرح حال و علائم بیمار"
    )
    objective = models.TextField(
        verbose_name='Objective - معاینه',
        help_text="Objective - یافته‌های معاینه و آزمایشات"
    )
    assessment = models.TextField(
        verbose_name='Assessment - ارزیابی',
        help_text="Assessment - ارزیابی و تشخیص"
    )
    plan = models.TextField(
        verbose_name='Plan - برنامه درمان',
        help_text="Plan - برنامه درمان"
    )
    
    # داده‌های ساختاریافته
    diagnoses = models.JSONField(
        default=list,
        verbose_name='تشخیص‌ها',
        help_text="لیست تشخیص‌ها با کد ICD"
    )
    medications = models.JSONField(
        default=list,
        verbose_name='داروها',
        help_text="داروهای تجویز شده"
    )
    lab_orders = models.JSONField(
        default=list,
        verbose_name='آزمایشات',
        help_text="درخواست‌های آزمایش"
    )
    follow_up = models.JSONField(
        default=dict,
        verbose_name='پیگیری',
        help_text="برنامه پیگیری"
    )
    
    # تاییدیه‌ها
    is_draft = models.BooleanField(
        default=True,
        verbose_name='پیش‌نویس'
    )
    doctor_approved = models.BooleanField(
        default=False,
        verbose_name='تایید پزشک'
    )
    doctor_approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان تایید پزشک'
    )
    patient_shared = models.BooleanField(
        default=False,
        verbose_name='اشتراک با بیمار'
    )
    patient_shared_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان اشتراک با بیمار'
    )
    
    # امضای دیجیتال
    doctor_signature = models.TextField(
        null=True,
        blank=True,
        verbose_name='امضای دیجیتال',
        help_text="امضای دیجیتال پزشک"
    )
    signature_timestamp = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان امضا'
    )
    
    # خروجی‌ها
    pdf_url = models.URLField(
        null=True,
        blank=True,
        verbose_name='آدرس PDF',
        help_text="آدرس فایل PDF"
    )
    markdown_content = models.TextField(
        null=True,
        blank=True,
        verbose_name='محتوای Markdown',
        help_text="محتوای Markdown"
    )
    
    # metadata
    generation_method = models.CharField(
        max_length=20,
        choices=GENERATION_METHODS,
        default='ai',
        verbose_name='روش تولید'
    )
    ai_confidence = models.FloatField(
        null=True,
        blank=True,
        verbose_name='اطمینان AI',
        help_text="امتیاز اطمینان AI"
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
        db_table = 'soap_reports'
        verbose_name = 'گزارش SOAP'
        verbose_name_plural = 'گزارش‌های SOAP'
        
    def __str__(self):
        return f"گزارش SOAP ملاقات {self.encounter_id}"
        
    @property
    def is_complete(self) -> bool:
        """آیا گزارش کامل است"""
        return all([
            self.subjective,
            self.objective,
            self.assessment,
            self.plan
        ])
        
    @property
    def has_prescriptions(self) -> bool:
        """آیا نسخه دارد"""
        return bool(self.medications)
        
    @property
    def needs_follow_up(self) -> bool:
        """آیا نیاز به پیگیری دارد"""
        return bool(self.follow_up.get('date'))
        
    def approve_by_doctor(self, doctor_id: str):
        """تایید گزارش توسط پزشک"""
        self.doctor_approved = True
        self.doctor_approved_at = timezone.now()
        self.is_draft = False
        self.save()
        
    def share_with_patient(self):
        """اشتراک گزارش با بیمار"""
        self.patient_shared = True
        self.patient_shared_at = timezone.now()
        self.save()
        
    def add_diagnosis(self, name: str, icd_code: str, is_primary: bool = False):
        """افزودن تشخیص"""
        diagnosis = {
            'name': name,
            'icd_code': icd_code,
            'is_primary': is_primary,
            'added_at': timezone.now().isoformat()
        }
        self.diagnoses.append(diagnosis)
        self.save()
        
    def add_medication(self, name: str, dosage: str, route: str, 
                      duration: str, instructions: str = ''):
        """افزودن دارو"""
        medication = {
            'name': name,
            'dosage': dosage,
            'route': route,
            'duration': duration,
            'instructions': instructions,
            'prescribed_at': timezone.now().isoformat()
        }
        self.medications.append(medication)
        self.save()