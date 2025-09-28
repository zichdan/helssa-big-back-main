"""
Views ساده برای تست API Gateway
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import JsonResponse
from django.utils import timezone


logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    بررسی سلامت سیستم
    """
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0',
            'app': 'api_gateway'
        }
        
        return Response(health_status, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def test_endpoint(request):
    """
    endpoint تست
    """
    return Response(
        {
            'message': 'API Gateway is working!',
            'timestamp': timezone.now().isoformat()
        },
        status=status.HTTP_200_OK
    )
