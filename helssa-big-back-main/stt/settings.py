"""
تنظیمات اپ STT
"""
from django.conf import settings

# تنظیمات Whisper
WHISPER_SETTINGS = {
    # مدل پیش‌فرض
    'DEFAULT_MODEL': getattr(settings, 'STT_DEFAULT_MODEL', 'base'),
    
    # مدل‌های مجاز
    'ALLOWED_MODELS': getattr(settings, 'STT_ALLOWED_MODELS', [
        'tiny', 'base', 'small', 'medium', 'large'
    ]),
    
    # محل ذخیره مدل‌ها
    'MODEL_CACHE_DIR': getattr(settings, 'STT_MODEL_CACHE_DIR', '/tmp/whisper_models'),
    
    # Device (cuda/cpu)
    'DEVICE': getattr(settings, 'STT_DEVICE', 'auto'),  # auto will check CUDA availability
}

# تنظیمات فایل صوتی
AUDIO_SETTINGS = {
    # حداکثر حجم فایل (بایت)
    'MAX_FILE_SIZE': getattr(settings, 'STT_MAX_FILE_SIZE', 52428800),  # 50MB
    
    # حداکثر مدت زمان (ثانیه)
    'MAX_DURATION': getattr(settings, 'STT_MAX_DURATION', 600),  # 10 minutes
    
    # فرمت‌های مجاز
    'ALLOWED_FORMATS': getattr(settings, 'STT_ALLOWED_FORMATS', [
        'mp3', 'wav', 'ogg', 'm4a', 'webm', 'mp4', 'mpeg', 'mpga'
    ]),
    
    # Sample rate برای Whisper
    'TARGET_SAMPLE_RATE': 16000,
}

# تنظیمات Rate Limiting
RATE_LIMIT_SETTINGS = {
    # پنجره زمانی (ثانیه)
    'WINDOW': getattr(settings, 'STT_RATE_LIMIT_WINDOW', 3600),  # 1 hour
    
    # حداکثر درخواست برای هر نوع کاربر
    'MAX_REQUESTS': {
        'patient': getattr(settings, 'STT_RATE_LIMIT_PATIENT', 20),
        'doctor': getattr(settings, 'STT_RATE_LIMIT_DOCTOR', 50),
        'staff': getattr(settings, 'STT_RATE_LIMIT_STAFF', 100),
    }
}

# تنظیمات کش
CACHE_SETTINGS = {
    # فعال بودن کش نتایج
    'ENABLED': getattr(settings, 'STT_CACHE_ENABLED', True),
    
    # مدت زمان نگهداری در کش (ثانیه)
    'TIMEOUT': getattr(settings, 'STT_CACHE_TIMEOUT', 86400),  # 24 hours
    
    # Prefix برای کلیدهای کش
    'KEY_PREFIX': getattr(settings, 'STT_CACHE_PREFIX', 'stt_result_'),
}

# تنظیمات کیفیت
QUALITY_SETTINGS = {
    # آستانه اطمینان برای نیاز به بررسی
    'REVIEW_CONFIDENCE_THRESHOLD': getattr(settings, 'STT_REVIEW_CONFIDENCE_THRESHOLD', 0.5),
    
    # آستانه کیفیت صوت
    'AUDIO_QUALITY_THRESHOLD': getattr(settings, 'STT_AUDIO_QUALITY_THRESHOLD', 0.3),
    
    # فعال بودن تصحیح خودکار اصطلاحات پزشکی
    'AUTO_CORRECT_MEDICAL_TERMS': getattr(settings, 'STT_AUTO_CORRECT_MEDICAL_TERMS', True),
}

# تنظیمات Celery
CELERY_SETTINGS = {
    # نام صف پردازش
    'QUEUE_NAME': getattr(settings, 'STT_CELERY_QUEUE', 'stt_processing'),
    
    # اولویت وظایف
    'TASK_PRIORITY': {
        'doctor': 9,  # بالاترین اولویت
        'patient': 5,  # اولویت متوسط
        'default': 1,  # اولویت پایین
    },
    
    # Retry settings
    'MAX_RETRIES': getattr(settings, 'STT_MAX_RETRIES', 3),
    'RETRY_DELAY': getattr(settings, 'STT_RETRY_DELAY', 60),  # seconds
}

# تنظیمات ذخیره‌سازی
STORAGE_SETTINGS = {
    # محل ذخیره فایل‌های صوتی
    'AUDIO_UPLOAD_PATH': getattr(settings, 'STT_AUDIO_UPLOAD_PATH', 'stt/audio/%Y/%m/%d/'),
    
    # استفاده از S3/MinIO
    'USE_S3': getattr(settings, 'STT_USE_S3', False),
    
    # Bucket name برای S3
    'S3_BUCKET': getattr(settings, 'STT_S3_BUCKET', 'helssa-stt-audio'),
}

