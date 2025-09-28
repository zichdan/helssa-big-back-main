"""
ویوهای اپلیکیشن پرداخت
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache
from decimal import Decimal

from .models import Payment, PaymentMethod, Wallet, WalletTransaction
from .serializers import (
    PaymentSerializer, CreatePaymentSerializer,
    PaymentMethodSerializer, WalletSerializer,
    RefundRequestSerializer, PaymentReportSerializer
)
from .cores.orchestrator import CentralOrchestrator
from .cores.api_ingress import APIIngressCore

logger = logging.getLogger(__name__)


# ==================== ویوهای مشترک ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_methods(request):
    """
    دریافت روش‌های پرداخت کاربر
    """
    try:
        api_core = APIIngressCore()
        
        # دریافت روش‌های پرداخت فعال کاربر
        methods = PaymentMethod.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-is_default', '-created_at')
        
        serializer = PaymentMethodSerializer(methods, many=True)
        
        return api_core.format_response(
            success=True,
            data={'payment_methods': serializer.data}
        )
        
    except Exception as e:
        logger.error(f"Error getting payment methods: {str(e)}")
        api_core = APIIngressCore()
        return api_core.handle_error(e, "get_payment_methods")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_payment_method(request):
    """
    افزودن روش پرداخت جدید
    """
    try:
        api_core = APIIngressCore()
        
        # پردازش درخواست
        is_valid, processed_data = api_core.process_request(request)
        if not is_valid:
            return api_core.format_response(
                success=False,
                error=processed_data.get('error'),
                message=processed_data.get('message'),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # ایجاد روش پرداخت
        serializer = PaymentMethodSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            
            return api_core.format_response(
                success=True,
                data={'payment_method': serializer.data},
                status_code=status.HTTP_201_CREATED
            )
        else:
            return api_core.format_response(
                success=False,
                error='validation_error',
                message='داده‌های ارسالی نامعتبر است',
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Error adding payment method: {str(e)}")
        api_core = APIIngressCore()
        return api_core.handle_error(e, "add_payment_method")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_history(request):
    """
    دریافت تاریخچه پرداخت‌های کاربر
    """
    try:
        api_core = APIIngressCore()
        
        # فیلترهای جستجو
        payment_type = request.GET.get('payment_type')
        status_filter = request.GET.get('status')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # ایجاد query
        payments = Payment.objects.filter(user=request.user)
        
        if payment_type:
            payments = payments.filter(payment_type=payment_type)
        
        if status_filter:
            payments = payments.filter(status=status_filter)
            
        if start_date:
            payments = payments.filter(created_at__gte=start_date)
            
        if end_date:
            payments = payments.filter(created_at__lte=end_date)
        
        # مرتب‌سازی و محدودسازی
        payments = payments.order_by('-created_at')[:100]
        
        serializer = PaymentSerializer(payments, many=True)
        
        return api_core.format_response(
            success=True,
            data={
                'payments': serializer.data,
                'count': len(serializer.data)
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting payment history: {str(e)}")
        api_core = APIIngressCore()
        return api_core.handle_error(e, "get_payment_history")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_detail(request, payment_id):
    """
    دریافت جزئیات یک پرداخت
    """
    try:
        api_core = APIIngressCore()
        
        # دریافت پرداخت
        payment = Payment.objects.get(
            payment_id=payment_id,
            user=request.user
        )
        
        serializer = PaymentSerializer(payment)
        
        # دریافت تراکنش‌های مرتبط
        transactions = payment.transactions.all()
        
        return api_core.format_response(
            success=True,
            data={
                'payment': serializer.data,
                'transactions': [
                    {
                        'type': t.transaction_type,
                        'amount': str(t.amount),
                        'status': t.status,
                        'created_at': t.created_at.isoformat()
                    }
                    for t in transactions
                ]
            }
        )
        
    except Payment.DoesNotExist:
        return api_core.format_response(
            success=False,
            error='payment_not_found',
            message='پرداخت مورد نظر یافت نشد',
            status_code=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error getting payment detail: {str(e)}")
        api_core = APIIngressCore()
        return api_core.handle_error(e, "get_payment_detail")