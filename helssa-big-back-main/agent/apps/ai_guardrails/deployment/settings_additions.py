"""
تنظیمات اضافی برای ai_guardrails
Additional Settings for ai_guardrails
"""

# اضافه کردن به INSTALLED_APPS
INSTALLED_APPS += [
    'ai_guardrails.apps.AiGuardrailsConfig',
]

# Rate limiting
RATE_LIMIT_AI_GUARDRAILS = {
    'api_calls': '100/minute',
    'ai_requests': '20/minute',
}

# Logging
LOGGING['loggers']['ai_guardrails'] = {
    'handlers': ['file', 'console'],
    'level': 'INFO',
    'propagate': False,
}

# تنظیمات اختصاصی اپ
AI_GUARDRAILS = {
    'DEFAULT_ENFORCEMENT': 'warn',  # warn | block | log
    'SEVERITY_THRESHOLD_INPUT': 50,
    'SEVERITY_THRESHOLD_OUTPUT': 60,
    'MAX_CONTENT_LENGTH': 5000,
}
