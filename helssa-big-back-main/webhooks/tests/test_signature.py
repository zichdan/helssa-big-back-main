import hashlib
import hmac

from django.test import SimpleTestCase, override_settings

from webhooks.services.signature import verify_webhook_signature


class SignatureVerificationTests(SimpleTestCase):
    """
    تست‌های تایید امضای وب‌هوک
    """

    @override_settings(WEBHOOK_SECRET='test-secret')
    def test_valid_signature(self):
        payload = b'{"event":"x","payload":{}}'
        expected = hmac.new(b'test-secret', payload, hashlib.sha256).hexdigest()
        self.assertTrue(verify_webhook_signature(payload, expected))

    @override_settings(WEBHOOK_SECRET='another-secret')
    def test_invalid_signature(self):
        payload = b'{}'
        invalid = 'deadbeef'
        self.assertFalse(verify_webhook_signature(payload, invalid))

    def test_missing_signature(self):
        payload = b'{}'
        self.assertFalse(verify_webhook_signature(payload, None))