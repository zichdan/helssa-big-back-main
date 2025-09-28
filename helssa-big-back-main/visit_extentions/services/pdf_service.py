from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Optional
import base64

from django.template.loader import render_to_string
from weasyprint import HTML
from .qr_service import generate_qr_png_bytes


@dataclass
class CertificatePdfData:
    """
    داده‌های لازم برای تولید PDF گواهی استعلاجی
    """

    patient_full_name: str
    doctor_full_name: str
    days_off: int
    reason: str
    verify_url: str


def render_certificate_pdf(data: CertificatePdfData, template_name: str = 'visit_extentions/certificate.html') -> bytes:
    """
    رندر PDF گواهی با استفاده از قالب HTML
    """
    qr_png_b64 = base64.b64encode(generate_qr_png_bytes(data.verify_url)).decode('utf-8')
    html_content = render_to_string(template_name, {
        'patient_full_name': data.patient_full_name,
        'doctor_full_name': data.doctor_full_name,
        'days_off': data.days_off,
        'reason': data.reason,
        'verify_url': data.verify_url,
        'verify_qr_b64': qr_png_b64,
    })
    pdf_io = BytesIO()
    HTML(string=html_content).write_pdf(target=pdf_io)
    return pdf_io.getvalue()

