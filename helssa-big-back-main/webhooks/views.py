"""
ویوهای مربوط به دریافت و پردازش وب‌هوک‌ها
"""

from __future__ import annotations

import json
from typing import Any, Dict

from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from .serializers import WebhookPayloadSerializer
from .conf import (
    get_signature_header_name,
    get_source_id_header_name,
    get_rate_limit_config,
)
from .services.signature import verify_webhook_signature
from .services.rate_limit import RateLimitConfig, allow_request


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def webhook_handler(request: HttpRequest) -> JsonResponse:
    """
    دریافت وب‌هوک از سرویس‌های خارجی

    طبق مستندات: امضا از طریق هدر X-Webhook-Signature تایید می‌شود و سپس payload
    اعتبارسنجی و بر اساس نوع رویداد به سرویس‌های مربوطه سپرده می‌شود.
    """
    try:
        # ریت‌لیمیت بر اساس منبع
        source_header = get_source_id_header_name()
        source_id = request.headers.get(source_header) or request.META.get('REMOTE_ADDR', 'unknown')

        limit_cfg = get_rate_limit_config()
        rc = RateLimitConfig(limit=limit_cfg['limit'], window_seconds=limit_cfg['window_seconds'])
        if not allow_request(source_id, rc):
            return JsonResponse({'detail': 'تعداد درخواست‌ها بیش از حد مجاز است'}, status=429)

        # تایید امضا
        signature_header = get_signature_header_name()
        signature = request.headers.get(signature_header)
        if not verify_webhook_signature(request.body, signature):
            return JsonResponse({'error': 'امضای نامعتبر'}, status=401)

        # اعتبارسنجی داده‌ها
        try:
            data: Dict[str, Any] = json.loads(request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'ساختار JSON نامعتبر است'}, status=400)

        serializer = WebhookPayloadSerializer(data=data)
        if not serializer.is_valid():
            return JsonResponse({'errors': serializer.errors}, status=400)

        validated = serializer.validated_data
        # Dispatch ساده بر اساس نوع رویداد؛
        # مطابق مستندات فقط پردازش نمونه پرداخت را پیاده می‌کنیم.
        event_type = validated['event']
        payload = validated['payload']

        if event_type == 'payment':
            result = _process_payment(payload)
            status_code = 200 if result.get('success') else 422
            return JsonResponse(result, status=status_code)

        # برای سایر رویدادها پاسخ پیش‌فرض
        return JsonResponse({'status': 'processed', 'event': event_type})

    except Exception as exc:  # noqa: BLE001
        return JsonResponse({'error': 'خطای غیرمنتظره', 'detail': str(exc)}, status=500)


def _process_payment(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    پردازش وب‌هوک پرداخت مطابق نمونه موجود در مستندات.
    """
    payment_id = data.get('payment_id')
    status = data.get('status')
    gateway_ref = data.get('gateway_reference')

    if not all([payment_id, status, gateway_ref]):
        return {'success': False, 'error': 'فیلدهای اجباری ناقص است'}

    # در این مرحله فقط اعتبار اولیه را تایید می‌کنیم
    # و پاسخ موفق برمی‌گردانیم. (جزئیات به اپ مالی سپرده می‌شود)
    return {'success': True, 'processed': True}