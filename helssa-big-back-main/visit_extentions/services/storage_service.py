from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Tuple
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


@dataclass
class StoredObject:
    """
    نتیجه ذخیره‌سازی فایل در MinIO/S3
    """

    object_name: str
    file_size: int


def put_bytes(content: bytes, object_name: str) -> StoredObject:
    """
    ذخیره محتوای باینری در Storage پیش‌فرض (MinIO/S3)
    """
    saved_name = default_storage.save(object_name, ContentFile(content))
    file_size = len(content)
    return StoredObject(object_name=saved_name, file_size=file_size)


def build_public_url(object_name: str) -> str:
    """
    ساخت URL عمومی بر اساس تنظیمات Storage
    """
    base_url = os.environ.get('MINIO_PUBLIC_BASE_URL') or ''
    if base_url:
        return f"{base_url.rstrip('/')}/{object_name.lstrip('/')}"
    return default_storage.url(object_name)

