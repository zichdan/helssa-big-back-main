"""
سرویس‌های مرتبط با امضای وب‌هوک
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Optional

from ..conf import get_webhook_secret


def verify_webhook_signature(payload: bytes, signature: Optional[str]) -> bool:
    """
    تایید امضای وب‌هوک با استفاده از HMAC-SHA256

    Args:
        payload: بدنه خام درخواست
        signature: مقدار هدر امضا (X-Webhook-Signature)

    Returns:
        bool: معتبر بودن امضا
    """
    if not signature:
        return False

    secret = get_webhook_secret()
    expected_signature = hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)