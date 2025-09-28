from django.test import TestCase, override_settings
from django.core.cache import cache

from webhooks.services.rate_limit import RateLimitConfig, allow_request


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class RateLimitTests(TestCase):
    """
    تست‌های محدودسازی نرخ
    """

    def setUp(self):
        cache.clear()

    def test_allow_within_limit(self):
        cfg = RateLimitConfig(limit=3, window_seconds=60)
        self.assertTrue(allow_request('client-a', cfg))
        self.assertTrue(allow_request('client-a', cfg))
        self.assertTrue(allow_request('client-a', cfg))

    def test_block_over_limit(self):
        cfg = RateLimitConfig(limit=2, window_seconds=60)
        self.assertTrue(allow_request('client-b', cfg))
        self.assertTrue(allow_request('client-b', cfg))
        self.assertFalse(allow_request('client-b', cfg))