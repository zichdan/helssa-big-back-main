"""
تست‌های ماژول Privacy
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import DataClassification, DataField, ConsentRecord
from .services.redactor import PIIRedactor
from .services.consent_manager import ConsentManager

User = get_user_model()


class PrivacyModelsTestCase(TestCase):
    """
    تست‌های مدل‌های Privacy
    """
    
    def setUp(self):
        """راه‌اندازی داده‌های تست"""
        self.user = User.objects.create_user(
            username='09123456789',
            password='testpass123'
        )
        
        self.classification = DataClassification.objects.create(
            name='اطلاعات شخصی',
            classification_type='pii',
            description='اطلاعات شخصی قابل شناسایی'
        )
    
    def test_data_classification_creation(self):
        """تست ایجاد طبقه‌بندی داده"""
        self.assertEqual(self.classification.name, 'اطلاعات شخصی')
        self.assertEqual(self.classification.classification_type, 'pii')
        self.assertTrue(self.classification.is_active)
    
    def test_data_field_creation(self):
        """تست ایجاد فیلد داده"""
        field = DataField.objects.create(
            field_name='phone_number',
            model_name='UserProfile',
            app_name='auth_otp',
            classification=self.classification,
            redaction_pattern=r'\b09\d{9}\b',
            replacement_text='[شماره تلفن حذف شده]'
        )
        
        self.assertEqual(str(field), 'auth_otp.UserProfile.phone_number')
        self.assertEqual(field.classification, self.classification)
    
    def test_consent_record_creation(self):
        """تست ایجاد رکورد رضایت"""
        consent = ConsentRecord.objects.create(
            user=self.user,
            consent_type='data_processing',
            purpose='پردازش اطلاعات برای ارائه خدمات',
            legal_basis='رضایت آگاهانه کاربر'
        )
        
        self.assertEqual(consent.user, self.user)
        self.assertEqual(consent.status, 'granted')
        self.assertTrue(consent.is_active)


class PIIRedactorTestCase(TestCase):
    """
    تست‌های سرویس پنهان‌سازی
    """
    
    def setUp(self):
        """راه‌اندازی redactor"""
        self.redactor = PIIRedactor()
    
    def test_phone_number_redaction(self):
        """تست پنهان‌سازی شماره تلفن"""
        text = "شماره تماس من 09123456789 است"
        result, matches = self.redactor.redact_text(text, log_access=False)
        
        self.assertIn('[شماره تلفن حذف شده]', result)
        self.assertNotIn('09123456789', result)
        self.assertTrue(len(matches) > 0)
    
    def test_email_redaction(self):
        """تست پنهان‌سازی ایمیل"""
        text = "ایمیل من test@example.com است"
        result, matches = self.redactor.redact_text(text, log_access=False)
        
        self.assertIn('[ایمیل حذف شده]', result)
        self.assertNotIn('test@example.com', result)
    
    def test_multiple_patterns(self):
        """تست پنهان‌سازی چندین الگو"""
        text = "شماره من 09123456789 و ایمیل test@example.com است"
        result, matches = self.redactor.redact_text(text, log_access=False)
        
        self.assertEqual(len(matches), 2)
        self.assertNotIn('09123456789', result)
        self.assertNotIn('test@example.com', result)


class ConsentManagerTestCase(TestCase):
    """
    تست‌های مدیر رضایت
    """
    
    def setUp(self):
        """راه‌اندازی داده‌های تست"""
        self.user = User.objects.create_user(
            username='09123456789',
            password='testpass123'
        )
        
        self.classification = DataClassification.objects.create(
            name='اطلاعات شخصی',
            classification_type='pii'
        )
        
        self.consent_manager = ConsentManager()
    
    def test_grant_consent(self):
        """تست اعطای رضایت"""
        consent = self.consent_manager.grant_consent(
            user_id=str(self.user.id),
            consent_type='data_processing',
            purpose='پردازش اطلاعات',
            data_categories=[str(self.classification.id)],
            legal_basis='رضایت کاربر'
        )
        
        self.assertEqual(consent.user, self.user)
        self.assertEqual(consent.status, 'granted')
        self.assertTrue(consent.is_active)
    
    def test_check_consent(self):
        """تست بررسی رضایت"""
        # اعطای رضایت
        self.consent_manager.grant_consent(
            user_id=str(self.user.id),
            consent_type='data_processing',
            purpose='پردازش اطلاعات',
            data_categories=[str(self.classification.id)],
            legal_basis='رضایت کاربر'
        )
        
        # بررسی وجود رضایت
        has_consent = self.consent_manager.check_consent(
            user_id=str(self.user.id),
            consent_type='data_processing'
        )
        
        self.assertTrue(has_consent)
    
    def test_withdraw_consent(self):
        """تست پس‌گیری رضایت"""
        # اعطای رضایت
        self.consent_manager.grant_consent(
            user_id=str(self.user.id),
            consent_type='data_processing',
            purpose='پردازش اطلاعات',
            data_categories=[str(self.classification.id)],
            legal_basis='رضایت کاربر'
        )
        
        # پس‌گیری رضایت
        success = self.consent_manager.withdraw_consent(
            user_id=str(self.user.id),
            consent_type='data_processing',
            reason='تغییر نظر کاربر'
        )
        
        self.assertTrue(success)
        
        # بررسی عدم وجود رضایت فعال
        has_consent = self.consent_manager.check_consent(
            user_id=str(self.user.id),
            consent_type='data_processing'
        )
        
        self.assertFalse(has_consent)


class PrivacyAPITestCase(APITestCase):
    """
    تست‌های API های Privacy
    """
    
    def setUp(self):
        """راه‌اندازی کاربر تست"""
        self.user = User.objects.create_user(
            username='09123456789',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # ایجاد طبقه‌بندی و رضایت لازم
        self.classification = DataClassification.objects.create(
            name='اطلاعات شخصی',
            classification_type='pii'
        )
        
        # اعطای رضایت برای پردازش داده
        from .services.consent_manager import default_consent_manager
        default_consent_manager.grant_consent(
            user_id=str(self.user.id),
            consent_type='data_processing',
            purpose='تست API',
            data_categories=[str(self.classification.id)],
            legal_basis='تست'
        )
    
    def test_redact_text_api(self):
        """تست API پنهان‌سازی متن"""
        url = reverse('privacy:redact-text')
        data = {
            'text': 'شماره تماس من 09123456789 است',
            'redaction_level': 'standard',
            'log_access': False
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('data', response.data)
    
    def test_analyze_risks_api(self):
        """تست API تحلیل ریسک"""
        url = reverse('privacy:analyze-risks')
        data = {
            'text': 'شماره تماس من 09123456789 و ایمیل test@example.com است',
            'include_suggestions': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('analysis', response.data)
