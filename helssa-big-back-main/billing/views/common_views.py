"""
API های مشترک
Common APIs for both doctors and patients
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from decimal import Decimal

from ..models import Transaction, TransactionStatus
from ..services import PaymentService
from ..permissions import IsDoctorOrPatient, IsAuthenticatedAndActive


class PaymentMethodsView(APIView):
    """
    روش‌های پرداخت موجود
    Available Payment Methods
    """
    permission_classes = [IsDoctorOrPatient]
    
    def get(self, request: Request) -> Response:
        """دریافت لیست روش‌های پرداخت فعال"""
        try:
            payment_methods = [
                {
                    'id': 'zarinpal',
                    'name': 'زرین‌پال',
                    'logo': '/static/images/zarinpal.png',
                    'description': 'پرداخت آنلاین با کارت‌های بانکی',
                    'min_amount': 1000,
                    'max_amount': 50000000,
                    'fee_percentage': 1.5,
                    'is_active': True
                },
                {
                    'id': 'bitpay',
                    'name': 'بیت‌پی',
                    'logo': '/static/images/bitpay.png',
                    'description': 'درگاه پرداخت بیت‌پی',
                    'min_amount': 1000,
                    'max_amount': 20000000,
                    'fee_percentage': 2.0,
                    'is_active': True
                },
                {
                    'id': 'idpay',
                    'name': 'آیدی‌پی',
                    'logo': '/static/images/idpay.png',
                    'description': 'پرداخت سریع و امن',
                    'min_amount': 1000,
                    'max_amount': 10000000,
                    'fee_percentage': 1.8,
                    'is_active': True
                }
            ]
            
            # فیلتر روش‌های فعال
            active_methods = [method for method in payment_methods if method['is_active']]
            
            return Response({
                'payment_methods': active_methods,
                'total_count': len(active_methods)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'خطا در دریافت روش‌های پرداخت: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentStatusView(APIView):
    """
    بررسی وضعیت پرداخت
    Payment Status Check
    """
    permission_classes = [IsDoctorOrPatient]
    
    def get(self, request: Request, transaction_id: str) -> Response:
        """بررسی وضعیت یک تراکنش"""
        try:
            try:
                transaction = Transaction.objects.get(
                    id=transaction_id,
                    wallet__user=request.user
                )
            except Transaction.DoesNotExist:
                return Response(
                    {'error': 'تراکنش یافت نشد'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # بروزرسانی وضعیت از درگاه
            if transaction.status == TransactionStatus.PENDING:
                payment_service = PaymentService()
                updated_status = payment_service.verify_payment(transaction)
                
                if updated_status:
                    transaction.refresh_from_db()
            
            return Response({
                'transaction_id': transaction.id,
                'status': transaction.status,
                'amount': transaction.amount,
                'gateway': transaction.gateway,
                'created_at': transaction.created_at,
                'updated_at': transaction.updated_at,
                'description': transaction.description,
                'gateway_transaction_id': transaction.gateway_transaction_id
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'خطا در بررسی وضعیت پرداخت: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RefundPaymentView(APIView):
    """
    بازگشت وجه
    Payment Refund
    """
    permission_classes = [IsDoctorOrPatient]
    
    def post(self, request: Request) -> Response:
        """درخواست بازگشت وجه"""
        try:
            transaction_id = request.data.get('transaction_id')
            reason = request.data.get('reason', '')
            
            if not transaction_id:
                return Response(
                    {'error': 'شناسه تراکنش الزامی است'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                transaction = Transaction.objects.get(
                    id=transaction_id,
                    wallet__user=request.user
                )
            except Transaction.DoesNotExist:
                return Response(
                    {'error': 'تراکنش یافت نشد'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # بررسی قابلیت بازگشت
            if transaction.status != TransactionStatus.COMPLETED:
                return Response(
                    {'error': 'فقط تراکنش‌های تکمیل شده قابل بازگشت هستند'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # بررسی زمان (حداکثر 24 ساعت)
            time_limit = timezone.now() - timezone.timedelta(hours=24)
            if transaction.created_at < time_limit:
                return Response(
                    {'error': 'مهلت درخواست بازگشت وجه (24 ساعت) به پایان رسیده است'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # ایجاد درخواست بازگشت
            payment_service = PaymentService()
            result = payment_service.create_refund(
                transaction=transaction,
                reason=reason
            )
            
            if result['success']:
                return Response({
                    'message': 'درخواست بازگشت وجه با موفقیت ثبت شد',
                    'refund_id': result['refund_id']
                }, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {'error': f'خطا در درخواست بازگشت وجه: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@permission_classes([IsDoctorOrPatient])
def payment_limits(request: Request) -> Response:
    """
    محدودیت‌های پرداخت
    Payment Limits
    """
    try:
        user_type = request.user.user_type
        
        # محدودیت‌های پایه
        base_limits = {
            'min_payment': 1000,  # 1 هزار تومان
            'max_payment': 50000000,  # 50 میلیون تومان
            'daily_limit': 10000000,  # 10 میلیون تومان در روز
            'monthly_limit': 100000000  # 100 میلیون تومان در ماه
        }
        
        # محدودیت‌های ویژه بر اساس نوع کاربر
        if user_type == 'patient':
            limits = {
                **base_limits,
                'max_wallet_balance': 5000000,  # 5 میلیون تومان
                'subscription_discount': 10  # 10 درصد تخفیف اشتراک
            }
        elif user_type == 'doctor':
            limits = {
                **base_limits,
                'min_withdrawal': 50000,  # 50 هزار تومان
                'max_withdrawal': 20000000,  # 20 میلیون تومان
                'commission_rate': 15  # 15 درصد کمیسیون
            }
        else:
            limits = base_limits
        
        # بررسی تایید هویت
        if request.user.is_verified:
            limits['max_payment'] *= 2
            limits['daily_limit'] *= 2
            limits['monthly_limit'] *= 2
        
        return Response({
            'limits': limits,
            'user_type': user_type,
            'is_verified': request.user.is_verified
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'خطا در دریافت محدودیت‌ها: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsDoctorOrPatient])
def payment_fees(request: Request) -> Response:
    """
    کارمزدهای پرداخت
    Payment Fees
    """
    try:
        amount = request.query_params.get('amount', 0)
        gateway = request.query_params.get('gateway', 'zarinpal')
        
        try:
            amount = Decimal(str(amount))
        except (ValueError, TypeError):
            amount = Decimal('0')
        
        # محاسبه کارمزد بر اساس درگاه
        fee_rates = {
            'zarinpal': 1.5,
            'bitpay': 2.0,
            'idpay': 1.8,
            'stripe': 2.9,
            'paypal': 3.4
        }
        
        fee_percentage = fee_rates.get(gateway, 2.0)
        
        if amount > 0:
            fee_amount = amount * Decimal(str(fee_percentage / 100))
            total_amount = amount + fee_amount
        else:
            fee_amount = Decimal('0')
            total_amount = Decimal('0')
        
        return Response({
            'amount': amount,
            'fee_percentage': fee_percentage,
            'fee_amount': fee_amount,
            'total_amount': total_amount,
            'gateway': gateway
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'خطا در محاسبه کارمزد: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticatedAndActive])
def health_check(request: Request) -> Response:
    """
    بررسی سلامت سیستم مالی
    Financial System Health Check
    """
    try:
        from django.db import connection
        
        # بررسی اتصال به دیتابیس
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = cursor.fetchone() is not None
        
        # بررسی وضعیت کش
        from django.core.cache import cache
        cache_key = 'health_check_test'
        cache.set(cache_key, 'test_value', 30)
        cache_status = cache.get(cache_key) == 'test_value'
        
        # بررسی وضعیت درگاه‌ها (فعلاً همه فعال فرض می‌شوند)
        gateways_status = {
            'zarinpal': True,
            'bitpay': True,
            'idpay': True
        }
        
        overall_status = db_status and cache_status and all(gateways_status.values())
        
        return Response({
            'status': 'healthy' if overall_status else 'unhealthy',
            'timestamp': timezone.now(),
            'components': {
                'database': 'up' if db_status else 'down',
                'cache': 'up' if cache_status else 'down',
                'payment_gateways': gateways_status
            }
        }, status=status.HTTP_200_OK if overall_status else status.HTTP_503_SERVICE_UNAVAILABLE)
        
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'timestamp': timezone.now(),
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)