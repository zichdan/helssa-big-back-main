"""
نمونه تنظیمات برای اپ visit_extentions
این تنظیمات را در settings.py پروژه خود اضافه کنید.
"""

import os

# استوریج MinIO
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_S3_ENDPOINT_URL = os.environ.get('MINIO_ENDPOINT_URL', 'http://127.0.0.1:9000')
AWS_ACCESS_KEY_ID = os.environ.get('MINIO_ACCESS_KEY', 'minioadmin')
AWS_SECRET_ACCESS_KEY = os.environ.get('MINIO_SECRET_KEY', 'minioadmin')
AWS_STORAGE_BUCKET_NAME = os.environ.get('MINIO_BUCKET_NAME', 'helssa-media')
AWS_S3_REGION_NAME = os.environ.get('MINIO_REGION', 'us-east-1')
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_ADDRESSING_STYLE = 'path'
MINIO_PUBLIC_BASE_URL = os.environ.get('MINIO_PUBLIC_BASE_URL', 'http://127.0.0.1:9000/helssa-media')

# کاوه‌نگار
KAVENEGAR_API_KEY = os.environ.get('KAVENEGAR_API_KEY', '')
KAVENEGAR_SENDER = os.environ.get('KAVENEGAR_SENDER', '')
KAVENEGAR_DOWNLOAD_TEMPLATE = os.environ.get('KAVENEGAR_DOWNLOAD_TEMPLATE', 'download_link')

# DRF Throttling
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'visit_ext_default': '30/min',
    },
}

