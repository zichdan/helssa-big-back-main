"""
Serializer های پرداخت
Payment Serializers
"""

from rest_framework import serializers
from decimal import Decimal
from ..models import PaymentGateway


class CreatePaymentSerializer(serializers.Serializer):
    """Serializer ایجاد پرداخت"""
    
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=0,
        min_value=Decimal('1000'),
        max_value=Decimal('500000000'),
        error_messages={
            'min_value': 'حداقل مبلغ پرداخت 1000 ریال است',
            'max_value': 'حداکثر مبلغ پرداخت 500 میلیون ریال است',
            'invalid': 'مبلغ وارد شده نامعتبر است'
        }
    )
    
    description = serializers.CharField(
        max_length=500,
        help_text='توضیحات پرداخت'
    )
    
    gateway = serializers.ChoiceField(
        choices=PaymentGateway.choices,
        default=PaymentGateway.WALLET,
        help_text='درگاه پرداخت'
    )
    
    callback_url = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text='آدرس برگشت (برای درگاه‌های خارجی)'
    )
    
    metadata = serializers.JSONField(
        required=False,
        default=dict,
        help_text='اطلاعات اضافی (اختیاری)'
    )


class VerifyPaymentSerializer(serializers.Serializer):
    """Serializer تایید پرداخت"""
    
    transaction_id = serializers.UUIDField(
        help_text='شناسه تراکنش'
    )
    
    gateway_data = serializers.JSONField(
        help_text='داده‌های دریافتی از درگاه'
    )


class RefundPaymentSerializer(serializers.Serializer):
    """Serializer بازگشت پرداخت"""
    
    transaction_id = serializers.UUIDField(
        help_text='شناسه تراکنش'
    )
    
    refund_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=0,
        required=False,
        min_value=Decimal('1000'),
        help_text='مبلغ بازگشت (اختیاری - پیش‌فرض: کل مبلغ)'
    )
    
    reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text='دلیل بازگشت (اختیاری)'
    )


class PaymentMethodSerializer(serializers.Serializer):
    """Serializer روش‌های پرداخت"""
    
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    available = serializers.BooleanField(read_only=True)
    balance = serializers.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        read_only=True,
        required=False
    )
    icon = serializers.CharField(read_only=True)
    fees = serializers.DecimalField(
        max_digits=5, 
        decimal_places=4, 
        read_only=True
    )


class PaymentMethodsListSerializer(serializers.Serializer):
    """Serializer لیست روش‌های پرداخت"""
    
    payment_methods = PaymentMethodSerializer(many=True, read_only=True)
    default_method = serializers.CharField(read_only=True)


class PaymentStatusSerializer(serializers.Serializer):
    """Serializer وضعیت پرداخت"""
    
    transaction_id = serializers.UUIDField(read_only=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(read_only=True)
    gateway = serializers.CharField(read_only=True)
    reference_number = serializers.CharField(read_only=True)
    gateway_reference = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    completed_at = serializers.DateTimeField(read_only=True)
    payment_url = serializers.URLField(read_only=True, required=False)


class PaymentResponseSerializer(serializers.Serializer):
    """Serializer پاسخ ایجاد پرداخت"""
    
    transaction_id = serializers.UUIDField(read_only=True)
    payment_url = serializers.URLField(read_only=True, required=False)
    gateway_reference = serializers.CharField(read_only=True, required=False)
    amount = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    status = serializers.CharField(read_only=True)
    new_balance = serializers.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        read_only=True, 
        required=False
    )


class VerifyPaymentResponseSerializer(serializers.Serializer):
    """Serializer پاسخ تایید پرداخت"""
    
    transaction_id = serializers.UUIDField(read_only=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    gateway_reference = serializers.CharField(read_only=True)
    new_balance = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    verified_at = serializers.DateTimeField(read_only=True)


class RefundResponseSerializer(serializers.Serializer):
    """Serializer پاسخ بازگشت پرداخت"""
    
    original_transaction_id = serializers.UUIDField(read_only=True)
    refund_transaction_id = serializers.UUIDField(read_only=True)
    refund_amount = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    new_wallet_balance = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    refunded_at = serializers.DateTimeField(read_only=True)