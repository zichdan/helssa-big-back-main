"""
تنظیمات اپلیکیشن RBAC
RBAC Application Settings
"""

from django.conf import settings

# تنظیمات کاربر یکپارچه
UNIFIED_USER_SETTINGS = {
    # تنظیمات OTP
    'OTP_LENGTH': getattr(settings, 'OTP_LENGTH', 6),
    'OTP_LIFETIME': getattr(settings, 'OTP_LIFETIME', 120),  # seconds
    'OTP_MAX_ATTEMPTS': getattr(settings, 'OTP_MAX_ATTEMPTS', 3),
    'OTP_RESEND_COOLDOWN': getattr(settings, 'OTP_RESEND_COOLDOWN', 60),  # seconds
    
    # تنظیمات ورود
    'MAX_LOGIN_ATTEMPTS': getattr(settings, 'MAX_LOGIN_ATTEMPTS', 5),
    'LOGIN_LOCKOUT_TIME': getattr(settings, 'LOGIN_LOCKOUT_TIME', 1800),  # 30 minutes
    
    # تنظیمات توکن JWT
    'ACCESS_TOKEN_LIFETIME': getattr(settings, 'ACCESS_TOKEN_LIFETIME', 900),  # 15 minutes
    'REFRESH_TOKEN_LIFETIME': getattr(settings, 'REFRESH_TOKEN_LIFETIME', 604800),  # 7 days
    'JWT_ALGORITHM': getattr(settings, 'JWT_ALGORITHM', 'HS256'),
    
    # تنظیمات نشست
    'SESSION_TIMEOUT': getattr(settings, 'SESSION_TIMEOUT', 7200),  # 2 hours inactivity
    'MAX_SESSIONS_PER_USER': getattr(settings, 'MAX_SESSIONS_PER_USER', 5),
    # aliasهای سازگاری (هر دو نام پشتیبانی شوند)
    'ALLOW_CONCURRENT_SESSIONS': getattr(
        settings, 'ALLOW_CONCURRENT_SESSIONS',
        getattr(settings, 'CONCURRENT_SESSIONS', True)
    ),
    'CONCURRENT_SESSIONS': getattr(
        settings, 'ALLOW_CONCURRENT_SESSIONS',
        getattr(settings, 'CONCURRENT_SESSIONS', True)
    ),
    # تنظیمات امنیتی
    'ENABLE_TWO_FACTOR': getattr(settings, 'ENABLE_TWO_FACTOR', True),
    'PASSWORD_MIN_LENGTH': getattr(settings, 'PASSWORD_MIN_LENGTH', 8),
    'PASSWORD_REQUIRE_SPECIAL': getattr(settings, 'PASSWORD_REQUIRE_SPECIAL', True),
    'PASSWORD_REQUIRE_NUMBER': getattr(settings, 'PASSWORD_REQUIRE_NUMBER', True),
    'PASSWORD_REQUIRE_UPPERCASE': getattr(settings, 'PASSWORD_REQUIRE_UPPERCASE', True),
}

# تنظیمات RBAC
RBAC_SETTINGS = {
    # کش مجوزها
    'PERMISSION_CACHE_TTL': getattr(settings, 'RBAC_PERMISSION_CACHE_TTL', 300),  # 5 minutes
    'ROLE_CACHE_TTL': getattr(settings, 'RBAC_ROLE_CACHE_TTL', 600),  # 10 minutes
    
    # تنظیمات پیش‌فرض
    'DEFAULT_PATIENT_ROLE': 'patient_basic',
    'DEFAULT_DOCTOR_ROLE': 'doctor_basic',
    'DEFAULT_ADMIN_ROLE': 'admin',
    'DEFAULT_STAFF_ROLE': 'staff',
    
    # محدودیت‌ها
    'MAX_ROLES_PER_USER': getattr(settings, 'MAX_ROLES_PER_USER', 10),
    'MAX_PERMISSIONS_PER_ROLE': getattr(settings, 'MAX_PERMISSIONS_PER_ROLE', 100),
}

