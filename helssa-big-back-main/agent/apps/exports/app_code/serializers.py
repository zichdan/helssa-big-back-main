"""
سریالایزرهای اپلیکیشن
Application Serializers
"""

from rest_framework import serializers
from app_standards.serializers.base_serializers import BaseSerializer


class RequestSerializer(BaseSerializer):
    """
    اعتبارسنجی ورودی اصلی
    """
    payload = serializers.DictField(required=False)

