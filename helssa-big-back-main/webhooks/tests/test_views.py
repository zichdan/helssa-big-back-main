import hashlib
import hmac
import json

from django.test import TestCase, override_settings
from django.urls import path, include
from django.http import HttpResponse

from django.conf import settings
from django.test import Client

# ساخت URLConf موقت برای تست
urlpatterns = [
    path('webhooks/', include('webhooks.urls')),
]


@override_settings(
    ROOT_URLCONF=__name__,
    WEBHOOK_SECRET='test-secret',
)
class WebhookViewTests(TestCase):
    """
    تست‌های ویوی دریافت وب‌هوک
    """

    def setUp(self):
        self.client = Client()

    def _sign(self, body: bytes) -> str:
        return hmac.new(b'test-secret', body, hashlib.sha256).hexdigest()

    def test_rejects_invalid_signature(self):
        body = json.dumps({'event': 'payment', 'payload': {}}).encode()
        resp = self.client.post('/webhooks/receive/', data=body, content_type='application/json',
            HTTP_X_WEBHOOK_SIGNATURE='invalid')
        self.assertEqual(resp.status_code, 401)

    def test_accepts_valid_signature_and_payload(self):
        payload = {'event': 'payment', 'payload': {'payment_id': '1', 'status': 'success', 'gateway_reference': 'x'}}
        body = json.dumps(payload).encode()
        sig = self._sign(body)
        resp = self.client.post('/webhooks/receive/', data=body, content_type='application/json',
            HTTP_X_WEBHOOK_SIGNATURE=sig)
        self.assertEqual(resp.status_code, 200)
        self.assertJSONEqual(
            resp.content.decode(),
            {"success": True, "processed": True}
        )

    def test_validation_error(self):
        # missing payload
        body = json.dumps({'event': 'payment'}).encode()
        sig = self._sign(body)
        resp = self.client.post('/webhooks/receive/', data=body, content_type='application/json',
            HTTP_X_WEBHOOK_SIGNATURE=sig)
        self.assertEqual(resp.status_code, 400)