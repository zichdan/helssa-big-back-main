"""
پیکربندی اپلیکیشن STT (Speech-to-Text)
"""
from django.apps import AppConfig


class SttConfig(AppConfig):
    """پیکربندی اپ تبدیل گفتار به متن"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stt'
    verbose_name = 'تبدیل گفتار به متن'
    
    def ready(self):
        """
        اجرای کارهای مورد نیاز هنگام بارگذاری اپ
        
        - ثبت سیگنال‌ها
        - بررسی وابستگی‌ها
        """
        # Import signals if any
        try:
            from . import signals  # noqa
        except ImportError:
            pass
            
        # بررسی نصب whisper
        try:
            import whisper  # noqa
            import ffmpeg  # noqa
        except ImportError:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                "Whisper یا ffmpeg نصب نشده است. "
                "لطفاً با دستور pip install openai-whisper ffmpeg-python نصب کنید."
            )