from django.db import models
from django.utils import timezone
import uuid


class Prescription(models.Model):
    """مدل نسخه پزشکی"""
    
    PRESCRIPTION_STATUS = [
        ('draft', 'پیش‌نویس'),
        ('issued', 'صادر شده'),
        ('dispensed', 'تحویل داده شده'),
        ('cancelled', 'لغو شده'),
    ]
    
    DOSAGE_FORMS = [
        ('tablet', 'قرص'),
        ('capsule', 'کپسول'),
        ('syrup', 'شربت'),
        ('injection', 'تزریق'),
        ('drops', 'قطره'),
        ('ointment', 'پماد'),
        ('cream', 'کرم'),
        ('inhaler', 'اسپری'),
        ('suppository', 'شیاف'),
        ('patch', 'چسب'),
        ('other', 'سایر'),
    ]
    
    ROUTES = [
        ('oral', 'خوراکی'),
        ('sublingual', 'زیرزبانی'),
        ('topical', 'موضعی'),
        ('inhalation', 'استنشاقی'),
        ('injection', 'تزریقی'),
        ('rectal', 'رکتال'),
        ('ophthalmic', 'چشمی'),
        ('otic', 'گوش'),
        ('nasal', 'بینی'),
        ('other', 'سایر'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    encounter = models.ForeignKey(
        'Encounter',
        on_delete=models.CASCADE,
        related_name='prescriptions',
        verbose_name='ملاقات'
    )
    
    # اطلاعات نسخه
    prescription_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='شماره نسخه'
    )
    status = models.CharField(
        max_length=20,
        choices=PRESCRIPTION_STATUS,
        default='draft',
        verbose_name='وضعیت'
    )
    
    # داروها
    medications = models.JSONField(
        default=list,
        verbose_name='داروها',
        help_text="""
        لیست داروها شامل:
        - name: نام دارو
        - generic_name: نام ژنریک
        - dosage: دوز
        - form: شکل دارویی
        - route: روش مصرف
        - frequency: تعداد دفعات
        - duration: مدت مصرف
        - quantity: تعداد
        - instructions: دستورالعمل
        """
    )
    
    # تاییدیه و امضا
    is_signed = models.BooleanField(
        default=False,
        verbose_name='امضا شده'
    )
    signed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان امضا'
    )
    digital_signature = models.TextField(
        null=True,
        blank=True,
        verbose_name='امضای دیجیتال'
    )
    
    # اطلاعات داروخانه
    pharmacy_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='شناسه داروخانه'
    )
    dispensed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان تحویل'
    )
    dispensed_by = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='تحویل دهنده'
    )
    
    # یادداشت‌ها
    doctor_notes = models.TextField(
        null=True,
        blank=True,
        verbose_name='یادداشت پزشک'
    )
    pharmacy_notes = models.TextField(
        null=True,
        blank=True,
        verbose_name='یادداشت داروخانه'
    )
    
    # خروجی‌ها
    pdf_url = models.URLField(
        null=True,
        blank=True,
        verbose_name='آدرس PDF'
    )
    qr_code = models.TextField(
        null=True,
        blank=True,
        verbose_name='QR Code'
    )
    
    # metadata
    insurance_code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='کد بیمه'
    )
    is_electronic = models.BooleanField(
        default=True,
        verbose_name='الکترونیکی'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ایجاد'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاریخ به‌روزرسانی'
    )
    expires_at = models.DateTimeField(
        verbose_name='تاریخ انقضا',
        help_text="تاریخ انقضای نسخه"
    )
    
    class Meta:
        db_table = 'prescriptions'
        verbose_name = 'نسخه'
        verbose_name_plural = 'نسخه‌ها'
        indexes = [
            models.Index(fields=['prescription_number']),
            models.Index(fields=['encounter', 'status']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
        
    def __str__(self):
        return f"نسخه {self.prescription_number}"
        
    @property
    def medication_count(self) -> int:
        """تعداد داروها"""
        return len(self.medications)
        
    @property
    def is_expired(self) -> bool:
        """آیا نسخه منقضی شده"""
        return timezone.now() > self.expires_at
        
    @property
    def can_dispense(self) -> bool:
        """آیا قابل تحویل است"""
        return (
            self.status == 'issued' and
            self.is_signed and
            not self.is_expired
        )
        
    def add_medication(self, medication_data: dict):
        """افزودن دارو به نسخه"""
        required_fields = ['name', 'dosage', 'form', 'route', 'frequency', 'duration']
        if not all(field in medication_data for field in required_fields):
            raise ValueError("اطلاعات دارو ناقص است")
            
        medication_data['added_at'] = timezone.now().isoformat()
        self.medications.append(medication_data)
        self.save()
        
    def issue(self):
        """صدور نسخه"""
        self.status = 'issued'
        self.save()
        
    def sign(self, digital_signature: str):
        """امضای نسخه"""
        self.is_signed = True
        self.signed_at = timezone.now()
        self.digital_signature = digital_signature
        self.save()
        
    def dispense(self, pharmacy_id: str, dispensed_by: str):
        """تحویل نسخه"""
        self.status = 'dispensed'
        self.pharmacy_id = pharmacy_id
        self.dispensed_at = timezone.now()
        self.dispensed_by = dispensed_by
        self.save()
        
    def cancel(self, reason: str = ''):
        """لغو نسخه"""
        self.status = 'cancelled'
        if reason:
            self.doctor_notes = f"دلیل لغو: {reason}\n{self.doctor_notes or ''}"
        self.save()
        
    def save(self, *args, **kwargs):
        """override save برای تولید شماره نسخه"""
        if not self.prescription_number:
            # تولید شماره نسخه یکتا
            from ..utils.generators import generate_prescription_number
            self.prescription_number = generate_prescription_number()
            
        if not self.expires_at:
            # تنظیم تاریخ انقضا (پیش‌فرض 6 ماه)
            self.expires_at = timezone.now() + timezone.timedelta(days=180)
            
        super().save(*args, **kwargs)