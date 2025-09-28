"""
ویوهای اپلیکیشن
Application Views
"""

from typing import Any, Dict
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .cores.orchestrator import CentralOrchestrator
from .serializers import RequestSerializer
from app_standards.four_cores import with_api_ingress


logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@with_api_ingress(rate_limit=50, rate_window=60)
def main_endpoint(request) -> Response:
    """
    نقطه ورود اصلی API
    """
    try:
        orchestrator = CentralOrchestrator()
        ingress = orchestrator.api_core

        # Validation
        is_valid, data = ingress.validate_request(request.data, RequestSerializer)
        if not is_valid:
            return Response(
                ingress.build_error_response('validation', data),
                status=status.HTTP_400_BAD_REQUEST
            )

        # Process
        result = orchestrator.execute_workflow(
            'main_workflow',
            data,
            request.user
        )

        if result.status.value == 'completed':
            return Response(result.data, status=status.HTTP_200_OK)

        return Response(
            {'error': 'Processing failed', 'details': result.errors},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

