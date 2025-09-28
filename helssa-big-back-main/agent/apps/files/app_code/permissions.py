"""
دسترسی‌های سفارشی برای اپ فایل‌ها
Custom permissions for Files app
"""

from app_standards.views.permissions import BasePermission


class IsFileOwner(BasePermission):
    """
    فقط مالک فایل اجازه عملیات تخریبی دارد
    """

    message = 'دسترسی فقط برای مالک فایل مجاز است'

    def has_object_permission(self, request, view, obj):
        return getattr(obj, 'created_by', None) == getattr(request, 'user', None)

