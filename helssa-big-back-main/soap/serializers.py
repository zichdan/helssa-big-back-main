from __future__ import annotations

"""
سریالایزرهای اپ SOAP
"""

from typing import Any, Dict
from rest_framework import serializers

from .models import SOAPReport


class GenerateSOAPInputSerializer(serializers.Serializer):
    """
    ورودی تولید گزارش SOAP
    """
    encounter_id = serializers.CharField(max_length=100)
    transcript = serializers.CharField()
    patient_id = serializers.IntegerField()
    doctor_id = serializers.IntegerField(required=False, allow_null=True)


class SOAPReportSerializer(serializers.ModelSerializer):
    """
    خروجی استاندارد گزارش SOAP
    """

    class Meta:
        model = SOAPReport
        fields = [
            'id', 'encounter_id', 'patient', 'doctor', 'subjective', 'objective',
            'assessment', 'plan', 'metadata', 'generated_at', 'updated_at'
        ]