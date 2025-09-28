"""
سریالایزرهای مربوط به وب‌هوک‌ها
"""

from typing import Any, Dict
from rest_framework import serializers


class WebhookPayloadSerializer(serializers.Serializer):
    """
    اعتبارسنجی ورودی وب‌هوک عمومی

    فیلدها:
        - event: نام رویداد
        - payload: محتوای رویداد (داده‌های خام)
    """

    event = serializers.CharField(max_length=128)
    payload = serializers.DictField(child=serializers.JSONField(), allow_empty=False)

    def validate_event(self, value: str) -> str:
        """
        اعتبارسنجی مقدار رویداد. در صورت وجود لیست رویدادهای مجاز در تنظیمات، بررسی می‌شود.
        """
        from .conf import get_allowed_events

        allowed = get_allowed_events()
        if allowed and value not in allowed:
            raise serializers.ValidationError('رویداد مجاز نیست')
        return value

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        ولیدیشن نهایی روی داده‌ها
        """
        return attrs