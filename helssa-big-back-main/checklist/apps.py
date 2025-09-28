"""
تنظیمات اپلیکیشن Checklist
"""
from django.apps import AppConfig


class ChecklistConfig(AppConfig):
    """
    کلاس پیکربندی اپلیکیشن Checklist
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'checklist'
    verbose_name = 'چک‌لیست‌ها'