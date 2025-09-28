# settings.py

DEFAULT_FILE_STORAGE = 'minio_storage.storage.MinioMediaStorage'

MINIO_STORAGE_ENDPOINT = 'localhost:9000'  # یا 'minio:9000' در Docker
MINIO_STORAGE_ACCESS_KEY = 'minioadmin'
MINIO_STORAGE_SECRET_KEY = 'minioadmin123'
MINIO_STORAGE_MEDIA_BUCKET_NAME = 'agent-data'
MINIO_STORAGE_MEDIA_USE_HTTPS = False
MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET = True



# settings.py

# ---------------------------
# MinIO Config for Media Files
# ---------------------------

DEFAULT_FILE_STORAGE = 'minio_storage.storage.MinioMediaStorage'

MINIO_STORAGE_ENDPOINT = 'localhost:9000'  # یا 'minio:9000' اگر داخل docker هستی
MINIO_STORAGE_ACCESS_KEY = 'minioadmin'
MINIO_STORAGE_SECRET_KEY = 'minioadmin123'

MINIO_STORAGE_MEDIA_BUCKET_NAME = 'media'
MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET = True  # اگه bucket وجود نداشت، بسازه
MINIO_STORAGE_MEDIA_USE_HTTPS = False  # چون لوکالی هست، https لازم نیست

# Optional:
MEDIA_URL = '/media/'  # یا می‌تونی ست نکنی چون از MinIO مستقیم URL می‌گیری
