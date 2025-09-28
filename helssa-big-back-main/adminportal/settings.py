"""
تنظیمات پنل ادمین
AdminPortal Settings
"""

from django.conf import settings
import os

# تنظیمات پایه adminportal
ADMINPORTAL_SETTINGS = {
    # تنظیمات کلی
    'ENABLED': getattr(settings, 'ADMINPORTAL_ENABLED', True),
    'DEBUG': getattr(settings, 'ADMINPORTAL_DEBUG', getattr(settings, 'DEBUG', False)),
    
    # تنظیمات احراز هویت
    'REQUIRE_AUTHENTICATION': True,
    'REQUIRE_ADMIN_PROFILE': True,
    'SESSION_TIMEOUT': 3600,  # 1 ساعت
    'MAX_CONCURRENT_SESSIONS': 3,
    
    # تنظیمات Rate Limiting
    'RATE_LIMIT_ENABLED': True,
    'RATE_LIMIT_REQUESTS': 100,  # درخواست در ساعت
    'RATE_LIMIT_WINDOW': 3600,  # ثانیه
    
    # تنظیمات امنیتی
    'SECURITY_ENABLED': True,
    'IP_WHITELIST': getattr(settings, 'ADMINPORTAL_IP_WHITELIST', []),
    'IP_BLACKLIST': getattr(settings, 'ADMINPORTAL_IP_BLACKLIST', []),
    'REQUIRE_HTTPS': getattr(settings, 'ADMINPORTAL_REQUIRE_HTTPS', False),
    'ALLOWED_TIME_RANGE': None,  # مثال: ('08:00', '20:00')
    
    # تنظیمات logging
    'ENABLE_AUDIT_LOG': True,
    'LOG_LEVEL': getattr(settings, 'ADMINPORTAL_LOG_LEVEL', 'INFO'),
    'LOG_FILE': getattr(settings, 'ADMINPORTAL_LOG_FILE', None),
    'LOG_RETENTION_DAYS': 90,
    
    # تنظیمات cache
    'CACHE_ENABLED': True,
    'CACHE_TIMEOUT': 300,  # 5 دقیقه
    'CACHE_PREFIX': 'adminportal',
    
    # تنظیمات پردازش صوت
    'SPEECH_PROCESSING_ENABLED': True,
    'MAX_AUDIO_FILE_SIZE': 10 * 1024 * 1024,  # 10 MB
    'MAX_AUDIO_DURATION': 300,  # 5 دقیقه
    'SUPPORTED_AUDIO_FORMATS': ['wav', 'mp3', 'ogg', 'webm', 'm4a'],
    
    # تنظیمات پردازش متن
    'TEXT_PROCESSING_ENABLED': True,
    'MAX_TEXT_LENGTH': 10000,
    'CONTENT_FILTER_LEVEL': 'medium',  # low, medium, high
    'ENABLE_SENTIMENT_ANALYSIS': True,
    
    # تنظیمات گزارش‌گیری
    'REPORTS_ENABLED': True,
    'MAX_REPORT_ITEMS': 10000,
    'REPORT_EXPORT_FORMATS': ['json', 'csv', 'pdf'],
    'REPORT_CACHE_TIMEOUT': 1800,  # 30 دقیقه
    
    # تنظیمات عملیات دسته‌ای
    'BULK_OPERATIONS_ENABLED': True,
    'MAX_BULK_ITEMS': 1000,
    'BULK_OPERATION_TIMEOUT': 300,  # 5 دقیقه
    
    # تنظیمات مانیتورینگ
    'MONITORING_ENABLED': True,
    'MONITORING_INTERVAL': 60,  # ثانیه
    'METRICS_RETENTION_DAYS': 30,
    'ALERT_THRESHOLDS': {
        'cpu_usage': 80,
        'memory_usage': 85,
        'disk_usage': 90,
        'response_time': 2000,  # میلی‌ثانیه
    },
    
    # تنظیمات پیجینیشن
    'PAGINATION_ENABLED': True,
    'DEFAULT_PAGE_SIZE': 20,
    'MAX_PAGE_SIZE': 100,
    
    # تنظیمات فایل‌ها
    'FILE_UPLOAD_ENABLED': True,
    'MAX_FILE_SIZE': 50 * 1024 * 1024,  # 50 MB
    'ALLOWED_FILE_TYPES': ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'csv'],
    'FILE_STORAGE_PATH': 'adminportal/uploads/',
    
    # تنظیمات ایمیل
    'EMAIL_NOTIFICATIONS_ENABLED': True,
    'NOTIFICATION_EMAIL_FROM': getattr(settings, 'DEFAULT_FROM_EMAIL', 'admin@helssa.com'),
    'ADMIN_EMAIL_LIST': getattr(settings, 'ADMINPORTAL_ADMIN_EMAILS', []),
    
    # تنظیمات SMS
    'SMS_NOTIFICATIONS_ENABLED': True,
    'SMS_PROVIDER': 'kavenegar',
    'SMS_API_KEY': getattr(settings, 'KAVENEGAR_API_KEY', ''),
    'SMS_SENDER': getattr(settings, 'KAVENEGAR_SENDER', '10004346'),
    
    # تنظیمات تسک‌های پس‌زمینه
    'BACKGROUND_TASKS_ENABLED': True,
    'CELERY_ENABLED': hasattr(settings, 'CELERY_BROKER_URL'),
    'TASK_TIMEOUT': 300,  # 5 دقیقه
    'MAX_RETRY_ATTEMPTS': 3,
    
    # تنظیمات API
    'API_ENABLED': True,
    'API_VERSION': 'v1',
    'API_PAGINATION_SIZE': 20,
    'API_THROTTLE_RATE': '100/hour',
    
    # تنظیمات پشتیبان‌گیری
    'BACKUP_ENABLED': True,
    'BACKUP_SCHEDULE': '0 2 * * *',  # هر روز ساعت 2 صبح
    'BACKUP_RETENTION_DAYS': 30,
    'BACKUP_LOCATION': getattr(settings, 'ADMINPORTAL_BACKUP_PATH', '/tmp/adminportal_backups/'),
    
    # تنظیمات توسعه
    'DEVELOPMENT_MODE': getattr(settings, 'DEBUG', False),
    'ENABLE_DEBUG_TOOLBAR': False,
    'MOCK_EXTERNAL_SERVICES': getattr(settings, 'ADMINPORTAL_MOCK_SERVICES', False),
}

