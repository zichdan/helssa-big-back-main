"""
سرویس‌های اپ ممیزی (Audit)

مطابق اسناد security-compliance و architecture-conventions.
"""
from __future__ import annotations

from typing import Optional, Dict, Any

from django.utils import timezone
from django.http import HttpRequest
from django.contrib.auth import get_user_model

from .models import AuditLog, SecurityEvent
from . import settings as audit_settings


User = get_user_model()


class AuditLogger:
    """
    ثبت رویدادهای ممیزی با ساختار استاندارد
    """

    @staticmethod
    def _extract_context(request: Optional[HttpRequest]) -> Dict[str, Any]:
        """
        استخراج context از درخواست برای ثبت در لاگ
        """
        if request is None:
            return {}
        return {
            'ip_address': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'session_id': getattr(getattr(request, 'session', None), 'session_key', '') or request.META.get('HTTP_X_SESSION_ID', ''),
            'path': getattr(request, 'path', ''),
            'method': getattr(request, 'method', ''),
        }

    @classmethod
    def log_event(
        cls,
        *,
        event_type: str,
        action: str,
        result: str = 'success',
        resource: str = '',
        user: Optional[User] = None,
        request: Optional[HttpRequest] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        ثبت رویداد ممیزی مطابق فرمت مشخص
        """
        context = cls._extract_context(request)
        entry = AuditLog.objects.create(
            timestamp=timezone.now(),
            user=user,
            event_type=event_type,
            resource=resource,
            action=action,
            result=result,
            ip_address=context.get('ip_address'),
            user_agent=context.get('user_agent', ''),
            session_id=context.get('session_id', ''),
            metadata={
                **(metadata or {}),
                'context': context,
            },
        )
        return entry


class SecurityEventLogger:
    """
    ثبت رویدادهای امنیتی و محاسبه severity/risk_score ساده
    """

    CRITICAL_EVENTS = {
        'authentication_failed',
        'authorization_denied',
        'data_breach_attempt',
        'malware_detected',
        'invalid_access_pattern',
    }

    @classmethod
    def _calculate_severity(cls, event_type: str, result: str) -> str:
        if event_type in cls.CRITICAL_EVENTS:
            return 'critical'
        if result == 'failed':
            return 'warning'
        return 'info'

    @classmethod
    def _calculate_risk_score(cls, event_type: str, result: str) -> float:
        if event_type in cls.CRITICAL_EVENTS:
            return 0.9
        if result == 'failed':
            return 0.6
        return 0.2

    @classmethod
    def log_security_event(
        cls,
        *,
        event_type: str,
        result: str = 'detected',
        user: Optional[User] = None,
        request: Optional[HttpRequest] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> SecurityEvent:
        context = AuditLogger._extract_context(request)
        severity = cls._calculate_severity(event_type, result)
        risk = cls._calculate_risk_score(event_type, result)
        event = SecurityEvent.objects.create(
            timestamp=timezone.now(),
            event_type=event_type,
            severity=severity,
            risk_score=risk,
            ip_address=context.get('ip_address'),
            user_agent=context.get('user_agent', ''),
            user=user,
            details={
                **(details or {}),
                'context': context,
            },
            result=result,
        )
        return event

