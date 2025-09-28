"""
ویوهای اپلیکیشن اعلان‌ها
Application Views for Notifications
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from app_standards.four_cores import APIIngressCore, CentralOrchestrator
from app_standards.views.api_views import AIRequestThrottle
from .serializers import NotificationRequestSerializer, NotificationResponseSerializer
from .permissions import CanSendNotification


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanSendNotification])
@throttle_classes([AIRequestThrottle])
def send_notification(request):
    """
    ارسال اعلان از طریق Orchestrator با رعایت API Ingress
    """
    ingress = APIIngressCore()

    # اعتبارسنجی ورودی
    is_valid, data = ingress.validate_request(request.data, NotificationRequestSerializer)
    if not is_valid:
        return Response(
            ingress.build_error_response('validation', data),
            status=status.HTTP_400_BAD_REQUEST
        )

    # اجرای workflow استاندارد ارسال اعلان؛ طبق مستندات چهار هسته‌ای
    orchestrator = CentralOrchestrator()
    result = orchestrator.execute_workflow(
        'send_notification',  # نام گردش‌کار مطابق مستندات؛ اگر تعریف نشده باشد تناقض گزارش می‌شود
        data,
        request.user
    )

    # بررسی وضعیت اجرا
    if getattr(result, 'status', None) == getattr(result, 'status').COMPLETED if hasattr(result, 'status') else False:
        payload = {
            'queued': True,
            'notification_type': data['notification_type'],
            'title': data['title'],
            'content': data['content'],
            'priority': data.get('priority', 'normal'),
            'scheduled_for': data.get('scheduled_for'),
            'reference_id': result.data.get('notification_id', 'unknown') if isinstance(result.data, dict) else 'unknown'
        }
        resp = NotificationResponseSerializer(payload)
        return Response(resp.data, status=status.HTTP_200_OK)

    # در صورت نبود workflow یا خطا، مطابق سیاست‌ها پاسخ استاندارد بدهیم
    if getattr(result, 'errors', None):
        return Response(
            ingress.build_error_response('internal', {'errors': result.errors}),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # اگر orchestration در مستندات تعریف نشده باشد: ثبت تناقض
    return Response(
        ingress.build_error_response('internal', {'issue': 'workflow send_notification not defined in orchestrator'}),
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