# تنظیمات قالب‌ها
ADMINPORTAL_TEMPLATES = {
    'BASE_TEMPLATE': 'adminportal/base.html',
    'DASHBOARD_TEMPLATE': 'adminportal/dashboard.html',
    'LOGIN_TEMPLATE': 'adminportal/login.html',
    'ERROR_TEMPLATE': 'adminportal/error.html',
}

# تنظیمات static files
ADMINPORTAL_STATIC = {
    'CSS_FILES': [
        'adminportal/css/bootstrap.min.css',
        'adminportal/css/admin.css',
        'adminportal/css/dashboard.css',
    ],
    'JS_FILES': [
        'adminportal/js/jquery.min.js',
        'adminportal/js/bootstrap.min.js',
        'adminportal/js/admin.js',
        'adminportal/js/dashboard.js',
    ],
}

# تنظیمات نقش‌ها و دسترسی‌ها
ADMINPORTAL_ROLES = {
    'super_admin': {
        'name': 'ادمین کل',
        'permissions': ['*'],
        'can_create_admins': True,
        'can_delete_admins': True,
        'access_all_features': True,
    },
    'support_admin': {
        'name': 'ادمین پشتیبانی',
        'permissions': [
            'view_users', 'manage_tickets', 'view_reports', 'generate_reports'
        ],
        'can_create_admins': False,
        'can_delete_admins': False,
        'access_all_features': False,
    },
    'content_admin': {
        'name': 'ادمین محتوا',
        'permissions': [
            'view_users', 'content_analysis', 'text_processing', 'voice_processing'
        ],
        'can_create_admins': False,
        'can_delete_admins': False,
        'access_all_features': False,
    },
    'financial_admin': {
        'name': 'ادمین مالی',
        'permissions': [
            'view_users', 'view_reports', 'generate_reports', 'export_reports'
        ],
        'can_create_admins': False,
        'can_delete_admins': False,
        'access_all_features': False,
    },
    'technical_admin': {
        'name': 'ادمین فنی',
        'permissions': [
            'manage_operations', 'system_admin', 'view_system_metrics', 
            'backup_data', 'restore_data'
        ],
        'can_create_admins': False,
        'can_delete_admins': False,
        'access_all_features': False,
    },
}

# تنظیمات اعلان‌ها
ADMINPORTAL_NOTIFICATIONS = {
    'CHANNELS': ['email', 'sms', 'in_app'],
    'EVENTS': {
        'high_priority_ticket': {
            'enabled': True,
            'channels': ['email', 'sms'],
            'recipients': 'support_admins',
        },
        'system_error': {
            'enabled': True,
            'channels': ['email', 'in_app'],
            'recipients': 'technical_admins',
        },
        'security_alert': {
            'enabled': True,
            'channels': ['email', 'sms', 'in_app'],
            'recipients': 'super_admins',
        },
        'failed_operation': {
            'enabled': True,
            'channels': ['email'],
            'recipients': 'technical_admins',
        },
    },
}

