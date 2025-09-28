"""
سرویس مدیریت کیف پول
"""
import logging
from typing import Dict, Any, Tuple, Optional
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from ..models import Wallet, WalletTransaction, Payment
from ..settings import WALLET_SETTINGS

User = get_user_model()
logger = logging.getLogger(__name__)


class WalletService:
    """
    سرویس مدیریت کیف پول کاربران
    """
    
    def __init__(self):
        self.logger = logger
        
    def get_or_create_wallet(self, user: User) -> Wallet:
        """
        دریافت یا ایجاد کیف پول کاربر
        
        Args:
            user: کاربر
            
        Returns:
            Wallet: کیف پول
        """
        wallet, created = Wallet.objects.get_or_create(
            user=user,
            defaults={
                'balance': WALLET_SETTINGS.get('INITIAL_BALANCE', 0)
            }
        )
        
        if created:
            self.logger.info(f"Wallet created for user: {user.id}")
            
        return wallet
    
    def charge_wallet(
        self,
        user: User,
        amount: Decimal,
        payment: Optional[Payment] = None,
        description: str = 'شارژ کیف پول'
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        شارژ کیف پول
        
        Args:
            user: کاربر
            amount: مبلغ
            payment: پرداخت مرتبط
            description: توضیحات
            
        Returns:
            Tuple[bool, Dict]: (موفقیت، نتیجه)
        """
        try:
            with transaction.atomic():
                wallet = self.get_or_create_wallet(user)
                
                # بررسی سقف موجودی
                max_balance = WALLET_SETTINGS.get('MAX_BALANCE', Decimal('1000000000'))
                if wallet.balance + amount > max_balance:
                    return False, {
                        'error': 'max_balance_exceeded',
                        'message': f'موجودی کیف پول نمی‌تواند بیشتر از {max_balance} ریال باشد'
                    }
                
                # شارژ کیف پول
                balance_before = wallet.balance
                wallet.balance += amount
                wallet.last_transaction_at = timezone.now()
                wallet.save()
                
                # ثبت تراکنش
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='deposit',
                    amount=amount,
                    balance_before=balance_before,
                    balance_after=wallet.balance,
                    description=description,
                    payment=payment
                )
                
                self.logger.info(
                    f"Wallet charged successfully",
                    extra={
                        'user_id': user.id,
                        'amount': str(amount),
                        'new_balance': str(wallet.balance)
                    }
                )
                
                return True, {
                    'balance': wallet.balance,
                    'charged_amount': amount,
                    'message': 'کیف پول با موفقیت شارژ شد'
                }
                
        except Exception as e:
            self.logger.error(f"Error charging wallet: {str(e)}")
            return False, {
                'error': 'charge_failed',
                'message': 'خطا در شارژ کیف پول'
            }
    
    def withdraw_from_wallet(
        self,
        user: User,
        amount: Decimal,
        payment: Optional[Payment] = None,
        description: str = 'برداشت از کیف پول'
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        برداشت از کیف پول
        
        Args:
            user: کاربر
            amount: مبلغ
            payment: پرداخت مرتبط
            description: توضیحات
            
        Returns:
            Tuple[bool, Dict]: (موفقیت، نتیجه)
        """
        try:
            with transaction.atomic():
                wallet = self.get_or_create_wallet(user)
                
                # بررسی موجودی
                if wallet.available_balance < amount:
                    return False, {
                        'error': 'insufficient_balance',
                        'message': f'موجودی کافی نیست. موجودی قابل استفاده: {wallet.available_balance} ریال'
                    }
                
                # برداشت از کیف پول
                balance_before = wallet.balance
                wallet.balance -= amount
                wallet.last_transaction_at = timezone.now()
                wallet.save()
                
                # ثبت تراکنش
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='withdraw',
                    amount=amount,
                    balance_before=balance_before,
                    balance_after=wallet.balance,
                    description=description,
                    payment=payment
                )
                
                self.logger.info(
                    f"Withdrawal successful",
                    extra={
                        'user_id': user.id,
                        'amount': str(amount),
                        'new_balance': str(wallet.balance)
                    }
                )
                
                return True, {
                    'balance': wallet.balance,
                    'withdrawn_amount': amount,
                    'message': 'برداشت با موفقیت انجام شد'
                }
                
        except Exception as e:
            self.logger.error(f"Error withdrawing from wallet: {str(e)}")
            return False, {
                'error': 'withdrawal_failed',
                'message': 'خطا در برداشت از کیف پول'
            }
    
    def block_amount(
        self,
        user: User,
        amount: Decimal,
        reason: str = 'مسدود شدن موقت'
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        مسدود کردن مبلغی از کیف پول
        
        Args:
            user: کاربر
            amount: مبلغ
            reason: دلیل
            
        Returns:
            Tuple[bool, Dict]: (موفقیت، نتیجه)
        """
        try:
            with transaction.atomic():
                wallet = self.get_or_create_wallet(user)
                
                # بررسی موجودی قابل استفاده
                if wallet.available_balance < amount:
                    return False, {
                        'error': 'insufficient_balance',
                        'message': 'موجودی کافی برای مسدود کردن وجود ندارد'
                    }
                
                # مسدود کردن مبلغ
                wallet.blocked_balance += amount
                wallet.save()
                
                # ثبت تراکنش
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='block',
                    amount=amount,
                    balance_before=wallet.balance,
                    balance_after=wallet.balance,
                    description=reason
                )
                
                return True, {
                    'blocked_amount': amount,
                    'available_balance': wallet.available_balance,
                    'message': f'{amount} ریال از کیف پول مسدود شد'
                }
                
        except Exception as e:
            self.logger.error(f"Error blocking amount: {str(e)}")
            return False, {
                'error': 'block_failed',
                'message': 'خطا در مسدود کردن مبلغ'
            }
    
    def unblock_amount(
        self,
        user: User,
        amount: Decimal,
        reason: str = 'رفع مسدودی'
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        رفع مسدودی مبلغ
        
        Args:
            user: کاربر
            amount: مبلغ
            reason: دلیل
            
        Returns:
            Tuple[bool, Dict]: (موفقیت، نتیجه)
        """
        try:
            with transaction.atomic():
                wallet = self.get_or_create_wallet(user)
                
                # بررسی مبلغ مسدود شده
                if wallet.blocked_balance < amount:
                    return False, {
                        'error': 'invalid_amount',
                        'message': 'مبلغ درخواستی بیشتر از مبلغ مسدود شده است'
                    }
                
                # رفع مسدودی
                wallet.blocked_balance -= amount
                wallet.save()
                
                # ثبت تراکنش
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='unblock',
                    amount=amount,
                    balance_before=wallet.balance,
                    balance_after=wallet.balance,
                    description=reason
                )
                
                return True, {
                    'unblocked_amount': amount,
                    'available_balance': wallet.available_balance,
                    'message': f'مسدودی {amount} ریال رفع شد'
                }
                
        except Exception as e:
            self.logger.error(f"Error unblocking amount: {str(e)}")
            return False, {
                'error': 'unblock_failed',
                'message': 'خطا در رفع مسدودی'
            }
    
    def refund_to_wallet(
        self,
        user: User,
        amount: Decimal,
        payment: Optional[Payment] = None,
        description: str = 'بازگشت وجه'
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        بازگشت وجه به کیف پول
        
        Args:
            user: کاربر
            amount: مبلغ
            payment: پرداخت مرتبط
            description: توضیحات
            
        Returns:
            Tuple[bool, Dict]: (موفقیت، نتیجه)
        """
        try:
            # استفاده از متد charge_wallet با توضیحات مناسب
            return self.charge_wallet(
                user=user,
                amount=amount,
                payment=payment,
                description=description
            )
            
        except Exception as e:
            self.logger.error(f"Error refunding to wallet: {str(e)}")
            return False, {
                'error': 'refund_failed',
                'message': 'خطا در بازگشت وجه'
            }