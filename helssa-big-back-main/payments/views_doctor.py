"""
ویوهای مربوط به دکتر در اپلیکیشن پرداخت
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction, models
from django.utils import timezone
from django.core.cache import cache
from decimal import Decimal
import jdatetime

from .models import Payment, PaymentMethod, Wallet, WalletTransaction
from .serializers import (
    PaymentSerializer, PaymentMethodSerializer,
    WalletSerializer, WalletTransactionSerializer
)
from .cores.orchestrator import CentralOrchestrator
from .cores.api_ingress import APIIngressCore

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def doctor_create_withdrawal(request):
    """
    درخواست برداشت توسط دکتر
    """
    try:
        api_core = APIIngressCore()
        orchestrator = CentralOrchestrator()
        
        # بررسی نوع کاربر
        user_type = getattr(request.user, 'user_type', 'doctor')
        if user_type != 'doctor':
            return api_core.format_response(
                success=False,
                error='unauthorized',
                message='این عملیات فقط برای پزشکان مجاز است',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # دریافت داده‌های درخواست
        amount = request.data.get('amount')
        bank_account = request.data.get('bank_account')
        
        if not amount or not bank_account:
            return api_core.format_response(
                success=False,
                error='missing_data',
                message='مبلغ و اطلاعات حساب بانکی الزامی است',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # بررسی موجودی کیف پول
        try:
            wallet = Wallet.objects.get(user=request.user)
            available = wallet.available_balance
            
            if Decimal(amount) > available:
                return api_core.format_response(
                    success=False,
                    error='insufficient_balance',
                    message=f'موجودی کافی نیست. موجودی قابل برداشت: {available} ریال',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                
        except Wallet.DoesNotExist:
            return api_core.format_response(
                success=False,
                error='no_wallet',
                message='کیف پولی برای شما یافت نشد',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # پردازش درخواست برداشت
        payment_data = {
            'type': 'withdrawal',
            'amount': amount,
            'bank_account': bank_account
        }
        
        success, processed_data = orchestrator.process_payment_request(
            user_type='doctor',
            payment_data=payment_data
        )
        
        if not success:
            return api_core.format_response(
                success=False,
                error=processed_data.get('error'),
                message=processed_data.get('message'),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # ایجاد رکورد برداشت
        with transaction.atomic():
            payment = Payment.objects.create(
                user=request.user,
                user_type='doctor',
                payment_type='withdrawal',
                amount=amount,
                description=f'برداشت به حساب {bank_account}',
                status='pending',
                metadata={
                    'bank_account': bank_account,
                    'wallet_balance_before': str(wallet.balance)
                }
            )
            
            # مسدود کردن مبلغ در کیف پول
            wallet.blocked_balance += Decimal(amount)
            wallet.save()
            
            # ثبت تراکنش کیف پول
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='block',
                amount=amount,
                balance_before=wallet.balance,
                balance_after=wallet.balance,
                description='مسدود شدن برای برداشت',
                payment=payment
            )
            
            return api_core.format_response(
                success=True,
                data={
                    'payment_id': str(payment.payment_id),
                    'tracking_code': payment.tracking_code,
                    'amount': str(payment.amount),
                    'status': payment.status,
                    'message': 'درخواست برداشت با موفقیت ثبت شد و در حال بررسی است'
                },
                status_code=status.HTTP_201_CREATED
            )
            
    except Exception as e:
        logger.error(f"Error creating doctor withdrawal: {str(e)}")
        api_core = APIIngressCore()
        return api_core.handle_error(e, "doctor_create_withdrawal")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_get_earnings(request):
    """
    دریافت گزارش درآمد دکتر
    """
    try:
        api_core = APIIngressCore()
        
        # بررسی نوع کاربر
        user_type = getattr(request.user, 'user_type', 'doctor')
        if user_type != 'doctor':
            return api_core.format_response(
                success=False,
                error='unauthorized',
                message='این عملیات فقط برای پزشکان مجاز است',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # دریافت پارامترهای زمانی
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # محاسبه درآمدها
        earnings_query = Payment.objects.filter(
            doctor_id=str(request.user.id),
            status='success',
            payment_type__in=['appointment', 'consultation']
        )
        
        if start_date:
            earnings_query = earnings_query.filter(paid_at__gte=start_date)
        if end_date:
            earnings_query = earnings_query.filter(paid_at__lte=end_date)
        
        # آمار کلی
        total_earnings = earnings_query.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
        
        # درآمد به تفکیک نوع
        earnings_by_type = earnings_query.values('payment_type').annotate(
            total=models.Sum('amount'),
            count=models.Count('payment_id')
        )
        
        # برداشت‌ها
        withdrawals = Payment.objects.filter(
            user=request.user,
            payment_type='withdrawal',
            status='success'
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
        
        # موجودی کیف پول
        try:
            wallet = Wallet.objects.get(user=request.user)
            wallet_balance = wallet.balance
            available_balance = wallet.available_balance
        except Wallet.DoesNotExist:
            wallet_balance = Decimal('0')
            available_balance = Decimal('0')
        
        return api_core.format_response(
            success=True,
            data={
                'total_earnings': str(total_earnings),
                'earnings_by_type': [
                    {
                        'type': item['payment_type'],
                        'total': str(item['total']),
                        'count': item['count']
                    }
                    for item in earnings_by_type
                ],
                'total_withdrawals': str(withdrawals),
                'wallet_balance': str(wallet_balance),
                'available_balance': str(available_balance),
                'period': {
                    'start': start_date,
                    'end': end_date
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting doctor earnings: {str(e)}")
        api_core = APIIngressCore()
        return api_core.handle_error(e, "doctor_get_earnings")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_get_commissions(request):
    """
    دریافت گزارش کمیسیون‌های دکتر
    """
    try:
        api_core = APIIngressCore()
        
        # بررسی نوع کاربر
        user_type = getattr(request.user, 'user_type', 'doctor')
        if user_type != 'doctor':
            return api_core.format_response(
                success=False,
                error='unauthorized',
                message='این عملیات فقط برای پزشکان مجاز است',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # دریافت کمیسیون‌ها
        commissions = Payment.objects.filter(
            user=request.user,
            payment_type='commission'
        ).order_by('-created_at')[:50]
        
        # محاسبه مجموع
        total_commissions = commissions.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
        
        serializer = PaymentSerializer(commissions, many=True)
        
        return api_core.format_response(
            success=True,
            data={
                'commissions': serializer.data,
                'total_commissions': str(total_commissions),
                'count': len(serializer.data)
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting doctor commissions: {str(e)}")
        api_core = APIIngressCore()
        return api_core.handle_error(e, "doctor_get_commissions")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def doctor_update_bank_info(request):
    """
    بروزرسانی اطلاعات بانکی دکتر
    """
    try:
        api_core = APIIngressCore()
        
        # بررسی نوع کاربر
        user_type = getattr(request.user, 'user_type', 'doctor')
        if user_type != 'doctor':
            return api_core.format_response(
                success=False,
                error='unauthorized',
                message='این عملیات فقط برای پزشکان مجاز است',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # دریافت اطلاعات بانکی
        bank_name = request.data.get('bank_name')
        account_number = request.data.get('account_number')
        iban = request.data.get('iban')
        card_number = request.data.get('card_number')
        
        if not all([bank_name, account_number, iban]):
            return api_core.format_response(
                success=False,
                error='missing_data',
                message='نام بانک، شماره حساب و شبا الزامی است',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # ذخیره یا بروزرسانی روش پرداخت
        payment_method, created = PaymentMethod.objects.update_or_create(
            user=request.user,
            method_type='card',
            title='حساب بانکی اصلی',
            defaults={
                'details': {
                    'bank_name': bank_name,
                    'account_number': account_number,
                    'iban': iban,
                    'card_number': card_number
                },
                'is_default': True,
                'is_active': True
            }
        )
        
        # غیرفعال کردن سایر حساب‌های پیش‌فرض
        if payment_method.is_default:
            PaymentMethod.objects.filter(
                user=request.user,
                is_default=True
            ).exclude(id=payment_method.id).update(is_default=False)
        
        return api_core.format_response(
            success=True,
            data={
                'message': 'اطلاعات بانکی با موفقیت بروزرسانی شد',
                'payment_method_id': payment_method.id
            }
        )
        
    except Exception as e:
        logger.error(f"Error updating doctor bank info: {str(e)}")
        api_core = APIIngressCore()
        return api_core.handle_error(e, "doctor_update_bank_info")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_get_wallet_transactions(request):
    """
    دریافت تراکنش‌های کیف پول دکتر
    """
    try:
        api_core = APIIngressCore()
        
        # بررسی نوع کاربر
        user_type = getattr(request.user, 'user_type', 'doctor')
        if user_type != 'doctor':
            return api_core.format_response(
                success=False,
                error='unauthorized',
                message='این عملیات فقط برای پزشکان مجاز است',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # دریافت کیف پول
        try:
            wallet = Wallet.objects.get(user=request.user)
        except Wallet.DoesNotExist:
            return api_core.format_response(
                success=False,
                error='no_wallet',
                message='کیف پولی برای شما یافت نشد',
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # فیلترها
        transaction_type = request.GET.get('type')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # دریافت تراکنش‌ها
        transactions = WalletTransaction.objects.filter(wallet=wallet)
        
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)
        if start_date:
            transactions = transactions.filter(created_at__gte=start_date)
        if end_date:
            transactions = transactions.filter(created_at__lte=end_date)
            
        transactions = transactions.order_by('-created_at')[:100]
        
        serializer = WalletTransactionSerializer(transactions, many=True)
        
        return api_core.format_response(
            success=True,
            data={
                'wallet_info': {
                    'balance': str(wallet.balance),
                    'blocked_balance': str(wallet.blocked_balance),
                    'available_balance': str(wallet.available_balance)
                },
                'transactions': serializer.data,
                'count': len(serializer.data)
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting doctor wallet transactions: {str(e)}")
        api_core = APIIngressCore()
        return api_core.handle_error(e, "doctor_get_wallet_transactions")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_financial_report(request):
    """
    گزارش مالی جامع دکتر
    """
    try:
        api_core = APIIngressCore()
        
        # بررسی نوع کاربر
        user_type = getattr(request.user, 'user_type', 'doctor')
        if user_type != 'doctor':
            return api_core.format_response(
                success=False,
                error='unauthorized',
                message='این عملیات فقط برای پزشکان مجاز است',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # دریافت بازه زمانی
        period = request.GET.get('period', 'month')  # day, week, month, year
        custom_start = request.GET.get('start_date')
        custom_end = request.GET.get('end_date')
        
        # محاسبه بازه زمانی
        end_date = timezone.now()
        if period == 'day':
            start_date = end_date - timezone.timedelta(days=1)
        elif period == 'week':
            start_date = end_date - timezone.timedelta(weeks=1)
        elif period == 'month':
            start_date = end_date - timezone.timedelta(days=30)
        elif period == 'year':
            start_date = end_date - timezone.timedelta(days=365)
        else:
            start_date = custom_start or end_date - timezone.timedelta(days=30)
            end_date = custom_end or end_date
        
        # درآمدها
        earnings = Payment.objects.filter(
            doctor_id=str(request.user.id),
            status='success',
            paid_at__gte=start_date,
            paid_at__lte=end_date
        ).aggregate(
            total=models.Sum('amount'),
            count=models.Count('payment_id')
        )
        
        # کمیسیون‌ها
        commissions = Payment.objects.filter(
            user=request.user,
            payment_type='commission',
            created_at__gte=start_date,
            created_at__lte=end_date
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
        
        # برداشت‌ها
        withdrawals = Payment.objects.filter(
            user=request.user,
            payment_type='withdrawal',
            status='success',
            paid_at__gte=start_date,
            paid_at__lte=end_date
        ).aggregate(
            total=models.Sum('amount'),
            count=models.Count('payment_id')
        )
        
        # خالص درآمد
        net_income = (earnings['total'] or Decimal('0')) - commissions
        
        # وضعیت کیف پول
        try:
            wallet = Wallet.objects.get(user=request.user)
            wallet_data = {
                'balance': str(wallet.balance),
                'available': str(wallet.available_balance),
                'blocked': str(wallet.blocked_balance)
            }
        except Wallet.DoesNotExist:
            wallet_data = {
                'balance': '0',
                'available': '0',
                'blocked': '0'
            }
        
        return api_core.format_response(
            success=True,
            data={
                'period': {
                    'type': period,
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'start_jalali': jdatetime.datetime.fromgregorian(
                        datetime=start_date
                    ).strftime('%Y/%m/%d'),
                    'end_jalali': jdatetime.datetime.fromgregorian(
                        datetime=end_date
                    ).strftime('%Y/%m/%d')
                },
                'earnings': {
                    'total': str(earnings['total'] or 0),
                    'count': earnings['count']
                },
                'commissions': str(commissions),
                'withdrawals': {
                    'total': str(withdrawals['total'] or 0),
                    'count': withdrawals['count']
                },
                'net_income': str(net_income),
                'wallet': wallet_data
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating doctor financial report: {str(e)}")
        api_core = APIIngressCore()
        return api_core.handle_error(e, "doctor_financial_report")