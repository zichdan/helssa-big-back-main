from django.apps import AppConfig


class EncountersConfig(AppConfig):
    """تنظیمات اپ ملاقات‌ها"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'encounters'
    verbose_name = 'مدیریت ملاقات‌ها'
    
    def ready(self):
        """اجرای کارهای اولیه هنگام بارگذاری اپ"""
        # Import signals
        try:
            from . import signals
        except ImportError:
            pass