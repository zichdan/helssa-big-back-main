"""
تنظیمات مخصوص ماژول Privacy
"""

from django.conf import settings

# تنظیمات پیش‌فرض
PRIVACY_SETTINGS = {
    # کش
    'CACHE_TIMEOUT': 3600,  # یک ساعت
    'CACHE_KEY_PREFIX': 'privacy:',
    
    # پنهان‌سازی
    'DEFAULT_REDACTION_LEVEL': 'standard',
    'ENABLE_LOGGING': True,
    'LOG_REDACTED_VALUES': False,  # برای امنیت، هش ذخیره می‌شود
    
    # رضایت‌ها
    'DEFAULT_CONSENT_EXPIRY_DAYS': 365,  # یک سال
    'REQUIRE_CONSENT_FOR_PROCESSING': True,
    'AUTO_EXPIRE_CONSENTS': True,
    
    # نگهداری داده‌ها
    'DEFAULT_RETENTION_DAYS': 365,
    'AUTO_DELETE_EXPIRED_DATA': False,
    'ARCHIVE_BEFORE_DELETE': True,
    
    # لاگ‌گیری
    'ACCESS_LOG_RETENTION_DAYS': 90,
    'LOG_ALL_ACCESSES': True,
    'LOG_ANONYMOUS_ACCESSES': False,
    
    # اطلاع‌رسانی
    'NOTIFY_EXPIRING_CONSENTS': True,
    'NOTIFICATION_DAYS_BEFORE': 7,
    
    # امنیت
    'ENCRYPT_SENSITIVE_FIELDS': True,
    'HASH_ORIGINAL_VALUES': True,
    'SECURE_DELETE': True,
    
    # API
    'API_RATE_LIMIT': '100/hour',
    'API_REQUIRE_AUTHENTICATION': True,
    'API_ADMIN_ONLY_ENDPOINTS': [
        'statistics',
        'bulk_operations'
    ],
    
    # گزارش‌گیری
    'GENERATE_WEEKLY_REPORTS': True,
    'REPORT_EMAIL_RECIPIENTS': [],
    'INCLUDE_DETAILED_STATS': False,
}


def get_privacy_setting(key, default=None):
    """
    دریافت تنظیم خاص Privacy
    
    Args:
        key: کلید تنظیم
        default: مقدار پیش‌فرض
        
    Returns:
        مقدار تنظیم
    """
    # ابتدا از settings اصلی Django بررسی کن
    django_key = f'PRIVACY_{key}'
    if hasattr(settings, django_key):
        return getattr(settings, django_key)
    
    # سپس از تنظیمات داخلی
    return PRIVACY_SETTINGS.get(key, default)


# تنظیمات خاص برای محیط‌های مختلف
if hasattr(settings, 'DEBUG') and settings.DEBUG:
    # تنظیمات Development
    PRIVACY_SETTINGS.update({
        'CACHE_TIMEOUT': 300,  # 5 دقیقه در development
        'LOG_ALL_ACCESSES': True,
        'INCLUDE_DETAILED_STATS': True,
    })

# تنظیمات برای تست
if hasattr(settings, 'TESTING') and settings.TESTING:
    PRIVACY_SETTINGS.update({
        'CACHE_TIMEOUT': 0,  # بدون کش در تست
        'ENABLE_LOGGING': False,
        'AUTO_EXPIRE_CONSENTS': False,
    })


class PrivacyConfig:
    """
    کلاس پیکربندی Privacy
    """
    
    @classmethod
    def get_redaction_config(cls):
        """دریافت تنظیمات پنهان‌سازی"""
        return {
            'default_level': get_privacy_setting('DEFAULT_REDACTION_LEVEL'),
            'enable_logging': get_privacy_setting('ENABLE_LOGGING'),
            'log_redacted_values': get_privacy_setting('LOG_REDACTED_VALUES'),
            'cache_timeout': get_privacy_setting('CACHE_TIMEOUT'),
        }
    
    @classmethod
    def get_consent_config(cls):
        """دریافت تنظیمات رضایت"""
        return {
            'default_expiry_days': get_privacy_setting('DEFAULT_CONSENT_EXPIRY_DAYS'),
            'require_for_processing': get_privacy_setting('REQUIRE_CONSENT_FOR_PROCESSING'),
            'auto_expire': get_privacy_setting('AUTO_EXPIRE_CONSENTS'),
            'notification_days_before': get_privacy_setting('NOTIFICATION_DAYS_BEFORE'),
        }
    
    @classmethod
    def get_retention_config(cls):
        """دریافت تنظیمات نگهداری"""
        return {
            'default_retention_days': get_privacy_setting('DEFAULT_RETENTION_DAYS'),
            'auto_delete_expired': get_privacy_setting('AUTO_DELETE_EXPIRED_DATA'),
            'archive_before_delete': get_privacy_setting('ARCHIVE_BEFORE_DELETE'),
            'access_log_retention': get_privacy_setting('ACCESS_LOG_RETENTION_DAYS'),
        }
    
    @classmethod
    def get_security_config(cls):
        """دریافت تنظیمات امنیتی"""
        return {
            'encrypt_sensitive_fields': get_privacy_setting('ENCRYPT_SENSITIVE_FIELDS'),
            'hash_original_values': get_privacy_setting('HASH_ORIGINAL_VALUES'),
            'secure_delete': get_privacy_setting('SECURE_DELETE'),
        }
    
    @classmethod
    def get_api_config(cls):
        """دریافت تنظیمات API"""
        return {
            'rate_limit': get_privacy_setting('API_RATE_LIMIT'),
            'require_authentication': get_privacy_setting('API_REQUIRE_AUTHENTICATION'),
            'admin_only_endpoints': get_privacy_setting('API_ADMIN_ONLY_ENDPOINTS'),
        }
    
    @classmethod
    def validate_settings(cls):
        """اعتبارسنجی تنظیمات"""
        errors = []
        
        # بررسی تنظیمات ضروری
        required_settings = [
            'DEFAULT_REDACTION_LEVEL',
            'CACHE_TIMEOUT',
            'DEFAULT_RETENTION_DAYS'
        ]
        
        for setting in required_settings:
            if get_privacy_setting(setting) is None:
                errors.append(f"تنظیم {setting} تعریف نشده است")
        
        # بررسی مقادیر معتبر
        valid_redaction_levels = ['none', 'standard', 'strict']
        redaction_level = get_privacy_setting('DEFAULT_REDACTION_LEVEL')
        if redaction_level not in valid_redaction_levels:
            errors.append(f"سطح پنهان‌سازی {redaction_level} معتبر نیست")
        
        # بررسی مقادیر عددی
        numeric_settings = [
            'CACHE_TIMEOUT',
            'DEFAULT_RETENTION_DAYS',
            'ACCESS_LOG_RETENTION_DAYS'
        ]
        
        for setting in numeric_settings:
            value = get_privacy_setting(setting)
            if not isinstance(value, int) or value < 0:
                errors.append(f"تنظیم {setting} باید عدد مثبت باشد")
        
        return errors


# Export کردن تنظیمات برای استفاده آسان
REDACTION_CONFIG = PrivacyConfig.get_redaction_config()
CONSENT_CONFIG = PrivacyConfig.get_consent_config()
RETENTION_CONFIG = PrivacyConfig.get_retention_config()
SECURITY_CONFIG = PrivacyConfig.get_security_config()
API_CONFIG = PrivacyConfig.get_api_config()