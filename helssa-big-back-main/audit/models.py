"""
مدل‌های اپ ممیزی (Audit)

طبق مستندات:
- استفاده از UnifiedUser از طریق get_user_model
- ثبت رویدادهای امنیتی و فعالیت‌ها با ساختار مشخص
"""
from __future__ import annotations

from typing import Dict, Any, Optional

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


User = get_user_model()


class AuditLog(models.Model):
    """
    ثبت رویدادهای ممیزی سیستم

    فرمت مطابق "Audit Log Format" در ARCHITECTURE_CONVENTIONS.md
    """
    id = models.BigAutoField(primary_key=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='audit_logs')
    event_type = models.CharField(max_length=50, db_index=True)  # authentication, authorization, data_access, system, security
    resource = models.CharField(max_length=100, blank=True, db_index=True)
    action = models.CharField(max_length=100)
    result = models.CharField(max_length=20, default='success', db_index=True)  # success/failed
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=64, blank=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'لاگ ممیزی'
        verbose_name_plural = 'لاگ‌های ممیزی'
        indexes = [
            models.Index(fields=['event_type', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['resource', 'action', '-timestamp']),
        ]


class SecurityEvent(models.Model):
    """
    ثبت رویدادهای امنیتی مهم
    مطابق SecurityEventLogger در امنیت و Compliance
    """
    id = models.BigAutoField(primary_key=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    event_type = models.CharField(max_length=100, db_index=True)
    severity = models.CharField(max_length=20, blank=True, db_index=True)
    risk_score = models.FloatField(default=0)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='security_events')
    details = models.JSONField(default=dict, blank=True)
    result = models.CharField(max_length=20, default='detected', db_index=True)

    class Meta:
        verbose_name = 'رویداد امنیتی'
        verbose_name_plural = 'رویدادهای امنیتی'
        indexes = [
            models.Index(fields=['event_type', 'severity', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
        ]

