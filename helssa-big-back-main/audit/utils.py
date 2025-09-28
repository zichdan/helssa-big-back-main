"""
ابزارهای HMAC برای امضا و اعتبارسنجی داده‌ها طبق مستندات
"""
from __future__ import annotations

import hmac
import hashlib
from typing import Optional

from django.conf import settings

from . import settings as audit_settings


def generate_hmac_signature(message: bytes, secret: Optional[str] = None) -> str:
    """
    تولید امضای HMAC-SHA256 برای پیام داده‌شده

    Args:
        message: داده خام
        secret: کلید محرمانه؛ در صورت None از AUDIT_HMAC_SECRET_KEY استفاده می‌شود

    Returns:
        str: امضا به صورت hex
    """
    key = (secret or audit_settings.AUDIT_HMAC_SECRET_KEY).encode()
    digest = hmac.new(key, message, getattr(hashlib, audit_settings.AUDIT_HMAC_ALGORITHM))
    return digest.hexdigest()


def verify_hmac_signature(message: bytes, signature: str, secret: Optional[str] = None) -> bool:
    """
    اعتبارسنجی امضای HMAC برای پیام داده‌شده
    """
    expected = generate_hmac_signature(message, secret)
    return hmac.compare_digest(expected, signature)

