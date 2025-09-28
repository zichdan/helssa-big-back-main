"""
نمونه تنظیمات برای استفاده از auth_otp
Sample Settings for auth_otp Usage
"""

# این تنظیمات را به settings.py پروژه خود اضافه کنید

from datetime import timedelta
import os

# ==================================
# تنظیمات کاوه‌نگار
# ==================================

KAVENEGAR_API_KEY = os.environ.get('KAVENEGAR_API_KEY', 'your-api-key-here')
KAVENEGAR_SENDER = os.environ.get('KAVENEGAR_SENDER', '10004346')  # شماره ارسال
KAVENEGAR_OTP_TEMPLATE = os.environ.get('KAVENEGAR_OTP_TEMPLATE', 'verify')  # نام قالب تأیید

# ==================================
# تنظیمات JWT
# ==================================

SIMPLE_JWT = {
    # زمان اعتبار توکن‌ها
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    
    # Rotation و Blacklist
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    
    # الگوریتم و کلیدها
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    
    # Header types
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    
    # Token classes
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    
    # Claims
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# ==================================
# تنظیمات REST Framework
# ==================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
}

# ==================================
# تنظیمات کش (برای Rate Limiting)
# ==================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'helssa_otp',
        'TIMEOUT': 300,  # 5 دقیقه
    }
}

# ==================================
# تنظیمات لاگینگ
# ==================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/auth_otp.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'auth_otp': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ==================================
# تنظیمات OTP سفارشی
# ==================================

# محدودیت‌های نرخ OTP
OTP_RATE_LIMITS = {
    'minute': 1,    # حداکثر 1 درخواست در دقیقه
    'hour': 5,      # حداکثر 5 درخواست در ساعت
    'day': 10,      # حداکثر 10 درخواست در روز
    'block_duration': 24,  # مدت مسدودیت به ساعت
    'max_failed_attempts': 10,  # حداکثر تلاش ناموفق
}

# تنظیمات OTP
OTP_SETTINGS = {
    'code_length': 6,           # طول کد OTP
    'validity_minutes': 3,      # مدت اعتبار به دقیقه
    'max_verify_attempts': 3,   # حداکثر تلاش برای تأیید
}

# ==================================
# تنظیمات Celery (برای تسک‌های پاکسازی)
# ==================================

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'cleanup-expired-otp': {
        'task': 'auth_otp.tasks.cleanup_expired_otp',
        'schedule': crontab(hour=3, minute=0),  # هر روز ساعت 3 صبح
    },
    'cleanup-expired-tokens': {
        'task': 'auth_otp.tasks.cleanup_expired_tokens',
        'schedule': crontab(hour=3, minute=30),  # هر روز ساعت 3:30 صبح
    },
}

# ==================================
# Middleware
# ==================================

MIDDLEWARE = [
    # ... سایر middleware ها
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # افزودن CORS برای API
    'corsheaders.middleware.CorsMiddleware',
]

# ==================================
# CORS Settings
# ==================================

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # دامنه‌های production را اضافه کنید
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]