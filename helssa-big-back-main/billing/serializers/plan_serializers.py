"""
Serializer های پلن اشتراک
Subscription Plan Serializers
"""

from rest_framework import serializers
from ..models import SubscriptionPlan


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer پلن اشتراک"""
    
    target_user_type = serializers.CharField(read_only=True)
    effective_yearly_price = serializers.DecimalField(
        max_digits=10, 
        decimal_places=0, 
        read_only=True
    )
    monthly_savings = serializers.DecimalField(
        max_digits=10, 
        decimal_places=0, 
        read_only=True
    )
    popular_features = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id',
            'name',
            'type',
            'monthly_price',
            'yearly_price',
            'yearly_discount_percent',
            'effective_yearly_price',
            'monthly_savings',
            'limits',
            'features',
            'commission_rate',
            'is_recommended',
            'display_order',
            'color_code',
            'icon',
            'description',
            'features_description',
            'trial_days',
            'target_user_type',
            'popular_features',
        ]
        read_only_fields = [
            'id',
            'target_user_type',
            'effective_yearly_price',
            'monthly_savings',
            'popular_features',
        ]
    
    def get_popular_features(self, obj):
        """دریافت ویژگی‌های محبوب"""
        return obj.get_popular_features()


class PlanListSerializer(serializers.Serializer):
    """Serializer لیست پلن‌ها"""
    
    user_type = serializers.CharField(
        required=False,
        help_text='نوع کاربر (patient/doctor) - برای فیلتر کردن پلن‌ها'
    )
    
    include_inactive = serializers.BooleanField(
        default=False,
        help_text='شامل پلن‌های غیرفعال'
    )


class PlanComparisonSerializer(serializers.Serializer):
    """Serializer مقایسه پلن‌ها"""
    
    plan_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=2,
        max_length=5,
        help_text='فهرست شناسه پلن‌ها برای مقایسه'
    )
    
    billing_cycle = serializers.ChoiceField(
        choices=['monthly', 'yearly'],
        default='monthly',
        help_text='دوره صورت‌حساب برای محاسبه قیمت'
    )


class PlanFeatureSerializer(serializers.Serializer):
    """Serializer ویژگی پلن"""
    
    feature_key = serializers.CharField(read_only=True)
    feature_name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    limit = serializers.IntegerField(read_only=True)
    unlimited = serializers.BooleanField(read_only=True)


class PlanComparisonResponseSerializer(serializers.Serializer):
    """Serializer پاسخ مقایسه پلن‌ها"""
    
    plans = SubscriptionPlanSerializer(many=True, read_only=True)
    comparison_matrix = serializers.JSONField(read_only=True)
    recommended_plan = serializers.UUIDField(read_only=True, required=False)
    billing_cycle = serializers.CharField(read_only=True)


class PlanPriceCalculatorSerializer(serializers.Serializer):
    """Serializer محاسبه قیمت پلن"""
    
    plan_id = serializers.UUIDField(
        help_text='شناسه پلن'
    )
    
    billing_cycle = serializers.ChoiceField(
        choices=['monthly', 'yearly'],
        default='monthly',
        help_text='دوره صورت‌حساب'
    )
    
    coupon_code = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        help_text='کد تخفیف (اختیاری)'
    )


class PriceCalculationResponseSerializer(serializers.Serializer):
    """Serializer پاسخ محاسبه قیمت"""
    
    plan_name = serializers.CharField(read_only=True)
    billing_cycle = serializers.CharField(read_only=True)
    base_price = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
    discount_percent = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
    final_price = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
    savings_amount = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
    coupon_applied = serializers.BooleanField(read_only=True)
    trial_days = serializers.IntegerField(read_only=True)