"""
Notifications Application
"""

from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """
    پیکربندی اپلیکیشن اعلان‌ها
    """
    default_auto_field = 'django.db.models.BigAutoField'
    # مسیر کامل پکیج اپلیکیشن مطابق ساختار پوشه
    name = 'agent.apps.notifications.app_code'
    verbose_name = 'Notifications'

    def ready(self) -> None:
        """
        آماده‌سازی اپلیکیشن
        """
        return None

