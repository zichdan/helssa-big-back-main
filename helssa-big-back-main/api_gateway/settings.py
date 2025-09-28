"""
تنظیمات اپ API Gateway
"""
import os
from django.conf import settings

# تنظیمات اصلی API Gateway
API_GATEWAY_SETTINGS = {
    # نسخه
    'VERSION': '1.0.0',
    
    # Rate Limiting
    'RATE_LIMIT_ENABLED': True,
    'DEFAULT_RATE_LIMIT': 100,  # درخواست در ساعت
    'RATE_LIMIT_WINDOW_MINUTES': 60,
    
    # حداکثر اندازه درخواست‌ها
    'MAX_REQUEST_SIZE': 10 * 1024 * 1024,  # 10MB
    'MAX_TEXT_LENGTH': 50000,  # کاراکتر
    'MAX_AUDIO_SIZE': 50 * 1024 * 1024,  # 50MB
    
    # تنظیمات پردازش
    'MAX_CONCURRENT_TASKS': 10,
    'TASK_TIMEOUT': 300,  # ثانیه
    'DEFAULT_PROCESSOR_TIMEOUT': 30,  # ثانیه
    
    # زبان‌های پشتیبانی شده
    'SUPPORTED_LANGUAGES': ['fa', 'en', 'ar'],
    'DEFAULT_LANGUAGE': 'fa',
    
    # فرمت‌های صوتی پشتیبانی شده
    'SUPPORTED_AUDIO_FORMATS': ['wav', 'mp3', 'ogg', 'flac', 'm4a'],
    'DEFAULT_AUDIO_FORMAT': 'wav',
    
    # تنظیمات cache
    'CACHE_TIMEOUT': 3600,  # ثانیه
    'CACHE_KEY_PREFIX': 'api_gateway:',
    
    # تنظیمات logging
    'LOG_REQUESTS': True,
    'LOG_RESPONSES': True,
    'LOG_SENSITIVE_DATA': False,
    'LOG_RETENTION_DAYS': 30,
    
    # تنظیمات امنیتی
    'ENABLE_REQUEST_VALIDATION': True,
    'ENABLE_RESPONSE_SANITIZATION': True,
    'ALLOWED_HOSTS_STRICT': False,
    
    # تنظیمات monitoring
    'ENABLE_METRICS': True,
    'METRICS_RETENTION_DAYS': 7,
    'HEALTH_CHECK_TIMEOUT': 5,  # ثانیه
    
    # تنظیمات workflow
    'MAX_WORKFLOW_STEPS': 50,
    'WORKFLOW_TIMEOUT': 1800,  # 30 دقیقه
    'AUTO_CLEANUP_WORKFLOWS': True,
    'WORKFLOW_RETENTION_DAYS': 30,
}

# تنظیمات cores
CORE_SETTINGS = {
    'API_INGRESS': {
        'ENABLED': True,
        'VALIDATE_CONTENT_TYPE': True,
        'MAX_HEADER_SIZE': 8192,  # بایت
        'ALLOWED_METHODS': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
    },
    
    'TEXT_PROCESSOR': {
        'ENABLED': True,
        'DEFAULT_LANGUAGE': 'fa',
        'ENABLE_SENTIMENT_ANALYSIS': True,
        'ENABLE_ENTITY_EXTRACTION': True,
        'ENABLE_KEYWORD_EXTRACTION': True,
        'MAX_SUMMARY_LENGTH': 500,
    },
    
    'SPEECH_PROCESSOR': {
        'ENABLED': True,
        'DEFAULT_LANGUAGE': 'fa',
        'ENABLE_NOISE_REDUCTION': False,
        'DEFAULT_SAMPLE_RATE': 22050,
        'MAX_AUDIO_DURATION': 600,  # ثانیه
    },
    
    'ORCHESTRATOR': {
        'ENABLED': True,
        'MAX_PARALLEL_WORKFLOWS': 5,
        'DEFAULT_PRIORITY': 3,
        'ENABLE_WORKFLOW_RECOVERY': True,
    }
}

# تنظیمات پیام‌ها
MESSAGES = {
    'fa': {
        'REQUEST_PROCESSED': 'درخواست با موفقیت پردازش شد',
        'VALIDATION_FAILED': 'اعتبارسنجی ناموفق',
        'RATE_LIMIT_EXCEEDED': 'تعداد درخواست‌ها بیش از حد مجاز',
        'INTERNAL_ERROR': 'خطای داخلی سرور',
        'WORKFLOW_STARTED': 'فرآیند کاری شروع شد',
        'WORKFLOW_COMPLETED': 'فرآیند کاری تکمیل شد',
        'WORKFLOW_FAILED': 'فرآیند کاری ناموفق',
    },
    'en': {
        'REQUEST_PROCESSED': 'Request processed successfully',
        'VALIDATION_FAILED': 'Validation failed',
        'RATE_LIMIT_EXCEEDED': 'Rate limit exceeded',
        'INTERNAL_ERROR': 'Internal server error',
        'WORKFLOW_STARTED': 'Workflow started',
        'WORKFLOW_COMPLETED': 'Workflow completed',
        'WORKFLOW_FAILED': 'Workflow failed',
    }
}

# تنظیمات خطا
ERROR_CODES = {
    'VALIDATION_ERROR': 'GW001',
    'RATE_LIMIT_ERROR': 'GW002',
    'PROCESSING_ERROR': 'GW003',
    'WORKFLOW_ERROR': 'GW004',
    'AUTHENTICATION_ERROR': 'GW005',
    'AUTHORIZATION_ERROR': 'GW006',
    'INTERNAL_ERROR': 'GW999',
}

