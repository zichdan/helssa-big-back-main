from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework import status

from .models import (
    SecurityLayer, SecurityLog, MFAConfig, Role,
    TemporaryAccess, SecurityIncident
)

User = get_user_model()


class SecurityLayerModelTest(TestCase):
    """تست مدل SecurityLayer"""
    
    def setUp(self):
        self.layer = SecurityLayer.objects.create(
            name='Test Layer',
            layer_type='network',
            priority=1,
            config={
                'firewall_rules': [],
                'rate_limit_config': {}
            }
        )
    
    def test_layer_creation(self):
        """تست ایجاد لایه امنیتی"""
        self.assertEqual(self.layer.name, 'Test Layer')
        self.assertEqual(self.layer.layer_type, 'network')
        self.assertTrue(self.layer.is_active)
        
    def test_layer_str(self):
        """تست نمایش رشته‌ای لایه"""
        self.assertIn('Test Layer', str(self.layer))


class SecurityLogModelTest(TestCase):
    """تست مدل SecurityLog"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
    def test_security_log_creation(self):
        """تست ایجاد لاگ امنیتی"""
        log = SecurityLog.objects.create(
            event_type='authentication_failed',
            layer='application',
            reason='Invalid credentials',
            ip_address='192.168.1.1',
            user=self.user,
            risk_score=50
        )
        
        self.assertEqual(log.event_type, 'authentication_failed')
        self.assertEqual(log.risk_score, 50)
        self.assertEqual(log.user, self.user)


class TemporaryAccessModelTest(TestCase):
    """تست مدل TemporaryAccess"""
    
    def setUp(self):
        self.doctor = User.objects.create_user(
            username='doctor',
            password='doctorpass123'
        )
        self.granter = User.objects.create_user(
            username='granter',
            password='granterpass123'
        )
        
    def test_temporary_access_creation(self):
        """تست ایجاد دسترسی موقت"""
        access = TemporaryAccess.objects.create(
            doctor=self.doctor,
            patient_id='12345678-1234-1234-1234-123456789012',
            granted_by=self.granter,
            reason='Emergency consultation',
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        self.assertTrue(access.is_valid())
        self.assertEqual(access.doctor, self.doctor)
        
    def test_expired_access(self):
        """تست دسترسی منقضی شده"""
        access = TemporaryAccess.objects.create(
            doctor=self.doctor,
            patient_id='12345678-1234-1234-1234-123456789012',
            granted_by=self.granter,
            reason='Old consultation',
            expires_at=timezone.now() - timedelta(hours=1)
        )
        
        self.assertFalse(access.is_valid())


class SecurityIncidentModelTest(TestCase):
    """تست مدل SecurityIncident"""
    
    def test_incident_creation(self):
        """تست ایجاد حادثه امنیتی"""
        incident = SecurityIncident.objects.create(
            incident_type='unauthorized_access',
            severity='high',
            details={'ip': '192.168.1.100', 'attempts': 5},
            detected_at=timezone.now()
        )
        
        self.assertEqual(incident.status, 'detected')
        self.assertEqual(incident.severity, 'high')
        self.assertIsNone(incident.resolved_at)


# تست‌های API
class SecurityLayerAPITest(APITestCase):
    """تست API لایه‌های امنیتی"""
    
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin',
            password='adminpass123'
        )
        self.user = User.objects.create_user(
            username='user',
            password='userpass123'
        )
        
    def test_list_security_layers_requires_auth(self):
        """تست نیاز به احراز هویت برای مشاهده لایه‌ها"""
        response = self.client.get('/compliance/api/security-layers/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_admin_can_create_layer(self):
        """تست ایجاد لایه توسط ادمین"""
        self.client.force_authenticate(user=self.admin)
        data = {
            'name': 'New Layer',
            'layer_type': 'network',
            'priority': 1,
            'config': {
                'firewall_rules': [],
                'rate_limit_config': {}
            }
        }
        response = self.client.post('/compliance/api/security-layers/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
    def test_regular_user_cannot_create_layer(self):
        """تست عدم امکان ایجاد لایه توسط کاربر عادی"""
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'New Layer',
            'layer_type': 'network',
            'priority': 1,
            'config': {}
        }
        response = self.client.post('/compliance/api/security-layers/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# TODO: تست‌های بیشتر برای:
# - MFA endpoints
# - Role management
# - Audit logs
# - HIPAA compliance reports
# - Security incidents
# - Medical files