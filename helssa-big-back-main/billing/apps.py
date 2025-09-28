"""
تنظیمات اپ Billing
Billing App Configuration
"""

from django.apps import AppConfig


class BillingConfig(AppConfig):
    """تنظیمات اپ سیستم مالی"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'billing'
    verbose_name = 'سیستم مالی و اشتراک'
    
    def ready(self):
        """راه‌اندازی اولیه اپ"""
        import billing.signals  # noqa F401