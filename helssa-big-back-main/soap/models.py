from __future__ import annotations

"""
مدل‌های اپ SOAP
"""

from typing import Any
from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class SOAPReport(models.Model):
    """
    ذخیره گزارش SOAP تولید شده
    """
    id = models.BigAutoField(primary_key=True)
    encounter_id = models.CharField(max_length=100, db_index=True)
    patient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='soap_reports_as_patient'
    )
    doctor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='soap_reports_as_doctor'
    )
    subjective = models.JSONField(default=dict)
    objective = models.JSONField(default=dict)
    assessment = models.JSONField(default=dict)
    plan = models.JSONField(default=dict)
    metadata = models.JSONField(default=dict)
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'گزارش SOAP'
        verbose_name_plural = 'گزارش‌های SOAP'
        indexes = [
            models.Index(fields=['encounter_id']),
            models.Index(fields=['patient']),
            models.Index(fields=['doctor']),
        ]

    def __str__(self) -> str:
        """
        نمایش رشته‌ای گزارش SOAP
        """
        return f"SOAP {self.encounter_id}"