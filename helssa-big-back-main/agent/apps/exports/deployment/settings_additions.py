"""
تنظیمات اضافی برای exports
Additional Settings for exports
"""

# اضافه کردن به INSTALLED_APPS
INSTALLED_APPS += [
    'exports.apps.ExportsConfig',
]

# Rate limiting
RATE_LIMIT_EXPORTS = {
    'api_calls': '100/minute',
    'ai_requests': '20/minute',
}

# Logging
LOGGING['loggers']['exports'] = {
    'handlers': ['file', 'console'],
    'level': 'INFO',
    'propagate': False,
}

