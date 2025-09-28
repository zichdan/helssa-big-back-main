from __future__ import annotations

"""
ویوهای اپ SOAP
"""

from typing import Any, Dict
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .permissions import IsDoctor
from agent.app_standards.four_cores.api_ingress import APIIngressCore, with_api_ingress

from .serializers import GenerateSOAPInputSerializer, SOAPReportSerializer
from .models import SOAPReport
from .services import SOAPReportGenerator, generate_markdown


User = get_user_model()


class GenerateSOAPView(APIView):
    """
    API برای تولید گزارش SOAP
    """

    permission_classes = [IsAuthenticated, IsDoctor]

    @with_api_ingress(rate_limit=50, rate_window=60)
    def post(self, request, *args, **kwargs):
        ingress = APIIngressCore()

        is_valid, data_or_errors = ingress.validate_request(
            request.data, GenerateSOAPInputSerializer
        )
        if not is_valid:
            return Response(
                ingress.build_error_response('validation', data_or_errors),
                status=status.HTTP_400_BAD_REQUEST
            )

        validated = data_or_errors

        patient = get_object_or_404(User, id=validated['patient_id'])
        doctor = None
        if validated.get('doctor_id'):
            doctor = get_object_or_404(User, id=validated['doctor_id'])

        generator = SOAPReportGenerator()
        soap_dict = generator.generate(
            transcript=validated['transcript'],
            context={
                'encounter_id': validated['encounter_id'],
                'patient_id': validated['patient_id'],
                'doctor_id': validated.get('doctor_id'),
            }
        )

        report = SOAPReport.objects.create(
            encounter_id=soap_dict['encounter_id'],
            patient=patient,
            doctor=doctor,
            subjective=soap_dict['subjective'],
            objective=soap_dict['objective'],
            assessment=soap_dict['assessment'],
            plan=soap_dict['plan'],
            metadata=soap_dict['metadata'],
        )

        serializer = SOAPReportSerializer(report)
        return Response({'soap_report': serializer.data}, status=status.HTTP_201_CREATED)


class SOAPFormatsView(APIView):
    """
    API برای تولید فرمت‌های مختلف گزارش SOAP
    """

    permission_classes = [IsAuthenticated, IsDoctor]

    @with_api_ingress(rate_limit=50, rate_window=60)
    def get(self, request, report_id: int, *args, **kwargs):
        ingress = APIIngressCore()
        report = get_object_or_404(SOAPReport, id=report_id)

        # Markdown تنها بر اساس مستندات
        md = generate_markdown(SOAPReportSerializer(report).data)
        return Response({'markdown': md}, status=status.HTTP_200_OK)