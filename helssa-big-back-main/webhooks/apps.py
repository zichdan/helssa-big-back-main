"""
پیکربندی اپلیکیشن webhooks
"""

from django.apps import AppConfig


class WebhooksConfig(AppConfig):
    """
    پیکربندی اپ webhooks
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'webhooks'
    verbose_name = 'وب‌هوک‌ها'

    def ready(self) -> None:
        """
        نقطه ورود برای انجام کارهای اولیه اپلیکیشن.
        """
        # سیگنال‌ها در صورت نیاز اینجا import می‌شوند
        # import webhooks.signals  # noqa: F401
        return None