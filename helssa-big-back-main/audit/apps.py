from django.apps import AppConfig


class AuditConfig(AppConfig):
    """
    پیکربندی اپ Audit

    - بارگذاری تنظیمات داخلی اپ از audit.settings
    - راه‌اندازی logging ساختاریافته در صورت نیاز
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit'
    verbose_name = 'ممیزی و لاگ (Audit)'

    def ready(self):
        # بارگذاری تنظیمات داخلی اپ
        try:
            from . import settings as audit_settings  # noqa: F401
        except Exception:
            # اگر تنظیمات اپ موجود نباشد، از خطا عبور می‌کنیم تا اجرا مختل نشود
            pass

