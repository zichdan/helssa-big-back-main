"""
تنظیمات اضافی برای files
Additional Settings for files
"""

# اضافه کردن به INSTALLED_APPS
INSTALLED_APPS += [
    'files.apps.FilesConfig',
]

# Rate limiting اختصاصی اپ فایل‌ها
RATE_LIMIT_FILES = {
    'api_calls': '200/hour',
    'file_uploads': '20/hour',
}

# تنظیمات ذخیره‌سازی فایل‌ها (قابل override از تنظیمات اصلی پروژه)
FILES_STORAGE = {
    'MAX_UPLOAD_SIZE': 10 * 1024 * 1024,  # 10MB
    'ALLOWED_MIME_TYPES': [
        'image/jpeg', 'image/png', 'image/gif',
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ],
}

# Logging
LOGGING['loggers']['files'] = {
    'handlers': ['file', 'console'],
    'level': 'INFO',
    'propagate': False,
}

