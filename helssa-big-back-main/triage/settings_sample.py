"""
تنظیمات اپلیکیشن تریاژ پزشکی
نمونه تنظیمات که باید در settings.py اصلی پروژه اضافه شوند
"""

# تنظیمات تریاژ
TRIAGE_SETTINGS = {
    # تنظیمات عمومی
    'URGENCY_LEVELS': {
        1: 'غیر اورژانس',
        2: 'کم اولویت', 
        3: 'متوسط',
        4: 'بالا',
        5: 'اورژانس'
    },
    
    # حداکثر تعداد علائم در هر جلسه
    'MAX_SYMPTOMS_PER_SESSION': 20,
    
    # حداکثر تعداد تشخیص‌های احتمالی
    'MAX_DIFFERENTIAL_DIAGNOSES': 10,
    
    # زمان انتظار پیش‌فرض برای هر سطح اورژانس (به دقیقه)
    'DEFAULT_WAIT_TIMES': {
        1: 240,  # 4 ساعت
        2: 120,  # 2 ساعت  
        3: 60,   # 1 ساعت
        4: 30,   # 30 دقیقه
        5: 0     # فوری
    },
    
    # تنظیمات هوش مصنوعی
    'AI_CONFIDENCE_THRESHOLD': 0.7,
    'RED_FLAG_THRESHOLD': 8,  # امتیاز اورژانس برای علائم خطر
    
    # تنظیمات کش
    'CACHE_TIMEOUT': {
        'SYMPTOMS_SEARCH': 900,      # 15 دقیقه
        'DIAGNOSES_LIST': 1800,      # 30 دقیقه
        'STATISTICS': 300,           # 5 دقیقه
        'ANALYSIS_RESULTS': 600      # 10 دقیقه
    },
    
    # تنظیمات امنیتی
    'RATE_LIMITING': {
        'CREATE_SESSION': '10/hour',     # حداکثر 10 جلسه در ساعت
        'ANALYZE_SYMPTOMS': '50/hour',   # حداکثر 50 تحلیل در ساعت
        'SEARCH_SYMPTOMS': '100/hour'    # حداکثر 100 جستجو در ساعت
    },
    
    # تنظیمات لاگ
    'LOGGING': {
        'ENABLE_DETAILED_LOGS': True,
        'LOG_ANALYSIS_RESULTS': True,
        'LOG_USER_INTERACTIONS': True
    },
    
    # تنظیمات اعلان‌ها
    'NOTIFICATIONS': {
        'SEND_URGENT_ALERTS': True,
        'NOTIFY_ON_RED_FLAGS': True,
        'EMAIL_TEMPLATES': {
            'URGENT_ALERT': 'triage/emails/urgent_alert.html',
            'ANALYSIS_COMPLETE': 'triage/emails/analysis_complete.html'
        }
    },
    
    # علائم خطر پیش‌فرض
    'DEFAULT_RED_FLAGS': [
        'درد قفسه سینه',
        'تنگی نفس شدید', 
        'از دست دادن هوشیاری',
        'خونریزی شدید',
        'درد شکم حاد',
        'تب بالای 39 درجه',
        'سردرد ناگهانی و شدید',
        'اختلال بینایی ناگهانی',
        'فلج یا ضعف ناگهانی',
        'تشنج'
    ],
    
    # پیام‌های پیش‌فرض
    'DEFAULT_MESSAGES': {
        'URGENT_REFERRAL': 'فوراً به نزدیک‌ترین مرکز درمانی مراجعه کنید',
        'DOCTOR_CONSULTATION': 'در اسرع وقت با پزشک مشورت کنید',
        'MONITOR_SYMPTOMS': 'علائم خود را تحت نظر داشته باشید',
        'HOME_CARE': 'مراقبت خانگی کافی است'
    },
    
    # تنظیمات پرداخت (در صورت نیاز)
    'PAYMENT_SETTINGS': {
        'FREE_SESSIONS_PER_MONTH': 3,
        'PREMIUM_ANALYSIS_COST': 50000,  # به ریال
        'URGENT_CONSULTATION_COST': 100000
    },
    
    # تنظیمات گزارش‌دهی
    'REPORTING': {
        'GENERATE_DAILY_REPORTS': True,
        'EXPORT_FORMATS': ['PDF', 'Excel', 'JSON'],
        'INCLUDE_STATISTICS': True
    }
}

# تنظیمات دیتابیس برای تریاژ
DATABASES_TRIAGE = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'helssa_triage',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    }
}

# تنظیمات Celery برای پردازش‌های پس‌زمینه
CELERY_TRIAGE_TASKS = {
    'triage.tasks.analyze_session_async': {
        'queue': 'triage_analysis',
        'routing_key': 'triage.analysis'
    },
    'triage.tasks.generate_daily_report': {
        'queue': 'triage_reports', 
        'routing_key': 'triage.reports'
    },
    'triage.tasks.cleanup_old_sessions': {
        'queue': 'triage_cleanup',
        'routing_key': 'triage.cleanup'
    }
}

# تنظیمات REST Framework برای تریاژ
REST_FRAMEWORK_TRIAGE = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'triage_analysis': '50/hour'
    }
}

# تنظیمات Redis برای کش تریاژ  
CACHES_TRIAGE = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/2',  # دیتابیس 2 برای تریاژ
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'triage',
        'TIMEOUT': 300  # 5 دقیقه پیش‌فرض
    }
}

# تنظیمات لاگینگ تریاژ
LOGGING_TRIAGE = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'triage_formatter': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'triage_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/triage.log',
            'formatter': 'triage_formatter',
        },
        'triage_analysis_file': {
            'level': 'DEBUG', 
            'class': 'logging.FileHandler',
            'filename': 'logs/triage_analysis.log',
            'formatter': 'triage_formatter',
        },
    },
    'loggers': {
        'triage': {
            'handlers': ['triage_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'triage.services': {
            'handlers': ['triage_analysis_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# متغیرهای محیطی مورد نیاز
"""
# .env variables for triage app
TRIAGE_AI_API_KEY=your_ai_api_key
TRIAGE_ENABLE_ML=True  
TRIAGE_DEBUG_MODE=False
TRIAGE_CACHE_ENABLED=True
TRIAGE_RATE_LIMITING=True
TRIAGE_NOTIFICATIONS_ENABLED=True
TRIAGE_EMAIL_NOTIFICATIONS=True
TRIAGE_SMS_NOTIFICATIONS=True
"""

# نصب پکیج‌های مورد نیاز اضافی در requirements.txt
"""
# Additional packages for triage app
django-filter>=23.0
django-redis>=5.0
celery[redis]>=5.0
pandas>=2.0
numpy>=1.24
scikit-learn>=1.3
matplotlib>=3.7
seaborn>=0.12
python-dateutil>=2.8
jsonschema>=4.17
"""