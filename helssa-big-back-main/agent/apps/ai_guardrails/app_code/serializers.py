"""
سریالایزرهای اپلیکیشن
Application Serializers
"""

from rest_framework import serializers
from app_standards.serializers.base_serializers import BaseModelSerializer
from .models import GuardrailPolicy, RedFlagRule, PolicyViolationLog
from django.conf import settings

class GuardrailPolicySerializer(BaseModelSerializer):
    """
    سریالایزر سیاست گاردریل
    """

    class Meta:
        model = GuardrailPolicy
        fields = [
            'id', 'name', 'description', 'is_active', 'enforcement_mode',
            'applies_to', 'priority', 'conditions', 'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def validate_conditions(self, value):
        sev = value.get('severity_min')
        if sev is not None:
            if not isinstance(sev, int) or not (0 <= sev <= 100):
                raise serializers.ValidationError(
                    "conditions.severity_min باید عدد بین 0 و 100 باشد"
                )
        return value

class RedFlagRuleSerializer(BaseModelSerializer):
    """
    سریالایزر قانون رد-فلگ
    """

    class Meta:
        model = RedFlagRule
        fields = [
            'id', 'name', 'pattern_type', 'pattern', 'category', 'severity',
            'is_active', 'metadata', 'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def validate(self, attrs):
        pattern_type = attrs.get('pattern_type')
        pattern = attrs.get('pattern')
        if pattern_type == 'regex' and pattern:
            import re
            try:
                re.compile(pattern)
            except re.error as e:
                raise serializers.ValidationError({'pattern': f'الگوی regex نامعتبر: {e}'})
        return attrs

class PolicyViolationLogSerializer(BaseModelSerializer):
    """
    سریالایزر گزارش نقض سیاست
    """

    class Meta:
        model = PolicyViolationLog
        fields = [
            'id', 'user', 'policy', 'rule', 'content_snapshot', 'direction',
            'context', 'action_taken', 'risk_score', 'matched_spans',
            'request_path', 'ip_address', 'user_agent', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class EvaluateContentSerializer(serializers.Serializer):
    """
    ورودی ارزیابی محتوای AI
    """
    content = serializers.CharField(
        min_length=1,
        max_length=getattr(settings, 'AI_GUARDRAILS', {}).get('MAX_CONTENT_LENGTH', 5000)
    )
    direction = serializers.ChoiceField(choices=['input', 'output', 'both'], default='both')
    context = serializers.DictField(required=False)


class EvaluationResultSerializer(serializers.Serializer):
    """
    خروجی ارزیابی محتوای AI
    """
    allowed = serializers.BooleanField()
    action = serializers.ChoiceField(choices=['allow', 'warn', 'block'])
    risk_score = serializers.IntegerField()
    reasons = serializers.ListField(child=serializers.CharField(), default=list)
    matches = serializers.ListField(child=serializers.DictField(), default=list)
    applied_policy = serializers.CharField(allow_blank=True, required=False)
