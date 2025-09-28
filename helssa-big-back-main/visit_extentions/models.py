from __future__ import annotations

import uuid
from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    """
    مدل پایه با فیلدهای زمان‌دار
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Certificate(TimeStampedModel):
    """
    مدل گواهی استعلاجی و لینک/QR اعتبارسنجی

    - تولید توسط پزشک در بستر ویزیت
    - قابل ابطال توسط پزشک
    - دارای فایل PDF ذخیره شده در MinIO
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    visit_id = models.UUIDField()

    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='issued_certificates',
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='patient_certificates',
    )

    # اطلاعات محتوایی گواهی
    days_off = models.PositiveSmallIntegerField()
    reason = models.CharField(max_length=512)

    # وضعیت و اعتبارسنجی
    is_revoked = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)

    # لینک و QR
    verify_token = models.CharField(max_length=64, unique=True)
    verify_url = models.URLField(max_length=512)

    # فایل‌ها
    pdf_object_name = models.CharField(max_length=512, help_text='نام شیء در MinIO')
    pdf_file_size = models.PositiveIntegerField(default=0)
    pdf_generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'visit_ext_certificates'
        indexes = [
            models.Index(fields=['visit_id']),
            models.Index(fields=['verify_token', 'is_revoked']),
            models.Index(fields=['doctor', 'patient']),
        ]

    def __str__(self) -> str:
        return f"Certificate {self.id} (visit={self.visit_id})"

