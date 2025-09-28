"""
مدل‌های اپلیکیشن اعلان‌ها
Application Models for Notifications
"""

from django.db import models
from django.contrib.auth import get_user_model

# توجه: طبق قوانین پروژه، مدل کاربر جدید ایجاد نمی‌کنیم
User = get_user_model()


class NotificationTemplate(models.Model):
    """
    الگوی متن اعلان‌ها برای استفاده داخلی اپ

    توجه: این مدل مستقل از UnifiedNotification است و صرفاً برای ذخیره قالب‌ها
    به‌کار می‌رود. برای ارسال/ردیابی اعلان، از جریان‌های API استفاده می‌شود.
    """

    code = models.CharField(max_length=100, unique=True, verbose_name='کد الگو')
    title_template = models.CharField(max_length=255, verbose_name='قالب عنوان')
    content_template = models.TextField(verbose_name='قالب محتوا')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین تغییر')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notification_templates_created',
        verbose_name='ایجادکننده'
    )

    class Meta:
        verbose_name = 'الگوی اعلان'
        verbose_name_plural = 'الگوهای اعلان'
        ordering = ['-created_at']

    def __str__(self) -> str:  # type: ignore[override]
        return self.code

