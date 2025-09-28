"""
مدل تراکنش‌های مالی
Financial Transactions Model
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from .base import BaseModel
from .wallet import Wallet


class TransactionType(models.TextChoices):
    """انواع تراکنش"""
    DEPOSIT = 'deposit', 'واریز'
    WITHDRAWAL = 'withdrawal', 'برداشت'
    PAYMENT = 'payment', 'پرداخت'
    REFUND = 'refund', 'بازگشت'
    TRANSFER_IN = 'transfer_in', 'انتقال ورودی'
    TRANSFER_OUT = 'transfer_out', 'انتقال خروجی'
    COMMISSION = 'commission', 'کمیسیون'
    SUBSCRIPTION = 'subscription', 'اشتراک'
    VISIT_PAYMENT = 'visit_payment', 'پرداخت ویزیت'
    GIFT_CREDIT = 'gift_credit', 'اعتبار هدیه'


class TransactionStatus(models.TextChoices):
    """وضعیت‌های تراکنش"""
    PENDING = 'pending', 'در انتظار'
    PROCESSING = 'processing', 'در حال پردازش'
    COMPLETED = 'completed', 'تکمیل شده'
    FAILED = 'failed', 'ناموفق'
    CANCELLED = 'cancelled', 'لغو شده'
    REFUNDED = 'refunded', 'بازگشت داده شده'


class PaymentGateway(models.TextChoices):
    """درگاه‌های پرداخت"""
    BITPAY = 'bitpay', 'BitPay.ir'
    ZARINPAL = 'zarinpal', 'ZarinPal'
    IDPAY = 'idpay', 'IDPay'
    STRIPE = 'stripe', 'Stripe'
    WALLET = 'wallet', 'کیف پول'


class Transaction(BaseModel):
    """مدل تراکنش‌های مالی"""
    
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name='کیف پول'
    )
    
    # مشخصات تراکنش
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name='مبلغ',
        help_text='مبلغ به ریال (مثبت: واریز، منفی: برداشت)'
    )
    
    type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        verbose_name='نوع تراکنش'
    )
    
    status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
        verbose_name='وضعیت'
    )
    
    # شماره مرجع
    reference_number = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name='شماره مرجع'
    )
    
    gateway_reference = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        verbose_name='مرجع درگاه'
    )
    
    # اطلاعات پرداخت
    gateway = models.CharField(
        max_length=20,
        choices=PaymentGateway.choices,
        null=True,
        blank=True,
        verbose_name='درگاه پرداخت'
    )
    
    # روابط
    related_transaction = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_transactions',
        verbose_name='تراکنش مرتبط'
    )
    
    related_wallet = models.ForeignKey(
        Wallet,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_transactions',
        verbose_name='کیف پول مرتبط'
    )
    
    # توضیحات
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='توضیحات'
    )
    
    # زمان‌ها
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان تکمیل'
    )
    
    # اطلاعات اضافی
    fee_amount = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='مبلغ کارمزد'
    )
    
    exchange_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name='نرخ تبدیل ارز'
    )
    
    # IP و اطلاعات امنیتی
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='آدرس IP'
    )
    
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name='User Agent'
    )
    
    class Meta:
        db_table = 'billing_transactions'
        verbose_name = 'تراکنش'
        verbose_name_plural = 'تراکنش‌ها'
        indexes = [
            models.Index(fields=['wallet', 'status', 'created_at']),
            models.Index(fields=['type', 'status']),
            models.Index(fields=['reference_number']),
            models.Index(fields=['gateway_reference']),
            models.Index(fields=['gateway', 'status']),
            models.Index(fields=['completed_at']),
        ]
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.get_type_display()} - {self.amount:,} ریال - {self.get_status_display()}"
        
    @property
    def is_income(self) -> bool:
        """آیا این تراکنش درآمد است؟"""
        return self.amount > 0
        
    @property
    def is_expense(self) -> bool:
        """آیا این تراکنش هزینه است؟"""
        return self.amount < 0
        
    @property
    def net_amount(self) -> Decimal:
        """مبلغ خالص (بدون کارمزد)"""
        if self.is_income:
            return self.amount - self.fee_amount
        else:
            return self.amount + self.fee_amount
            
    def mark_completed(self, gateway_reference: str = None):
        """علامت‌گذاری به عنوان تکمیل شده"""
        self.status = TransactionStatus.COMPLETED
        self.completed_at = timezone.now()
        if gateway_reference:
            self.gateway_reference = gateway_reference
        self.save()
        
    def mark_failed(self, reason: str = None):
        """علامت‌گذاری به عنوان ناموفق"""
        self.status = TransactionStatus.FAILED
        if reason:
            self.metadata['failure_reason'] = reason
        self.save()
        
    def mark_cancelled(self, reason: str = None):
        """علامت‌گذاری به عنوان لغو شده"""
        self.status = TransactionStatus.CANCELLED
        if reason:
            self.metadata['cancellation_reason'] = reason
        self.save()
        
    def can_be_refunded(self) -> bool:
        """آیا قابل بازگشت است؟"""
        return (
            self.status == TransactionStatus.COMPLETED and
            self.type in [TransactionType.PAYMENT, TransactionType.SUBSCRIPTION] and
            self.amount > 0
        )
        
    def create_refund(self, amount: Decimal = None, description: str = '') -> 'Transaction':
        """ایجاد تراکنش بازگشت"""
        if not self.can_be_refunded():
            raise ValueError("این تراکنش قابل بازگشت نیست")
            
        refund_amount = amount or self.amount
        if refund_amount > self.amount:
            raise ValueError("مبلغ بازگشت نمی‌تواند بیشتر از مبلغ اصلی باشد")
            
        return Transaction.objects.create(
            wallet=self.wallet,
            amount=refund_amount,
            type=TransactionType.REFUND,
            status=TransactionStatus.COMPLETED,
            reference_number=f"REF_{self.reference_number}",
            related_transaction=self,
            description=description or f"بازگشت تراکنش {self.reference_number}",
            gateway=self.gateway
        )