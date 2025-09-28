"""
نمونه تنظیمات برای استفاده از اپ webhooks
"""

import os

# کلید امضای وب‌هوک‌ها
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'change-me')

# هدر امضا و منبع
WEBHOOK_SIGNATURE_HEADER = 'X-Webhook-Signature'
WEBHOOK_SOURCE_HEADER = 'X-Webhook-Source'

# رویدادهای مجاز (اختیاری)
WEBHOOK_ALLOWED_EVENTS = [
    'payment',
    'lab_results_ready',
    'referral_accepted',
]

# تنظیمات محدودیت نرخ
WEBHOOK_RATE_LIMIT = {
    'limit': 60,            # حداکثر تعداد درخواست
    'window_seconds': 60,   # در بازه ثانیه
}

# نمونه CACHES برای استفاده از ریت‌لیمیت مبتنی بر Redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'helssa_webhooks',
        'TIMEOUT': 300,
    }
}