"""
مدل‌های اپلیکیشن فایل‌ها
Application Models for Files
"""

from django.db import models
from django.contrib.auth import get_user_model
from app_standards.models.base_models import FileAttachmentModel


User = get_user_model()


class StoredFile(FileAttachmentModel):
    """
    مدل فایل ذخیره‌شده توسط کاربر

    این مدل بر پایه FileAttachmentModel ساخته شده و شامل متادیتای تکمیلی است.
    """

    original_mime_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='نوع MIME اصلی'
    )
    tags = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='برچسب‌ها'
    )

    class Meta:
        verbose_name = 'فایل'
        verbose_name_plural = 'فایل‌ها'
        ordering = ['-created_at']

