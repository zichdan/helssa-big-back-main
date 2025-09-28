"""
ویوهای مربوط به بیمار در اپلیکیشن پرداخت
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

from .models import Payment, PaymentMethod, Wallet, WalletTransaction
from .serializers import (
    PaymentSerializer, CreatePaymentSerializer,
    WalletSerializer, RefundRequestSerializer
)
from .cores.orchestrator import CentralOrchestrator
from .cores.api_ingress import APIIngressCore

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def patient_create_payment(request):
    """
    ایجاد پرداخت جدید برای بیمار
    """
    try:
        api_core = APIIngressCore()
        orchestrator = CentralOrchestrator()
        
        # بررسی نوع کاربر
        user_type = getattr(request.user, 'user_type', 'patient')
        if user_type != 'patient':
            return api_core.format_response(
                success=False,
                error='unauthorized',
                message='این عملیات فقط برای بیماران مجاز است',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # اعتبارسنجی داده‌ها
        serializer = CreatePaymentSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return api_core.format_response(
                success=False,
                error='validation_error',
                message='داده‌های ارسالی نامعتبر است',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # پردازش پرداخت
        payment_data = serializer.validated_data
        payment_data['context'] = {
            'user_name': request.user.get_full_name() if hasattr(request.user, 'get_full_name') else str(request.user),
            'user_id': request.user.id
        }
        
        success, processed_data = orchestrator.process_payment_request(
            user_type='patient',
            payment_data=payment_data
        )
        
        if not success:
            return api_core.format_response(
                success=False,
                error=processed_data.get('error'),
                message=processed_data.get('message'),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # ایجاد رکورد پرداخت
        with transaction.atomic():
            payment = Payment.objects.create(
                user=request.user,
                user_type='patient',
                payment_type=payment_data['payment_type'],
                amount=payment_data['amount'],
                description=processed_data.get('description', ''),
                status='pending',
                metadata=payment_data.get('metadata', {}),
                appointment_id=payment_data.get('appointment_id'),
                doctor_id=payment_data.get('doctor_id'),
                payment_method_id=payment_data.get('payment_method_id')
            )
            
            # TODO: اتصال به درگاه پرداخت
            # فعلاً فقط وضعیت را pending می‌گذاریم
            
            payment_response = orchestrator.generate_payment_response(
                {
                    'status': payment.status,
                    'tracking_code': payment.tracking_code,
                    'amount': payment.amount,
                    'timestamp': payment.created_at.isoformat(),
                    'description': payment.description
                },
                include_audio=False
            )
            
            return api_core.format_response(
                success=True,
                data={
                    'payment_id': str(payment.payment_id),
                    'tracking_code': payment.tracking_code,
                    'status': payment.status,
                    'payment_url': f'/payments/gateway/{payment.payment_id}',  # URL درگاه
                    **payment_response
                },
                status_code=status.HTTP_201_CREATED
            )
            
    except Exception as e:
        logger.error(f"Error creating patient payment: {str(e)}")
        api_core = APIIngressCore()
        return api_core.handle_error(e, "patient_create_payment")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def patient_request_refund(request):
    """
    درخواست بازپرداخت توسط بیمار
    """
    try:
        api_core = APIIngressCore()
        
        # بررسی نوع کاربر
        user_type = getattr(request.user, 'user_type', 'patient')
        if user_type != 'patient':
            return api_core.format_response(
                success=False,
                error='unauthorized',
                message='این عملیات فقط برای بیماران مجاز است',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # اعتبارسنجی درخواست
        serializer = RefundRequestSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return api_core.format_response(
                success=False,
                error='validation_error',
                message='داده‌های ارسالی نامعتبر است',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # پرداخت مورد نظر
        payment = serializer.context['payment']
        refund_amount = serializer.validated_data.get('amount', payment.amount)
        
        # بررسی امکان بازپرداخت
        if payment.status != 'success':
            return api_core.format_response(
                success=False,
                error='invalid_status',
                message='فقط پرداخت‌های موفق قابل بازپرداخت هستند',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # ایجاد درخواست بازپرداخت
        with transaction.atomic():
            # تغییر وضعیت پرداخت
            if refund_amount == payment.amount:
                payment.status = 'refunded'
                payment.refunded_at = timezone.now()
            else:
                payment.status = 'partially_refunded'
                
            payment.save()
            
            # TODO: ارسال درخواست به درگاه
            
            return api_core.format_response(
                success=True,
                data={
                    'message': 'درخواست بازپرداخت با موفقیت ثبت شد',
                    'payment_id': str(payment.payment_id),
                    'refund_amount': str(refund_amount),
                    'status': payment.status
                }
            )
            
    except Exception as e:
        logger.error(f"Error requesting refund: {str(e)}")
        api_core = APIIngressCore()
        return api_core.handle_error(e, "patient_request_refund")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_get_wallet(request):
    """
    دریافت اطلاعات کیف پول بیمار
    """
    try:
        api_core = APIIngressCore()
        
        # بررسی نوع کاربر
        user_type = getattr(request.user, 'user_type', 'patient')
        if user_type != 'patient':
            return api_core.format_response(
                success=False,
                error='unauthorized',
                message='این عملیات فقط برای بیماران مجاز است',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # دریافت یا ایجاد کیف پول
        wallet, created = Wallet.objects.get_or_create(
            user=request.user,
            defaults={'balance': Decimal('0')}
        )
        
        serializer = WalletSerializer(wallet)
        
        # دریافت آخرین تراکنش‌ها
        recent_transactions = WalletTransaction.objects.filter(
            wallet=wallet
        ).order_by('-created_at')[:10]
        
        return api_core.format_response(
            success=True,
            data={
                'wallet': serializer.data,
                'recent_transactions': [
                    {
                        'type': t.transaction_type,
                        'amount': str(t.amount),
                        'description': t.description,
                        'created_at': t.created_at.isoformat()
                    }
                    for t in recent_transactions
                ]
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting patient wallet: {str(e)}")
        api_core = APIIngressCore()
        return api_core.handle_error(e, "patient_get_wallet")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def patient_charge_wallet(request):
    """
    شارژ کیف پول بیمار
    """
    try:
        api_core = APIIngressCore()
        
        # بررسی نوع کاربر
        user_type = getattr(request.user, 'user_type', 'patient')
        if user_type != 'patient':
            return api_core.format_response(
                success=False,
                error='unauthorized',
                message='این عملیات فقط برای بیماران مجاز است',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # دریافت مبلغ
        amount = request.data.get('amount')
        if not amount:
            return api_core.format_response(
                success=False,
                error='missing_amount',
                message='مبلغ شارژ الزامی است',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount = Decimal(amount)
            if amount < 10000:  # حداقل 10 هزار تومان
                raise ValueError("مبلغ کم است")
        except:
            return api_core.format_response(
                success=False,
                error='invalid_amount',
                message='مبلغ شارژ باید حداقل 10,000 ریال باشد',
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # ایجاد پرداخت برای شارژ
        with transaction.atomic():
            payment = Payment.objects.create(
                user=request.user,
                user_type='patient',
                payment_type='deposit',  # نوع جدید برای شارژ کیف پول
                amount=amount,
                description='شارژ کیف پول',
                status='pending',
                metadata={'wallet_charge': True}
            )
            
            # TODO: اتصال به درگاه پرداخت
            
            return api_core.format_response(
                success=True,
                data={
                    'payment_id': str(payment.payment_id),
                    'tracking_code': payment.tracking_code,
                    'amount': str(amount),
                    'payment_url': f'/payments/gateway/{payment.payment_id}'
                },
                status_code=status.HTTP_201_CREATED
            )
            
    except Exception as e:
        logger.error(f"Error charging patient wallet: {str(e)}")
        api_core = APIIngressCore()
        return api_core.handle_error(e, "patient_charge_wallet")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_payment_report(request):
    """
    گزارش پرداخت‌های بیمار
    """
    try:
        api_core = APIIngressCore()
        
        # بررسی نوع کاربر
        user_type = getattr(request.user, 'user_type', 'patient')
        if user_type != 'patient':
            return api_core.format_response(
                success=False,
                error='unauthorized',
                message='این عملیات فقط برای بیماران مجاز است',
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # دریافت پارامترها
        days = int(request.GET.get('days', 30))
        
        # محاسبه تاریخ شروع
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=days)
        
        # دریافت پرداخت‌ها
        payments = Payment.objects.filter(
            user=request.user,
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # آمار کلی
        stats = payments.aggregate(
            total_amount=models.Sum('amount'),
            total_count=models.Count('payment_id'),
            success_count=models.Count(
                'payment_id',
                filter=models.Q(status='success')
            ),
            failed_count=models.Count(
                'payment_id',
                filter=models.Q(status='failed')
            )
        )
        
        # آمار به تفکیک نوع
        by_type = payments.values('payment_type').annotate(
            count=models.Count('payment_id'),
            total=models.Sum('amount')
        ).order_by('-total')
        
        return api_core.format_response(
            success=True,
            data={
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'days': days
                },
                'summary': {
                    'total_amount': str(stats['total_amount'] or 0),
                    'total_count': stats['total_count'],
                    'success_count': stats['success_count'],
                    'failed_count': stats['failed_count'],
                    'success_rate': round(
                        (stats['success_count'] / stats['total_count'] * 100)
                        if stats['total_count'] > 0 else 0,
                        2
                    )
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
        )
        
    except Exception as e:
        logger.error(f"Error getting patient payment report: {str(e)}")
        api_core = APIIngressCore()
        return api_core.handle_error(e, "patient_payment_report")