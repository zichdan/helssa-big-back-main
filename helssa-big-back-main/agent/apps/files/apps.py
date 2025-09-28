"""
تنظیمات اپلیکیشن Files (ماژول سطح بالا)
Top-level Files AppConfig to align with deployment imports
"""

from django.apps import AppConfig


class FilesConfig(AppConfig):
    """پیکربندی اپلیکیشن Files"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'files'
    verbose_name = 'Files'

    def ready(self) -> None:
        """آماده‌سازی اپلیکیشن"""
        return None

