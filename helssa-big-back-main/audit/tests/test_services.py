from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model

from audit.services import AuditLogger, SecurityEventLogger
from audit.models import AuditLog, SecurityEvent


class AuditServicesTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username='u2', password='pass')

    def test_audit_logger_log_event(self):
        request = self.factory.get('/api/v1/test/')
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        entry = AuditLogger.log_event(
            event_type='authentication',
            action='LOGIN',
            result='success',
            resource='AUTH',
            user=self.user,
            request=request,
            metadata={'method': 'OTP'},
        )
        self.assertIsInstance(entry, AuditLog)
        self.assertEqual(entry.user, self.user)
        self.assertEqual(entry.resource, 'AUTH')

    def test_security_event_logger(self):
        request = self.factory.post('/api/v1/auth/')
        request.META['REMOTE_ADDR'] = '10.0.0.1'
        event = SecurityEventLogger.log_security_event(
            event_type='authentication_failed',
            result='failed',
            user=self.user,
            request=request,
            details={'reason': 'invalid_otp'},
        )
        self.assertIsInstance(event, SecurityEvent)
        self.assertEqual(event.severity, 'critical')
        self.assertGreater(event.risk_score, 0.5)

