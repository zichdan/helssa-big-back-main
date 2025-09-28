"""
Serializer های کیف پول
Wallet Serializers
"""

from rest_framework import serializers
from decimal import Decimal
from django.contrib.auth import get_user_model

User = get_user_model()


class WalletInfoSerializer(serializers.Serializer):
    """Serializer اطلاعات کیف پول"""
    
    wallet_id = serializers.UUIDField(read_only=True)
    balance = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    blocked_balance = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    available_balance = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    gift_credit = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
    total_credit = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    daily_limit = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
    monthly_limit = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
    today_withdrawals = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
    month_withdrawals = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
    remaining_daily_limit = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
    remaining_monthly_limit = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
    last_transaction = serializers.DateTimeField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class DepositSerializer(serializers.Serializer):
    """Serializer واریز به کیف پول"""
    
    amount = serializers.DecimalField(
        max_digits=12, 
        decimal_places=0,
        min_value=Decimal('1000'),
        max_value=Decimal('500000000'),
        error_messages={
            'min_value': 'حداقل مبلغ واریز 1000 ریال است',
            'max_value': 'حداکثر مبلغ واریز 500 میلیون ریال است',
            'invalid': 'مبلغ وارد شده نامعتبر است'
        }
    )
    
    description = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text='توضیحات واریز (اختیاری)'
    )
    
    source = serializers.CharField(
        max_length=50,
        default='manual',
        help_text='منبع واریز'
    )
    
    reference = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text='شماره مرجع (اختیاری)'
    )


class WithdrawSerializer(serializers.Serializer):
    """Serializer برداشت از کیف پول"""
    
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=0,
        min_value=Decimal('1000'),
        max_value=Decimal('500000000'),
        error_messages={
            'min_value': 'حداقل مبلغ برداشت 1000 ریال است',
            'max_value': 'حداکثر مبلغ برداشت 500 میلیون ریال است',
            'invalid': 'مبلغ وارد شده نامعتبر است'
        }
    )
    
    description = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text='توضیحات برداشت (اختیاری)'
    )
    
    destination = serializers.CharField(
        max_length=100,
        default='bank_account',
        help_text='مقصد برداشت'
    )


class TransferSerializer(serializers.Serializer):
    """Serializer انتقال وجه"""
    
    to_user_id = serializers.UUIDField(
        help_text='شناسه کاربر گیرنده'
    )
    
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=0,
        min_value=Decimal('1000'),
        max_value=Decimal('100000000'),
        error_messages={
            'min_value': 'حداقل مبلغ انتقال 1000 ریال است',
            'max_value': 'حداکثر مبلغ انتقال 100 میلیون ریال است',
            'invalid': 'مبلغ وارد شده نامعتبر است'
        }
    )
    
    description = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text='توضیحات انتقال (اختیاری)'
    )
    
    commission_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal('0.005'),  # 0.5%
        min_value=Decimal('0'),
        max_value=Decimal('0.1'),  # حداکثر 10%
        help_text='نرخ کمیسیون'
    )
    
    def validate_to_user_id(self, value):
        """اعتبارسنجی کاربر گیرنده"""
        try:
            user = User.objects.get(id=value, is_active=True)
            if not hasattr(user, 'wallet') or not user.wallet.is_active:
                raise serializers.ValidationError('کیف پول گیرنده فعال نیست')
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError('کاربر گیرنده یافت نشد')


class TransactionHistorySerializer(serializers.Serializer):
    """Serializer تاریخچه تراکنش‌ها"""
    
    limit = serializers.IntegerField(
        default=20,
        min_value=1,
        max_value=100,
        help_text='تعداد نتایج (حداکثر 100)'
    )
    
    offset = serializers.IntegerField(
        default=0,
        min_value=0,
        help_text='جابجایی'
    )
    
    transaction_type = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='نوع تراکنش (اختیاری)'
    )
    
    start_date = serializers.DateTimeField(
        required=False,
        help_text='تاریخ شروع (اختیاری)'
    )
    
    end_date = serializers.DateTimeField(
        required=False,
        help_text='تاریخ پایان (اختیاری)'
    )


class BlockAmountSerializer(serializers.Serializer):
    """Serializer بلوک کردن مبلغ"""
    
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=0,
        min_value=Decimal('1000'),
        error_messages={
            'min_value': 'حداقل مبلغ بلوک 1000 ریال است',
            'invalid': 'مبلغ وارد شده نامعتبر است'
        }
    )
    
    reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text='دلیل بلوک (اختیاری)'
    )


class UnblockAmountSerializer(serializers.Serializer):
    """Serializer آزاد کردن مبلغ بلوک شده"""
    
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=0,
        min_value=Decimal('1000'),
        error_messages={
            'min_value': 'حداقل مبلغ آزادسازی 1000 ریال است',
            'invalid': 'مبلغ وارد شده نامعتبر است'
        }
    )
    
    reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text='دلیل آزادسازی (اختیاری)'
    )


class TransactionDetailSerializer(serializers.Serializer):
    """Serializer جزئیات تراکنش"""
    
    id = serializers.UUIDField(read_only=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    type = serializers.CharField(read_only=True)
    type_display = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    reference_number = serializers.CharField(read_only=True)
    gateway = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    completed_at = serializers.DateTimeField(read_only=True)
    is_income = serializers.BooleanField(read_only=True)
    is_expense = serializers.BooleanField(read_only=True)


class TransactionListSerializer(serializers.Serializer):
    """Serializer لیست تراکنش‌ها"""
    
    transactions = TransactionDetailSerializer(many=True, read_only=True)
    total_count = serializers.IntegerField(read_only=True)
    limit = serializers.IntegerField(read_only=True)
    offset = serializers.IntegerField(read_only=True)
    has_more = serializers.BooleanField(read_only=True)