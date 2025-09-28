"""
تنظیمات اپلیکیشن تریاژ پزشکی
Triage App Configuration
"""

from django.apps import AppConfig


class TriageConfig(AppConfig):
    """
    پیکربندی اپلیکیشن triage
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'triage'
    verbose_name = 'تریاژ پزشکی'
    
    def ready(self):
        """
        عملیات اولیه هنگام بارگذاری اپلیکیشن را انجام می‌دهد.
        
        این متد پس از آماده‌شدن رجیستری اپلیکیشن فراخوانی می‌شود و نقطهٔ مناسب برای انجام تنظیمات مرتبط با چرخهٔ اجرای اپ (مانند واردکردن هندلرهای سیگنال، ثبت validation checks یا راه‌اندازی اجزای مرتبط با اپ) است.
        """
        # می‌توانید سیگنال‌ها را اینجا import کنید
        # import triage.signals
        pass