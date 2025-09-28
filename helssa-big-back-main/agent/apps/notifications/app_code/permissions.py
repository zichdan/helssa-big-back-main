"""
دسترسی‌های سفارشی اپ اعلان‌ها
Custom Permissions for Notifications
"""

from app_standards.views.permissions import BasePermission, HasActiveSubscription


class CanSendNotification(BasePermission):
    """
    اجازه ارسال اعلان برای کاربران احراز هویت‌شده
    (می‌توان در آینده قوانین بیشتری اضافه کرد)
    """

    message = 'اجازه ارسال اعلان را ندارید'

    def has_permission(self, request, view):  # type: ignore[override]
        if not super().has_permission(request, view):
            return False
        # نیاز به اشتراک فعال (سیاست امنیتی)
        return HasActiveSubscription().has_permission(request, view)

