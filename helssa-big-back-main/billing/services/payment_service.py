"""
سرویس مدیریت پرداخت‌ها
Payment Management Service
"""

from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
from django.db import transaction as db_transaction
from django.contrib.auth import get_user_model
from django.utils import timezone

from .base_service import BaseService
from ..models import Transaction, TransactionType, TransactionStatus, PaymentGateway

User = get_user_model()


class PaymentService(BaseService):
    """سرویس مدیریت پرداخت‌ها"""
    
    def __init__(self):
        super().__init__()
        
    def create_payment(
        self,
        user_id: str,
        amount: Decimal,
        description: str,
        gateway: str = 'wallet',
        metadata: Optional[Dict] = None,
        callback_url: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        ایجاد پرداخت جدید
        
        Args:
            user_id: شناسه کاربر
            amount: مبلغ پرداخت
            description: توضیحات
            gateway: درگاه پرداخت
            metadata: متادیتا
            callback_url: آدرس برگشت
            
        Returns:
            Tuple[bool, Dict]: نتیجه ایجاد پرداخت
        """
        try:
            # دریافت کاربر
            user = User.objects.get(id=user_id)
            
            # اعتبارسنجی کاربر و کیف پول
            success, result = self.validate_wallet(user)
            if not success:
                return success, result
            
            wallet = result['data']['wallet']
            
            # اعتبارسنجی مبلغ
            success, result = self.validate_amount(amount)
            if not success:
                return success, result
            
            amount = result['data']['validated_amount']
            
            # بررسی نرخ محدودیت
            success, result = self.check_rate_limit(user, 'payment')
            if not success:
                return success, result
            
            if gateway == PaymentGateway.WALLET:
                # پرداخت از کیف پول
                return self._process_wallet_payment(
                    wallet, amount, description, metadata
                )
            else:
                # پرداخت از درگاه خارجی
                return self._process_gateway_payment(
                    wallet, amount, description, gateway, 
                    callback_url, metadata
                )
                
        except User.DoesNotExist:
            return self.error_response('user_not_found', 'کاربر یافت نشد')
        except Exception as e:
            self.logger.error(f"خطا در ایجاد پرداخت: {str(e)}")
            return self.error_response(
                'payment_creation_failed',
                'خطا در ایجاد پرداخت'
            )
    
    def verify_payment(
        self,
        transaction_id: str,
        gateway_data: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        تایید پرداخت
        
        Args:
            transaction_id: شناسه تراکنش
            gateway_data: داده‌های درگاه
            
        Returns:
            Tuple[bool, Dict]: نتیجه تایید
        """
        try:
            with db_transaction.atomic():
                transaction = Transaction.objects.select_for_update().get(
                    id=transaction_id,
                    status=TransactionStatus.PENDING
                )
                
                # تایید با درگاه مربوطه
                if transaction.gateway == PaymentGateway.BITPAY:
                    success, result = self._verify_bitpay_payment(
                        transaction, gateway_data
                    )
                elif transaction.gateway == PaymentGateway.ZARINPAL:
                    success, result = self._verify_zarinpal_payment(
                        transaction, gateway_data
                    )
                elif transaction.gateway == PaymentGateway.IDPAY:
                    success, result = self._verify_idpay_payment(
                        transaction, gateway_data
                    )
                else:
                    return self.error_response(
                        'unsupported_gateway',
                        'درگاه پرداخت پشتیبانی نمی‌شود'
                    )
                
                if success:
                    # تکمیل تراکنش
                    from .transaction_service import TransactionService
                    transaction_service = TransactionService()
                    
                    transaction_service.complete_transaction(
                        str(transaction.id),
                        result.get('gateway_reference')
                    )
                    
                    # واریز به کیف پول
                    wallet = transaction.wallet
                    wallet.deposit(transaction.amount, transaction.description)
                    
                    self.log_operation('verify_payment', wallet.user, {
                        'transaction_id': str(transaction.id),
                        'amount': transaction.amount,
                        'gateway': transaction.gateway,
                        'gateway_reference': result.get('gateway_reference')
                    })
                    
                    return self.success_response({
                        'transaction_id': str(transaction.id),
                        'amount': transaction.amount,
                        'gateway_reference': result.get('gateway_reference'),
                        'new_balance': wallet.balance
                    }, 'پرداخت با موفقیت تایید شد')
                else:
                    # ثبت شکست
                    from .transaction_service import TransactionService
                    transaction_service = TransactionService()
                    
                    transaction_service.fail_transaction(
                        str(transaction.id),
                        result.get('error', 'Payment verification failed')
                    )
                    
                    return self.error_response(
                        'payment_verification_failed',
                        result.get('message', 'تایید پرداخت ناموفق بود')
                    )
                    
        except Transaction.DoesNotExist:
            return self.error_response('transaction_not_found', 'تراکنش یافت نشد')
        except Exception as e:
            self.logger.error(f"خطا در تایید پرداخت: {str(e)}")
            return self.error_response(
                'payment_verification_error',
                'خطا در تایید پرداخت'
            )
    
    def refund_payment(
        self,
        transaction_id: str,
        refund_amount: Decimal = None,
        reason: str = ''
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        بازگشت پرداخت
        
        Args:
            transaction_id: شناسه تراکنش
            refund_amount: مبلغ بازگشت
            reason: دلیل بازگشت
            
        Returns:
            Tuple[bool, Dict]: نتیجه بازگشت
        """
        try:
            from .transaction_service import TransactionService
            transaction_service = TransactionService()
            
            return transaction_service.refund_transaction(
                transaction_id, refund_amount, reason
            )
            
        except Exception as e:
            self.logger.error(f"خطا در بازگشت پرداخت: {str(e)}")
            return self.error_response(
                'refund_failed',
                'خطا در بازگشت پرداخت'
            )
    
    def get_payment_methods(self, user_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        دریافت روش‌های پرداخت در دسترس
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            Tuple[bool, Dict]: روش‌های پرداخت
        """
        try:
            user = User.objects.get(id=user_id)
            
            # بررسی موجودی کیف پول
            wallet_available = False
            wallet_balance = 0
            
            if hasattr(user, 'wallet') and user.wallet.is_active:
                wallet_available = True
                wallet_balance = user.wallet.available_balance
            
            # روش‌های پرداخت
            payment_methods = [
                {
                    'id': 'wallet',
                    'name': 'کیف پول',
                    'available': wallet_available,
                    'balance': wallet_balance,
                    'icon': 'wallet',
                    'fees': 0
                },
                {
                    'id': 'bitpay',
                    'name': 'BitPay.ir',
                    'available': True,
                    'icon': 'bitpay',
                    'fees': 0.005  # 0.5%
                },
                {
                    'id': 'zarinpal',
                    'name': 'زرین‌پال',
                    'available': True,
                    'icon': 'zarinpal',
                    'fees': 0.01  # 1%
                },
                {
                    'id': 'idpay',
                    'name': 'آیدی‌پی',
                    'available': True,
                    'icon': 'idpay',
                    'fees': 0.005  # 0.5%
                }
            ]
            
            return self.success_response({
                'payment_methods': payment_methods,
                'default_method': 'wallet' if wallet_available else 'zarinpal'
            })
            
        except User.DoesNotExist:
            return self.error_response('user_not_found', 'کاربر یافت نشد')
        except Exception as e:
            self.logger.error(f"خطا در دریافت روش‌های پرداخت: {str(e)}")
            return self.error_response(
                'payment_methods_error',
                'خطا در دریافت روش‌های پرداخت'
            )
    
    def get_payment_status(self, transaction_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        وضعیت پرداخت
        
        Args:
            transaction_id: شناسه تراکنش
            
        Returns:
            Tuple[bool, Dict]: وضعیت پرداخت
        """
        try:
            from .transaction_service import TransactionService
            transaction_service = TransactionService()
            
            return transaction_service.get_transaction(transaction_id)
            
        except Exception as e:
            self.logger.error(f"خطا در دریافت وضعیت پرداخت: {str(e)}")
            return self.error_response(
                'payment_status_error',
                'خطا در دریافت وضعیت پرداخت'
            )
    
    def _process_wallet_payment(
        self,
        wallet,
        amount: Decimal,
        description: str,
        metadata: Optional[Dict]
    ) -> Tuple[bool, Dict[str, Any]]:
        """پردازش پرداخت از کیف پول"""
        
        # بررسی موجودی
        if not wallet.has_sufficient_balance(amount):
            return self.error_response(
                'insufficient_balance',
                f'موجودی کافی نیست. موجودی فعلی: {wallet.available_balance:,} ریال'
            )
        
        try:
            with db_transaction.atomic():
                # ایجاد تراکنش
                from .transaction_service import TransactionService
                transaction_service = TransactionService()
                
                transaction = transaction_service.create_transaction(
                    wallet=wallet,
                    amount=-amount,  # منفی برای پرداخت
                    transaction_type=TransactionType.PAYMENT,
                    description=description,
                    gateway=PaymentGateway.WALLET,
                    metadata=metadata or {}
                )
                
                # برداشت از کیف پول
                wallet.withdraw(amount, description)
                
                # تکمیل تراکنش
                transaction_service.complete_transaction(str(transaction.id))
                
                return self.success_response({
                    'transaction_id': str(transaction.id),
                    'amount': amount,
                    'new_balance': wallet.balance,
                    'status': 'completed'
                }, f'پرداخت {amount:,} ریال از کیف پول انجام شد')
                
        except Exception as e:
            self.logger.error(f"خطا در پرداخت از کیف پول: {str(e)}")
            return self.error_response(
                'wallet_payment_failed',
                'خطا در پرداخت از کیف پول'
            )
    
    def _process_gateway_payment(
        self,
        wallet,
        amount: Decimal,
        description: str,
        gateway: str,
        callback_url: str,
        metadata: Optional[Dict]
    ) -> Tuple[bool, Dict[str, Any]]:
        """پردازش پرداخت از درگاه خارجی"""
        
        try:
            # ایجاد تراکنش در وضعیت pending
            from .transaction_service import TransactionService
            transaction_service = TransactionService()
            
            transaction = transaction_service.create_transaction(
                wallet=wallet,
                amount=amount,
                transaction_type=TransactionType.PAYMENT,
                description=description,
                gateway=gateway,
                metadata=metadata or {}
            )
            
            # ایجاد پرداخت در درگاه
            if gateway == PaymentGateway.BITPAY:
                gateway_result = self._create_bitpay_payment(
                    transaction, callback_url
                )
            elif gateway == PaymentGateway.ZARINPAL:
                gateway_result = self._create_zarinpal_payment(
                    transaction, callback_url
                )
            elif gateway == PaymentGateway.IDPAY:
                gateway_result = self._create_idpay_payment(
                    transaction, callback_url
                )
            else:
                return self.error_response(
                    'unsupported_gateway',
                    'درگاه پرداخت پشتیبانی نمی‌شود'
                )
            
            if gateway_result['success']:
                return self.success_response({
                    'transaction_id': str(transaction.id),
                    'payment_url': gateway_result['payment_url'],
                    'gateway_reference': gateway_result['reference'],
                    'amount': amount,
                    'status': 'pending'
                }, 'پرداخت ایجاد شد')
            else:
                # شکست در ایجاد پرداخت
                transaction_service.fail_transaction(
                    str(transaction.id),
                    gateway_result.get('error', 'Gateway error')
                )
                
                return self.error_response(
                    'gateway_error',
                    gateway_result.get('message', 'خطا در ایجاد پرداخت')
                )
                
        except Exception as e:
            self.logger.error(f"خطا در پرداخت از درگاه: {str(e)}")
            return self.error_response(
                'gateway_payment_failed',
                'خطا در پرداخت از درگاه'
            )
    
    def _create_bitpay_payment(
        self,
        transaction: Transaction,
        callback_url: str
    ) -> Dict[str, Any]:
        """ایجاد پرداخت در BitPay"""
        
        try:
            from ..gateways.bitpay_gateway import BitPayGateway
            
            # تنظیمات BitPay (باید از settings خوانده شود)
            config = {
                'api_key': 'your_bitpay_api_key',
                'callback_url': callback_url
            }
            
            gateway = BitPayGateway(config)
            
            result = gateway.create_payment(
                amount=int(transaction.amount),
                order_id=transaction.reference_number,
                callback_url=callback_url,
                description=transaction.description
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"خطا در ایجاد پرداخت BitPay: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'خطا در اتصال به درگاه BitPay'
            }
    
    def _create_zarinpal_payment(
        self,
        transaction: Transaction,
        callback_url: str
    ) -> Dict[str, Any]:
        """ایجاد پرداخت در زرین‌پال"""
        
        try:
            from ..gateways.zarinpal_gateway import ZarinPalGateway
            
            # تنظیمات زرین‌پال
            config = {
                'merchant_id': 'your_zarinpal_merchant_id',
                'callback_url': callback_url
            }
            
            gateway = ZarinPalGateway(config)
            
            result = gateway.create_payment(
                amount=int(transaction.amount),
                order_id=transaction.reference_number,
                callback_url=callback_url,
                description=transaction.description
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"خطا در ایجاد پرداخت زرین‌پال: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'خطا در اتصال به درگاه زرین‌پال'
            }
    
    def _create_idpay_payment(
        self,
        transaction: Transaction,
        callback_url: str
    ) -> Dict[str, Any]:
        """ایجاد پرداخت در آیدی‌پی"""
        
        try:
            from ..gateways.idpay_gateway import IDPayGateway
            
            # تنظیمات آیدی‌پی
            config = {
                'api_key': 'your_idpay_api_key',
                'callback_url': callback_url
            }
            
            gateway = IDPayGateway(config)
            
            result = gateway.create_payment(
                amount=int(transaction.amount),
                order_id=transaction.reference_number,
                callback_url=callback_url,
                description=transaction.description
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"خطا در ایجاد پرداخت آیدی‌پی: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'خطا در اتصال به درگاه آیدی‌پی'
            }
    
    def _verify_bitpay_payment(
        self,
        transaction: Transaction,
        gateway_data: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """تایید پرداخت BitPay"""
        
        try:
            from ..gateways.bitpay_gateway import BitPayGateway
            
            config = {
                'api_key': 'your_bitpay_api_key'
            }
            
            gateway = BitPayGateway(config)
            
            result = gateway.verify_payment(
                reference=gateway_data.get('id_get', ''),
                amount=int(transaction.amount)
            )
            
            return result['success'], result
            
        except Exception as e:
            self.logger.error(f"خطا در تایید پرداخت BitPay: {str(e)}")
            return False, {'error': str(e)}
    
    def _verify_zarinpal_payment(
        self,
        transaction: Transaction,
        gateway_data: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """تایید پرداخت زرین‌پال"""
        
        try:
            from ..gateways.zarinpal_gateway import ZarinPalGateway
            
            config = {
                'merchant_id': 'your_zarinpal_merchant_id'
            }
            
            gateway = ZarinPalGateway(config)
            
            result = gateway.verify_payment(
                reference=gateway_data.get('Authority', ''),
                amount=int(transaction.amount)
            )
            
            return result['success'], result
            
        except Exception as e:
            self.logger.error(f"خطا در تایید پرداخت زرین‌پال: {str(e)}")
            return False, {'error': str(e)}
    
    def _verify_idpay_payment(
        self,
        transaction: Transaction,
        gateway_data: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """تایید پرداخت آیدی‌پی"""
        
        try:
            from ..gateways.idpay_gateway import IDPayGateway
            
            config = {
                'api_key': 'your_idpay_api_key'
            }
            
            gateway = IDPayGateway(config)
            
            result = gateway.verify_payment(
                reference=gateway_data.get('id', ''),
                amount=int(transaction.amount)
            )
            
            return result['success'], result
            
        except Exception as e:
            self.logger.error(f"خطا در تایید پرداخت آیدی‌پی: {str(e)}")
            return False, {'error': str(e)}