# نقش‌های پیش‌فرض سیستم
DEFAULT_SYSTEM_ROLES = [
    {
        'name': 'patient_basic',
        'display_name': 'بیمار عادی',
        'description': 'دسترسی‌های پایه برای بیماران',
        'is_system': True,
        'priority': 1,
    },
    {
        'name': 'patient_premium',
        'display_name': 'بیمار ویژه',
        'description': 'دسترسی‌های پیشرفته برای بیماران ویژه',
        'is_system': True,
        'priority': 2,
    },
    {
        'name': 'doctor_basic',
        'display_name': 'پزشک عمومی',
        'description': 'دسترسی‌های پایه برای پزشکان',
        'is_system': True,
        'priority': 10,
    },
    {
        'name': 'doctor_specialist',
        'display_name': 'پزشک متخصص',
        'description': 'دسترسی‌های پیشرفته برای پزشکان متخصص',
        'is_system': True,
        'priority': 11,
    },
    {
        'name': 'admin',
        'display_name': 'مدیر سیستم',
        'description': 'دسترسی کامل به سیستم',
        'is_system': True,
        'priority': 100,
    },
    {
        'name': 'staff',
        'display_name': 'کارمند',
        'description': 'دسترسی‌های اداری',
        'is_system': True,
        'priority': 50,
    },
]

# مجوزهای پیش‌فرض سیستم
DEFAULT_SYSTEM_PERMISSIONS = [
    # مجوزهای بیمار
    {
        'name': 'مشاهده پروفایل شخصی',
        'codename': 'view_own_profile',
        'resource': 'patient_profile',
        'action': 'read',
        'description': 'امکان مشاهده پروفایل شخصی بیمار',
    },
    {
        'name': 'ویرایش پروفایل شخصی',
        'codename': 'edit_own_profile',
        'resource': 'patient_profile',
        'action': 'write',
        'description': 'امکان ویرایش پروفایل شخصی بیمار',
    },
    {
        'name': 'مشاهده سوابق پزشکی',
        'codename': 'view_medical_records',
        'resource': 'medical_record',
        'action': 'read',
        'description': 'امکان مشاهده سوابق پزشکی',
    },
    {
        'name': 'رزرو نوبت',
        'codename': 'book_appointment',
        'resource': 'appointment',
        'action': 'create',
        'description': 'امکان رزرو نوبت ویزیت',
    },
    {
        'name': 'لغو نوبت',
        'codename': 'cancel_appointment',
        'resource': 'appointment',
        'action': 'delete',
        'description': 'امکان لغو نوبت ویزیت',
    },
    
    # مجوزهای پزشک
    {
        'name': 'مشاهده لیست بیماران',
        'codename': 'view_patients_list',
        'resource': 'patient_list',
        'action': 'read',
        'description': 'امکان مشاهده لیست بیماران',
    },
    {
        'name': 'مشاهده پرونده بیمار',
        'codename': 'view_patient_record',
        'resource': 'patient_record',
        'action': 'read',
        'description': 'امکان مشاهده پرونده بیماران',
    },
    {
        'name': 'نوشتن نسخه',
        'codename': 'write_prescription',
        'resource': 'prescription',
        'action': 'create',
        'description': 'امکان نوشتن نسخه برای بیماران',
    },
    {
        'name': 'ویرایش نسخه',
        'codename': 'edit_prescription',
        'resource': 'prescription',
        'action': 'write',
        'description': 'امکان ویرایش نسخه‌های نوشته شده',
    },
    {
        'name': 'ثبت یادداشت SOAP',
        'codename': 'write_soap_note',
        'resource': 'soap_note',
        'action': 'create',
        'description': 'امکان ثبت یادداشت‌های SOAP',
    },
    
    # مجوزهای مدیر
    {
        'name': 'مدیریت کاربران',
        'codename': 'manage_users',
        'resource': 'user',
        'action': 'all',
        'description': 'دسترسی کامل به مدیریت کاربران',
    },
    {
        'name': 'مدیریت نقش‌ها',
        'codename': 'manage_roles',
        'resource': 'role',
        'action': 'all',
        'description': 'دسترسی کامل به مدیریت نقش‌ها',
    },
    {
        'name': 'مشاهده گزارشات',
        'codename': 'view_reports',
        'resource': 'report',
        'action': 'read',
        'description': 'امکان مشاهده گزارشات سیستم',
    },
    {
        'name': 'مشاهده لاگ‌ها',
        'codename': 'view_audit_logs',
        'resource': 'audit_log',
        'action': 'read',
        'description': 'امکان مشاهده لاگ‌های امنیتی',
    },
]

