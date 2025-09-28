from django.apps import AppConfig


class ComplianceConfig(AppConfig):
    """
    کانفیگ اپ Compliance
    
    این اپ مسئول مدیریت و پیاده‌سازی استانداردهای امنیتی و رعایت مقررات است
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'compliance'
    verbose_name = 'مدیریت Compliance و امنیت'