"""
API های مخصوص پزشکان
Doctor-specific APIs
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Sum, Q
from decimal import Decimal
from typing import Dict, Any

from ..models import (
    Wallet, Transaction, TransactionType, TransactionStatus,
    Commission, Subscription, SubscriptionStatus
)
from ..serializers import (
    WalletSerializer, TransactionSerializer, CommissionSerializer
)
from ..services import (
    WalletService, PaymentService, CommissionService
)
from ..permissions import (
    IsDoctor, CanAccessFinancialData, CanViewCommission,
    IsAuthenticatedAndActive
)


class DoctorWalletView(APIView):
    """
    مدیریت کیف پول پزشک
    Doctor Wallet Management
    """
    permission_classes = [IsDoctor, CanAccessFinancialData]
    
    def get(self, request: Request) -> Response:
        """دریافت اطلاعات کیف پول پزشک"""
        try:
            wallet = request.user.wallet
            serializer = WalletSerializer(wallet)
            
            # محاسبه آمار اضافی
            total_earnings = Commission.objects.filter(
                doctor=request.user,
                status='paid'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            pending_earnings = Commission.objects.filter(
                doctor=request.user,
                status='pending'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            data = serializer.data
            data.update({
                'total_earnings': total_earnings,
                'pending_earnings': pending_earnings,
                'available_for_withdrawal': wallet.balance
            })
            
            return Response(data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'خطا در دریافت اطلاعات کیف پول: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DoctorCommissionView(APIView):
    """
    مدیریت کمیسیون پزشک
    Doctor Commission Management
    """
    permission_classes = [IsDoctor, CanViewCommission]
    
    def get(self, request: Request) -> Response:
        """دریافت لیست کمیسیون‌های پزشک"""
        try:
            commissions = Commission.objects.filter(
                doctor=request.user
            ).order_by('-created_at')
            
            # فیلتر بر اساس وضعیت
            commission_status = request.query_params.get('status')
            if commission_status:
                commissions = commissions.filter(status=commission_status)
            
            # فیلتر بر اساس تاریخ
            from_date = request.query_params.get('from_date')
            to_date = request.query_params.get('to_date')
            
            if from_date:
                commissions = commissions.filter(created_at__gte=from_date)
            if to_date:
                commissions = commissions.filter(created_at__lte=to_date)
            
            # Pagination
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            start = (page - 1) * page_size
            end = start + page_size
            
            total_count = commissions.count()
            commissions_page = commissions[start:end]
            
            serializer = CommissionSerializer(commissions_page, many=True)
            
            return Response({
                'results': serializer.data,
                'count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'خطا در دریافت کمیسیون‌ها: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DoctorFinancialSummaryView(APIView):
    """
    خلاصه مالی پزشک
    Doctor Financial Summary
    """
    permission_classes = [IsDoctor, CanAccessFinancialData]
    
    def get(self, request: Request) -> Response:
        """دریافت خلاصه مالی پزشک"""
        try:
            # محاسبه آمار ماهانه
            current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # کمیسیون این ماه
            monthly_commission = Commission.objects.filter(
                doctor=request.user,
                created_at__gte=current_month,
                status='paid'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # تعداد بیماران این ماه
            monthly_patients = Subscription.objects.filter(
                created_at__gte=current_month,
                status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]
            ).values('user').distinct().count()
            
            # کل درآمد
            total_earnings = Commission.objects.filter(
                doctor=request.user,
                status='paid'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # کمیسیون در انتظار
            pending_commission = Commission.objects.filter(
                doctor=request.user,
                status='pending'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # برداشت‌های این ماه
            monthly_withdrawals = Transaction.objects.filter(
                wallet__user=request.user,
                transaction_type=TransactionType.WITHDRAWAL,
                status=TransactionStatus.COMPLETED,
                created_at__gte=current_month
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            return Response({
                'monthly_stats': {
                    'commission': monthly_commission,
                    'patients_count': monthly_patients,
                    'withdrawals': monthly_withdrawals
                },
                'total_stats': {
                    'total_earnings': total_earnings,
                    'pending_commission': pending_commission,
                    'current_balance': request.user.wallet.balance
                },
                'wallet_info': {
                    'balance': request.user.wallet.balance,
                    'is_active': request.user.wallet.is_active,
                    'last_update': request.user.wallet.updated_at
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'خطا در دریافت خلاصه مالی: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DoctorWithdrawView(APIView):
    """
    برداشت وجه پزشک
    Doctor Withdrawal
    """
    permission_classes = [IsDoctor, CanAccessFinancialData]
    
    def post(self, request: Request) -> Response:
        """درخواست برداشت وجه"""
        try:
            amount = Decimal(str(request.data.get('amount', 0)))
            description = request.data.get('description', '')
            
            if amount <= 0:
                return Response(
                    {'error': 'مبلغ باید بیشتر از صفر باشد'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            wallet = request.user.wallet
            
            # بررسی موجودی
            if wallet.balance < amount:
                return Response(
                    {'error': 'موجودی کافی نیست'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # حداقل مبلغ برداشت
            min_withdrawal = Decimal('50000')  # 50 هزار تومان
            if amount < min_withdrawal:
                return Response(
                    {'error': f'حداقل مبلغ برداشت {min_withdrawal} تومان است'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # ایجاد تراکنش برداشت
            wallet_service = WalletService()
            transaction = wallet_service.create_withdrawal(
                wallet=wallet,
                amount=amount,
                description=description or 'برداشت توسط پزشک'
            )
            
            serializer = TransactionSerializer(transaction)
            
            return Response({
                'message': 'درخواست برداشت با موفقیت ثبت شد',
                'transaction': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except ValueError:
            return Response(
                {'error': 'مبلغ نامعتبر است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'خطا در ثبت درخواست برداشت: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DoctorTransactionHistoryView(APIView):
    """
    تاریخچه تراکنش‌های پزشک
    Doctor Transaction History
    """
    permission_classes = [IsDoctor, CanAccessFinancialData]
    
    def get(self, request: Request) -> Response:
        """دریافت تاریخچه تراکنش‌ها"""
        try:
            transactions = Transaction.objects.filter(
                wallet__user=request.user
            ).order_by('-created_at')
            
            # فیلتر بر اساس نوع تراکنش
            transaction_type = request.query_params.get('type')
            if transaction_type:
                transactions = transactions.filter(transaction_type=transaction_type)
            
            # فیلتر بر اساس وضعیت
            transaction_status = request.query_params.get('status')
            if transaction_status:
                transactions = transactions.filter(status=transaction_status)
            
            # فیلتر بر اساس تاریخ
            from_date = request.query_params.get('from_date')
            to_date = request.query_params.get('to_date')
            
            if from_date:
                transactions = transactions.filter(created_at__gte=from_date)
            if to_date:
                transactions = transactions.filter(created_at__lte=to_date)
            
            # Pagination
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            start = (page - 1) * page_size
            end = start + page_size
            
            total_count = transactions.count()
            transactions_page = transactions[start:end]
            
            serializer = TransactionSerializer(transactions_page, many=True)
            
            # محاسبه آمار
            total_deposit = transactions.filter(
                transaction_type=TransactionType.DEPOSIT,
                status=TransactionStatus.COMPLETED
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            total_withdrawal = transactions.filter(
                transaction_type=TransactionType.WITHDRAWAL,
                status=TransactionStatus.COMPLETED
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            return Response({
                'results': serializer.data,
                'count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size,
                'stats': {
                    'total_deposit': total_deposit,
                    'total_withdrawal': total_withdrawal,
                    'net_amount': total_deposit - total_withdrawal
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'خطا در دریافت تاریخچه تراکنش‌ها: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@permission_classes([IsDoctor])
def doctor_commission_stats(request: Request) -> Response:
    """
    آمار کمیسیون پزشک
    Doctor Commission Statistics
    """
    try:
        # آمار کلی
        total_commission = Commission.objects.filter(
            doctor=request.user,
            status='paid'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        pending_commission = Commission.objects.filter(
            doctor=request.user,
            status='pending'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # آمار ماهانه (12 ماه گذشته)
        monthly_stats = []
        current_date = timezone.now()
        
        for i in range(12):
            month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if i > 0:
                month_start = month_start.replace(month=month_start.month - i)
            
            month_end = month_start.replace(month=month_start.month + 1) if month_start.month < 12 else month_start.replace(year=month_start.year + 1, month=1)
            
            month_commission = Commission.objects.filter(
                doctor=request.user,
                created_at__gte=month_start,
                created_at__lt=month_end,
                status='paid'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            monthly_stats.append({
                'month': month_start.strftime('%Y-%m'),
                'commission': month_commission
            })
        
        return Response({
            'total_commission': total_commission,
            'pending_commission': pending_commission,
            'monthly_stats': monthly_stats[::-1]  # از قدیم به جدید
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'خطا در دریافت آمار کمیسیون: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )