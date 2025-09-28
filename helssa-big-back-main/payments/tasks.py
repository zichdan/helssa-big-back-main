"""
تسک‌های Celery برای پردازش‌های پس‌زمینه
"""
from celery import shared_task
import logging
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Payment, Wallet
from .services import PaymentService
from .settings import PAYMENT_SETTINGS

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task
def process_pending_payments():
    """
    پردازش پرداخت‌های معلق
    """
    try:
        # دریافت پرداخت‌های معلق قدیمی‌تر از 10 دقیقه
        timeout_minutes = PAYMENT_SETTINGS.get('PAYMENT_TIMEOUT', 600) // 60
        cutoff_time = timezone.now() - timezone.timedelta(minutes=timeout_minutes)
        
        pending_payments = Payment.objects.filter(
            status='pending',
            created_at__lt=cutoff_time
        )
        
        cancelled_count = 0
        for payment in pending_payments:
            payment.status = 'cancelled'
            payment.save()
            cancelled_count += 1
            
            logger.info(f"Payment {payment.payment_id} cancelled due to timeout")
        
        return f"Cancelled {cancelled_count} timed out payments"
        
    except Exception as e:
        logger.error(f"Error processing pending payments: {str(e)}")
        raise


@shared_task
def calculate_daily_commissions():
    """
    محاسبه کمیسیون‌های روزانه
    """
    try:
        from django.db.models import Sum
        
        # دریافت پرداخت‌های موفق دیروز
        yesterday = timezone.now().date() - timezone.timedelta(days=1)
        
        payments = Payment.objects.filter(
            status='success',
            paid_at__date=yesterday,
            payment_type__in=['appointment', 'consultation']
        )
        
        service = PaymentService()
        total_commission = Decimal('0')
        
        for payment in payments:
            commission = service.calculate_commission(
                payment.payment_type,
                payment.amount
            )
            
            # ایجاد رکورد کمیسیون
            if payment.doctor_id:
                try:
                    doctor = User.objects.get(id=payment.doctor_id)
                    
                    commission_payment = Payment.objects.create(
                        user=doctor,
                        user_type='doctor',
                        payment_type='commission',
                        amount=commission,
                        status='success',
                        description=f'کمیسیون {payment.get_payment_type_display()} - {payment.tracking_code}',
                        metadata={
                            'original_payment_id': str(payment.payment_id),
                            'commission_rate': PAYMENT_SETTINGS.get(
                                f'{payment.payment_type.upper()}_COMMISSION_RATE',
                                PAYMENT_SETTINGS.get('DEFAULT_COMMISSION_RATE', 10)
                            )
                        }
                    )
                    
                    total_commission += commission
                    
                except User.DoesNotExist:
                    logger.error(f"Doctor with id {payment.doctor_id} not found")
                    
        return f"Total commission calculated: {total_commission} Rials"
        
    except Exception as e:
        logger.error(f"Error calculating daily commissions: {str(e)}")
        raise


@shared_task
def process_withdrawal_requests():
    """
    پردازش درخواست‌های برداشت
    """
    try:
        # دریافت درخواست‌های برداشت در حال پردازش
        withdrawals = Payment.objects.filter(
            payment_type='withdrawal',
            status='processing'
        )
        
        processed_count = 0
        for withdrawal in withdrawals:
            # TODO: اتصال به سیستم بانکی برای انتقال وجه
            # فعلاً شبیه‌سازی می‌کنیم
            
            # فرض می‌کنیم انتقال موفق بوده
            withdrawal.status = 'success'
            withdrawal.paid_at = timezone.now()
            withdrawal.save()
            
            # بروزرسانی کیف پول
            try:
                wallet = Wallet.objects.get(user=withdrawal.user)
                
                # رفع مسدودی مبلغ
                if wallet.blocked_balance >= withdrawal.amount:
                    wallet.blocked_balance -= withdrawal.amount
                    wallet.balance -= withdrawal.amount
                    wallet.save()
                    
                processed_count += 1
                logger.info(f"Withdrawal {withdrawal.payment_id} processed successfully")
                
            except Wallet.DoesNotExist:
                logger.error(f"Wallet not found for user {withdrawal.user.id}")
                
        return f"Processed {processed_count} withdrawal requests"
        
    except Exception as e:
        logger.error(f"Error processing withdrawals: {str(e)}")
        raise


@shared_task
def generate_monthly_report(user_id: int, month: int, year: int):
    """
    تولید گزارش ماهانه برای کاربر
    
    Args:
        user_id: شناسه کاربر
        month: ماه (1-12)
        year: سال
    """
    try:
        from django.db.models import Sum, Count
        import jdatetime
        
        user = User.objects.get(id=user_id)
        
        # محاسبه بازه زمانی
        start_date = timezone.datetime(year, month, 1, tzinfo=timezone.get_current_timezone())
        if month == 12:
            end_date = timezone.datetime(year + 1, 1, 1, tzinfo=timezone.get_current_timezone())
        else:
            end_date = timezone.datetime(year, month + 1, 1, tzinfo=timezone.get_current_timezone())
        
        # دریافت پرداخت‌های کاربر در این ماه
        payments = Payment.objects.filter(
            user=user,
            created_at__gte=start_date,
            created_at__lt=end_date
        )
        
        # آمار کلی
        stats = payments.aggregate(
            total_amount=Sum('amount'),
            total_count=Count('payment_id'),
            success_count=Count('payment_id', filter=models.Q(status='success')),
            failed_count=Count('payment_id', filter=models.Q(status='failed'))
        )
        
        # آمار به تفکیک نوع
        by_type = payments.values('payment_type').annotate(
            count=Count('payment_id'),
            total=Sum('amount')
        )
        
        # تولید گزارش
        report = {
            'user': {
                'id': user.id,
                'name': user.get_full_name() if hasattr(user, 'get_full_name') else str(user),
                'type': getattr(user, 'user_type', 'unknown')
            },
            'period': {
                'month': month,
                'year': year,
                'month_name_fa': jdatetime.date(year, month, 1).j_months_fa[month - 1]
            },
            'summary': {
                'total_amount': str(stats['total_amount'] or 0),
                'total_count': stats['total_count'],
                'success_count': stats['success_count'],
                'failed_count': stats['failed_count']
            },
            'by_type': [
                {
                    'type': item['payment_type'],
                    'count': item['count'],
                    'total': str(item['total'] or 0)
                }
                for item in by_type
            ]
        }
        
        # TODO: ارسال گزارش به کاربر (ایمیل/SMS/نوتیفیکیشن)
        logger.info(f"Monthly report generated for user {user_id}")
        
        return report
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error generating monthly report: {str(e)}")
        raise


@shared_task
def check_wallet_limits():
    """
    بررسی محدودیت‌های کیف پول
    """
    try:
        max_balance = WALLET_SETTINGS.get('MAX_BALANCE', Decimal('1000000000'))
        
        # کیف پول‌های با موجودی بیش از حد مجاز
        over_limit_wallets = Wallet.objects.filter(
            balance__gt=max_balance,
            is_active=True
        )
        
        for wallet in over_limit_wallets:
            logger.warning(
                f"Wallet {wallet.id} for user {wallet.user.id} "
                f"exceeds max balance: {wallet.balance}"
            )
            
            # TODO: اقدام مناسب (مثلاً ارسال اخطار به کاربر)
            
        return f"Found {over_limit_wallets.count()} wallets over limit"
        
    except Exception as e:
        logger.error(f"Error checking wallet limits: {str(e)}")
        raise