# تنظیمات مخصوص محیط‌ها
if hasattr(settings, 'ENVIRONMENT'):
    if settings.ENVIRONMENT == 'production':
        ADMINPORTAL_SETTINGS.update({
            'DEBUG': False,
            'REQUIRE_HTTPS': True,
            'SECURITY_ENABLED': True,
            'LOG_LEVEL': 'WARNING',
            'DEVELOPMENT_MODE': False,
        })
    elif settings.ENVIRONMENT == 'staging':
        ADMINPORTAL_SETTINGS.update({
            'DEBUG': True,
            'MOCK_EXTERNAL_SERVICES': True,
            'LOG_LEVEL': 'INFO',
        })
    elif settings.ENVIRONMENT == 'development':
        ADMINPORTAL_SETTINGS.update({
            'DEBUG': True,
            'DEVELOPMENT_MODE': True,
            'MOCK_EXTERNAL_SERVICES': True,
            'ENABLE_DEBUG_TOOLBAR': True,
            'LOG_LEVEL': 'DEBUG',
        })

# تابع دریافت تنظیمات
def get_adminportal_setting(key, default=None):
    """
    دریافت تنظیم خاص adminportal
    
    Args:
        key: کلید تنظیم
        default: مقدار پیش‌فرض
        
    Returns:
        مقدار تنظیم
    """
    return ADMINPORTAL_SETTINGS.get(key, default)

# تابع بروزرسانی تنظیمات
def update_adminportal_setting(key, value):
    """
    بروزرسانی تنظیم adminportal
    
    Args:
        key: کلید تنظیم
        value: مقدار جدید
    """
    ADMINPORTAL_SETTINGS[key] = value

# تابع اعتبارسنجی تنظیمات
def validate_adminportal_settings():
    """
    اعتبارسنجی تنظیمات adminportal
    
    Returns:
        tuple: (is_valid, errors)
    """
    errors = []
    
    # بررسی تنظیمات ضروری
    required_settings = [
        'ENABLED', 'REQUIRE_AUTHENTICATION', 'SECURITY_ENABLED'
    ]
    
    for setting in required_settings:
        if setting not in ADMINPORTAL_SETTINGS:
            errors.append(f'تنظیم {setting} یافت نشد')
    
    # بررسی تنظیمات عددی
    numeric_settings = {
        'RATE_LIMIT_REQUESTS': (1, 10000),
        'RATE_LIMIT_WINDOW': (60, 86400),
        'SESSION_TIMEOUT': (300, 86400),
        'MAX_AUDIO_FILE_SIZE': (1024, 100*1024*1024),
    }
    
    for setting, (min_val, max_val) in numeric_settings.items():
        value = ADMINPORTAL_SETTINGS.get(setting)
        if value is not None and not (min_val <= value <= max_val):
            errors.append(f'تنظیم {setting} باید بین {min_val} تا {max_val} باشد')
    
    # بررسی فرمت‌های فایل
    allowed_formats = ADMINPORTAL_SETTINGS.get('SUPPORTED_AUDIO_FORMATS', [])
    valid_formats = ['wav', 'mp3', 'ogg', 'webm', 'm4a', 'aac']
    for fmt in allowed_formats:
        if fmt not in valid_formats:
            errors.append(f'فرمت صوتی {fmt} پشتیبانی نمی‌شود')
    
    return len(errors) == 0, errors

# اجرای اعتبارسنجی در زمان import
is_valid, validation_errors = validate_adminportal_settings()
if not is_valid:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"AdminPortal settings validation errors: {validation_errors}")

# تنظیمات logging مخصوص adminportal
ADMINPORTAL_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'adminportal': {
            'format': '[{levelname}] {asctime} {name}: {message}',
            'style': '{',
        },
        'adminportal_detailed': {
            'format': '[{levelname}] {asctime} {name} {pathname}:{lineno}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'adminportal_file': {
            'level': ADMINPORTAL_SETTINGS['LOG_LEVEL'],
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': ADMINPORTAL_SETTINGS.get('LOG_FILE', 'logs/adminportal.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,
            'formatter': 'adminportal_detailed',
        },
        'adminportal_console': {
            'level': ADMINPORTAL_SETTINGS['LOG_LEVEL'],
            'class': 'logging.StreamHandler',
            'formatter': 'adminportal',
        },
    },
    'loggers': {
        'adminportal': {
            'handlers': ['adminportal_file', 'adminportal_console'],
            'level': ADMINPORTAL_SETTINGS['LOG_LEVEL'],
            'propagate': False,
        },
    },
}

# اضافه کردن تنظیمات logging به Django settings
if hasattr(settings, 'LOGGING'):
    settings.LOGGING['formatters'].update(ADMINPORTAL_LOGGING['formatters'])
    settings.LOGGING['handlers'].update(ADMINPORTAL_LOGGING['handlers'])
    settings.LOGGING['loggers'].update(ADMINPORTAL_LOGGING['loggers'])
else:
    settings.LOGGING = ADMINPORTAL_LOGGING