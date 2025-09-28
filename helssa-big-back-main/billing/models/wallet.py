"""
مدل کیف پول دیجیتال
Digital Wallet Model
"""

from decimal import Decimal
from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
from .base import BaseModel

User = get_user_model()


class Wallet(BaseModel):
    """مدل کیف پول دیجیتال"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        related_name='wallet',
        verbose_name='کاربر'
    )
    
    # موجودی‌ها
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='موجودی',
        help_text='موجودی به ریال'
    )
    
    blocked_balance = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='موجودی بلوکه شده',
        help_text='موجودی بلوکه شده به ریال'
    )
    
    # اعتبار هدیه
    gift_credit = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='اعتبار هدیه',
        help_text='اعتبار هدیه به ریال'
    )
    
    gift_credit_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاریخ انقضای اعتبار هدیه'
    )
    
    # وضعیت تأیید
    is_verified = models.BooleanField(
        default=False,
        verbose_name='تأیید شده'
    )
    
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان تأیید'
    )
    
    # محدودیت‌های برداشت
    daily_withdrawal_limit = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=50000000,  # 50 میلیون ریال
        verbose_name='محدودیت برداشت روزانه'
    )
    
    monthly_withdrawal_limit = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=500000000,  # 500 میلیون ریال
        verbose_name='محدودیت برداشت ماهانه'
    )
    
    # زمان آخرین تراکنش
    last_transaction_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='آخرین تراکنش'
    )
    
    class Meta:
        db_table = 'billing_wallets'
        verbose_name = 'کیف پول'
        verbose_name_plural = 'کیف پول‌ها'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['is_verified']),
        ]
        
    def __str__(self):
        return f"کیف پول {self.user.phone_number} - موجودی: {self.balance:,} ریال"
        
    @property
    def available_balance(self) -> Decimal:
        """موجودی قابل استفاده"""
        return self.balance - self.blocked_balance
        
    @property
    def total_credit(self) -> Decimal:
        """کل اعتبار (موجودی + اعتبار هدیه)"""
        gift_amount = 0
        if self.gift_credit > 0 and self.gift_credit_expires_at:
            if timezone.now() < self.gift_credit_expires_at:
                gift_amount = self.gift_credit
        return self.available_balance + gift_amount
        
    def has_sufficient_balance(self, amount: Decimal) -> bool:
        """بررسی کفایت موجودی"""
        return self.total_credit >= amount
        
    def can_withdraw(self, amount: Decimal) -> bool:
        """بررسی امکان برداشت"""
        return (
            self.is_active and
            self.available_balance >= amount and
            amount > 0
        )
        
    @transaction.atomic
    def deposit(self, amount: Decimal, description: str = '') -> bool:
        """واریز به کیف پول"""
        if amount <= 0:
            return False
            
        self.balance += amount
        self.last_transaction_at = timezone.now()
        self.save()
        
        return True
        
    @transaction.atomic
    def withdraw(self, amount: Decimal, description: str = '') -> bool:
        """برداشت از کیف پول"""
        if not self.can_withdraw(amount):
            return False
            
        self.balance -= amount
        self.last_transaction_at = timezone.now()
        self.save()
        
        return True
        
    @transaction.atomic
    def block_amount(self, amount: Decimal) -> bool:
        """بلوک کردن مبلغ"""
        if self.available_balance < amount:
            return False
            
        self.blocked_balance += amount
        self.save()
        return True
        
    @transaction.atomic
    def unblock_amount(self, amount: Decimal) -> bool:
        """آزاد کردن مبلغ بلوک شده"""
        if self.blocked_balance < amount:
            return False
            
        self.blocked_balance -= amount
        self.save()
        return True
        
    def verify_wallet(self):
        """تأیید کیف پول"""
        self.is_verified = True
        self.verified_at = timezone.now()
        self.save()
        
    def expire_gift_credit(self):
        """منقضی کردن اعتبار هدیه"""
        if self.gift_credit > 0:
            self.gift_credit = 0
            self.gift_credit_expires_at = None
            self.save()