"""
سریالایزرهای اپ ممیزی (Audit)
"""
from __future__ import annotations

from typing import Any, Dict

from rest_framework import serializers
from django.contrib.auth import get_user_model

from ..models import AuditLog, SecurityEvent
from .. import settings as audit_settings


User = get_user_model()


class AuditLogSerializer(serializers.ModelSerializer):
    """
    سریالایزر لاگ ممیزی جهت اعتبارسنجی ورودی‌ها
    """

    class Meta:
        model = AuditLog
        fields = [
            'id', 'timestamp', 'user', 'event_type', 'resource', 'action',
            'result', 'ip_address', 'user_agent', 'session_id', 'metadata'
        ]
        read_only_fields = ['id', 'timestamp']

    def validate_event_type(self, value: str) -> str:
        if value not in audit_settings.AUDIT_EVENT_TYPES:
            raise serializers.ValidationError('نوع رویداد نامعتبر است')
        return value

    def validate_result(self, value: str) -> str:
        if value not in {'success', 'failed'}:
            raise serializers.ValidationError('نتیجه نامعتبر است')
        return value


class SecurityEventSerializer(serializers.ModelSerializer):
    """
    سریالایزر رویداد امنیتی
    """

    class Meta:
        model = SecurityEvent
        fields = [
            'id', 'timestamp', 'event_type', 'severity', 'risk_score', 'ip_address',
            'user_agent', 'user', 'details', 'result'
        ]
        read_only_fields = ['id', 'timestamp', 'severity', 'risk_score']

    def validate_result(self, value: str) -> str:
        if value not in {'detected', 'failed', 'blocked'}:
            raise serializers.ValidationError('نتیجه نامعتبر است')
        return value