# تنظیمات performance
PERFORMANCE_SETTINGS = {
    'ENABLE_ASYNC_PROCESSING': True,
    'CONNECTION_POOL_SIZE': 10,
    'REQUEST_TIMEOUT': 30,
    'RESPONSE_TIMEOUT': 30,
    'RETRY_ATTEMPTS': 3,
    'RETRY_DELAY': 1,  # ثانیه
}

# تنظیمات integration
INTEGRATION_SETTINGS = {
    # سرویس‌های خارجی
    'KAVENEGAR_API_KEY': os.getenv('KAVENEGAR_API_KEY', ''),
    'TALKBOT_API': os.getenv('TALKBOT_API', ''),
    
    # تنظیمات STT/TTS
    'STT_SERVICE_URL': os.getenv('STT_SERVICE_URL', ''),
    'TTS_SERVICE_URL': os.getenv('TTS_SERVICE_URL', ''),
    
    # تنظیمات AI
    'AI_SERVICE_URL': os.getenv('AI_SERVICE_URL', ''),
    'AI_API_KEY': os.getenv('AI_API_KEY', ''),
}

# تنظیمات development/production
if getattr(settings, 'DEBUG', False):
    # تنظیمات development
    API_GATEWAY_SETTINGS.update({
        'RATE_LIMIT_ENABLED': False,
        'LOG_SENSITIVE_DATA': True,
        'HEALTH_CHECK_TIMEOUT': 10,
    })
    
    PERFORMANCE_SETTINGS.update({
        'REQUEST_TIMEOUT': 60,
        'RESPONSE_TIMEOUT': 60,
    })
else:
    # تنظیمات production
    API_GATEWAY_SETTINGS.update({
        'RATE_LIMIT_ENABLED': True,
        'LOG_SENSITIVE_DATA': False,
        'ALLOWED_HOSTS_STRICT': True,
    })

# ترکیب تنظیمات با settings اصلی Django
def apply_settings():
    """
    اعمال تنظیمات API Gateway به settings Django
    """
    # اضافه کردن به INSTALLED_APPS
    if 'api_gateway' not in settings.INSTALLED_APPS:
        settings.INSTALLED_APPS.append('api_gateway')
    
    # تنظیمات logging
    if not hasattr(settings, 'LOGGING'):
        settings.LOGGING = {}
    
    # اضافه کردن logger برای API Gateway
    if 'loggers' not in settings.LOGGING:
        settings.LOGGING['loggers'] = {}
    
    settings.LOGGING['loggers']['api_gateway'] = {
        'handlers': ['console', 'file'] if 'file' in settings.LOGGING.get('handlers', {}) else ['console'],
        'level': 'INFO',
        'propagate': False,
    }
    
    # تنظیمات cache
    if API_GATEWAY_SETTINGS['RATE_LIMIT_ENABLED']:
        if not hasattr(settings, 'CACHES'):
            settings.CACHES = {
                'default': {
                    'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                    'LOCATION': 'api-gateway-cache',
                }
            }
    
    # اضافه کردن تنظیمات به settings
    for key, value in API_GATEWAY_SETTINGS.items():
        setattr(settings, f'API_GATEWAY_{key}', value)
    
    for core_name, core_settings in CORE_SETTINGS.items():
        for key, value in core_settings.items():
            setattr(settings, f'API_GATEWAY_{core_name}_{key}', value)
    
    # تنظیمات middleware
    if not hasattr(settings, 'MIDDLEWARE'):
        settings.MIDDLEWARE = []
    
    # اضافه کردن middleware های مورد نیاز
    required_middleware = [
        'corsheaders.middleware.CorsMiddleware',
        'django.middleware.security.SecurityMiddleware',
        'django.middleware.common.CommonMiddleware',
    ]
    
    for middleware in required_middleware:
        if middleware not in settings.MIDDLEWARE:
            settings.MIDDLEWARE.insert(0, middleware)

# Helper functions
def get_setting(key: str, default=None):
    """
    دریافت تنظیمات API Gateway
    
    Args:
        key: کلید تنظیمات
        default: مقدار پیش‌فرض
        
    Returns:
        مقدار تنظیمات
    """
    return API_GATEWAY_SETTINGS.get(key, default)

def get_core_setting(core_name: str, key: str, default=None):
    """
    دریافت تنظیمات یک core خاص
    
    Args:
        core_name: نام core
        key: کلید تنظیمات
        default: مقدار پیش‌فرض
        
    Returns:
        مقدار تنظیمات
    """
    return CORE_SETTINGS.get(core_name, {}).get(key, default)

def get_message(key: str, language: str = 'fa'):
    """
    دریافت پیام بر اساس زبان
    
    Args:
        key: کلید پیام
        language: زبان
        
    Returns:
        متن پیام
    """
    return MESSAGES.get(language, {}).get(key, key)

def is_feature_enabled(feature: str) -> bool:
    """
    بررسی فعال بودن یک ویژگی
    
    Args:
        feature: نام ویژگی
        
    Returns:
        bool: فعال بودن ویژگی
    """
    return API_GATEWAY_SETTINGS.get(f'ENABLE_{feature.upper()}', False)

# اعمال تنظیمات هنگام import
if hasattr(settings, 'INSTALLED_APPS'):
    apply_settings()