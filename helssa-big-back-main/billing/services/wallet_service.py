"""
سرویس مدیریت کیف پول
Wallet Management Service
"""

from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
from django.db import transaction as db_transaction
from django.contrib.auth import get_user_model
from django.utils import timezone

from .base_service import BaseService
from ..models import Wallet, Transaction, TransactionType, TransactionStatus

User = get_user_model()


class WalletService(BaseService):
    """سرویس مدیریت کیف پول دیجیتال"""
    
    def __init__(self):
        super().__init__()
        
    def create_wallet(self, user: User) -> Tuple[bool, Dict[str, Any]]:
        """
        ایجاد کیف پول برای کاربر
        
        Args:
            user: کاربر
            
        Returns:
            Tuple[bool, Dict]: نتیجه ایجاد کیف پول
        """
        try:
            # بررسی کاربر
            success, result = self.validate_user(user)
            if not success:
                return success, result
            
            # بررسی وجود کیف پول
            if hasattr(user, 'wallet'):
                return self.error_response(
                    'wallet_exists',
                    'کیف پول برای این کاربر از قبل وجود دارد'
                )
            
            # ایجاد کیف پول
            wallet = Wallet.objects.create(user=user)
            
            self.log_operation('create_wallet', user, {
                'wallet_id': str(wallet.id)
            })
            
            return self.success_response({
                'wallet_id': str(wallet.id),
                'balance': wallet.balance,
                'status': 'created'
            }, 'کیف پول با موفقیت ایجاد شد')
            
        except Exception as e:
            self.logger.error(f"خطا در ایجاد کیف پول: {str(e)}")
            return self.error_response(
                'wallet_creation_failed',
                'خطا در ایجاد کیف پول'
            )
    
    def get_wallet_info(self, user: User) -> Tuple[bool, Dict[str, Any]]:
        """
        دریافت اطلاعات کیف پول
        
        Args:
            user: کاربر
            
        Returns:
            Tuple[bool, Dict]: اطلاعات کیف پول
        """
        try:
            # اعتبارسنجی کیف پول
            success, result = self.validate_wallet(user)
            if not success:
                return success, result
                
            wallet = result['data']['wallet']
            
            # آمار کیف پول
            wallet_info = {
                'wallet_id': str(wallet.id),
                'balance': wallet.balance,
                'blocked_balance': wallet.blocked_balance,
                'available_balance': wallet.available_balance,
                'gift_credit': wallet.gift_credit,
                'total_credit': wallet.total_credit,
                'is_verified': wallet.is_verified,
                'daily_limit': wallet.daily_withdrawal_limit,
                'monthly_limit': wallet.monthly_withdrawal_limit,
                'last_transaction': wallet.last_transaction_at,
                'created_at': wallet.created_at,
            }
            
            # محاسبه آمار
            today_withdrawals = self._get_daily_withdrawal_total(wallet)
            month_withdrawals = self._get_monthly_withdrawal_total(wallet)
            
            wallet_info.update({
                'today_withdrawals': today_withdrawals,
                'month_withdrawals': month_withdrawals,
                'remaining_daily_limit': wallet.daily_withdrawal_limit - today_withdrawals,
                'remaining_monthly_limit': wallet.monthly_withdrawal_limit - month_withdrawals,
            })
            
            return self.success_response(wallet_info)
            
        except Exception as e:
            self.logger.error(f"خطا در دریافت اطلاعات کیف پول: {str(e)}")
            return self.error_response(
                'wallet_info_error',
                'خطا در دریافت اطلاعات کیف پول'
            )
    
    @db_transaction.atomic
    def deposit(
        self,
        user: User,
        amount: Decimal,
        source: str = 'manual',
        reference: str = None,
        description: str = '',
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        واریز به کیف پول
        
        Args:
            user: کاربر
            amount: مبلغ واریز
            source: منبع واریز
            reference: شماره مرجع
            description: توضیحات
            metadata: متادیتا
            
        Returns:
            Tuple[bool, Dict]: نتیجه واریز
        """
        try:
            # اعتبارسنجی کیف پول
            success, result = self.validate_wallet(user)
            if not success:
                return success, result
                
            wallet = result['data']['wallet']
            
            # اعتبارسنجی مبلغ
            success, result = self.validate_amount(amount)
            if not success:
                return success, result
                
            amount = result['data']['validated_amount']
            
            # تولید شماره مرجع
            if not reference:
                reference = self.generate_reference_number('DEP')
            
            # ایجاد تراکنش
            from .transaction_service import TransactionService
            transaction_service = TransactionService()
            
            transaction = transaction_service.create_transaction(
                wallet=wallet,
                amount=amount,
                transaction_type=TransactionType.DEPOSIT,
                reference_number=reference,
                description=description or f'واریز {amount:,} ریال',
                metadata=metadata or {}
            )
            
            # واریز به کیف پول
            wallet.deposit(amount, description)
            
            # تکمیل تراکنش
            transaction_service.complete_transaction(str(transaction.id))
            
            self.log_operation('wallet_deposit', user, {
                'amount': amount,
                'wallet_id': str(wallet.id),
                'transaction_id': str(transaction.id),
                'new_balance': wallet.balance
            })
            
            return self.success_response({
                'transaction_id': str(transaction.id),
                'amount': amount,
                'new_balance': wallet.balance,
                'reference': reference
            }, f'مبلغ {amount:,} ریال با موفقیت واریز شد')
            
        except Exception as e:
            self.logger.error(f"خطا در واریز: {str(e)}")
            return self.error_response(
                'deposit_failed',
                'خطا در واریز به کیف پول'
            )
    
    @db_transaction.atomic
    def withdraw(
        self,
        user: User,
        amount: Decimal,
        destination: str = 'bank_account',
        description: str = '',
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        برداشت از کیف پول
        
        Args:
            user: کاربر
            amount: مبلغ برداشت
            destination: مقصد برداشت
            description: توضیحات
            metadata: متادیتا
            
        Returns:
            Tuple[bool, Dict]: نتیجه برداشت
        """
        try:
            # اعتبارسنجی کیف پول
            success, result = self.validate_wallet(user)
            if not success:
                return success, result
                
            wallet = result['data']['wallet']
            
            # اعتبارسنجی مبلغ
            success, result = self.validate_amount(amount)
            if not success:
                return success, result
                
            amount = result['data']['validated_amount']
            
            # بررسی محدودیت‌های برداشت
            success, result = self._validate_withdrawal(wallet, amount)
            if not success:
                return success, result
            
            # بررسی موجودی
            if not wallet.can_withdraw(amount):
                return self.error_response(
                    'insufficient_balance',
                    f'موجودی کافی نیست. موجودی قابل استفاده: {wallet.available_balance:,} ریال'
                )
            
            # تولید شماره مرجع
            reference = self.generate_reference_number('WDR')
            
            # ایجاد تراکنش
            from .transaction_service import TransactionService
            transaction_service = TransactionService()
            
            transaction = transaction_service.create_transaction(
                wallet=wallet,
                amount=-amount,  # منفی برای برداشت
                transaction_type=TransactionType.WITHDRAWAL,
                reference_number=reference,
                description=description or f'برداشت {amount:,} ریال',
                metadata=metadata or {}
            )
            
            # برداشت از کیف پول
            wallet.withdraw(amount, description)
            
            # تکمیل تراکنش
            transaction_service.complete_transaction(str(transaction.id))
            
            self.log_operation('wallet_withdrawal', user, {
                'amount': amount,
                'wallet_id': str(wallet.id),
                'transaction_id': str(transaction.id),
                'new_balance': wallet.balance,
                'destination': destination
            })
            
            return self.success_response({
                'transaction_id': str(transaction.id),
                'amount': amount,
                'new_balance': wallet.balance,
                'reference': reference,
                'destination': destination
            }, f'مبلغ {amount:,} ریال با موفقیت برداشت شد')
            
        except Exception as e:
            self.logger.error(f"خطا در برداشت: {str(e)}")
            return self.error_response(
                'withdrawal_failed',
                'خطا در برداشت از کیف پول'
            )
    
    @db_transaction.atomic
    def transfer(
        self,
        from_user: User,
        to_user: User,
        amount: Decimal,
        description: str = '',
        commission_rate: Decimal = Decimal('0')
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        انتقال بین کیف پول‌ها
        
        Args:
            from_user: کاربر فرستنده
            to_user: کاربر گیرنده
            amount: مبلغ انتقال
            description: توضیحات
            commission_rate: نرخ کمیسیون
            
        Returns:
            Tuple[bool, Dict]: نتیجه انتقال
        """
        try:
            # اعتبارسنجی کیف پول فرستنده
            success, result = self.validate_wallet(from_user)
            if not success:
                return success, result
            from_wallet = result['data']['wallet']
            
            # اعتبارسنجی کیف پول گیرنده
            success, result = self.validate_wallet(to_user)
            if not success:
                return success, result
            to_wallet = result['data']['wallet']
            
            # اعتبارسنجی مبلغ
            success, result = self.validate_amount(amount)
            if not success:
                return success, result
            amount = result['data']['validated_amount']
            
            # محاسبه مبلغ کل (شامل کمیسیون)
            commission = amount * commission_rate
            total_amount = amount + commission
            
            # بررسی موجودی فرستنده
            if not from_wallet.has_sufficient_balance(total_amount):
                return self.error_response(
                    'insufficient_balance',
                    f'موجودی کافی نیست. مبلغ مورد نیاز: {total_amount:,} ریال'
                )
            
            # قفل هر دو کیف پول (جلوگیری از deadlock)
            wallets = [from_wallet, to_wallet]
            wallets.sort(key=lambda w: str(w.id))
            
            from .transaction_service import TransactionService
            transaction_service = TransactionService()
            
            # تراکنش برداشت از فرستنده
            from_ref = self.generate_reference_number('TRF')
            from_transaction = transaction_service.create_transaction(
                wallet=from_wallet,
                amount=-total_amount,
                transaction_type=TransactionType.TRANSFER_OUT,
                reference_number=from_ref,
                description=description or f'انتقال {amount:,} ریال',
                metadata={
                    'to_user_id': str(to_user.id),
                    'commission': commission,
                    'net_amount': amount
                }
            )
            
            # تراکنش واریز به گیرنده
            to_ref = self.generate_reference_number('TRF')
            to_transaction = transaction_service.create_transaction(
                wallet=to_wallet,
                amount=amount,
                transaction_type=TransactionType.TRANSFER_IN,
                reference_number=to_ref,
                description=description or f'دریافت {amount:,} ریال',
                metadata={
                    'from_user_id': str(from_user.id),
                    'commission': commission,
                    'gross_amount': total_amount
                },
                related_transaction=from_transaction
            )
            
            # اجرای انتقال
            from_wallet.withdraw(total_amount, "Transfer out")
            to_wallet.deposit(amount, "Transfer in")
            
            # تکمیل تراکنش‌ها
            transaction_service.complete_transaction(str(from_transaction.id))
            transaction_service.complete_transaction(str(to_transaction.id))
            
            # ثبت کمیسیون در صورت وجود
            commission_transaction = None
            if commission > 0:
                commission_transaction = self._record_commission(
                    commission, from_transaction
                )
            
            self.log_operation('wallet_transfer', from_user, {
                'amount': amount,
                'commission': commission,
                'total_amount': total_amount,
                'to_user_id': str(to_user.id),
                'from_transaction_id': str(from_transaction.id),
                'to_transaction_id': str(to_transaction.id)
            })
            
            result_data = {
                'from_transaction_id': str(from_transaction.id),
                'to_transaction_id': str(to_transaction.id),
                'amount': amount,
                'commission': commission,
                'total_amount': total_amount,
                'from_balance': from_wallet.balance,
                'to_balance': to_wallet.balance
            }
            
            if commission_transaction:
                result_data['commission_transaction_id'] = str(commission_transaction.id)
            
            return self.success_response(
                result_data,
                f'انتقال {amount:,} ریال با موفقیت انجام شد'
            )
            
        except Exception as e:
            self.logger.error(f"خطا در انتقال: {str(e)}")
            return self.error_response(
                'transfer_failed',
                'خطا در انتقال بین کیف پول‌ها'
            )
    
    def block_amount(
        self,
        user: User,
        amount: Decimal,
        reason: str = ''
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        بلوک کردن مبلغ در کیف پول
        
        Args:
            user: کاربر
            amount: مبلغ
            reason: دلیل بلوک
            
        Returns:
            Tuple[bool, Dict]: نتیجه بلوک
        """
        try:
            # اعتبارسنجی کیف پول
            success, result = self.validate_wallet(user)
            if not success:
                return success, result
            wallet = result['data']['wallet']
            
            # اعتبارسنجی مبلغ
            success, result = self.validate_amount(amount)
            if not success:
                return success, result
            amount = result['data']['validated_amount']
            
            # بلوک کردن مبلغ
            if wallet.block_amount(amount):
                self.log_operation('wallet_block', user, {
                    'amount': amount,
                    'reason': reason,
                    'new_blocked_balance': wallet.blocked_balance
                })
                
                return self.success_response({
                    'blocked_amount': amount,
                    'total_blocked': wallet.blocked_balance,
                    'available_balance': wallet.available_balance
                }, f'مبلغ {amount:,} ریال بلوک شد')
            else:
                return self.error_response(
                    'insufficient_balance',
                    'موجودی کافی برای بلوک کردن وجود ندارد'
                )
                
        except Exception as e:
            self.logger.error(f"خطا در بلوک کردن مبلغ: {str(e)}")
            return self.error_response(
                'block_failed',
                'خطا در بلوک کردن مبلغ'
            )
    
    def unblock_amount(
        self,
        user: User,
        amount: Decimal,
        reason: str = ''
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        آزاد کردن مبلغ بلوک شده
        
        Args:
            user: کاربر
            amount: مبلغ
            reason: دلیل آزادسازی
            
        Returns:
            Tuple[bool, Dict]: نتیجه آزادسازی
        """
        try:
            # اعتبارسنجی کیف پول
            success, result = self.validate_wallet(user)
            if not success:
                return success, result
            wallet = result['data']['wallet']
            
            # اعتبارسنجی مبلغ
            success, result = self.validate_amount(amount)
            if not success:
                return success, result
            amount = result['data']['validated_amount']
            
            # آزاد کردن مبلغ
            if wallet.unblock_amount(amount):
                self.log_operation('wallet_unblock', user, {
                    'amount': amount,
                    'reason': reason,
                    'new_blocked_balance': wallet.blocked_balance
                })
                
                return self.success_response({
                    'unblocked_amount': amount,
                    'total_blocked': wallet.blocked_balance,
                    'available_balance': wallet.available_balance
                }, f'مبلغ {amount:,} ریال آزاد شد')
            else:
                return self.error_response(
                    'insufficient_blocked_amount',
                    'مبلغ بلوک شده کافی وجود ندارد'
                )
                
        except Exception as e:
            self.logger.error(f"خطا در آزاد کردن مبلغ: {str(e)}")
            return self.error_response(
                'unblock_failed',
                'خطا در آزاد کردن مبلغ'
            )
    
    def get_transaction_history(
        self,
        user: User,
        limit: int = 20,
        offset: int = 0,
        transaction_type: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        دریافت تاریخچه تراکنش‌ها
        
        Args:
            user: کاربر
            limit: تعداد نتایج
            offset: جابجایی
            transaction_type: نوع تراکنش
            
        Returns:
            Tuple[bool, Dict]: تاریخچه تراکنش‌ها
        """
        try:
            # اعتبارسنجی کیف پول
            success, result = self.validate_wallet(user)
            if not success:
                return success, result
            wallet = result['data']['wallet']
            
            # فیلتر تراکنش‌ها
            queryset = Transaction.objects.filter(wallet=wallet)
            
            if transaction_type:
                queryset = queryset.filter(type=transaction_type)
            
            # صفحه‌بندی
            total_count = queryset.count()
            transactions = queryset[offset:offset + limit]
            
            # تبدیل به دیکشنری
            transaction_list = []
            for transaction in transactions:
                transaction_list.append({
                    'id': str(transaction.id),
                    'amount': transaction.amount,
                    'type': transaction.type,
                    'type_display': transaction.get_type_display(),
                    'status': transaction.status,
                    'status_display': transaction.get_status_display(),
                    'description': transaction.description,
                    'reference_number': transaction.reference_number,
                    'gateway': transaction.gateway,
                    'created_at': transaction.created_at,
                    'completed_at': transaction.completed_at,
                })
            
            return self.success_response({
                'transactions': transaction_list,
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_count
            })
            
        except Exception as e:
            self.logger.error(f"خطا در دریافت تاریخچه: {str(e)}")
            return self.error_response(
                'history_error',
                'خطا در دریافت تاریخچه تراکنش‌ها'
            )
    
    def _validate_withdrawal(
        self,
        wallet: Wallet,
        amount: Decimal
    ) -> Tuple[bool, Dict[str, Any]]:
        """بررسی محدودیت‌های برداشت"""
        
        # بررسی محدودیت روزانه
        daily_total = self._get_daily_withdrawal_total(wallet)
        if daily_total + amount > wallet.daily_withdrawal_limit:
            return self.error_response(
                'daily_limit_exceeded',
                f'از محدودیت برداشت روزانه ({wallet.daily_withdrawal_limit:,} ریال) تجاوز می‌کند'
            )
        
        # بررسی محدودیت ماهانه
        monthly_total = self._get_monthly_withdrawal_total(wallet)
        if monthly_total + amount > wallet.monthly_withdrawal_limit:
            return self.error_response(
                'monthly_limit_exceeded',
                f'از محدودیت برداشت ماهانه ({wallet.monthly_withdrawal_limit:,} ریال) تجاوز می‌کند'
            )
        
        # بررسی تایید هویت برای مبالغ بالا
        if amount > 10000000 and not wallet.is_verified:  # 10 میلیون ریال
            return self.error_response(
                'verification_required',
                'برای برداشت مبالغ بالای 10 میلیون ریال، تایید هویت الزامی است'
            )
        
        return self.success_response()
    
    def _get_daily_withdrawal_total(self, wallet: Wallet) -> Decimal:
        """محاسبه کل برداشت روزانه"""
        from datetime import date
        
        today = date.today()
        
        total = Transaction.objects.filter(
            wallet=wallet,
            type=TransactionType.WITHDRAWAL,
            status=TransactionStatus.COMPLETED,
            created_at__date=today
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
        
        return abs(total)  # مقدار مثبت
    
    def _get_monthly_withdrawal_total(self, wallet: Wallet) -> Decimal:
        """محاسبه کل برداشت ماهانه"""
        from datetime import date
        
        today = date.today()
        first_of_month = today.replace(day=1)
        
        total = Transaction.objects.filter(
            wallet=wallet,
            type=TransactionType.WITHDRAWAL,
            status=TransactionStatus.COMPLETED,
            created_at__date__gte=first_of_month
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
        
        return abs(total)  # مقدار مثبت
    
    def _record_commission(
        self,
        commission_amount: Decimal,
        source_transaction: Transaction
    ) -> Transaction:
        """ثبت کمیسیون"""
        from .transaction_service import TransactionService
        
        transaction_service = TransactionService()
        
        # فرض می‌کنیم کیف پول سیستم وجود دارد
        # در پیاده‌سازی واقعی باید کیف پول سیستم تعریف شود
        
        commission_transaction = transaction_service.create_transaction(
            wallet=source_transaction.wallet,  # موقتاً همان کیف پول
            amount=commission_amount,
            transaction_type=TransactionType.COMMISSION,
            reference_number=self.generate_reference_number('COM'),
            description=f'کمیسیون تراکنش {source_transaction.reference_number}',
            related_transaction=source_transaction
        )
        
        transaction_service.complete_transaction(str(commission_transaction.id))
        
        return commission_transaction