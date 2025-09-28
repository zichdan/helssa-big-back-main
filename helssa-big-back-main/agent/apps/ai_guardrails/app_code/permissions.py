"""
دسترسی‌های سفارشی اپلیکیشن
Custom Permissions
"""

from app_standards.views.permissions import BasePermission

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

class IsGuardrailsAuthenticated(BasePermission):
    """
    فقط کاربر لاگین‌کرده اجازه دسترسی داشته باشه.
    """
    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        return bool(user and getattr(user, "is_authenticated", False))


class IsGuardrailsAdminOrReadOnly(BasePermission):
    """
    GET/HEAD/OPTIONS آزاد، بقیه فقط برای ادمین.
    """
    def has_permission(self, request, view) -> bool:
        if request.method in SAFE_METHODS:
            return True
        user = getattr(request, "user", None)
        return bool(user and getattr(user, "is_staff", False))

__all__ = ["IsGuardrailsAuthenticated", "IsGuardrailsAdminOrReadOnly"]
