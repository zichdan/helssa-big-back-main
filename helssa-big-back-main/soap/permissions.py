from __future__ import annotations

"""
مجوزهای محلی اپ SOAP
"""

from typing import Any
from rest_framework.permissions import BasePermission


class IsDoctor(BasePermission):
    """
    دسترسی فقط برای پزشکان
    """
    message = 'دسترسی فقط برای پزشکان'

    def has_permission(self, request: Any, view: Any) -> bool:
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            self.message = 'احراز هویت الزامی است'
            return False
        if not getattr(user, 'is_active', True):
            self.message = 'حساب کاربری غیرفعال است'
            return False
        return getattr(user, 'user_type', None) == 'doctor'