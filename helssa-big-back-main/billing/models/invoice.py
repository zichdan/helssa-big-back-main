"""
مدل فاکتور و صورت‌حساب
Invoice and Billing Model
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
from .base import BaseModel
from .subscription import Subscription
from .transaction import Transaction

User = get_user_model()


class InvoiceStatus(models.TextChoices):
    """وضعیت‌های فاکتور"""
    DRAFT = 'draft', 'پیش‌نویس'
    PENDING = 'pending', 'در انتظار پرداخت'
    PAID = 'paid', 'پرداخت شده'
    PARTIAL = 'partial', 'پرداخت جزئی'
    CANCELLED = 'cancelled', 'لغو شده'
    REFUNDED = 'refunded', 'بازگشت داده شده'
    OVERDUE = 'overdue', 'سررسید گذشته'


class InvoiceType(models.TextChoices):
    """انواع فاکتور"""
    SUBSCRIPTION = 'subscription', 'اشتراک'
    VISIT = 'visit', 'ویزیت'
    TOPUP = 'topup', 'شارژ کیف پول'
    COMMISSION = 'commission', 'کمیسیون'
    REFUND = 'refund', 'بازگشت وجه'
    PENALTY = 'penalty', 'جریمه'
    ADJUSTMENT = 'adjustment', 'تعدیل'


class Invoice(BaseModel):
    """مدل فاکتور و صورت‌حساب"""
    
    # شناسه‌ها
    invoice_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name='شماره فاکتور'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='invoices',
        verbose_name='کاربر'
    )
    
    # نوع و وضعیت
    type = models.CharField(
        max_length=20,
        choices=InvoiceType.choices,
        verbose_name='نوع فاکتور'
    )
    
    status = models.CharField(
        max_length=20,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.DRAFT,
        verbose_name='وضعیت'
    )
    
    # مبالغ
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name='مبلغ کل',
        help_text='مبلغ قبل از تخفیف و مالیات'
    )
    
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='مبلغ تخفیف'
    )
    
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='مبلغ مالیات'
    )
    
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name='مبلغ نهایی'
    )
    
    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='مبلغ پرداخت شده'
    )
    
    # تاریخ‌ها
    issue_date = models.DateTimeField(
        verbose_name='تاریخ صدور'
    )
    
    due_date = models.DateTimeField(
        verbose_name='تاریخ سررسید'
    )
    
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان پرداخت'
    )
    
    # روابط
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        verbose_name='اشتراک'
    )
    
    related_invoice = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='فاکتور مرتبط'
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
    
    # کد تخفیف
    coupon_code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='کد تخفیف'
    )
    
    # اطلاعات پرداخت
    payment_method = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='روش پرداخت'
    )
    
    payment_reference = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='مرجع پرداخت'
    )
    
    class Meta:
        db_table = 'billing_invoices'
        verbose_name = 'فاکتور'
        verbose_name_plural = 'فاکتورها'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['invoice_number']),
            models.Index(fields=['type', 'status']),
            models.Index(fields=['due_date', 'status']),
            models.Index(fields=['subscription']),
        ]
        ordering = ['-created_at']
        
    def __str__(self):
        return f"فاکتور {self.invoice_number} - {self.total_amount:,} ریال"
        
    @property
    def is_paid(self) -> bool:
        """آیا کاملاً پرداخت شده؟"""
        return self.status == InvoiceStatus.PAID
        
    @property
    def is_overdue(self) -> bool:
        """آیا سررسید گذشته؟"""
        from django.utils import timezone
        return (
            self.status in [InvoiceStatus.PENDING, InvoiceStatus.PARTIAL] and
            self.due_date < timezone.now()
        )
        
    @property
    def remaining_amount(self) -> Decimal:
        """مبلغ باقی‌مانده"""
        return self.total_amount - self.paid_amount
        
    @property
    def payment_percentage(self) -> float:
        """درصد پرداخت"""
        if self.total_amount == 0:
            return 0
        return float((self.paid_amount / self.total_amount) * 100)
        
    def calculate_total(self):
        """محاسبه مبلغ نهایی"""
        self.total_amount = self.subtotal - self.discount_amount + self.tax_amount
        
    def mark_as_paid(self, transaction: Transaction = None):
        """علامت‌گذاری به عنوان پرداخت شده"""
        from django.utils import timezone
        
        self.status = InvoiceStatus.PAID
        self.paid_amount = self.total_amount
        self.paid_at = timezone.now()
        
        if transaction:
            self.payment_method = transaction.gateway or 'wallet'
            self.payment_reference = transaction.reference_number
            
        self.save()
        
    def add_payment(self, amount: Decimal, transaction: Transaction = None):
        """اضافه کردن پرداخت جزئی"""
        from django.utils import timezone
        
        self.paid_amount += amount
        
        if self.paid_amount >= self.total_amount:
            self.status = InvoiceStatus.PAID
            self.paid_at = timezone.now()
        elif self.paid_amount > 0:
            self.status = InvoiceStatus.PARTIAL
            
        if transaction and not self.payment_reference:
            self.payment_method = transaction.gateway or 'wallet'
            self.payment_reference = transaction.reference_number
            
        self.save()
        
    def cancel(self, reason: str = None):
        """لغو فاکتور"""
        self.status = InvoiceStatus.CANCELLED
        if reason:
            self.internal_notes = (self.internal_notes or '') + f"\nلغو: {reason}"
        self.save()
        
    def refund(self, amount: Decimal = None, reason: str = None):
        """بازگشت وجه"""
        refund_amount = amount or self.paid_amount
        
        if refund_amount > self.paid_amount:
            raise ValueError("مبلغ بازگشت نمی‌تواند بیشتر از مبلغ پرداخت شده باشد")
            
        self.paid_amount -= refund_amount
        
        if self.paid_amount == 0:
            self.status = InvoiceStatus.REFUNDED
        elif self.paid_amount < self.total_amount:
            self.status = InvoiceStatus.PARTIAL
            
        if reason:
            self.internal_notes = (self.internal_notes or '') + f"\nبازگشت: {reason}"
            
        self.save()
        
    def generate_invoice_number(self):
        """تولید شماره فاکتور"""
        from django.utils import timezone
        
        now = timezone.now()
        year = now.strftime('%Y')
        month = now.strftime('%m')
        
        # یافتن آخرین شماره فاکتور در ماه جاری
        prefix = f"INV{year}{month}"
        last_invoice = Invoice.objects.filter(
            invoice_number__startswith=prefix
        ).order_by('-invoice_number').first()
        
        if last_invoice:
            last_number = int(last_invoice.invoice_number[-4:])
            new_number = last_number + 1
        else:
            new_number = 1
            
        self.invoice_number = f"{prefix}{new_number:04d}"
        
    def save(self, *args, **kwargs):
        """ذخیره با تولید شماره فاکتور"""
        if not self.invoice_number:
            self.generate_invoice_number()
            
        # محاسبه مبلغ نهایی
        self.calculate_total()
        
        super().save(*args, **kwargs)


class InvoiceItem(BaseModel):
    """آیتم‌های فاکتور"""
    
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='فاکتور'
    )
    
    # توضیحات آیتم
    description = models.CharField(
        max_length=200,
        verbose_name='شرح'
    )
    
    # مقدار و قیمت
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(0.01)],
        verbose_name='تعداد'
    )
    
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name='قیمت واحد'
    )
    
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name='قیمت کل'
    )
    
    # تخفیف
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='درصد تخفیف'
    )
    
    # نوع آیتم
    item_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='نوع آیتم'
    )
    
    # شناسه مرجع (برای پیوند با سایر مدل‌ها)
    reference_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='شناسه مرجع'
    )
    
    class Meta:
        db_table = 'billing_invoice_items'
        verbose_name = 'آیتم فاکتور'
        verbose_name_plural = 'آیتم‌های فاکتور'
        
    def __str__(self):
        return f"{self.description} - {self.total_price:,} ریال"
        
    def calculate_total(self):
        """محاسبه قیمت کل آیتم"""
        base_total = self.quantity * self.unit_price
        if self.discount_percent > 0:
            discount = base_total * (self.discount_percent / 100)
            self.total_price = base_total - discount
        else:
            self.total_price = base_total
            
    def save(self, *args, **kwargs):
        """ذخیره با محاسبه قیمت کل"""
        self.calculate_total()
        super().save(*args, **kwargs)