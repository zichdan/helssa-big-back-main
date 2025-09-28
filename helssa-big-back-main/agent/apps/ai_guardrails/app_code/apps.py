"""
Ai Guardrails Application
"""

from django.apps import AppConfig


class AiGuardrailsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_guardrails'
File: agent/apps/ai_guardrails/app_code/apps.py
Lines: 11

    verbose_name = 'AI Guardrails'
    
    def ready(self) -> None:
        """آماده‌سازی اپلیکیشن"""
        ...
