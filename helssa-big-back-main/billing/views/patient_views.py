"""
API های مخصوص بیماران
Patient-specific APIs
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
    Subscription, SubscriptionStatus, SubscriptionPlan, Invoice
)
from ..serializers import (
    WalletSerializer, TransactionSerializer, SubscriptionSerializer,
    SubscriptionPlanSerializer, InvoiceSerializer
)
from ..services import (
    WalletService, PaymentService, SubscriptionService
)
from ..permissions import (
    IsPatient, CanAccessFinancialData, CanManageSubscription,
    CanMakePayment, HasWalletAccess
)


class PatientWalletView(APIView):
    """
    مدیریت کیف پول بیمار
    Patient Wallet Management
    """
    permission_classes = [IsPatient, CanAccessFinancialData, HasWalletAccess]
    
    def get(self, request: Request) -> Response:
        """دریافت اطلاعات کیف پول بیمار"""
        try:
            wallet = request.user.wallet
            serializer = WalletSerializer(wallet)
            
            # محاسبه آمار اضافی
            total_spent = Transaction.objects.filter(
                wallet=wallet,
                transaction_type=TransactionType.PAYMENT,
                status=TransactionStatus.COMPLETED
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            total_charged = Transaction.objects.filter(
                wallet=wallet,
                transaction_type=TransactionType.DEPOSIT,
                status=TransactionStatus.COMPLETED
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # اشتراک فعال
            active_subscription = Subscription.objects.filter(
                user=request.user,
                status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]
            ).first()
            
            data = serializer.data
            data.update({
                'total_spent': total_spent,
                'total_charged': total_charged,
                'current_balance': wallet.balance,
                'has_active_subscription': bool(active_subscription),
                'active_subscription': SubscriptionSerializer(active_subscription).data if active_subscription else None
            })
            
            return Response(data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'خطا در دریافت اطلاعات کیف پول: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PatientPaymentView(APIView):
    """
    پرداخت بیمار
    Patient Payment
    """
    permission_classes = [IsPatient, CanMakePayment]
    
    def post(self, request: Request) -> Response:
        """شارژ کیف پول"""
        try:
            amount = Decimal(str(request.data.get('amount', 0)))
            gateway = request.data.get('gateway', 'zarinpal')
            description = request.data.get('description', 'شارژ کیف پول')
            
            if amount <= 0:
                return Response(
                    {'error': 'مبلغ باید بیشتر از صفر باشد'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # حداقل مبلغ شارژ
            min_charge = Decimal('10000')  # 10 هزار تومان
            if amount < min_charge:
                return Response(
                    {'error': f'حداقل مبلغ شارژ {min_charge} تومان است'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # حداکثر مبلغ شارژ
            max_charge = Decimal('10000000')  # 10 میلیون تومان
            if amount > max_charge:
                return Response(
                    {'error': f'حداکثر مبلغ شارژ {max_charge} تومان است'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # ایجاد تراکنش پرداخت
            payment_service = PaymentService()
            payment_result = payment_service.create_payment(
                user=request.user,
                amount=amount,
                gateway=gateway,
                description=description
            )
            
            if payment_result['success']:
                return Response({
                    'message': 'درخواست پرداخت با موفقیت ایجاد شد',
                    'payment_url': payment_result['payment_url'],
                    'transaction_id': payment_result['transaction_id']
                }, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': payment_result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except ValueError:
            return Response(
                {'error': 'مبلغ نامعتبر است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'خطا در ایجاد پرداخت: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PatientSubscriptionView(APIView):
    """
    مدیریت اشتراک بیمار
    Patient Subscription Management
    """
    permission_classes = [IsPatient, CanManageSubscription]
    
    def get(self, request: Request) -> Response:
        """دریافت اطلاعات اشتراک فعلی"""
        try:
            subscription = Subscription.objects.filter(
                user=request.user
            ).order_by('-created_at').first()
            
            if subscription:
                serializer = SubscriptionSerializer(subscription)
                data = serializer.data
                
                # محاسبه روزهای باقی‌مانده
                if subscription.end_date:
                    remaining_days = (subscription.end_date - timezone.now().date()).days
                    data['remaining_days'] = max(0, remaining_days)
                
                return Response(data, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'message': 'اشتراک فعالی یافت نشد'},
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except Exception as e:
            return Response(
                {'error': f'خطا در دریافت اطلاعات اشتراک: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request: Request) -> Response:
        """خرید اشتراک جدید"""
        try:
            plan_id = request.data.get('plan_id')
            
            if not plan_id:
                return Response(
                    {'error': 'شناسه پلن الزامی است'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
            except SubscriptionPlan.DoesNotExist:
                return Response(
                    {'error': 'پلن مورد نظر یافت نشد یا غیرفعال است'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # بررسی اشتراک فعال
            active_subscription = Subscription.objects.filter(
                user=request.user,
                status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]
            ).exists()
            
            if active_subscription:
                return Response(
                    {'error': 'شما اشتراک فعالی دارید'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # خرید اشتراک
            subscription_service = SubscriptionService()
            result = subscription_service.purchase_subscription(
                user=request.user,
                plan=plan
            )
            
            if result['success']:
                return Response({
                    'message': 'اشتراک با موفقیت خریداری شد',
                    'subscription': SubscriptionSerializer(result['subscription']).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {'error': f'خطا در خرید اشتراک: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request: Request) -> Response:
        """تمدید اشتراک"""
        try:
            subscription = Subscription.objects.filter(
                user=request.user
            ).order_by('-created_at').first()
            
            if not subscription:
                return Response(
                    {'error': 'اشتراکی یافت نشد'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            subscription_service = SubscriptionService()
            result = subscription_service.renew_subscription(subscription)
            
            if result['success']:
                return Response({
                    'message': 'اشتراک با موفقیت تمدید شد',
                    'subscription': SubscriptionSerializer(result['subscription']).data
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {'error': f'خطا در تمدید اشتراک: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request: Request) -> Response:
        """لغو اشتراک"""
        try:
            subscription = Subscription.objects.filter(
                user=request.user,
                status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]
            ).first()
            
            if not subscription:
                return Response(
                    {'error': 'اشتراک فعالی یافت نشد'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            subscription_service = SubscriptionService()
            result = subscription_service.cancel_subscription(subscription)
            
            if result['success']:
                return Response({
                    'message': 'اشتراک با موفقیت لغو شد'
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {'error': f'خطا در لغو اشتراک: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PatientPlansView(APIView):
    """
    مشاهده پلن‌های اشتراک
    View Subscription Plans
    """
    permission_classes = [IsPatient]
    
    def get(self, request: Request) -> Response:
        """دریافت لیست پلن‌های فعال"""
        try:
            plans = SubscriptionPlan.objects.filter(
                is_active=True
            ).order_by('price')
            
            serializer = SubscriptionPlanSerializer(plans, many=True)
            
            # اضافه کردن اطلاعات مقایسه
            for plan_data in serializer.data:
                plan_data['features'] = []
                
                if plan_data['duration_days'] >= 30:
                    plan_data['features'].append('دسترسی به چت‌بات')
                if plan_data['duration_days'] >= 90:
                    plan_data['features'].append('مشاوره تخصصی')
                if plan_data['duration_days'] >= 365:
                    plan_data['features'].append('پشتیبانی 24/7')
                
                # محاسبه قیمت روزانه
                if plan_data['duration_days'] > 0:
                    plan_data['daily_price'] = float(plan_data['price']) / plan_data['duration_days']
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'خطا در دریافت پلن‌ها: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PatientTransactionHistoryView(APIView):
    """
    تاریخچه تراکنش‌های بیمار
    Patient Transaction History
    """
    permission_classes = [IsPatient, CanAccessFinancialData]
    
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
            total_deposits = transactions.filter(
                transaction_type=TransactionType.DEPOSIT,
                status=TransactionStatus.COMPLETED
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            total_payments = transactions.filter(
                transaction_type=TransactionType.PAYMENT,
                status=TransactionStatus.COMPLETED
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            return Response({
                'results': serializer.data,
                'count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size,
                'stats': {
                    'total_deposits': total_deposits,
                    'total_payments': total_payments,
                    'current_balance': request.user.wallet.balance
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'خطا در دریافت تاریخچه تراکنش‌ها: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@permission_classes([IsPatient])
def patient_spending_stats(request: Request) -> Response:
    """
    آمار خرج بیمار
    Patient Spending Statistics
    """
    try:
        # آمار کلی
        total_spent = Transaction.objects.filter(
            wallet__user=request.user,
            transaction_type=TransactionType.PAYMENT,
            status=TransactionStatus.COMPLETED
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        total_charged = Transaction.objects.filter(
            wallet__user=request.user,
            transaction_type=TransactionType.DEPOSIT,
            status=TransactionStatus.COMPLETED
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # آمار ماهانه (6 ماه گذشته)
        monthly_stats = []
        current_date = timezone.now()
        
        for i in range(6):
            month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if i > 0:
                month_start = month_start.replace(month=month_start.month - i)
            
            month_end = month_start.replace(month=month_start.month + 1) if month_start.month < 12 else month_start.replace(year=month_start.year + 1, month=1)
            
            month_spent = Transaction.objects.filter(
                wallet__user=request.user,
                transaction_type=TransactionType.PAYMENT,
                status=TransactionStatus.COMPLETED,
                created_at__gte=month_start,
                created_at__lt=month_end
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            month_charged = Transaction.objects.filter(
                wallet__user=request.user,
                transaction_type=TransactionType.DEPOSIT,
                status=TransactionStatus.COMPLETED,
                created_at__gte=month_start,
                created_at__lt=month_end
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            monthly_stats.append({
                'month': month_start.strftime('%Y-%m'),
                'spent': month_spent,
                'charged': month_charged
            })
        
        # اشتراک‌ها
        subscriptions_count = Subscription.objects.filter(user=request.user).count()
        active_subscription = Subscription.objects.filter(
            user=request.user,
            status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]
        ).exists()
        
        return Response({
            'total_spent': total_spent,
            'total_charged': total_charged,
            'current_balance': request.user.wallet.balance,
            'subscriptions_count': subscriptions_count,
            'has_active_subscription': active_subscription,
            'monthly_stats': monthly_stats[::-1]  # از قدیم به جدید
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'خطا در دریافت آمار خرج: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )