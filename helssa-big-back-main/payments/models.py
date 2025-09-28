"""
مدل‌های اپلیکیشن پرداخت
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from decimal import Decimal
import uuid
import jdatetime

User = get_user_model()


class BasePaymentModel(models.Model):
    """
    مدل پایه برای تمام مدل‌های پرداخت
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ایجاد'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاریخ آخرین بروزرسانی'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    
    class Meta:
        abstract = True
        
    def get_jalali_created(self):
        """برگرداندن تاریخ ایجاد به شمسی"""
        return jdatetime.datetime.fromgregorian(datetime=self.created_at)


class PaymentMethod(BasePaymentModel):
    """
    روش‌های پرداخت
    """
    METHOD_CHOICES = [
        ('online', 'پرداخت آنلاین'),
        ('card', 'کارت به کارت'),
        ('wallet', 'کیف پول'),
        ('insurance', 'بیمه'),
        ('installment', 'اقساط'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payment_methods',
        verbose_name='کاربر'
    )
    method_type = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES,
        verbose_name='نوع روش پرداخت'
    )
    title = models.CharField(
        max_length=100,
        verbose_name='عنوان'
    )
    details = models.JSONField(
        default=dict,
        verbose_name='جزئیات',
        help_text='اطلاعات خاص هر روش پرداخت'
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name='پیش‌فرض'
    )
    
    class Meta:
        verbose_name = 'روش پرداخت'
        verbose_name_plural = 'روش‌های پرداخت'
        unique_together = [['user', 'title']]
        ordering = ['-is_default', '-created_at']
        
    def __str__(self):
        return f"{self.title} - {self.user}"


class Payment(BasePaymentModel):
    """
    مدل اصلی پرداخت‌ها
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('processing', 'در حال پردازش'),
        ('success', 'موفق'),
        ('failed', 'ناموفق'),
        ('cancelled', 'لغو شده'),
        ('refunded', 'بازگشت داده شده'),
        ('partially_refunded', 'بازگشت جزئی'),
    ]
    
    PAYMENT_TYPE_CHOICES = [
        # انواع پرداخت بیمار
        ('appointment', 'نوبت پزشکی'),
        ('consultation', 'مشاوره آنلاین'),
        ('medication', 'دارو'),
        ('test', 'آزمایش'),
        ('imaging', 'تصویربرداری'),
        ('procedure', 'عملیات پزشکی'),
        # انواع پرداخت دکتر
        ('withdrawal', 'برداشت'),
        ('subscription', 'اشتراک'),
        ('commission', 'کمیسیون'),
        ('refund', 'بازپرداخت'),
        ('adjustment', 'تعدیل حساب'),
    ]
    
    payment_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='شناسه پرداخت'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='payments',
        verbose_name='کاربر'
    )
    user_type = models.CharField(
        max_length=10,
        choices=[('doctor', 'پزشک'), ('patient', 'بیمار')],
        verbose_name='نوع کاربر'
    )
    payment_type = models.CharField(
        max_length=30,
        choices=PAYMENT_TYPE_CHOICES,
        verbose_name='نوع پرداخت'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='مبلغ (ریال)'
    )
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name='وضعیت'
    )
    tracking_code = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name='کد پیگیری'
    )
    description = models.TextField(
        blank=True,
        verbose_name='توضیحات'
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name='روش پرداخت'
    )
    gateway_response = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='پاسخ درگاه'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='اطلاعات تکمیلی'
    )
    
    # فیلدهای مرتبط با سایر مدل‌ها (در صورت وجود)
    appointment_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='شناسه نوبت'
    )
    doctor_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='شناسه پزشک'
    )
    
    # زمان‌های مهم
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان پرداخت'
    )
    failed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان شکست'
    )
    refunded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان بازپرداخت'
    )
    
    class Meta:
        verbose_name = 'پرداخت'
        verbose_name_plural = 'پرداخت‌ها'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['tracking_code']),
            models.Index(fields=['payment_type', 'status']),
            models.Index(fields=['created_at']),
        ]
        
    def __str__(self):
        return f"{self.payment_type} - {self.amount} - {self.user}"
    
    def save(self, *args, **kwargs):
        if not self.tracking_code:
            self.tracking_code = self.generate_tracking_code()
        super().save(*args, **kwargs)
        
    def generate_tracking_code(self):
        """تولید کد پیگیری یکتا"""
        import random
        import string
        from django.utils import timezone
        
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_suffix = ''.join(random.choices(string.digits, k=6))
        return f"PAY{timestamp}{random_suffix}"


class Transaction(BasePaymentModel):
    """
    تراکنش‌های مالی
    """
    TRANSACTION_TYPE_CHOICES = [
        ('payment', 'پرداخت'),
        ('refund', 'بازپرداخت'),
        ('commission', 'کمیسیون'),
        ('withdrawal', 'برداشت'),
        ('deposit', 'واریز'),
    ]
    
    transaction_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='شناسه تراکنش'
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='پرداخت'
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        verbose_name='نوع تراکنش'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name='مبلغ (ریال)'
    )
    reference_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='شماره مرجع'
    )
    gateway_name = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='نام درگاه'
    )
    card_number_masked = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='شماره کارت (ماسک شده)',
        validators=[
            RegexValidator(
                regex=r'^\d{6}\*{6}\d{4}$',
                message='فرمت شماره کارت نامعتبر است'
            )
        ]
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'موفق'),
            ('failed', 'ناموفق'),
            ('reversed', 'برگشت خورده'),
        ],
        verbose_name='وضعیت'
    )
    
    class Meta:
        verbose_name = 'تراکنش'
        verbose_name_plural = 'تراکنش‌ها'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} - {self.payment.user}"


class Wallet(BasePaymentModel):
    """
    کیف پول کاربران
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='wallet',
        verbose_name='کاربر'
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='موجودی (ریال)'
    )
    blocked_balance = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='موجودی مسدود شده (ریال)'
    )
    last_transaction_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='آخرین تراکنش'
    )
    
    class Meta:
        verbose_name = 'کیف پول'
        verbose_name_plural = 'کیف پول‌ها'
        
    def __str__(self):
        return f"کیف پول {self.user} - موجودی: {self.balance}"
    
    @property
    def available_balance(self):
        """موجودی قابل استفاده"""
        return self.balance - self.blocked_balance


