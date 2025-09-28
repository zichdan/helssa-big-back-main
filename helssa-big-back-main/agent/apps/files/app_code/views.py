"""
ویوهای اپلیکیشن فایل‌ها
Application Views for Files
"""

from typing import Any, Dict

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.parsers import MultiPartParser, FormParser

from django.db.models.query import QuerySet

from app_standards.views.api_views import StandardUserThrottle
from app_standards.views.permissions import IsOwner

from .models import StoredFile
from .serializers import (
    StoredFileSerializer,
    StoredFileCreateSerializer,
)


class StoredFileViewSet(ModelViewSet):
    """
    ViewSet مدیریت فایل‌ها (آپلود/لیست/حذف)
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [StandardUserThrottle]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self) -> QuerySet[StoredFile]:
        """
        دریافت لیست فایل‌های کاربر جاری
        """
        return StoredFile.objects.filter(created_by=self.request.user, is_active=True).order_by('-created_at')

    def get_serializer_class(self):
        """
        انتخاب سریالایزر بر اساس اکشن
        """
        if self.action == 'create':
            return StoredFileCreateSerializer
        return StoredFileSerializer

    def create(self, request, *args, **kwargs) -> Response:
        """
        آپلود فایل جدید
        """
        input_serializer = StoredFileCreateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        upload = input_serializer.validated_data['file']
        description: str = input_serializer.validated_data.get('description', '')
        tags: str = input_serializer.validated_data.get('tags', '')

        # تعیین نوع فایل و MIME
        file_type = (upload.content_type or '').split('/')[-1] if getattr(upload, 'content_type', None) else ''
        original_mime = getattr(upload, 'content_type', '') or ''

        stored = StoredFile.objects.create(
            file=upload,
            description=description,
            tags=tags,
            file_type=file_type,
            original_mime_type=original_mime,
            created_by=request.user,
        )

        output = StoredFileSerializer(instance=stored, context={'request': request})
        headers = self.get_success_headers(output.data)
        return Response(output.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_destroy(self, instance: StoredFile) -> None:
        """
        حذف فایل (فقط توسط مالک)
        """
        # بررسی مالکیت
        if instance.created_by != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('دسترسی فقط برای مالک مجاز است')
        # حذف نرم برای حفظ تاریخچه
        instance.soft_delete()

