"""
تنظیمات اضافی برای اپ Checklist
این فایل باید به settings.py اصلی اضافه شود
"""

# اضافه کردن اپ به INSTALLED_APPS
CHECKLIST_APP = 'checklist'

# تنظیمات مربوط به Checklist
CHECKLIST_SETTINGS = {
    # آستانه اطمینان برای ارزیابی خودکار
    'CONFIDENCE_THRESHOLD': 0.6,
    
    # حداکثر تعداد کلمات کلیدی برای هر آیتم
    'MAX_KEYWORDS_PER_ITEM': 20,
    
    # طول context برای نمایش متن شاهد
    'EVIDENCE_CONTEXT_LENGTH': 100,
    
    # حداکثر تعداد مطابقت‌ها برای نمایش
    'MAX_EVIDENCE_MATCHES': 3,
    
    # تنظیمات cache برای نتایج ارزیابی
    'CACHE_EVALUATION_RESULTS': True,
    'CACHE_TIMEOUT': 3600,  # 1 ساعت
    
    # تنظیمات هشدارها
    'ALERTS': {
        'ENABLE_REALTIME_ALERTS': True,
        'ALERT_CHANNELS': ['database', 'websocket'],  # کانال‌های ارسال هشدار
        'CRITICAL_ITEM_THRESHOLD': 0.3,  # آستانه برای آیتم‌های بحرانی
    },
    
    # تنظیمات لاگ
    'ENABLE_EVALUATION_LOGGING': True,
    'LOG_LEVEL': 'INFO',
}

# Middleware اضافی (در صورت نیاز)
CHECKLIST_MIDDLEWARE = []

# تنظیمات REST Framework برای این اپ
CHECKLIST_REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'MAX_PAGE_SIZE': 200,
}

# تنظیمات Celery برای تسک‌های background (در صورت نیاز)
CHECKLIST_CELERY_TASKS = {
    'checklist.tasks.evaluate_encounter': {
        'queue': 'checklist',
        'routing_key': 'checklist.evaluate',
    },
    'checklist.tasks.generate_alerts': {
        'queue': 'alerts',
        'routing_key': 'checklist.alerts',
    },
}

# تنظیمات برای یکپارچه‌سازی با سایر اپ‌ها
CHECKLIST_INTEGRATIONS = {
    'ENCOUNTERS_APP': 'encounters',  # نام اپ encounters
    'USE_UNIFIED_AUTH': True,  # استفاده از unified_auth
    'USE_UNIFIED_ACCESS': True,  # استفاده از unified_access برای کنترل دسترسی
}