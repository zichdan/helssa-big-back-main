"""
مدل کمیسیون و تسویه حساب
Commission and Settlement Model
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from .base import BaseModel
from .transaction import Transaction

User = get_user_model()


class CommissionStatus(models.TextChoices):
    """وضعیت‌های کمیسیون"""
    PENDING = 'pending', 'در انتظار'
    CALCULATED = 'calculated', 'محاسبه شده'
    PAID = 'paid', 'پرداخت شده'
    CANCELLED = 'cancelled', 'لغو شده'
    DISPUTED = 'disputed', 'مورد اختلاف'


class CommissionType(models.TextChoices):
    """انواع کمیسیون"""
    VISIT = 'visit', 'ویزیت'
    SUBSCRIPTION = 'subscription', 'اشتراک'
    REFERRAL = 'referral', 'معرفی'
    BONUS = 'bonus', 'پاداش'
    PENALTY = 'penalty', 'جریمه'


class Commission(BaseModel):
    """مدل کمیسیون پزشکان"""
    
    # کاربر (پزشک)
    doctor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='doctor_commissions',
        verbose_name='پزشک'
    )
    
    # کاربر پرداخت‌کننده (بیمار)
    patient = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='patient_commissions',
        null=True,
        blank=True,
        verbose_name='بیمار'
    )
    
    # نوع و وضعیت
    type = models.CharField(
        max_length=20,
        choices=CommissionType.choices,
        verbose_name='نوع کمیسیون'
    )
    
    status = models.CharField(
        max_length=20,
        choices=CommissionStatus.choices,
        default=CommissionStatus.PENDING,
        verbose_name='وضعیت'
    )
    
    # مبالغ
    gross_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name='مبلغ ناخالص',
        help_text='مبلغ کل قبل از کسر کمیسیون'
    )
    
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='نرخ کمیسیون',
        help_text='درصد کمیسیون پلتفرم'
    )
    
    commission_amount = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name='مبلغ کمیسیون',
        help_text='مبلغ کمیسیون پلتفرم'
    )
    
    net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name='مبلغ خالص',
        help_text='مبلغ خالص پزشک'
    )
    
    # مالیات و کسورات
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='مبلغ مالیات'
    )
    
    other_deductions = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='سایر کسورات'
    )
    
    final_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name='مبلغ نهایی',
        help_text='مبلغ نهایی قابل پرداخت'
    )
    
    # تاریخ‌ها
    calculation_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاریخ محاسبه'
    )
    
    payment_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاریخ پرداخت'
    )
    
    # روابط
    source_transaction = models.ForeignKey(
        Transaction,
        on_delete=models.PROTECT,
        related_name='commissions',
        null=True,
        blank=True,
        verbose_name='تراکنش مبدأ'
    )
    
    payment_transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='تراکنش پرداخت'
    )
    
    # شناسه مرجع خارجی
    external_reference = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='مرجع خارجی',
        help_text='شناسه ویزیت، اشتراک و غیره'
    )
    
    # توضیحات
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='توضیحات'
    )
    
    internal_notes = models.TextField(
        null=True,
        blank=True,
        verbose_name='یادداشت‌های داخلی'
    )
    
    class Meta:
        db_table = 'billing_commissions'
        verbose_name = 'کمیسیون'
        verbose_name_plural = 'کمیسیون‌ها'
        indexes = [
            models.Index(fields=['doctor', 'status']),
            models.Index(fields=['type', 'status']),
            models.Index(fields=['calculation_date']),
            models.Index(fields=['payment_date']),
            models.Index(fields=['external_reference']),
        ]
        ordering = ['-created_at']
        
    def __str__(self):
        return f"کمیسیون {self.doctor.phone_number} - {self.final_amount:,} ریال"
        
    @property
    def commission_percentage(self) -> Decimal:
        """درصد کمیسیون از مبلغ ناخالص"""
        if self.gross_amount == 0:
            return Decimal('0')
        return (self.commission_amount / self.gross_amount) * 100
        
    @property
    def net_percentage(self) -> Decimal:
        """درصد مبلغ خالص از مبلغ ناخالص"""
        if self.gross_amount == 0:
            return Decimal('0')
        return (self.net_amount / self.gross_amount) * 100
        
    def calculate_amounts(self):
        """محاسبه مبالغ مختلف"""
        # محاسبه کمیسیون
        self.commission_amount = self.gross_amount * (self.commission_rate / 100)
        
        # محاسبه مبلغ خالص
        self.net_amount = self.gross_amount - self.commission_amount
        
        # محاسبه مبلغ نهایی
        self.final_amount = self.net_amount - self.tax_amount - self.other_deductions
        
    def mark_calculated(self):
        """علامت‌گذاری به عنوان محاسبه شده"""
        from django.utils import timezone
        
        self.status = CommissionStatus.CALCULATED
        self.calculation_date = timezone.now()
        self.save()
        
    def mark_paid(self, transaction: Transaction = None):
        """علامت‌گذاری به عنوان پرداخت شده"""
        from django.utils import timezone
        
        self.status = CommissionStatus.PAID
        self.payment_date = timezone.now()
        
        if transaction:
            self.payment_transaction = transaction
            
        self.save()
        
    def cancel(self, reason: str = None):
        """لغو کمیسیون"""
        self.status = CommissionStatus.CANCELLED
        if reason:
            self.internal_notes = (self.internal_notes or '') + f"\nلغو: {reason}"
        self.save()
        
    def dispute(self, reason: str = None):
        """علامت‌گذاری به عنوان مورد اختلاف"""
        self.status = CommissionStatus.DISPUTED
        if reason:
            self.internal_notes = (self.internal_notes or '') + f"\nاختلاف: {reason}"
        self.save()
        
    def save(self, *args, **kwargs):
        """ذخیره با محاسبه خودکار مبالغ"""
        self.calculate_amounts()
        super().save(*args, **kwargs)


class Settlement(BaseModel):
    """مدل تسویه حساب دوره‌ای"""
    
    doctor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='settlements',
        verbose_name='پزشک'
    )
    
    # دوره تسویه
    period_start = models.DateTimeField(
        verbose_name='شروع دوره'
    )
    
    period_end = models.DateTimeField(
        verbose_name='پایان دوره'
    )
    
    # آمار دوره
    total_visits = models.IntegerField(
        default=0,
        verbose_name='تعداد ویزیت'
    )
    
    total_gross_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name='کل مبلغ ناخالص'
    )
    
    total_commission = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name='کل کمیسیون'
    )
    
    total_net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name='کل مبلغ خالص'
    )
    
    total_deductions = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name='کل کسورات'
    )
    
    final_settlement_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name='مبلغ نهایی تسویه'
    )
    
    # وضعیت
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'در انتظار'),
            ('calculated', 'محاسبه شده'),
            ('approved', 'تأیید شده'),
            ('paid', 'پرداخت شده'),
            ('cancelled', 'لغو شده'),
        ],
        default='pending',
        verbose_name='وضعیت'
    )
    
    # تاریخ‌ها
    calculated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان محاسبه'
    )
    
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان تأیید'
    )
    
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان پرداخت'
    )
    
    # تراکنش پرداخت
    payment_transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='تراکنش پرداخت'
    )
    
    # یادداشت‌ها
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name='یادداشت‌ها'
    )
    
    class Meta:
        db_table = 'billing_settlements'
        verbose_name = 'تسویه حساب'
        verbose_name_plural = 'تسویه حساب‌ها'
        indexes = [
            models.Index(fields=['doctor', 'period_start', 'period_end']),
            models.Index(fields=['status']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'period_start', 'period_end'],
                name='unique_doctor_settlement_period'
            )
        ]
        
    def __str__(self):
        return f"تسویه {self.doctor.phone_number} - {self.period_start.date()} تا {self.period_end.date()}"
        
    def calculate_settlement(self):
        """محاسبه تسویه حساب"""
        commissions = Commission.objects.filter(
            doctor=self.doctor,
            status=CommissionStatus.CALCULATED,
            calculation_date__gte=self.period_start,
            calculation_date__lte=self.period_end
        )
        
        self.total_visits = commissions.filter(type=CommissionType.VISIT).count()
        self.total_gross_amount = sum(c.gross_amount for c in commissions)
        self.total_commission = sum(c.commission_amount for c in commissions)
        self.total_net_amount = sum(c.net_amount for c in commissions)
        self.total_deductions = sum(c.tax_amount + c.other_deductions for c in commissions)
        self.final_settlement_amount = sum(c.final_amount for c in commissions)
        
        self.status = 'calculated'
        self.calculated_at = timezone.now()
        self.save()
        
    def approve(self):
        """تأیید تسویه حساب"""
        from django.utils import timezone
        
        if self.status != 'calculated':
            raise ValueError("تسویه حساب باید ابتدا محاسبه شود")
            
        self.status = 'approved'
        self.approved_at = timezone.now()
        self.save()
        
    def mark_paid(self, transaction: Transaction):
        """علامت‌گذاری به عنوان پرداخت شده"""
        from django.utils import timezone
        
        self.status = 'paid'
        self.paid_at = timezone.now()
        self.payment_transaction = transaction
        self.save()
        
        # علامت‌گذاری کمیسیون‌های مرتبط
        Commission.objects.filter(
            doctor=self.doctor,
            status=CommissionStatus.CALCULATED,
            calculation_date__gte=self.period_start,
            calculation_date__lte=self.period_end
        ).update(
            status=CommissionStatus.PAID,
            payment_date=timezone.now(),
            payment_transaction=transaction
        )