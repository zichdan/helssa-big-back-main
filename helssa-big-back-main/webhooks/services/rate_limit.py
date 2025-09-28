"""
سرویس محدودسازی نرخ درخواست‌ها برای وب‌هوک‌ها
"""

from __future__ import annotations

from dataclasses import dataclass

from django.core.cache import cache


@dataclass
class RateLimitConfig:
    """
    تنظیمات محدودسازی نرخ
    """

    limit: int
    window_seconds: int


def _make_cache_key(identifier: str, window_seconds: int) -> str:
    return f"webhooks:ratelimit:{identifier}:{window_seconds}"


def allow_request(identifier: str, config: RateLimitConfig) -> bool:
    """
    بررسی مجوز درخواست با استفاده از cache increment

    Args:
        identifier: شناسه یکتا برای کلاینت (مثلا IP یا کلید ارائه‌دهنده)
        config: تنظیمات شامل سقف درخواست و پنجره زمانی

    Returns:
        bool: آیا مجاز است یا خیر
    """
    cache_key = _make_cache_key(identifier, config.window_seconds)
    try:
        current_count = cache.incr(cache_key)
    except ValueError:
        cache.add(cache_key, 1, config.window_seconds)
        current_count = 1

    return current_count <= config.limit