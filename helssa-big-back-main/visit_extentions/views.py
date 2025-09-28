from __future__ import annotations

import secrets
from typing import Any
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from rest_framework import permissions, status, throttling
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Certificate
from .serializers import (
    CertificateCreateSerializer,
    CertificateSerializer,
    CertificateRevokeSerializer,
)
from .services.pdf_service import CertificatePdfData, render_certificate_pdf
from .services.qr_service import generate_qr_png_bytes
from .services.storage_service import build_public_url, put_bytes
from .services.sms_service import send_download_link


class IsDoctor(permissions.BasePermission):
    """
    اجازه دسترسی برای پزشک (فرض: فیلد is_doctor در UnifiedUser)
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, 'is_doctor', False))


class DefaultRateThrottle(throttling.UserRateThrottle):
    scope = 'visit_ext_default'


class CertificateCreateView(APIView):
    """
    ایجاد گواهی استعلاجی و تولید PDF/QR و ذخیره در MinIO
    """

    permission_classes = [permissions.IsAuthenticated, IsDoctor]
    throttle_classes = [DefaultRateThrottle]

    @transaction.atomic
    def post(self, request, *args: Any, **kwargs: Any) -> Response:
        serializer = CertificateCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        verify_token = secrets.token_urlsafe(32)
        verify_url = request.build_absolute_uri(f"/verify/certificate/{verify_token}/")

        certificate = Certificate.objects.create(
            visit_id=data['visit_id'],
            doctor=request.user,
            patient=data['patient'],
            days_off=data['days_off'],
            reason=data['reason'],
            verify_token=verify_token,
            verify_url=verify_url,
            pdf_object_name='',
            pdf_file_size=0,
        )

        pdf_bytes = render_certificate_pdf(
            CertificatePdfData(
                patient_full_name=str(certificate.patient),
                doctor_full_name=str(certificate.doctor),
                days_off=certificate.days_off,
                reason=certificate.reason,
                verify_url=certificate.verify_url,
            )
        )

        object_name = f"visit_extentions/certificates/{certificate.id}.pdf"
        stored = put_bytes(pdf_bytes, object_name)

        certificate.pdf_object_name = stored.object_name
        certificate.pdf_file_size = stored.file_size
        certificate.save(update_fields=['pdf_object_name', 'pdf_file_size', 'updated_at'])

        # ارسال لینک دانلود به بیمار از طریق SMS
        try:
            download_url = build_public_url(stored.object_name)
            patient_phone = getattr(certificate.patient, 'phone_number', None)
            if patient_phone:
                send_download_link(patient_phone, download_url)
        except Exception:
            pass

        output = CertificateSerializer(certificate)
        return Response(output.data, status=status.HTTP_201_CREATED)


class CertificateRevokeView(APIView):
    """
    ابطال گواهی توسط پزشک
    """

    permission_classes = [permissions.IsAuthenticated, IsDoctor]
    throttle_classes = [DefaultRateThrottle]

    def post(self, request, certificate_id: str, *args: Any, **kwargs: Any) -> Response:
        certificate = get_object_or_404(Certificate, id=certificate_id, doctor=request.user)
        if certificate.is_revoked:
            return Response({'detail': 'گواهی قبلاً باطل شده است.'}, status=status.HTTP_200_OK)

        revoke_serializer = CertificateRevokeSerializer(data=request.data)
        revoke_serializer.is_valid(raise_exception=True)

        certificate.is_revoked = True
        certificate.revoked_at = timezone.now()
        certificate.save(update_fields=['is_revoked', 'revoked_at', 'updated_at'])
        return Response({'detail': 'گواهی باطل شد.'}, status=status.HTTP_200_OK)


class CertificateDetailView(APIView):
    """
    مشاهده جزئیات گواهی (پزشک/بیمار صاحب)
    """

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [DefaultRateThrottle]

    def get(self, request, certificate_id: str, *args: Any, **kwargs: Any) -> Response:
        certificate = get_object_or_404(
            Certificate,
            id=certificate_id,
            # مالکیت: پزشک صادرکننده یا بیمار دارنده
            Q(doctor=request.user) | Q(patient=request.user),
        )
        return Response(CertificateSerializer(certificate).data)


class CertificateVerifyPageView(APIView):
    """
    صفحه عمومی بررسی اعتبار گواهی از طریق توکن/QR
    """

    permission_classes: list[type[permissions.BasePermission]] = []
    authentication_classes: list = []
    throttle_classes = [DefaultRateThrottle]

    def get(self, request, token: str, *args: Any, **kwargs: Any):
        certificate = get_object_or_404(Certificate, verify_token=token)
        context = {
            'is_valid': not certificate.is_revoked,
            'certificate': certificate,
        }
        template = 'visit_extentions/verify_valid.html' if not certificate.is_revoked else 'visit_extentions/verify_invalid.html'
        return render(request, template, context)

