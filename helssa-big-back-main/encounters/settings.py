"""
تنظیمات اپ encounters

این تنظیمات باید به settings اصلی پروژه اضافه شود
"""

# تنظیمات Jitsi برای ویدیو کنفرانس
JITSI_DOMAIN = 'meet.jit.si'  # یا دامنه Jitsi خودتان
JITSI_JWT_SECRET = 'your-jitsi-jwt-secret'
JITSI_APP_ID = 'helssa'
JITSI_APP_SECRET = 'your-app-secret'

# تنظیمات TURN/STUN servers
TURN_SERVERS = [
    {
        'urls': 'stun:stun.l.google.com:19302'
    },
    {
        'urls': 'turn:your-turn-server.com:3478',
        'username': 'turn-username',
        'credential': 'turn-password'
    }
]

# تنظیمات Jibri برای ضبط
JIBRI_URL = 'http://jibri-server:8080'
JIBRI_TOKEN = 'your-jibri-token'

# تنظیمات MinIO/S3
MINIO_ENDPOINT = 'minio.helssa.ir'
MINIO_ACCESS_KEY = 'your-access-key'
MINIO_SECRET_KEY = 'your-secret-key'
MINIO_SECURE = True
MINIO_BUCKET_ENCOUNTERS = 'encounters'
MINIO_BUCKET_RECORDINGS = 'recordings'

# تنظیمات STT (Whisper)
WHISPER_API_URL = 'http://whisper-api:8000'
WHISPER_API_KEY = 'your-whisper-key'
WHISPER_MODEL = 'large-v3'
WHISPER_LANGUAGE = 'fa'

# تنظیمات AI (برای تولید SOAP)
AI_SERVICE_URL = 'http://ai-service:8000'
AI_SERVICE_API_KEY = 'your-ai-key'
AI_MODEL_SOAP = 'gpt-4'
AI_TEMPERATURE = 0.3
AI_MAX_TOKENS = 2000

# تنظیمات پردازش صوت
AUDIO_CHUNK_SIZE_MB = 10
AUDIO_OVERLAP_SECONDS = 2
AUDIO_MAX_FILE_SIZE_MB = 500
AUDIO_ALLOWED_FORMATS = ['webm', 'mp3', 'wav', 'ogg']

# تنظیمات ویزیت
VISIT_MIN_DURATION_MINUTES = 5
VISIT_MAX_DURATION_MINUTES = 180
VISIT_DEFAULT_DURATION_MINUTES = 30
VISIT_EARLY_JOIN_MINUTES = 10  # چند دقیقه قبل می‌توان وارد شد

# تنظیمات نسخه
PRESCRIPTION_EXPIRY_DAYS = 180  # 6 ماه
PRESCRIPTION_MAX_MEDICATIONS = 20

# تنظیمات فایل
FILE_MAX_SIZE_MB = 100
FILE_ALLOWED_TYPES = {
    'audio': ['audio/mpeg', 'audio/wav', 'audio/webm', 'audio/ogg'],
    'image': ['image/jpeg', 'image/png', 'image/gif'],
    'document': ['application/pdf', 'application/msword'],
    'video': ['video/mp4', 'video/webm'],
    'lab_result': ['application/pdf', 'image/jpeg', 'image/png'],
    'radiology': ['image/dicom', 'image/jpeg', 'image/png', 'application/pdf']
}

# تنظیمات امنیت
ENCOUNTER_ENCRYPTION_ALGORITHM = 'AES-256-GCM'
ENCOUNTER_ACCESS_TOKEN_EXPIRY_MINUTES = 60
ENCOUNTER_DOWNLOAD_TOKEN_EXPIRY_MINUTES = 60

# تنظیمات نگهداری داده (به روز)
DATA_RETENTION_POLICY = {
    'audio_files': 365,      # 1 سال
    'video_files': 180,      # 6 ماه
    'transcripts': 1825,     # 5 سال
    'soap_reports': 3650,    # 10 سال
    'prescriptions': 3650,   # 10 سال
}

# تنظیمات Celery queues
CELERY_QUEUES = {
    'stt': {
        'exchange': 'stt',
        'routing_key': 'stt',
        'priority': 5
    },
    'nlp': {
        'exchange': 'nlp',
        'routing_key': 'nlp',
        'priority': 3
    },
    'video': {
        'exchange': 'video',
        'routing_key': 'video',
        'priority': 4
    }
}

# تنظیمات rate limiting
ENCOUNTER_RATE_LIMITS = {
    'schedule_visit': '10/hour',
    'start_visit': '5/hour',
    'upload_audio': '100/hour',
    'generate_soap': '5/hour',
}

# تنظیمات صفحه‌بندی
ENCOUNTER_PAGE_SIZE = 20
AUDIO_CHUNK_PAGE_SIZE = 50
TRANSCRIPT_PAGE_SIZE = 30

# تنظیمات لاگ
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/encounters.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'encounters': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# تنظیمات مربوط به INSTALLED_APPS
INSTALLED_APPS_ADDITION = [
    'encounters',
]

# تنظیمات middleware مورد نیاز
MIDDLEWARE_ADDITION = [
    # میان‌افزارهای اختصاصی در صورت نیاز
]

# تنظیمات REST Framework برای این اپ
REST_FRAMEWORK_SETTINGS = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}