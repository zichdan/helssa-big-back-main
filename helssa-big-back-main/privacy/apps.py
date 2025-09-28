from django.apps import AppConfig


class PrivacyConfig(AppConfig):
    """
    پیکربندی اپلیکیشن Privacy
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'privacy'
    verbose_name = 'مدیریت حریم خصوصی'
    
    def ready(self):
        """اجرای کدهای مقداردهی اولیه"""
        # Import کردن signals در صورت نیاز
        # import privacy.signals
