"""
پیکربندی اپلیکیشن پنل ادمین
AdminPortal App Configuration
"""

from django.apps import AppConfig


class AdminPortalConfig(AppConfig):
    """پیکربندی اپلیکیشن پنل ادمین"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'adminportal'
    verbose_name = 'پنل ادمین'
    
    def ready(self):
        """راه‌اندازی اولیه اپلیکیشن"""
        # Import signals if any
        pass