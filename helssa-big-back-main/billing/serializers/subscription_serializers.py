"""
Serializer های اشتراک
Subscription Serializers
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import SubscriptionPlan, BillingCycle, PaymentMethod

User = get_user_model()


class CreateSubscriptionSerializer(serializers.Serializer):
    """Serializer ایجاد اشتراک"""
    
    plan_id = serializers.UUIDField(
        help_text='شناسه پلن اشتراک'
    )
    
    billing_cycle = serializers.ChoiceField(
        choices=BillingCycle.choices,
        default=BillingCycle.MONTHLY,
        help_text='دوره صورت‌حساب'
    )
    
    payment_method = serializers.ChoiceField(
        choices=PaymentMethod.choices,
        default=PaymentMethod.WALLET,
        help_text='روش پرداخت'
    )
    
    start_trial = serializers.BooleanField(
        default=True,
        help_text='شروع دوره آزمایشی'
    )
    
    coupon_code = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        help_text='کد تخفیف (اختیاری)'
    )
    
    def validate_plan_id(self, value):
        """اعتبارسنجی پلن"""
        try:
            plan = SubscriptionPlan.objects.get(id=value, is_active=True, is_public=True)
            return value
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError('پلن یافت نشد یا غیرفعال است')


class UpgradeSubscriptionSerializer(serializers.Serializer):
    """Serializer ارتقاء اشتراک"""
    
    subscription_id = serializers.UUIDField(
        help_text='شناسه اشتراک فعلی'
    )
    
    new_plan_id = serializers.UUIDField(
        help_text='شناسه پلن جدید'
    )
    
    def validate_new_plan_id(self, value):
        """اعتبارسنجی پلن جدید"""
        try:
            plan = SubscriptionPlan.objects.get(id=value, is_active=True)
            return value
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError('پلن جدید یافت نشد')


class CancelSubscriptionSerializer(serializers.Serializer):
    """Serializer لغو اشتراک"""
    
    subscription_id = serializers.UUIDField(
        help_text='شناسه اشتراک'
    )
    
    reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text='دلیل لغو (اختیاری)'
    )
    
    immediate = serializers.BooleanField(
        default=False,
        help_text='لغو فوری'
    )


class UsageLimitSerializer(serializers.Serializer):
    """Serializer بررسی محدودیت استفاده"""
    
    resource = serializers.CharField(
        max_length=50,
        help_text='نام منبع'
    )
    
    amount = serializers.IntegerField(
        default=1,
        min_value=1,
        help_text='مقدار استفاده'
    )


class SubscriptionInfoSerializer(serializers.Serializer):
    """Serializer اطلاعات اشتراک"""
    
    subscription_id = serializers.UUIDField(read_only=True)
    
    plan = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(read_only=True)
    billing_cycle = serializers.CharField(read_only=True)
    start_date = serializers.DateTimeField(read_only=True)
    end_date = serializers.DateTimeField(read_only=True)
    next_billing_date = serializers.DateTimeField(read_only=True)
    auto_renew = serializers.BooleanField(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    is_in_trial = serializers.BooleanField(read_only=True)
    trial_end_date = serializers.DateTimeField(read_only=True)
    usage_data = serializers.JSONField(read_only=True)
    effective_price = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
    discount_percent = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
    coupon_code = serializers.CharField(read_only=True)
    usage_stats = serializers.JSONField(read_only=True)
    
    def get_plan(self, obj):
        """دریافت اطلاعات پلن"""
        from .plan_serializers import SubscriptionPlanSerializer
        return SubscriptionPlanSerializer(obj.get('plan')).data


class SubscriptionResponseSerializer(serializers.Serializer):
    """Serializer پاسخ عملیات اشتراک"""
    
    subscription_id = serializers.UUIDField(read_only=True)
    plan_name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    trial_end_date = serializers.DateTimeField(read_only=True, required=False)
    next_billing_date = serializers.DateTimeField(read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
    trial_days = serializers.IntegerField(read_only=True, required=False)


class UpgradeResponseSerializer(serializers.Serializer):
    """Serializer پاسخ ارتقاء اشتراک"""
    
    subscription_id = serializers.UUIDField(read_only=True)
    old_plan = serializers.CharField(read_only=True)
    new_plan = serializers.CharField(read_only=True)
    proration_amount = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)


class CancelResponseSerializer(serializers.Serializer):
    """Serializer پاسخ لغو اشتراک"""
    
    subscription_id = serializers.UUIDField(read_only=True)
    status = serializers.CharField(read_only=True)
    cancelled_at = serializers.DateTimeField(read_only=True)
    end_date = serializers.DateTimeField(read_only=True)


class UsageResponseSerializer(serializers.Serializer):
    """Serializer پاسخ بررسی استفاده"""
    
    allowed = serializers.BooleanField(read_only=True)
    current_usage = serializers.IntegerField(read_only=True)
    limit = serializers.IntegerField(read_only=True)
    remaining = serializers.IntegerField(read_only=True)
    resource = serializers.CharField(read_only=True, required=False)


class RenewSubscriptionSerializer(serializers.Serializer):
    """Serializer تمدید اشتراک"""
    
    subscription_id = serializers.UUIDField(
        help_text='شناسه اشتراک'
    )


class RenewResponseSerializer(serializers.Serializer):
    """Serializer پاسخ تمدید اشتراک"""
    
    subscription_id = serializers.UUIDField(read_only=True)
    new_end_date = serializers.DateTimeField(read_only=True)
    next_billing_date = serializers.DateTimeField(read_only=True)
    renewal_price = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)