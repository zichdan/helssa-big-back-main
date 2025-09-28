"""
Exports Application
"""

from django.apps import AppConfig


class ExportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'exports'
    verbose_name = 'Exports'
    
    def ready(self):
        """آماده‌سازی اپلیکیشن"""
        pass

