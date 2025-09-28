"""
هسته API Ingress اختصاصی اپ فایل‌ها (در صورت نیاز به افزونه‌های خاص)
Files App API Ingress Core (extension point)
"""

from app_standards.four_cores import APIIngressCore


class FilesAPIIngress(APIIngressCore):
    """
    افزونه‌ای روی هسته استاندارد برای اعتبارسنجی/Rate Limit اختصاصی
    """

    pass

