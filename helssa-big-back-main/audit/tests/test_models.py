from django.test import TestCase
from django.contrib.auth import get_user_model

from audit.models import AuditLog, SecurityEvent


class AuditModelsTest(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username='u1', password='pass')

    def test_audit_log_create(self):
        log = AuditLog.objects.create(
            user=self.user,
            event_type='authentication',
            resource='AUTH',
            action='LOGIN',
            result='success',
            ip_address='127.0.0.1',
        )
        self.assertIsNotNone(log.id)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.event_type, 'authentication')

    def test_security_event_create(self):
        evt = SecurityEvent.objects.create(
            event_type='authentication_failed',
            result='failed',
            ip_address='127.0.0.1',
            user=self.user,
        )
        self.assertIsNotNone(evt.id)
        self.assertEqual(evt.user, self.user)

