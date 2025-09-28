"""
ویوهای اپلیکیشن
Application Views
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import logging
from rest_framework.request import Request
from app_standards.four_cores import APIIngressCore
from .cores.orchestrator import GuardrailsOrchestrator
from .serializers import (
    EvaluateContentSerializer,
    EvaluationResultSerializer,  # اگر ازش برای validate خروجی استفاده می‌کنی نگه دار؛ وگرنه حذفش کن
    GuardrailPolicySerializer,
    RedFlagRuleSerializer,
)
logger = logging.getLogger("ai_guardrails")
from .models import GuardrailPolicy, RedFlagRule
from django.core.paginator import Paginator
from django.conf import settings
from app_standards.views.permissions import RateLimitPermission


class AiRequestsRateLimitPermission(RateLimitPermission):
    rate = settings.RATE_LIMIT_AI_GUARDRAILS.get('ai_requests', '20/minute')


class ApiCallsRateLimitPermission(RateLimitPermission):
    rate = settings.RATE_LIMIT_AI_GUARDRAILS.get('api_calls', '100/minute')

@api_view(['POST'])
@permission_classes([IsAuthenticated, AiRequestsRateLimitPermission])
def evaluate(request):
    """
    ارزیابی محتوای ورودی/خروجی با گاردریل‌ها
    """
    ingress = APIIngressCore()

    is_valid, data = ingress.validate_request(request.data, EvaluateContentSerializer)
    if not is_valid:
        return Response(
            ingress.build_error_response('validation', data),
            status=status.HTTP_400_BAD_REQUEST
        )

    orchestrator = GuardrailsOrchestrator()
    result = orchestrator.evaluate(
        content=data['content'],
        user=request.user,
        direction=data.get('direction', 'both'),
        request=request
    )

    return Response(result, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, ApiCallsRateLimitPermission])
def policies(request):
    """
    لیست/ایجاد سیاست‌های گاردریل
    """
    if request.method == 'GET':
        qs = GuardrailPolicy.objects.all().order_by('priority')
        paginator = Paginator(qs, 20)
        page = paginator.get_page(request.GET.get('page', 1))
        serializer = GuardrailPolicySerializer(page, many=True)
        return Response({
            'count': paginator.count,
            'results': serializer.data
        })

    ingress = APIIngressCore()
    is_valid, data = ingress.validate_request(request.data, GuardrailPolicySerializer)
    if not is_valid:
        return Response(
            ingress.build_error_response('validation', data),
            status=status.HTTP_400_BAD_REQUEST
        )
    serializer = GuardrailPolicySerializer(data=data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    obj = serializer.save()
    return Response(GuardrailPolicySerializer(obj).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, ApiCallsRateLimitPermission])
def rules(request):
    """
    لیست/ایجاد قوانین رد-فلگ
    """
    if request.method == 'GET':
        qs = RedFlagRule.objects.all().order_by('-severity')
        paginator = Paginator(qs, 20)
        page = paginator.get_page(request.GET.get('page', 1))
        serializer = RedFlagRuleSerializer(page, many=True)
        return Response({
            'count': paginator.count,
            'results': serializer.data
        })

    ingress = APIIngressCore()
    is_valid, data = ingress.validate_request(request.data, RedFlagRuleSerializer)
    if not is_valid:
        return Response(
            ingress.build_error_response('validation', data),
            status=status.HTTP_400_BAD_REQUEST
        )
    serializer = RedFlagRuleSerializer(data=data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    obj = serializer.save()
    return Response(RedFlagRuleSerializer(obj).data, status=status.HTTP_201_CREATED)

