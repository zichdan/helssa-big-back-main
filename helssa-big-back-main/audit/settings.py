"""
تنظیمات داخلی اپ audit

نکته: طبق دستور کاربر، تنظیمات اپ داخل خود اپ نگهداری می‌شود و URL مرجع و تنظیمات اصلی پروژه دست نمی‌خورند.
"""
from datetime import timedelta
import os
from django.conf import settings


# HMAC و امنیت
AUDIT_HMAC_ENABLED: bool = getattr(settings, 'AUDIT_HMAC_ENABLED', True)
# از SECRET_KEY تنظیمات پروژه به طور مستقیم استفاده نمی‌کنیم تا در محیط تست خالی بودن آن خطا ایجاد نکند
AUDIT_HMAC_SECRET_KEY: str = getattr(
    settings,
    'AUDIT_HMAC_SECRET_KEY',
    os.getenv('AUDIT_HMAC_SECRET_KEY', os.getenv('SECRET_KEY', 'audit_test_secret'))
)
AUDIT_HMAC_ALGORITHM: str = getattr(settings, 'AUDIT_HMAC_ALGORITHM', 'sha256')

# نگهداری لاگ
AUDIT_RETENTION_DAYS: int = getattr(settings, 'AUDIT_RETENTION_DAYS', 365)

# دسته‌بندی رویدادها
AUDIT_EVENT_TYPES = getattr(settings, 'AUDIT_EVENT_TYPES', [
    'authentication',
    'authorization',
    'data_access',
    'system',
    'security',
])

# نرخ‌بندی و ذخیره‌سازی سرد (stub)
AUDIT_ARCHIVE_ENABLED: bool = getattr(settings, 'AUDIT_ARCHIVE_ENABLED', False)
AUDIT_ARCHIVE_AFTER: timedelta = getattr(settings, 'AUDIT_ARCHIVE_AFTER', timedelta(days=30))

