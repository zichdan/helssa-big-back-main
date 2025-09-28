"""
سرویس اصلی پرداخت
"""
import logging
from typing import Dict, Any, Tuple, Optional
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from ..models import Payment, Transaction, PaymentMethod
from ..settings import PAYMENT_SETTINGS
from .gateway_service import GatewayService
from .wallet_service import WalletService

User = get_user_model()
logger = logging.getLogger(__name__)


class PaymentService:
    """
    سرویس مدیریت پرداخت‌ها
    """
    
    def __init__(self):
        self.logger = logger
        self.gateway_service = GatewayService()
        self.wallet_service = WalletService()
        
    def create_payment(
        self,
        user: User,
        payment_type: str,
        amount: Decimal,
        payment_method_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        ایجاد پرداخت جدید
        
        Args:
            user: کاربر
            payment_type: نوع پرداخت
            amount: مبلغ
            payment_method_id: روش پرداخت
            metadata: اطلاعات تکمیلی
            
        Returns:
            Tuple[bool, Dict]: (موفقیت، نتیجه)
        """
        try:
            # اعتبارسنجی مبلغ
            if not self._validate_amount(amount, payment_type):
                return False, {
                    'error': 'invalid_amount',
                    'message': 'مبلغ پرداخت نامعتبر است'
                }
            
            # دریافت روش پرداخت
            payment_method = None
            if payment_method_id:
                try:
                    payment_method = PaymentMethod.objects.get(
                        id=payment_method_id,
                        user=user,
                        is_active=True
                    )
                except PaymentMethod.DoesNotExist:
                    return False, {
                        'error': 'invalid_payment_method',
                        'message': 'روش پرداخت نامعتبر است'
                    }
            
            # ایجاد رکورد پرداخت
            with transaction.atomic():
                payment = Payment.objects.create(
                    user=user,
                    user_type=getattr(user, 'user_type', 'patient'),
                    payment_type=payment_type,
                    amount=amount,
                    status='pending',
                    payment_method=payment_method,
                    metadata=metadata or {}
                )
                
                self.logger.info(
                    f"Payment created: {payment.payment_id}",
                    extra={
                        'user_id': user.id,
                        'amount': str(amount),
                        'type': payment_type
                    }
                )
                
                return True, {
                    'payment': payment,
                    'payment_id': str(payment.payment_id),
                    'tracking_code': payment.tracking_code
                }
                
        except Exception as e:
            self.logger.error(f"Error creating payment: {str(e)}")
            return False, {
                'error': 'creation_failed',
                'message': 'خطا در ایجاد پرداخت'
            }
    
    def process_payment(
        self,
        payment: Payment,
        gateway_name: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        پردازش پرداخت از طریق درگاه
        
        Args:
            payment: پرداخت
            gateway_name: نام درگاه
            
        Returns:
            Tuple[bool, Dict]: (موفقیت، نتیجه)
        """
        try:
            # بررسی وضعیت پرداخت
            if payment.status != 'pending':
                return False, {
                    'error': 'invalid_status',
                    'message': 'وضعیت پرداخت نامعتبر است'
                }
            
            # پردازش از طریق درگاه
            payment.status = 'processing'
            payment.save()
            
            success, gateway_result = self.gateway_service.process_payment(
                payment=payment,
                gateway_name=gateway_name
            )
            
            if success:
                # پرداخت موفق
                payment.status = 'success'
                payment.paid_at = timezone.now()
                payment.gateway_response = gateway_result
                payment.save()
                
                # ایجاد تراکنش
                Transaction.objects.create(
                    payment=payment,
                    transaction_type='payment',
                    amount=payment.amount,
                    reference_number=gateway_result.get('reference_number'),
                    gateway_name=gateway_result.get('gateway_name'),
                    status='success'
                )
                
                # بروزرسانی کیف پول در صورت نیاز
                if payment.payment_type == 'deposit':
                    self.wallet_service.charge_wallet(
                        user=payment.user,
                        amount=payment.amount,
                        payment=payment
                    )
                
                return True, {
                    'payment_id': str(payment.payment_id),
                    'reference_number': gateway_result.get('reference_number'),
                    'message': 'پرداخت با موفقیت انجام شد'
                }
            else:
                # پرداخت ناموفق
                payment.status = 'failed'
                payment.failed_at = timezone.now()
                payment.gateway_response = gateway_result
                payment.save()
                
                # ایجاد تراکنش ناموفق
                Transaction.objects.create(
                    payment=payment,
                    transaction_type='payment',
                    amount=payment.amount,
                    gateway_name=gateway_result.get('gateway_name'),
                    status='failed'
                )
                
                return False, {
                    'error': gateway_result.get('error', 'payment_failed'),
                    'message': gateway_result.get('message', 'پرداخت ناموفق بود')
                }
                
        except Exception as e:
            self.logger.error(f"Error processing payment: {str(e)}")
            
            payment.status = 'failed'
            payment.failed_at = timezone.now()
            payment.save()
            
            return False, {
                'error': 'processing_failed',
                'message': 'خطا در پردازش پرداخت'
            }
    
    def refund_payment(
        self,
        payment: Payment,
        amount: Optional[Decimal] = None,
        reason: str = ''
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        بازپرداخت
        
        Args:
            payment: پرداخت
            amount: مبلغ بازپرداخت (None = کل مبلغ)
            reason: دلیل بازپرداخت
            
        Returns:
            Tuple[bool, Dict]: (موفقیت، نتیجه)
        """
        try:
            # بررسی امکان بازپرداخت
            if payment.status != 'success':
                return False, {
                    'error': 'invalid_status',
                    'message': 'فقط پرداخت‌های موفق قابل بازپرداخت هستند'
                }
            
            # بررسی مهلت بازپرداخت
            days_passed = (timezone.now() - payment.paid_at).days
            max_refund_days = PAYMENT_SETTINGS.get('MAX_REFUND_DAYS', 7)
            
            if days_passed > max_refund_days:
                return False, {
                    'error': 'refund_expired',
                    'message': f'مهلت بازپرداخت ({max_refund_days} روز) گذشته است'
                }
            
            # تعیین مبلغ بازپرداخت
            refund_amount = amount or payment.amount
            if refund_amount > payment.amount:
                return False, {
                    'error': 'invalid_amount',
                    'message': 'مبلغ بازپرداخت بیشتر از مبلغ پرداخت است'
                }
            
            # پردازش بازپرداخت
            with transaction.atomic():
                # بروزرسانی وضعیت پرداخت
                if refund_amount == payment.amount:
                    payment.status = 'refunded'
                else:
                    payment.status = 'partially_refunded'
                
                payment.refunded_at = timezone.now()
                payment.metadata['refund_reason'] = reason
                payment.save()
                
                # ایجاد تراکنش بازپرداخت
                Transaction.objects.create(
                    payment=payment,
                    transaction_type='refund',
                    amount=refund_amount,
                    status='success'
                )
                
                # بازگرداندن به کیف پول
                if payment.user_type == 'patient':
                    self.wallet_service.refund_to_wallet(
                        user=payment.user,
                        amount=refund_amount,
                        payment=payment
                    )
                
                return True, {
                    'payment_id': str(payment.payment_id),
                    'refund_amount': str(refund_amount),
                    'status': payment.status,
                    'message': 'بازپرداخت با موفقیت انجام شد'
                }
                
        except Exception as e:
            self.logger.error(f"Error processing refund: {str(e)}")
            return False, {
                'error': 'refund_failed',
                'message': 'خطا در پردازش بازپرداخت'
            }
    
    def _validate_amount(self, amount: Decimal, payment_type: str) -> bool:
        """
        اعتبارسنجی مبلغ پرداخت
        
        Args:
            amount: مبلغ
            payment_type: نوع پرداخت
            
        Returns:
            bool: معتبر بودن
        """
        min_amount = PAYMENT_SETTINGS.get('MIN_PAYMENT_AMOUNT', 1000)
        max_amount = PAYMENT_SETTINGS.get('MAX_PAYMENT_AMOUNT', 500000000)
        
        if payment_type == 'withdrawal':
            min_amount = PAYMENT_SETTINGS.get('MIN_WITHDRAWAL_AMOUNT', 100000)
        
        return min_amount <= amount <= max_amount
    
    def calculate_commission(
        self,
        payment_type: str,
        amount: Decimal
    ) -> Decimal:
        """
        محاسبه کمیسیون
        
        Args:
            payment_type: نوع پرداخت
            amount: مبلغ
            
        Returns:
            Decimal: مبلغ کمیسیون
        """
        commission_rates = {
            'appointment': PAYMENT_SETTINGS.get('APPOINTMENT_COMMISSION_RATE', 10),
            'consultation': PAYMENT_SETTINGS.get('CONSULTATION_COMMISSION_RATE', 15),
        }
        
        rate = commission_rates.get(
            payment_type,
            PAYMENT_SETTINGS.get('DEFAULT_COMMISSION_RATE', 10)
        )
        
        commission = (amount * rate) / 100
        return commission.quantize(Decimal('1'))  # رند کردن به عدد صحیح