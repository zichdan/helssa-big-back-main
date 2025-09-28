"""
سریالایزرهای اپلیکیشن پرداخت
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.utils import timezone

from .models import (
    Payment, PaymentMethod, Transaction, 
    Wallet, WalletTransaction, PaymentGateway
)

User = get_user_model()


class PaymentMethodSerializer(serializers.ModelSerializer):
    """
    سریالایزر روش‌های پرداخت
    """
    method_type_display = serializers.CharField(
        source='get_method_type_display',
        read_only=True
    )
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'method_type', 'method_type_display',
            'title', 'details', 'is_default', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def validate_details(self, value):
        """اعتبارسنجی جزئیات بر اساس نوع روش"""
        method_type = self.initial_data.get('method_type')
        
        if method_type == 'card':
            if 'card_number' not in value:
                raise serializers.ValidationError(
                    "شماره کارت برای روش پرداخت کارتی الزامی است"
                )
        elif method_type == 'insurance':
            if 'insurance_code' not in value:
                raise serializers.ValidationError(
                    "کد بیمه برای روش پرداخت بیمه‌ای الزامی است"
                )
                
        return value
    
    def create(self, validated_data):
        """ایجاد روش پرداخت جدید"""
        # اگر پیش‌فرض است، سایر روش‌های پیش‌فرض را غیرفعال کن
        if validated_data.get('is_default', False):
            PaymentMethod.objects.filter(
                user=validated_data['user'],
                is_default=True
            ).update(is_default=False)
            
        return super().create(validated_data)


class CreatePaymentSerializer(serializers.Serializer):
    """
    سریالایزر ایجاد پرداخت جدید
    """
    payment_type = serializers.ChoiceField(
        choices=Payment.PAYMENT_TYPE_CHOICES,
        label='نوع پرداخت'
    )
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=0,
        min_value=Decimal('1000'),
        label='مبلغ (ریال)'
    )
    payment_method_id = serializers.IntegerField(
        required=False,
        label='شناسه روش پرداخت'
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        label='توضیحات'
    )
    appointment_id = serializers.CharField(
        required=False,
        allow_blank=True,
        label='شناسه نوبت'
    )
    doctor_id = serializers.CharField(
        required=False,
        allow_blank=True,
        label='شناسه پزشک'
    )
    metadata = serializers.JSONField(
        required=False,
        default=dict,
        label='اطلاعات تکمیلی'
    )
    
    def validate_payment_type(self, value):
        """اعتبارسنجی نوع پرداخت بر اساس نوع کاربر"""
        user = self.context['request'].user
        
        patient_types = [
            'appointment', 'consultation', 'medication',
            'test', 'imaging', 'procedure'
        ]
        doctor_types = [
            'withdrawal', 'subscription', 'commission',
            'refund', 'adjustment'
        ]
        
        if hasattr(user, 'user_type'):
            if user.user_type == 'patient' and value not in patient_types:
                raise serializers.ValidationError(
                    "این نوع پرداخت برای بیماران مجاز نیست"
                )
            elif user.user_type == 'doctor' and value not in doctor_types:
                raise serializers.ValidationError(
                    "این نوع پرداخت برای پزشکان مجاز نیست"
                )
                
        return value
    
    def validate_amount(self, value):
        """اعتبارسنجی مبلغ"""
        # حداقل مبلغ 1000 ریال
        if value < 1000:
            raise serializers.ValidationError(
                "حداقل مبلغ پرداخت 1000 ریال است"
            )
        # حداکثر مبلغ 500 میلیون ریال
        if value > 500000000:
            raise serializers.ValidationError(
                "حداکثر مبلغ پرداخت 500 میلیون ریال است"
            )
        return value
    
    def validate_payment_method_id(self, value):
        """اعتبارسنجی روش پرداخت"""
        user = self.context['request'].user
        
        if value:
            try:
                method = PaymentMethod.objects.get(
                    id=value,
                    user=user,
                    is_active=True
                )
            except PaymentMethod.DoesNotExist:
                raise serializers.ValidationError(
                    "روش پرداخت انتخابی نامعتبر است"
                )
                
        return value


class PaymentSerializer(serializers.ModelSerializer):
    """
    سریالایزر نمایش پرداخت
    """
    user_display = serializers.SerializerMethodField()
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    payment_type_display = serializers.CharField(
        source='get_payment_type_display',
        read_only=True
    )
    jalali_created = serializers.SerializerMethodField()
    payment_method_info = PaymentMethodSerializer(
        source='payment_method',
        read_only=True
    )
    
    class Meta:
        model = Payment
        fields = [
            'payment_id', 'user', 'user_display', 'user_type',
            'payment_type', 'payment_type_display', 'amount',
            'status', 'status_display', 'tracking_code',
            'description', 'payment_method_info', 'metadata',
            'appointment_id', 'doctor_id', 'created_at',
            'jalali_created', 'paid_at', 'failed_at', 'refunded_at'
        ]
        read_only_fields = [
            'payment_id', 'user', 'tracking_code',
            'created_at', 'paid_at', 'failed_at', 'refunded_at'
        ]
        
    def get_user_display(self, obj):
        """نمایش نام کاربر"""
        if hasattr(obj.user, 'get_full_name'):
            return obj.user.get_full_name()
        return str(obj.user)
    
    def get_jalali_created(self, obj):
        """تاریخ شمسی ایجاد"""
        return obj.get_jalali_created().strftime('%Y/%m/%d %H:%M')


class TransactionSerializer(serializers.ModelSerializer):
    """
    سریالایزر تراکنش‌ها
    """
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    jalali_created = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'transaction_id', 'payment', 'transaction_type',
            'transaction_type_display', 'amount', 'reference_number',
            'gateway_name', 'card_number_masked', 'status',
            'status_display', 'created_at', 'jalali_created'
        ]
        read_only_fields = ['transaction_id', 'created_at']
        
    def get_jalali_created(self, obj):
        """تاریخ شمسی ایجاد"""
        return obj.get_jalali_created().strftime('%Y/%m/%d %H:%M')


class WalletSerializer(serializers.ModelSerializer):
    """
    سریالایزر کیف پول
    """
    available_balance = serializers.ReadOnlyField()
    jalali_last_transaction = serializers.SerializerMethodField()
    
    class Meta:
        model = Wallet
        fields = [
            'id', 'user', 'balance', 'blocked_balance',
            'available_balance', 'last_transaction_at',
            'jalali_last_transaction', 'created_at', 'is_active'
        ]
        read_only_fields = [
            'id', 'user', 'balance', 'blocked_balance',
            'last_transaction_at', 'created_at'
        ]
        
    def get_jalali_last_transaction(self, obj):
        """تاریخ شمسی آخرین تراکنش"""
        if obj.last_transaction_at:
            jalali = jdatetime.datetime.fromgregorian(
                datetime=obj.last_transaction_at
            )
            return jalali.strftime('%Y/%m/%d %H:%M')
        return None


class WalletTransactionSerializer(serializers.ModelSerializer):
    """
    سریالایزر تراکنش‌های کیف پول
    """
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display',
        read_only=True
    )
    jalali_created = serializers.SerializerMethodField()
    payment_info = PaymentSerializer(
        source='payment',
        read_only=True
    )
    
    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'wallet', 'transaction_type', 'transaction_type_display',
            'amount', 'balance_before', 'balance_after', 'description',
            'payment_info', 'created_at', 'jalali_created'
        ]
        read_only_fields = [
            'id', 'wallet', 'balance_before', 'balance_after', 'created_at'
        ]
        
    def get_jalali_created(self, obj):
        """تاریخ شمسی ایجاد"""
        return obj.get_jalali_created().strftime('%Y/%m/%d %H:%M')


class PaymentGatewaySerializer(serializers.ModelSerializer):
    """
    سریالایزر درگاه‌های پرداخت
    """
    gateway_type_display = serializers.CharField(
        source='get_gateway_type_display',
        read_only=True
    )
    
    class Meta:
        model = PaymentGateway
        fields = [
            'id', 'name', 'display_name', 'gateway_type',
            'gateway_type_display', 'is_active', 'priority'
        ]
        read_only_fields = ['id']


class RefundRequestSerializer(serializers.Serializer):
    """
    سریالایزر درخواست بازپرداخت
    """
    payment_id = serializers.UUIDField(
        label='شناسه پرداخت'
    )
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=0,
        min_value=Decimal('0'),
        required=False,
        label='مبلغ بازپرداخت (اختیاری)'
    )
    reason = serializers.CharField(
        max_length=500,
        label='دلیل بازپرداخت'
    )
    
    def validate_payment_id(self, value):
        """اعتبارسنجی پرداخت"""
        try:
            payment = Payment.objects.get(
                payment_id=value,
                status='success'
            )
            
            # بررسی مالکیت
            user = self.context['request'].user
            if payment.user != user:
                raise serializers.ValidationError(
                    "شما مجاز به بازپرداخت این تراکنش نیستید"
                )
                
            # بررسی وضعیت
            if payment.status != 'success':
                raise serializers.ValidationError(
                    "فقط پرداخت‌های موفق قابل بازپرداخت هستند"
                )
                
            self.context['payment'] = payment
            
        except Payment.DoesNotExist:
            raise serializers.ValidationError(
                "پرداخت مورد نظر یافت نشد"
            )
            
        return value
    
    def validate_amount(self, value):
        """اعتبارسنجی مبلغ بازپرداخت"""
        if 'payment' in self.context:
            payment = self.context['payment']
            
            if value and value > payment.amount:
                raise serializers.ValidationError(
                    f"مبلغ بازپرداخت نمی‌تواند بیشتر از {payment.amount} ریال باشد"
                )
                
        return value


class PaymentReportSerializer(serializers.Serializer):
    """
    سریالایزر گزارش پرداخت‌ها
    """
    start_date = serializers.DateTimeField(
        required=False,
        label='تاریخ شروع'
    )
    end_date = serializers.DateTimeField(
        required=False,
        label='تاریخ پایان'
    )
    payment_type = serializers.ChoiceField(
        choices=Payment.PAYMENT_TYPE_CHOICES,
        required=False,
        label='نوع پرداخت'
    )
    status = serializers.ChoiceField(
        choices=Payment.PAYMENT_STATUS_CHOICES,
        required=False,
        label='وضعیت'
    )
    
    def validate(self, attrs):
        """اعتبارسنجی بازه زمانی"""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise serializers.ValidationError(
                    "تاریخ شروع نمی‌تواند بعد از تاریخ پایان باشد"
                )
                
            # حداکثر بازه 3 ماه
            diff = end_date - start_date
            if diff.days > 90:
                raise serializers.ValidationError(
                    "حداکثر بازه گزارش 3 ماه است"
                )
                
        return attrs