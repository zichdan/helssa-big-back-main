"""
تنظیمات اپلیکیشن بیمار
Patient App Configuration
"""

from django.apps import AppConfig


class PatientConfig(AppConfig):
    """
    تنظیمات اپلیکیشن مدیریت بیماران
    Patient management application configuration
    """
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'patient'
    verbose_name = 'مدیریت بیماران'
    
    def ready(self):
        """
        عملیات مقداردهی اولیه اپ
        App initialization operations
        """
        try:
            import patient.signals  # noqa
        except ImportError:
            pass