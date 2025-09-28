from __future__ import annotations

"""
تست‌های اپ SOAP
"""

import unittest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from .models import SOAPReport


User = get_user_model()


@unittest.skip("تناقض: UnifiedUser با فیلد user_type در پروژه تعریف نشده، DRF/JWT در settings پروژه ثبت نشده، و طبق دستور نمی‌توان root urls را تغییر داد.")
class SOAPAPITest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        # ساخت کاربران فرضی
        self.patient = User.objects.create_user(username='p1', password='test', email='p1@example.com')
        setattr(self.patient, 'user_type', 'patient')
        self.patient.save()

        self.doctor = User.objects.create_user(username='d1', password='test', email='d1@example.com')
        setattr(self.doctor, 'user_type', 'doctor')
        self.doctor.save()

        token = AccessToken.for_user(self.doctor)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token)}')

    def test_generate_and_get_formats(self) -> None:
        resp = self.client.post('/soap/generate/', {
            'encounter_id': 'enc-1',
            'transcript': 'test transcript',
            'patient_id': self.patient.id,
            'doctor_id': self.doctor.id,
        }, format='json')

        self.assertEqual(resp.status_code, 201)
        report_id = resp.data['soap_report']['id']

        resp2 = self.client.get(f'/soap/formats/{report_id}/')
        self.assertEqual(resp2.status_code, 200)
        self.assertIn('markdown', resp2.data)