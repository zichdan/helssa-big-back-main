from __future__ import annotations

from typing import Any
from django.utils import timezone
from rest_framework import serializers

from .models import Certificate


class CertificateCreateSerializer(serializers.ModelSerializer):
    """
    اعتبارسنجی ورودی برای ایجاد گواهی استعلاجی
    """

    class Meta:
        model = Certificate
        fields = (
            'visit_id',
            'patient',
            'days_off',
            'reason',
        )
        extra_kwargs = {
            'patient': {'write_only': True},
        }


class CertificateSerializer(serializers.ModelSerializer):
    """
    نمایش اطلاعات گواهی
    """

    class Meta:
        model = Certificate
        fields = (
            'id',
            'visit_id',
            'doctor',
            'patient',
            'days_off',
            'reason',
            'is_revoked',
            'verify_url',
            'pdf_object_name',
            'pdf_file_size',
            'pdf_generated_at',
            'created_at',
        )
        read_only_fields = (
            'id', 'doctor', 'is_revoked', 'verify_url', 'pdf_object_name',
            'pdf_file_size', 'pdf_generated_at', 'created_at',
        )


class CertificateRevokeSerializer(serializers.Serializer):
    """
    ورودی برای ابطال گواهی
    """

    reason = serializers.CharField(required=False, allow_blank=True, max_length=512)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        return attrs

