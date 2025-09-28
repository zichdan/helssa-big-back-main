"""
تنظیمات اختصاصی اپ SOAP

توجه: مطابق دستور کار، تنظیمات در اپ قرار می‌گیرد و نیازی به تغییر
آدرس‌های مرجع ریشه پروژه نیست.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Dict, Any


def get_app_settings() -> Dict[str, Any]:
    """
    دریافت تنظیمات اختصاصی اپ SOAP

    Returns:
        dict: تنظیمات اپ شامل نرخ محدودیت، تنظیمات JWT برای استفاده در ویوها،
        و مسیر قالب‌ها.
    """
    return {
        'RATE_LIMIT': {
            'generate_soap': {
                'limit': 20,
                'window': 3600,
            },
        },
        'TEMPLATES': {
            'soap_report': 'soap/templates/soap_report.html',
        },
        'JWT': {
            'ACCESS_LIFETIME': timedelta(minutes=15),
            'REFRESH_LIFETIME': timedelta(days=1),
        },
    }