"""
تنظیمات اپلیکیشن Files
Files Application Config
"""

from django.apps import AppConfig


class FilesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'files'
    verbose_name = 'Files'

    def ready(self) -> None:
        """
        آماده‌سازی اپلیکیشن
        """
        return None

