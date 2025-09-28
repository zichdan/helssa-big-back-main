"""
تنظیمات اپلیکیشن پرداخت
"""
from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    """
    پیکربندی اپلیکیشن پرداخت
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payments'
    verbose_name = 'مدیریت پرداخت‌ها'
    
    def ready(self):
        """
        اجرای کدهای مورد نیاز هنگام بارگذاری اپلیکیشن
        """
        # Import سیگنال‌ها (در صورت وجود)
        try:
            from . import signals
        except ImportError:
            pass
        
        # ایجاد کیف پول برای کاربران جدید
        from django.db.models.signals import post_save
        from django.contrib.auth import get_user_model
        from .models import Wallet
        
        User = get_user_model()
        
        def create_wallet_for_new_user(sender, instance, created, **kwargs):
            """ایجاد کیف پول برای کاربر جدید"""
            if created:
                from .settings import WALLET_SETTINGS
                if WALLET_SETTINGS.get('AUTO_CREATE', True):
                    Wallet.objects.get_or_create(
                        user=instance,
                        defaults={
                            'balance': WALLET_SETTINGS.get('INITIAL_BALANCE', 0)
                        }
                    )
        
        # اتصال سیگنال
        post_save.connect(create_wallet_for_new_user, sender=User)