class WalletTransaction(BasePaymentModel):
    """
    تراکنش‌های کیف پول
    """
    TRANSACTION_TYPE_CHOICES = [
        ('deposit', 'واریز'),
        ('withdraw', 'برداشت'),
        ('payment', 'پرداخت'),
        ('refund', 'بازگشت'),
        ('commission', 'کمیسیون'),
        ('block', 'مسدودسازی'),
        ('unblock', 'رفع مسدودی'),
    ]
    
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='کیف پول'
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        verbose_name='نوع تراکنش'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name='مبلغ (ریال)'
    )
    balance_before = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name='موجودی قبل'
    )
    balance_after = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name='موجودی بعد'
    )
    description = models.TextField(
        blank=True,
        verbose_name='توضیحات'
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wallet_transactions',
        verbose_name='پرداخت مرتبط'
    )
    
    class Meta:
        verbose_name = 'تراکنش کیف پول'
        verbose_name_plural = 'تراکنش‌های کیف پول'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} - {self.wallet.user}"


class PaymentGateway(BasePaymentModel):
    """
    درگاه‌های پرداخت
    """
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='نام درگاه'
    )
    display_name = models.CharField(
        max_length=100,
        verbose_name='نام نمایشی'
    )
    gateway_type = models.CharField(
        max_length=20,
        choices=[
            ('bank', 'بانکی'),
            ('wallet', 'کیف پول'),
            ('crypto', 'رمزارز'),
        ],
        verbose_name='نوع درگاه'
    )
    configuration = models.JSONField(
        default=dict,
        verbose_name='تنظیمات'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    priority = models.IntegerField(
        default=0,
        verbose_name='اولویت',
        help_text='عدد بالاتر = اولویت بیشتر'
    )
    
    class Meta:
        verbose_name = 'درگاه پرداخت'
        verbose_name_plural = 'درگاه‌های پرداخت'
        ordering = ['-priority', 'name']
        
    def __str__(self):
        return self.display_name