# تنظیمات Rate Limiting
RATE_LIMIT_SETTINGS = {
    '/api/auth/login/': (5, 300),      # 5 requests per 5 minutes
    '/api/auth/register/': (3, 3600),  # 3 requests per hour
    '/api/auth/verify-otp/': (10, 300), # 10 requests per 5 minutes
    '/api/auth/refresh/': (10, 60),    # 10 requests per minute
}

# تنظیمات Audit Log
AUDIT_LOG_SETTINGS = {
    'ENABLE_AUDIT_LOG': getattr(settings, 'ENABLE_AUDIT_LOG', True),
    'LOG_RETENTION_DAYS': getattr(settings, 'AUDIT_LOG_RETENTION_DAYS', 90),
    'LOG_BATCH_SIZE': getattr(settings, 'AUDIT_LOG_BATCH_SIZE', 100),
    'ASYNC_LOGGING': getattr(settings, 'ASYNC_AUDIT_LOGGING', True),
}

# پیام‌های خطا
ERROR_MESSAGES = {
    'INVALID_PHONE': 'شماره موبایل نامعتبر است',
    'INVALID_OTP': 'کد تایید نامعتبر است',
    'OTP_EXPIRED': 'کد تایید منقضی شده است',
    'USER_NOT_FOUND': 'کاربر یافت نشد',
    'USER_INACTIVE': 'حساب کاربری غیرفعال است',
    'USER_LOCKED': 'حساب کاربری قفل شده است',
    'PERMISSION_DENIED': 'شما دسترسی لازم برای این عملیات را ندارید',
    'ROLE_NOT_FOUND': 'نقش مورد نظر یافت نشد',
    'SESSION_EXPIRED': 'نشست شما منقضی شده است',
    'INVALID_TOKEN': 'توکن نامعتبر است',
    'TOKEN_EXPIRED': 'توکن منقضی شده است',
    'RATE_LIMIT_EXCEEDED': 'تعداد درخواست‌ها بیش از حد مجاز است',
    'DUPLICATE_PHONE': 'این شماره موبایل قبلاً ثبت شده است',
    'DUPLICATE_EMAIL': 'این ایمیل قبلاً ثبت شده است',
    'DUPLICATE_NATIONAL_ID': 'این کد ملی قبلاً ثبت شده است',
    'WEAK_PASSWORD': 'رمز عبور ضعیف است',
}

# تنظیمات کاوه‌نگار
KAVENEGAR_SETTINGS = {
    'API_KEY': getattr(settings, 'KAVENEGAR_API_KEY', ''),
    'SENDER': getattr(settings, 'KAVENEGAR_SENDER', ''),
    'OTP_TEMPLATE': getattr(settings, 'KAVENEGAR_OTP_TEMPLATE', 'helssa-otp'),
    'NOTIFICATION_TEMPLATE': getattr(settings, 'KAVENEGAR_NOTIFICATION_TEMPLATE', 'helssa-notify'),
}

# تنظیمات Redis
REDIS_SETTINGS = {
    'HOST': getattr(settings, 'REDIS_HOST', 'localhost'),
    'PORT': getattr(settings, 'REDIS_PORT', 6379),
    'DB': getattr(settings, 'REDIS_DB', 0),
    'PASSWORD': getattr(settings, 'REDIS_PASSWORD', None),
    'KEY_PREFIX': getattr(settings, 'REDIS_KEY_PREFIX', 'helssa:rbac:'),
    'CONNECTION_POOL_SIZE': getattr(settings, 'REDIS_CONNECTION_POOL_SIZE', 10),
}