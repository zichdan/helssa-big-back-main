"""
تنظیمات اضافی برای ai_helsabrain
Additional Settings for ai_helsabrain
"""

# اضافه کردن به INSTALLED_APPS
INSTALLED_APPS += [
    'ai_helsabrain.apps.AiHelsabrainConfig',
]

# Rate limiting
RATE_LIMIT_AI_HELSABRAIN = {
    'api_calls': '100/minute',
    'ai_requests': '20/minute',
}

# Logging
LOGGING['loggers']['ai_helsabrain'] = {
    'handlers': ['file', 'console'],
    'level': 'INFO',
    'propagate': False,
}
