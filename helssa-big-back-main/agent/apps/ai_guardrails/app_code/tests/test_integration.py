"""
تست‌های ادغام برای ai_guardrails
Integration tests for ai_guardrails
"""

from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.urls import reverse
from ..models import GuardrailPolicy, RedFlagRule


User = get_user_model()


class GuardrailsIntegrationTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')  # noqa: S106
        self.client.force_authenticate(user=self.user)
        # یک قانون رد-فلگ ساده
        RedFlagRule.objects.create(
            name='pii_national_code',
            pattern_type='regex',
            pattern=r"\b\d{10}\b",
            category='pii',
            severity=80,
            created_by=self.user,
        )

        # سیاست اعمال بلوک برای شدت بالا
        GuardrailPolicy.objects.create(
            name='block_high_severity',
            enforcement_mode='block',
            applies_to='both',
            priority=10,
            conditions={'severity_min': 70},
            created_by=self.user,
        )

    def test_evaluate_block_on_pii(self) -> None:
        url = reverse('ai_guardrails:evaluate')
        payload = {
            'content': 'کد ملی من 1234567890 است',
            'direction': 'input'
        }
        response = self.client.post(url, payload, format='json')
        assert response.status_code == 200
        assert 'action' in response.data
        assert response.data['action'] == 'block'
        assert response.data['allowed'] is False

