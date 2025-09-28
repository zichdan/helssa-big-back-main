"""
مدل‌های سیستم تریاژ پزشکی
Triage System Models
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta
import uuid

User = get_user_model()


class SymptomCategory(models.Model):
    """
    دسته‌بندی علائم پزشکی
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='نام دسته'
    )
    
    name_en = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='نام انگلیسی'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='توضیحات'
    )
    
    priority_level = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='سطح اولویت',
        help_text='1 = کم اولویت، 10 = اورژانس'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
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
        db_table = 'triage_symptom_categories'
        verbose_name = 'دسته‌بندی علائم'
        verbose_name_plural = 'دسته‌بندی‌های علائم'
        ordering = ['priority_level', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.priority_level})"


class Symptom(models.Model):
    """
    علائم پزشکی
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name='نام علامت'
    )
    
    name_en = models.CharField(
        max_length=200,
        verbose_name='نام انگلیسی'
    )
    
    category = models.ForeignKey(
        SymptomCategory,
        on_delete=models.CASCADE,
        related_name='symptoms',
        verbose_name='دسته‌بندی'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='توضیحات'
    )
    
    severity_levels = models.JSONField(
        default=list,
        verbose_name='سطوح شدت',
        help_text='لیست سطوح شدت قابل انتخاب'
    )
    
    common_locations = models.JSONField(
        default=list,
        verbose_name='محل‌های رایج',
        help_text='محل‌های رایج بروز علامت'
    )
    
    related_symptoms = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=True,
        verbose_name='علائم مرتبط'
    )
    
    urgency_score = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='امتیاز اورژانس'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
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
        db_table = 'triage_symptoms'
        verbose_name = 'علامت'
        verbose_name_plural = 'علائم'
        ordering = ['-urgency_score', 'name']
        indexes = [
            models.Index(fields=['urgency_score', 'is_active']),
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} (اورژانس: {self.urgency_score})"


class DifferentialDiagnosis(models.Model):
    """
    تشخیص‌های افتراقی
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name='نام تشخیص'
    )
    
    name_en = models.CharField(
        max_length=200,
        verbose_name='نام انگلیسی'
    )
    
    icd_10_code = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='کد ICD-10'
    )
    
    description = models.TextField(
        verbose_name='توضیحات'
    )
    
    typical_symptoms = models.ManyToManyField(
        Symptom,
        through='DiagnosisSymptom',
        verbose_name='علائم معمول'
    )
    
    urgency_level = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='سطح اورژانس'
    )
    
    recommended_actions = models.JSONField(
        default=list,
        verbose_name='اقدامات توصیه شده'
    )
    
    red_flags = models.JSONField(
        default=list,
        verbose_name='علائم هشدار',
        help_text='علائمی که نیاز به مراجعه فوری دارند'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
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
        db_table = 'triage_differential_diagnoses'
        verbose_name = 'تشخیص افتراقی'
        verbose_name_plural = 'تشخیص‌های افتراقی'
        ordering = ['-urgency_level', 'name']
        indexes = [
            models.Index(fields=['urgency_level', 'is_active']),
            models.Index(fields=['icd_10_code']),
        ]
    
    def __str__(self):
        return f"{self.name} (اورژانس: {self.urgency_level})"


class DiagnosisSymptom(models.Model):
    """
    رابطه تشخیص و علائم با وزن
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    diagnosis = models.ForeignKey(
        DifferentialDiagnosis,
        on_delete=models.CASCADE,
        verbose_name='تشخیص'
    )
    
    symptom = models.ForeignKey(
        Symptom,
        on_delete=models.CASCADE,
        verbose_name='علامت'
    )
    
    weight = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(10.0)],
        verbose_name='وزن',
        help_text='اهمیت این علامت در تشخیص'
    )
    
    is_mandatory = models.BooleanField(
        default=False,
        verbose_name='اجباری',
        help_text='آیا این علامت برای تشخیص اجباری است؟'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ایجاد'
    )
    
    class Meta:
        db_table = 'triage_diagnosis_symptoms'
        verbose_name = 'رابطه تشخیص-علامت'
        verbose_name_plural = 'روابط تشخیص-علامت'
        unique_together = ['diagnosis', 'symptom']
    
    def __str__(self):
        return f"{self.diagnosis.name} - {self.symptom.name} (وزن: {self.weight})"


class TriageSession(models.Model):
    """
    جلسات تریاژ بیماران
    """
    
    STATUS_CHOICES = [
        ('started', 'شروع شده'),
        ('in_progress', 'در حال انجام'),
        ('completed', 'تکمیل شده'),
        ('cancelled', 'لغو شده'),
        ('escalated', 'ارجاع شده'),
    ]
    
    URGENCY_LEVELS = [
        (1, 'غیر اورژانس'),
        (2, 'کم اولویت'),
        (3, 'متوسط'),
        (4, 'بالا'),
        (5, 'اورژانس'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='triage_sessions',
        verbose_name='بیمار'
    )
    
    chief_complaint = models.TextField(
        verbose_name='شکایت اصلی'
    )
    
    reported_symptoms = models.JSONField(
        default=list,
        verbose_name='علائم گزارش شده',
        help_text='علائم که بیمار گزارش کرده است'
    )
    
    identified_symptoms = models.ManyToManyField(
        Symptom,
        through='SessionSymptom',
        verbose_name='علائم شناسایی شده'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='started',
        verbose_name='وضعیت'
    )
    
    urgency_level = models.IntegerField(
        choices=URGENCY_LEVELS,
        null=True,
        blank=True,
        verbose_name='سطح اورژانس'
    )
    
    preliminary_diagnoses = models.ManyToManyField(
        DifferentialDiagnosis,
        through='SessionDiagnosis',
        verbose_name='تشخیص‌های اولیه'
    )
    
    recommended_actions = models.JSONField(
        default=list,
        verbose_name='اقدامات توصیه شده'
    )
    
    red_flags_detected = models.JSONField(
        default=list,
        verbose_name='علائم خطر شناسایی شده'
    )
    
    triage_notes = models.TextField(
        blank=True,
        verbose_name='یادداشت‌های تریاژ'
    )
    
    ai_confidence_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name='امتیاز اطمینان هوش مصنوعی'
    )
    
    requires_immediate_attention = models.BooleanField(
        default=False,
        verbose_name='نیاز به توجه فوری'
    )
    
    estimated_wait_time = models.DurationField(
        null=True,
        blank=True,
        verbose_name='زمان انتظار تخمینی'
    )
    
    completed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_triages',
        verbose_name='تکمیل شده توسط'
    )
    
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='شروع'
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تکمیل'
    )
    
    metadata = models.JSONField(
        default=dict,
        verbose_name='متادیتا'
    )
    
    class Meta:
        db_table = 'triage_sessions'
        verbose_name = 'جلسه تریاژ'
        verbose_name_plural = 'جلسات تریاژ'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['patient', 'status', '-started_at']),
            models.Index(fields=['urgency_level', '-started_at']),
            models.Index(fields=['requires_immediate_attention', '-started_at']),
        ]
    
    def __str__(self):
        return f"تریاژ {self.patient} - {self.started_at.strftime('%Y/%m/%d %H:%M')}"
    
    @property
    def duration(self) -> timedelta:
        """مدت زمان جلسه"""
        if self.completed_at:
            return self.completed_at - self.started_at
        return timezone.now() - self.started_at
    
    def calculate_urgency(self) -> int:
        """محاسبه سطح اورژانس بر اساس علائم"""
        if not self.identified_symptoms.exists():
            return 1
        
        max_urgency = self.identified_symptoms.aggregate(
            max_urgency=models.Max('urgency_score')
        )['max_urgency']
        
        return min(max_urgency // 2 + 1, 5) if max_urgency else 1


class SessionSymptom(models.Model):
    """
    رابطه جلسه تریاژ و علائم
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    session = models.ForeignKey(
        TriageSession,
        on_delete=models.CASCADE,
        verbose_name='جلسه'
    )
    
    symptom = models.ForeignKey(
        Symptom,
        on_delete=models.CASCADE,
        verbose_name='علامت'
    )
    
    severity = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='شدت'
    )
    
    duration_hours = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='مدت (ساعت)'
    )
    
    location = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='محل'
    )
    
    additional_details = models.TextField(
        blank=True,
        verbose_name='جزئیات اضافی'
    )
    
    reported_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='گزارش شده در'
    )
    
    class Meta:
        db_table = 'triage_session_symptoms'
        verbose_name = 'علامت جلسه'
        verbose_name_plural = 'علائم جلسه'
        unique_together = ['session', 'symptom']
    
    def __str__(self):
        return f"{self.session} - {self.symptom.name} (شدت: {self.severity})"


