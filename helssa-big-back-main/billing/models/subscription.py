"""
مدل اشتراک کاربران
User Subscriptions Model
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .base import BaseModel
from .plan import SubscriptionPlan

User = get_user_model()


class SubscriptionStatus(models.TextChoices):
    """وضعیت‌های اشتراک"""
    TRIAL = 'trial', 'دوره آزمایشی'
    ACTIVE = 'active', 'فعال'
    PAST_DUE = 'past_due', 'معوق'
    CANCELLED = 'cancelled', 'لغو شده'
    EXPIRED = 'expired', 'منقضی شده'
    SUSPENDED = 'suspended', 'تعلیق شده'


class BillingCycle(models.TextChoices):
    """دوره‌های صورت‌حساب"""
    MONTHLY = 'monthly', 'ماهانه'
    YEARLY = 'yearly', 'سالانه'


class PaymentMethod(models.TextChoices):
    """روش‌های پرداخت"""
    WALLET = 'wallet', 'کیف پول'
    CARD = 'card', 'کارت بانکی'
    GATEWAY = 'gateway', 'درگاه پرداخت'


class Subscription(BaseModel):
    """مدل اشتراک کاربران"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name='کاربر'
    )
    
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        verbose_name='پلن'
    )
    
    # وضعیت
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.TRIAL,
        verbose_name='وضعیت'
    )
    
    # دوره اشتراک
    billing_cycle = models.CharField(
        max_length=10,
        choices=BillingCycle.choices,
        default=BillingCycle.MONTHLY,
        verbose_name='دوره صورت‌حساب'
    )
    
    # تاریخ‌ها
    trial_end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='پایان دوره آزمایشی'
    )
    
    start_date = models.DateTimeField(
        verbose_name='تاریخ شروع'
    )
    
    end_date = models.DateTimeField(
        verbose_name='تاریخ پایان'
    )
    
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان لغو'
    )
    
    suspended_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان تعلیق'
    )
    
    # پرداخت
    auto_renew = models.BooleanField(
        default=True,
        verbose_name='تمدید خودکار'
    )
    
    next_billing_date = models.DateTimeField(
        verbose_name='تاریخ صورت‌حساب بعدی'
    )
    
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.WALLET,
        verbose_name='روش پرداخت'
    )
    
    # استفاده از منابع
    usage_data = models.JSONField(
        default=dict,
        verbose_name='داده‌های استفاده',
        help_text='آمار استفاده از ویژگی‌های پلن'
    )
    
    # تخفیفات
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='درصد تخفیف'
    )
    
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        verbose_name='مبلغ تخفیف'
    )
    
    # کد تخفیف
    coupon_code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='کد تخفیف'
    )
    
    # تنظیمات ویژه
    custom_limits = models.JSONField(
        default=dict,
        verbose_name='محدودیت‌های سفارشی',
        help_text='محدودیت‌های خاص این اشتراک'
    )
    
    # علت لغو
    cancellation_reason = models.TextField(
        null=True,
        blank=True,
        verbose_name='علت لغو'
    )
    
    # یادداشت‌های داخلی
    internal_notes = models.TextField(
        null=True,
        blank=True,
        verbose_name='یادداشت‌های داخلی'
    )
    
    class Meta:
        db_table = 'billing_subscriptions'
        verbose_name = 'اشتراک'
        verbose_name_plural = 'اشتراک‌ها'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['plan', 'status']),
            models.Index(fields=['status', 'next_billing_date']),
            models.Index(fields=['end_date', 'status']),
            models.Index(fields=['trial_end_date']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(status__in=['trial', 'active']),
                name='unique_active_subscription_per_user'
            )
        ]
        
    def __str__(self):
        return f"{self.user.phone_number} - {self.plan.name} ({self.get_status_display()})"
        
    @property
    def is_active(self) -> bool:
        """آیا اشتراک فعال است؟"""
        return self.status in [SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE]
        
    @property
    def is_expired(self) -> bool:
        """آیا اشتراک منقضی شده؟"""
        now = timezone.now()
        return self.end_date < now and self.status != SubscriptionStatus.CANCELLED
        
    @property
    def days_remaining(self) -> int:
        """روزهای باقی‌مانده تا انقضا"""
        if self.is_expired:
            return 0
        return (self.end_date - timezone.now()).days
        
    @property
    def is_in_trial(self) -> bool:
        """آیا در دوره آزمایشی است؟"""
        return (
            self.status == SubscriptionStatus.TRIAL and
            self.trial_end_date and
            timezone.now() < self.trial_end_date
        )
        
    @property
    def effective_price(self) -> Decimal:
        """قیمت مؤثر با احتساب تخفیف"""
        base_price = self.plan.calculate_price(self.billing_cycle)
        
        if self.discount_amount > 0:
            return max(0, base_price - self.discount_amount)
        elif self.discount_percent > 0:
            discount = base_price * (self.discount_percent / 100)
            return max(0, base_price - discount)
        
        return base_price
        
    def get_usage(self, feature: str) -> int:
        """دریافت میزان استفاده از یک ویژگی"""
        return self.usage_data.get(feature, 0)
        
    def get_limit(self, feature: str) -> int:
        """دریافت محدودیت یک ویژگی"""
        # ابتدا محدودیت‌های سفارشی را بررسی کن
        if feature in self.custom_limits:
            return self.custom_limits[feature]
        
        # سپس محدودیت‌های پلن
        return self.plan.get_limit(feature, -1)  # -1 یعنی نامحدود
        
    def can_use_feature(self, feature: str, amount: int = 1) -> bool:
        """بررسی امکان استفاده از ویژگی"""
        if not self.is_active:
            return False
            
        limit = self.get_limit(feature)
        if limit == -1:  # نامحدود
            return True
            
        current_usage = self.get_usage(feature)
        return current_usage + amount <= limit
        
    def use_feature(self, feature: str, amount: int = 1) -> bool:
        """استفاده از ویژگی و به‌روزرسانی آمار"""
        if not self.can_use_feature(feature, amount):
            return False
            
        current_usage = self.get_usage(feature)
        self.usage_data[feature] = current_usage + amount
        self.save()
        return True
        
    def reset_usage(self):
        """ریست کردن آمار استفاده (معمولاً در شروع دوره جدید)"""
        self.usage_data = {}
        self.save()
        
    def extend_subscription(self, days: int):
        """تمدید اشتراک"""
        self.end_date += timedelta(days=days)
        if self.billing_cycle == BillingCycle.MONTHLY:
            self.next_billing_date += timedelta(days=30)
        else:
            self.next_billing_date += timedelta(days=365)
        self.save()
        
    def cancel(self, reason: str = None, immediate: bool = False):
        """لغو اشتراک"""
        self.status = SubscriptionStatus.CANCELLED
        self.cancelled_at = timezone.now()
        self.auto_renew = False
        
        if reason:
            self.cancellation_reason = reason
            
        if immediate:
            self.end_date = timezone.now()
            
        self.save()
        
    def suspend(self, reason: str = None):
        """تعلیق اشتراک"""
        self.status = SubscriptionStatus.SUSPENDED
        self.suspended_at = timezone.now()
        
        if reason:
            self.internal_notes = (self.internal_notes or '') + f"\nتعلیق: {reason}"
            
        self.save()
        
    def reactivate(self):
        """فعال‌سازی مجدد اشتراک"""
        if self.status == SubscriptionStatus.SUSPENDED:
            self.status = SubscriptionStatus.ACTIVE
            self.suspended_at = None
            self.save()
            
    def mark_past_due(self):
        """علامت‌گذاری به عنوان معوق"""
        self.status = SubscriptionStatus.PAST_DUE
        self.save()
        
    def calculate_proration(self, new_plan: SubscriptionPlan) -> Decimal:
        """محاسبه مبلغ تناسبی برای تغییر پلن"""
        days_remaining = self.days_remaining
        if days_remaining <= 0:
            return Decimal('0')
            
        # محاسبه اعتبار باقی‌مانده از پلن فعلی
        if self.billing_cycle == BillingCycle.MONTHLY:
            total_days = 30
            old_daily_rate = self.effective_price / total_days
        else:
            total_days = 365
            old_daily_rate = self.effective_price / total_days
            
        remaining_credit = old_daily_rate * days_remaining
        
        # محاسبه هزینه پلن جدید
        new_price = new_plan.calculate_price(self.billing_cycle)
        new_daily_rate = new_price / total_days
        new_cost = new_daily_rate * days_remaining
        
        return new_cost - remaining_credit