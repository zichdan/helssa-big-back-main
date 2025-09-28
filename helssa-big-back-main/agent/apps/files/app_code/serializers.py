"""
سریالایزرهای اپلیکیشن فایل‌ها
Application Serializers for Files
"""

from typing import Any, Dict

from rest_framework import serializers

from app_standards.serializers.base_serializers import (
    BaseModelSerializer,
    FileUploadSerializer,
)
from .models import StoredFile


class StoredFileSerializer(BaseModelSerializer):
    """
    سریالایزر نمایش/ایجاد فایل ذخیره‌شده
    """

    class Meta:
        model = StoredFile
        fields = [
            'id', 'file', 'file_name', 'file_size', 'file_type',
            'original_mime_type', 'description', 'tags',
            'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['id', 'file_name', 'file_size', 'created_by', 'created_at', 'updated_at']

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        اعتبارسنجی ورودی‌ها
        """
        return super().validate(attrs)


class StoredFileCreateSerializer(FileUploadSerializer):
    """
    سریالایزر ایجاد فایل (برای اعتبارسنجی ورودی آپلود)
    """
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    tags = serializers.CharField(max_length=200, required=False, allow_blank=True)

