"""
هسته API Ingress برای اپلیکیشن
API Ingress Core for Application
"""

from app_standards.four_cores import APIIngressCore as BaseAPIIngressCore

class APIIngress(BaseAPIIngressCore):
    """Facade مخصوص این اپ؛ آماده برای هوک‌ کردن ولیدیشن/لاگ/ریت‌لیمیت."""
    pass

__all__ = ["APIIngress"]
