"""
سرویس مدیریت تراکنش‌ها
Transaction Management Service
"""

from decimal import Decimal
from typing import Dict, Any, Optional, Tuple, List
from django.db import transaction as db_transaction
from django.utils import timezone
from django.db import models
from django.db.models import Q, Sum, Count, Avg

from .base_service import BaseService
from ..models import (
    Transaction, TransactionType, TransactionStatus, 
    Wallet, PaymentGateway
)


class TransactionService(BaseService):
    """سرویس مدیریت تراکنش‌های مالی"""
    
    def __init__(self):
        super().__init__()
        
    def create_transaction(
        self,
        wallet: Wallet,
        amount: Decimal,
        transaction_type: str,
        reference_number: str = None,
        description: str = '',
        gateway: str = None,
        metadata: Optional[Dict] = None,
        related_transaction: Transaction = None,
        related_wallet: Wallet = None
    ) -> Transaction:
        """
        ایجاد تراکنش جدید
        
        Args:
            wallet: کیف پول
            amount: مبلغ
            transaction_type: نوع تراکنش
            reference_number: شماره مرجع
            description: توضیحات
            gateway: درگاه پرداخت
            metadata: متادیتا
            related_transaction: تراکنش مرتبط
            related_wallet: کیف پول مرتبط
            
        Returns:
            Transaction: تراکنش ایجاد شده
        """
        try:
            # تولید شماره مرجع در صورت عدم وجود
            if not reference_number:
                reference_number = self.generate_reference_number('TXN')
            
            # ایجاد تراکنش
            transaction = Transaction.objects.create(
                wallet=wallet,
                amount=amount,
                type=transaction_type,
                reference_number=reference_number,
                description=description,
                gateway=gateway,
                metadata=metadata or {},
                related_transaction=related_transaction,
                related_wallet=related_wallet
            )
            
            self.log_operation('create_transaction', wallet.user, {
                'transaction_id': str(transaction.id),
                'amount': amount,
                'type': transaction_type,
                'reference': reference_number
            })
            
            return transaction
            
        except Exception as e:
            self.logger.error(f"خطا در ایجاد تراکنش: {str(e)}")
            raise
    
    def complete_transaction(
        self,
        transaction_id: str,
        gateway_reference: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        تکمیل تراکنش
        
        Args:
            transaction_id: شناسه تراکنش
            gateway_reference: مرجع درگاه
            
        Returns:
            Tuple[bool, Dict]: نتیجه تکمیل
        """
        try:
            with db_transaction.atomic():
                transaction = Transaction.objects.select_for_update().get(
                    id=transaction_id,
                    status=TransactionStatus.PENDING
                )
                
                # تکمیل تراکنش
                transaction.mark_completed(gateway_reference)
                
                self.log_operation('complete_transaction', transaction.wallet.user, {
                    'transaction_id': str(transaction.id),
                    'reference': transaction.reference_number,
                    'gateway_reference': gateway_reference
                })
                
                return self.success_response({
                    'transaction_id': str(transaction.id),
                    'status': transaction.status,
                    'completed_at': transaction.completed_at
                }, 'تراکنش با موفقیت تکمیل شد')
                
        except Transaction.DoesNotExist:
            return self.error_response(
                'transaction_not_found',
                'تراکنش یافت نشد یا قابل تکمیل نیست'
            )
        except Exception as e:
            self.logger.error(f"خطا در تکمیل تراکنش: {str(e)}")
            return self.error_response(
                'completion_failed',
                'خطا در تکمیل تراکنش'
            )
    
    def fail_transaction(
        self,
        transaction_id: str,
        reason: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        ثبت شکست تراکنش
        
        Args:
            transaction_id: شناسه تراکنش
            reason: دلیل شکست
            
        Returns:
            Tuple[bool, Dict]: نتیجه ثبت شکست
        """
        try:
            transaction = Transaction.objects.get(id=transaction_id)
            
            # ثبت شکست
            transaction.mark_failed(reason)
            
            # بازگشت تغییرات کیف پول در صورت نیاز
            if transaction.type in [TransactionType.WITHDRAWAL, TransactionType.TRANSFER_OUT]:
                self._reverse_wallet_changes(transaction)
            
            self.log_operation('fail_transaction', transaction.wallet.user, {
                'transaction_id': str(transaction.id),
                'reason': reason
            })
            
            return self.success_response({
                'transaction_id': str(transaction.id),
                'status': transaction.status,
                'failure_reason': reason
            }, 'تراکنش ناموفق ثبت شد')
            
        except Transaction.DoesNotExist:
            return self.error_response('transaction_not_found', 'تراکنش یافت نشد')
        except Exception as e:
            self.logger.error(f"خطا در ثبت شکست تراکنش: {str(e)}")
            return self.error_response(
                'fail_recording_failed',
                'خطا در ثبت شکست تراکنش'
            )
    
    def get_transaction(self, transaction_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        دریافت جزئیات تراکنش
        
        Args:
            transaction_id: شناسه تراکنش
            
        Returns:
            Tuple[bool, Dict]: جزئیات تراکنش
        """
        try:
            transaction = Transaction.objects.select_related('wallet__user').get(
                id=transaction_id
            )
            
            transaction_data = {
                'id': str(transaction.id),
                'wallet_id': str(transaction.wallet.id),
                'user_id': str(transaction.wallet.user.id),
                'amount': transaction.amount,
                'type': transaction.type,
                'type_display': transaction.get_type_display(),
                'status': transaction.status,
                'status_display': transaction.get_status_display(),
                'reference_number': transaction.reference_number,
                'gateway_reference': transaction.gateway_reference,
                'gateway': transaction.gateway,
                'description': transaction.description,
                'fee_amount': transaction.fee_amount,
                'net_amount': transaction.net_amount,
                'created_at': transaction.created_at,
                'completed_at': transaction.completed_at,
                'metadata': transaction.metadata,
                'is_income': transaction.is_income,
                'is_expense': transaction.is_expense,
            }
            
            # تراکنش مرتبط
            if transaction.related_transaction:
                transaction_data['related_transaction_id'] = str(transaction.related_transaction.id)
            
            # کیف پول مرتبط
            if transaction.related_wallet:
                transaction_data['related_wallet_id'] = str(transaction.related_wallet.id)
            
            return self.success_response(transaction_data)
            
        except Transaction.DoesNotExist:
            return self.error_response('transaction_not_found', 'تراکنش یافت نشد')
        except Exception as e:
            self.logger.error(f"خطا در دریافت تراکنش: {str(e)}")
            return self.error_response(
                'transaction_retrieval_failed',
                'خطا در دریافت اطلاعات تراکنش'
            )
    
    def get_transaction_report(
        self,
        wallet_id: str,
        start_date: timezone.datetime,
        end_date: timezone.datetime,
        transaction_type: str = None,
        status: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        گزارش تراکنش‌ها
        
        Args:
            wallet_id: شناسه کیف پول
            start_date: تاریخ شروع
            end_date: تاریخ پایان
            transaction_type: نوع تراکنش
            status: وضعیت تراکنش
            
        Returns:
            Tuple[bool, Dict]: گزارش تراکنش‌ها
        """
        try:
            # Query builder
            query = Transaction.objects.filter(
                wallet_id=wallet_id,
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            
            if transaction_type:
                query = query.filter(type=transaction_type)
            
            if status:
                query = query.filter(status=status)
            
            # آمار کلی
            summary = query.aggregate(
                total_count=Count('id'),
                total_income=Sum('amount', filter=Q(amount__gt=0)),
                total_expense=Sum('amount', filter=Q(amount__lt=0)),
                net_amount=Sum('amount'),
                total_fees=Sum('fee_amount')
            )
            
            # پردازش نتایج null
            for key, value in summary.items():
                if value is None:
                    summary[key] = 0
            
            # گروه‌بندی بر اساس نوع
            by_type = query.values('type').annotate(
                count=Count('id'),
                total_amount=Sum('amount'),
                avg_amount=models.Avg('amount')
            ).order_by('-total_amount')
            
            # گروه‌بندی بر اساس وضعیت
            by_status = query.values('status').annotate(
                count=Count('id'),
                total_amount=Sum('amount')
            ).order_by('-count')
            
            # تراکنش‌های اخیر
            recent_transactions = query.order_by('-created_at')[:20]
            
            recent_list = []
            for transaction in recent_transactions:
                recent_list.append({
                    'id': str(transaction.id),
                    'amount': transaction.amount,
                    'type': transaction.type,
                    'type_display': transaction.get_type_display(),
                    'status': transaction.status,
                    'status_display': transaction.get_status_display(),
                    'reference_number': transaction.reference_number,
                    'description': transaction.description,
                    'created_at': transaction.created_at,
                })
            
            return self.success_response({
                'summary': summary,
                'by_type': list(by_type),
                'by_status': list(by_status),
                'recent_transactions': recent_list,
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                }
            })
            
        except Exception as e:
            self.logger.error(f"خطا در تولید گزارش: {str(e)}")
            return self.error_response(
                'report_generation_failed',
                'خطا در تولید گزارش تراکنش‌ها'
            )
    
    def search_transactions(
        self,
        wallet_id: str,
        search_term: str,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        جستجو در تراکنش‌ها
        
        Args:
            wallet_id: شناسه کیف پول
            search_term: عبارت جستجو
            limit: تعداد نتایج
            offset: جابجایی
            
        Returns:
            Tuple[bool, Dict]: نتایج جستجو
        """
        try:
            # جستجو در فیلدهای مختلف
            query = Transaction.objects.filter(
                wallet_id=wallet_id
            ).filter(
                Q(reference_number__icontains=search_term) |
                Q(gateway_reference__icontains=search_term) |
                Q(description__icontains=search_term) |
                Q(amount__icontains=search_term.replace(',', ''))
            )
            
            # تعداد کل
            total_count = query.count()
            
            # صفحه‌بندی
            transactions = query.order_by('-created_at')[offset:offset + limit]
            
            # تبدیل به لیست
            transaction_list = []
            for transaction in transactions:
                transaction_list.append({
                    'id': str(transaction.id),
                    'amount': transaction.amount,
                    'type': transaction.type,
                    'type_display': transaction.get_type_display(),
                    'status': transaction.status,
                    'status_display': transaction.get_status_display(),
                    'reference_number': transaction.reference_number,
                    'gateway_reference': transaction.gateway_reference,
                    'description': transaction.description,
                    'created_at': transaction.created_at,
                    'completed_at': transaction.completed_at,
                })
            
            return self.success_response({
                'transactions': transaction_list,
                'total_count': total_count,
                'search_term': search_term,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_count
            })
            
        except Exception as e:
            self.logger.error(f"خطا در جستجو: {str(e)}")
            return self.error_response(
                'search_failed',
                'خطا در جستجوی تراکنش‌ها'
            )
    
    def refund_transaction(
        self,
        transaction_id: str,
        refund_amount: Decimal = None,
        reason: str = ''
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        بازگشت تراکنش
        
        Args:
            transaction_id: شناسه تراکنش
            refund_amount: مبلغ بازگشت
            reason: دلیل بازگشت
            
        Returns:
            Tuple[bool, Dict]: نتیجه بازگشت
        """
        try:
            with db_transaction.atomic():
                original_transaction = Transaction.objects.select_for_update().get(
                    id=transaction_id
                )
                
                # بررسی قابلیت بازگشت
                if not original_transaction.can_be_refunded():
                    return self.error_response(
                        'refund_not_allowed',
                        'این تراکنش قابل بازگشت نیست'
                    )
                
                # ایجاد تراکنش بازگشت
                refund_transaction = original_transaction.create_refund(
                    amount=refund_amount,
                    description=reason or f'بازگشت تراکنش {original_transaction.reference_number}'
                )
                
                # بازگشت مبلغ به کیف پول
                wallet = original_transaction.wallet
                wallet.deposit(refund_transaction.amount, "Refund")
                
                # به‌روزرسانی وضعیت تراکنش اصلی
                original_transaction.status = TransactionStatus.REFUNDED
                original_transaction.save()
                
                self.log_operation('refund_transaction', wallet.user, {
                    'original_transaction_id': str(original_transaction.id),
                    'refund_transaction_id': str(refund_transaction.id),
                    'refund_amount': refund_transaction.amount,
                    'reason': reason
                })
                
                return self.success_response({
                    'original_transaction_id': str(original_transaction.id),
                    'refund_transaction_id': str(refund_transaction.id),
                    'refund_amount': refund_transaction.amount,
                    'new_wallet_balance': wallet.balance
                }, f'مبلغ {refund_transaction.amount:,} ریال بازگشت داده شد')
                
        except Transaction.DoesNotExist:
            return self.error_response('transaction_not_found', 'تراکنش یافت نشد')
        except ValueError as e:
            return self.error_response('invalid_refund', str(e))
        except Exception as e:
            self.logger.error(f"خطا در بازگشت تراکنش: {str(e)}")
            return self.error_response(
                'refund_failed',
                'خطا در بازگشت تراکنش'
            )
    
    def get_daily_summary(self, wallet_id: str, date: timezone.date = None) -> Tuple[bool, Dict[str, Any]]:
        """
        خلاصه تراکنش‌های روزانه
        
        Args:
            wallet_id: شناسه کیف پول
            date: تاریخ (پیش‌فرض: امروز)
            
        Returns:
            Tuple[bool, Dict]: خلاصه روزانه
        """
        try:
            if not date:
                date = timezone.now().date()
            
            # تراکنش‌های روز
            transactions = Transaction.objects.filter(
                wallet_id=wallet_id,
                created_at__date=date,
                status=TransactionStatus.COMPLETED
            )
            
            # محاسبه آمار
            summary = transactions.aggregate(
                total_transactions=Count('id'),
                total_income=Sum('amount', filter=Q(amount__gt=0)),
                total_expense=Sum('amount', filter=Q(amount__lt=0)),
                net_change=Sum('amount')
            )
            
            # پردازش null values
            for key, value in summary.items():
                if value is None:
                    summary[key] = 0
            
            # تراکنش‌های بر اساس نوع
            by_type = transactions.values('type').annotate(
                count=Count('id'),
                total=Sum('amount')
            ).order_by('-count')
            
            return self.success_response({
                'date': date.isoformat(),
                'summary': summary,
                'by_type': list(by_type)
            })
            
        except Exception as e:
            self.logger.error(f"خطا در خلاصه روزانه: {str(e)}")
            return self.error_response(
                'daily_summary_failed',
                'خطا در تولید خلاصه روزانه'
            )
    
    def _reverse_wallet_changes(self, transaction: Transaction):
        """بازگشت تغییرات کیف پول"""
        try:
            wallet = transaction.wallet
            
            if transaction.type == TransactionType.WITHDRAWAL:
                # بازگشت مبلغ برداشت شده
                wallet.deposit(abs(transaction.amount), "Reversal of failed withdrawal")
            elif transaction.type == TransactionType.TRANSFER_OUT:
                # بازگشت مبلغ انتقال یافته
                wallet.deposit(abs(transaction.amount), "Reversal of failed transfer")
                
            self.log_operation('reverse_wallet_changes', wallet.user, {
                'transaction_id': str(transaction.id),
                'reversed_amount': abs(transaction.amount),
                'new_balance': wallet.balance
            })
            
        except Exception as e:
            self.logger.error(f"خطا در بازگشت تغییرات کیف پول: {str(e)}")