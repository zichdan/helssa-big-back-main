"""
Ai Helsabrain Application
"""

from django.apps import AppConfig


class AiHelsabrainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_helsabrain'
    verbose_name = 'Ai Helsabrain'
    
    def ready(self):
        """آماده‌سازی اپلیکیشن"""
        pass