# تنظیمات پردازش متن
TEXT_PROCESSING_SETTINGS = {
    # فعال بودن پردازش متن
    'ENABLED': getattr(settings, 'STT_TEXT_PROCESSING_ENABLED', True),
    
    # دیکشنری اصطلاحات پزشکی
    'MEDICAL_DICTIONARY_PATH': getattr(
        settings, 
        'STT_MEDICAL_DICTIONARY_PATH',
        'stt/data/medical_terms.json'
    ),
    
    # Context types
    'CONTEXT_TYPES': {
        'general': {
            'name': 'عمومی',
            'medical_terms': False,
            'auto_punctuation': True,
        },
        'medical': {
            'name': 'پزشکی',
            'medical_terms': True,
            'auto_punctuation': True,
        },
        'prescription': {
            'name': 'نسخه',
            'medical_terms': True,
            'auto_punctuation': True,
            'extract_medications': True,
        },
        'symptoms': {
            'name': 'علائم',
            'medical_terms': True,
            'auto_punctuation': True,
            'extract_symptoms': True,
        },
    }
}

# تنظیمات لاگ
LOGGING_SETTINGS = {
    # سطح لاگ
    'LEVEL': getattr(settings, 'STT_LOG_LEVEL', 'INFO'),
    
    # ذخیره لاگ API calls
    'LOG_API_CALLS': getattr(settings, 'STT_LOG_API_CALLS', True),
    
    # ذخیره لاگ خطاهای Whisper
    'LOG_WHISPER_ERRORS': getattr(settings, 'STT_LOG_WHISPER_ERRORS', True),
}

# تنظیمات امنیتی
SECURITY_SETTINGS = {
    # بررسی نوع MIME فایل
    'CHECK_FILE_MIME': getattr(settings, 'STT_CHECK_FILE_MIME', True),
    
    # اسکن ویروس
    'VIRUS_SCAN_ENABLED': getattr(settings, 'STT_VIRUS_SCAN_ENABLED', False),
    
    # رمزنگاری فایل‌های صوتی
    'ENCRYPT_AUDIO_FILES': getattr(settings, 'STT_ENCRYPT_AUDIO_FILES', False),
}

# پیام‌های خطا
ERROR_MESSAGES = {
    'file_too_large': 'حجم فایل نباید بیشتر از {max_size} مگابایت باشد.',
    'invalid_format': 'فرمت فایل {format} پشتیبانی نمی‌شود.',
    'rate_limit_exceeded': 'تعداد درخواست‌های شما بیش از حد مجاز است. لطفاً {retry_after} ثانیه دیگر تلاش کنید.',
    'processing_failed': 'خطا در پردازش فایل صوتی. لطفاً مجدداً تلاش کنید.',
    'low_quality_audio': 'کیفیت فایل صوتی پایین است. لطفاً در محیط آرام‌تر ضبط کنید.',
    'no_speech_detected': 'صدایی در فایل شناسایی نشد.',
    'language_not_supported': 'زبان {language} پشتیبانی نمی‌شود.',
}

# تنظیمات پیشرفته
ADVANCED_SETTINGS = {
    # استفاده از VAD (Voice Activity Detection)
    'USE_VAD': getattr(settings, 'STT_USE_VAD', True),
    
    # حذف نویز پس‌زمینه
    'DENOISE_AUDIO': getattr(settings, 'STT_DENOISE_AUDIO', True),
    
    # نرمال‌سازی صدا
    'NORMALIZE_AUDIO': getattr(settings, 'STT_NORMALIZE_AUDIO', True),
    
    # استفاده از GPU برای پردازش
    'PREFER_GPU': getattr(settings, 'STT_PREFER_GPU', True),
    
    # Batch processing
    'BATCH_SIZE': getattr(settings, 'STT_BATCH_SIZE', 1),
}

# تنظیمات مانیتورینگ
MONITORING_SETTINGS = {
    # ارسال متریک به Prometheus
    'PROMETHEUS_ENABLED': getattr(settings, 'STT_PROMETHEUS_ENABLED', False),
    
    # ذخیره آمار روزانه
    'DAILY_STATS_ENABLED': getattr(settings, 'STT_DAILY_STATS_ENABLED', True),
    
    # هشدار برای کیفیت پایین
    'ALERT_ON_LOW_QUALITY': getattr(settings, 'STT_ALERT_ON_LOW_QUALITY', True),
    
    # آستانه هشدار (درصد)
    'ALERT_THRESHOLD': getattr(settings, 'STT_ALERT_THRESHOLD', 30),
}