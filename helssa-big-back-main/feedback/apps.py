from django.apps import AppConfig


class FeedbackConfig(AppConfig):
    """
    تنظیمات اپلیکیشن feedback
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'feedback'
    verbose_name = 'سیستم بازخورد و نظرسنجی'
    
    def ready(self):
        """اجرای کدهای اولیه هنگام آماده شدن اپ"""
        try:
            # Import signals if any
            # import feedback.signals
            pass
        except ImportError:
            pass
