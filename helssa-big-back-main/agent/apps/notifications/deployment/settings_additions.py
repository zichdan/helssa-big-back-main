"""
تنظیمات اضافی برای notifications
Additional Settings for notifications
"""

# اضافه کردن به INSTALLED_APPS
INSTALLED_APPS += [
    'agent.apps.notifications.app_code.apps.NotificationsConfig',
]

# Rate limiting اختصاصی اپ
RATE_LIMIT_NOTIFICATIONS = {
    'api_calls': '100/minute',
    'ai_requests': '20/minute',
}

# Logging
LOGGING['loggers']['notifications'] = {
    'handlers': ['file', 'console'],
    'level': 'INFO',
    'propagate': False,
}

# تنظیمات داخلی اپ (مطابق دستور کاربر: تنظیمات داخل اپ)
NOTIFICATIONS_SETTINGS = {
    'DEFAULT_PRIORITY': 'normal',
    'MAX_CONTENT_LENGTH_SMS': 1000,
}

