"""
تنظیمات اپ Compliance

این تنظیمات باید در settings اصلی پروژه import و استفاده شوند
"""

# تنظیمات امنیتی
SECURITY_SETTINGS = {
    # تنظیمات MFA
    'MFA': {
        'ISSUER_NAME': 'HELSSA Medical Platform',
        'TOKEN_VALIDITY_WINDOW': 1,  # پنجره اعتبار توکن (دقیقه)
        'BACKUP_CODES_COUNT': 10,
        'QR_CODE_SIZE': 10,
    },
    
    # تنظیمات Rate Limiting
    'RATE_LIMITING': {
        'LOGIN_ATTEMPTS': 5,  # تعداد تلاش‌های مجاز
        'LOGIN_WINDOW': 300,  # پنجره زمانی (ثانیه)
        'API_RATE_LIMIT': '100/hour',  # محدودیت API
    },
    
    # تنظیمات Session
    'SESSION': {
        'TIMEOUT': 1800,  # 30 دقیقه
        'ABSOLUTE_TIMEOUT': 43200,  # 12 ساعت
        'RENEW_THRESHOLD': 300,  # 5 دقیقه قبل از انقضا
    },
    
    # تنظیمات Password
    'PASSWORD': {
        'MIN_LENGTH': 8,
        'REQUIRE_UPPERCASE': True,
        'REQUIRE_LOWERCASE': True,
        'REQUIRE_NUMBERS': True,
        'REQUIRE_SPECIAL': True,
        'HISTORY_COUNT': 5,  # تعداد رمزهای قبلی که نباید تکرار شوند
        'MAX_AGE_DAYS': 90,  # حداکثر عمر رمز عبور
    },
}

# تنظیمات HIPAA
HIPAA_SETTINGS = {
    'AUDIT_LOG_RETENTION_DAYS': 2555,  # 7 سال
    'PHI_ENCRYPTION_REQUIRED': True,
    'ACCESS_LOG_REQUIRED': True,
    'MINIMUM_NECESSARY_RULE': True,
    'BREACH_NOTIFICATION_HOURS': 72,
}

# تنظیمات رمزنگاری
ENCRYPTION_SETTINGS = {
    'ALGORITHM': 'AES-256-GCM',
    'KEY_ROTATION_DAYS': 90,
    'BACKUP_ENCRYPTION': True,
    'DATABASE_ENCRYPTION': True,
    'FILE_ENCRYPTION': True,
}

# تنظیمات Audit
AUDIT_SETTINGS = {
    'ENABLED': True,
    'LOG_ALL_ACTIONS': True,
    'LOG_FAILED_ATTEMPTS': True,
    'ARCHIVE_AFTER_DAYS': 365,
    'COMPRESSION': True,
    'REAL_TIME_ALERTS': True,
}

# تنظیمات حوادث امنیتی
INCIDENT_SETTINGS = {
    'AUTO_RESPONSE_ENABLED': True,
    'NOTIFICATION_CHANNELS': ['email', 'sms', 'dashboard'],
    'ESCALATION_THRESHOLDS': {
        'low': 24,  # ساعت
        'medium': 12,
        'high': 4,
        'critical': 1,
    },
    'INVESTIGATION_TIMEOUT': 48,  # ساعت
}

# لیست IP های مجاز (Whitelist)
ALLOWED_IPS = []

# لیست IP های مسدود (Blacklist)
BLOCKED_IPS = []

# تنظیمات CORS برای امنیت
CORS_SETTINGS = {
    'ALLOWED_ORIGINS': [
        'https://helssa.ir',
        'https://www.helssa.ir',
    ],
    'ALLOWED_METHODS': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    'ALLOWED_HEADERS': ['Authorization', 'Content-Type', 'X-Requested-With'],
    'EXPOSE_HEADERS': ['Content-Length', 'X-Request-ID'],
    'MAX_AGE': 86400,  # 24 ساعت
    'ALLOW_CREDENTIALS': True,
}

# Security Headers
SECURITY_HEADERS = {
    'X_FRAME_OPTIONS': 'DENY',
    'X_CONTENT_TYPE_OPTIONS': 'nosniff',
    'X_XSS_PROTECTION': '1; mode=block',
    'STRICT_TRANSPORT_SECURITY': 'max-age=31536000; includeSubDomains',
    'REFERRER_POLICY': 'strict-origin-when-cross-origin',
    'CONTENT_SECURITY_POLICY': "default-src 'self'; script-src 'self' 'unsafe-inline';",
    'PERMISSIONS_POLICY': "geolocation=(), microphone=(), camera=()",
}

# تنظیمات پشتیبان‌گیری امن
BACKUP_SETTINGS = {
    'ENABLED': True,
    'SCHEDULE': '0 2 * * *',  # هر روز ساعت 2 صبح
    'RETENTION_DAYS': 30,
    'ENCRYPTION_REQUIRED': True,
    'OFFSITE_BACKUP': True,
    'TEST_RESTORE_FREQUENCY': 7,  # هر 7 روز یکبار
}

# تنظیمات مانیتورینگ امنیتی
MONITORING_SETTINGS = {
    'ENABLED': True,
    'ALERT_CHANNELS': ['email', 'sms'],
    'METRICS': [
        'failed_login_attempts',
        'unauthorized_access',
        'suspicious_patterns',
        'high_risk_scores',
        'compliance_violations',
    ],
    'DASHBOARD_REFRESH_SECONDS': 30,
}

# مجوزهای سیستم
SYSTEM_PERMISSIONS = {
    # مجوزهای بیمار
    'PATIENT': [
        'view_own_records',
        'book_appointment',
        'chat_with_ai',
        'view_prescriptions',
        'update_profile',
    ],
    
    # مجوزهای پزشک
    'DOCTOR': [
        'view_patient_records',
        'write_prescription',
        'create_soap_report',
        'order_tests',
        'view_test_results',
        'create_referral',
    ],
    
    # مجوزهای ادمین
    'ADMIN': [
        'manage_users',
        'view_all_records',
        'system_settings',
        'view_audit_logs',
        'manage_roles',
        'manage_security',
    ],
    
    # مجوزهای پرستار
    'NURSE': [
        'view_patient_records',
        'update_vitals',
        'view_prescriptions',
        'create_notes',
    ],
    
    # مجوزهای کارمند
    'STAFF': [
        'manage_appointments',
        'view_basic_info',
        'create_bills',
        'process_payments',
    ],
}