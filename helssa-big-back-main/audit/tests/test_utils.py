from django.test import TestCase

from audit.utils import generate_hmac_signature, verify_hmac_signature


class AuditUtilsTest(TestCase):
    def test_hmac_generate_and_verify(self):
        msg = b"hello-world"
        sig = generate_hmac_signature(msg, secret="secret-key")
        self.assertTrue(verify_hmac_signature(msg, sig, secret="secret-key"))
        self.assertFalse(verify_hmac_signature(msg, sig, secret="wrong"))