class SessionDiagnosis(models.Model):
    """
    رابطه جلسه تریاژ و تشخیص‌های اولیه
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    session = models.ForeignKey(
        TriageSession,
        on_delete=models.CASCADE,
        verbose_name='جلسه'
    )
    
    diagnosis = models.ForeignKey(
        DifferentialDiagnosis,
        on_delete=models.CASCADE,
        verbose_name='تشخیص'
    )
    
    probability_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name='امتیاز احتمال'
    )
    
    confidence_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='سطح اطمینان'
    )
    
    reasoning = models.TextField(
        blank=True,
        verbose_name='استدلال'
    )
    
    suggested_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='پیشنهاد شده در'
    )
    
    class Meta:
        db_table = 'triage_session_diagnoses'
        verbose_name = 'تشخیص جلسه'
        verbose_name_plural = 'تشخیص‌های جلسه'
        unique_together = ['session', 'diagnosis']
        ordering = ['-probability_score']
    
    def __str__(self):
        return f"{self.session} - {self.diagnosis.name} ({self.probability_score:.2f})"


class TriageRule(models.Model):
    """
    قوانین تریاژ خودکار
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name='نام قانون'
    )
    
    description = models.TextField(
        verbose_name='توضیحات'
    )
    
    conditions = models.JSONField(
        verbose_name='شرایط',
        help_text='شرایط اعمال قانون'
    )
    
    actions = models.JSONField(
        verbose_name='اقدامات',
        help_text='اقداماتی که باید انجام شود'
    )
    
    priority = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='اولویت'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ایجاد'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاریخ به‌روزرسانی'
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='ایجاد شده توسط'
    )
    
    class Meta:
        db_table = 'triage_rules'
        verbose_name = 'قانون تریاژ'
        verbose_name_plural = 'قوانین تریاژ'
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return f"{self.name} (اولویت: {self.priority})"