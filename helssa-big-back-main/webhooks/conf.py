"""
تنظیمات اختصاصی اپ webhooks

بر اساس مستندات، تنظیمات باید داخل خود اپ نگهداری شود. این ماژول با استفاده از
مقادیر تنظیمات پروژه (در صورت وجود) و مقادیر پیش‌فرض، تنظیمات لازم را فراهم می‌کند.
"""

from __future__ import annotations

import os
from typing import List

from django.conf import settings


DEFAULT_WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'change-me')
DEFAULT_ALLOWED_EVENTS: List[str] = []
DEFAULT_SIGNATURE_HEADER = 'X-Webhook-Signature'
DEFAULT_RATE_LIMIT = {
    'limit': 60,            # حداکثر ۶۰ درخواست
    'window_seconds': 60,   # در ۶۰ ثانیه
}
DEFAULT_SOURCE_ID_HEADER = 'X-Webhook-Source'


def get_webhook_secret() -> str:
    """
    دریافت کلید امضای وب‌هوک
    """
    return getattr(settings, 'WEBHOOK_SECRET', DEFAULT_WEBHOOK_SECRET)


def get_allowed_events() -> List[str]:
    """
    لیست رویدادهای مجاز
    """
    return getattr(settings, 'WEBHOOK_ALLOWED_EVENTS', DEFAULT_ALLOWED_EVENTS)


def get_signature_header_name() -> str:
    """
    نام هدر امضاء
    """
    return getattr(settings, 'WEBHOOK_SIGNATURE_HEADER', DEFAULT_SIGNATURE_HEADER)


def get_source_id_header_name() -> str:
    """
    نام هدر مشخص‌کننده منبع/شناسه فرستنده
    """
    return getattr(settings, 'WEBHOOK_SOURCE_HEADER', DEFAULT_SOURCE_ID_HEADER)


def get_rate_limit_config() -> dict:
    """
    تنظیمات ریت‌لیمیت
    """
    config = getattr(settings, 'WEBHOOK_RATE_LIMIT', DEFAULT_RATE_LIMIT)
    limit = int(config.get('limit', DEFAULT_RATE_LIMIT['limit']))
    window_seconds = int(config.get('window_seconds', DEFAULT_RATE_LIMIT['window_seconds']))
    return {'limit': limit, 'window_seconds': window_seconds}