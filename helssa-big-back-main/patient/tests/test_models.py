"""
تست‌های مدل‌های سیستم مدیریت بیماران
Patient Management System Models Tests
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from decimal import Decimal

from ..models import PatientProfile, MedicalRecord, PrescriptionHistory, MedicalConsent

User = get_user_model()


class PatientProfileModelTests(TestCase):
    """تست‌های مدل پروفایل بیمار"""
    
    def setUp(self):
        """آماده‌سازی داده‌های تست"""
        self.user = User.objects.create_user(
            username='09123456789',
            user_type='patient'
        )
        
        self.patient_data = {
            'user': self.user,
            'national_code': '1234567890',
            'first_name': 'احمد',
            'last_name': 'احمدی',
            'birth_date': date(1990, 1, 1),
            'gender': 'male',
            'emergency_contact_name': 'مریم احمدی',
            'emergency_contact_phone': '09123456788',
            'emergency_contact_relation': 'همسر',
            'address': 'تهران، خیابان آزادی',
            'city': 'تهران',
            'province': 'تهران',
            'postal_code': '1234567890',
            'marital_status': 'married'
        }
    
    def test_patient_profile_creation(self):
        """تست ایجاد پروفایل بیمار"""
        patient = PatientProfile.objects.create(**self.patient_data)
        
        self.assertEqual(patient.first_name, 'احمد')
        self.assertEqual(patient.last_name, 'احمدی')
        self.assertEqual(patient.national_code, '1234567890')
        self.assertTrue(patient.is_active)
        self.assertIsNotNone(patient.medical_record_number)
    
    def test_patient_full_name(self):
        """تست نام کامل بیمار"""
        patient = PatientProfile.objects.create(**self.patient_data)
        self.assertEqual(patient.get_full_name(), 'احمد احمدی')
    
    def test_patient_age_calculation(self):
        """تست محاسبه سن"""
        patient = PatientProfile.objects.create(**self.patient_data)
        expected_age = date.today().year - 1990
        if (date.today().month, date.today().day) < (1, 1):
            expected_age -= 1
        self.assertEqual(patient.age, expected_age)
    
    def test_patient_bmi_calculation(self):
        """تست محاسبه BMI"""
        self.patient_data['height'] = 175.0
        self.patient_data['weight'] = 70.0
        patient = PatientProfile.objects.create(**self.patient_data)
        
        expected_bmi = round(70 / (1.75 ** 2), 2)
        self.assertEqual(patient.bmi, expected_bmi)
    
    def test_auto_medical_record_number_generation(self):
        """تست تولید خودکار شماره پرونده"""
        patient = PatientProfile.objects.create(**self.patient_data)
        
        # شماره پرونده باید با P و سال جاری شروع شود
        year = date.today().year
        self.assertTrue(patient.medical_record_number.startswith(f'P{year}'))
    
    def test_duplicate_national_code_validation(self):
        """تست اعتبارسنجی کد ملی تکراری"""
        PatientProfile.objects.create(**self.patient_data)
        
        # ایجاد کاربر دوم
        user2 = User.objects.create_user(
            username='09123456788',
            user_type='patient'
        )
        
        # تلاش برای ایجاد بیمار با کد ملی تکراری
        patient_data2 = self.patient_data.copy()
        patient_data2['user'] = user2
        
        with self.assertRaises(Exception):  # اگر unique constraint تنظیم شده باشد
            PatientProfile.objects.create(**patient_data2)


class MedicalRecordModelTests(TestCase):
    """تست‌های مدل سابقه پزشکی"""
    
    def setUp(self):
        """آماده‌سازی داده‌های تست"""
        self.user = User.objects.create_user(
            username='09123456789',
            user_type='patient'
        )
        
        self.patient = PatientProfile.objects.create(
            user=self.user,
            national_code='1234567890',
            first_name='احمد',
            last_name='احمدی',
            birth_date=date(1990, 1, 1),
            gender='male',
            emergency_contact_name='مریم احمدی',
            emergency_contact_phone='09123456788',
            emergency_contact_relation='همسر',
            address='تهران، خیابان آزادی',
            city='تهران',
            province='تهران',
            postal_code='1234567890',
            marital_status='married'
        )
        
        self.record_data = {
            'patient': self.patient,
            'record_type': 'allergy',
            'title': 'آلرژی به پنی‌سیلین',
            'description': 'بیمار آلرژی شدید به پنی‌سیلین دارد',
            'severity': 'severe',
            'start_date': date.today(),
            'is_ongoing': True
        }
    
    def test_medical_record_creation(self):
        """تست ایجاد سابقه پزشکی"""
        record = MedicalRecord.objects.create(**self.record_data)
        
        self.assertEqual(record.title, 'آلرژی به پنی‌سیلین')
        self.assertEqual(record.record_type, 'allergy')
        self.assertEqual(record.severity, 'severe')
        self.assertTrue(record.is_ongoing)
    
    def test_medical_record_str_representation(self):
        """تست نمایش متنی سابقه پزشکی"""
        record = MedicalRecord.objects.create(**self.record_data)
        expected_str = f"{self.patient.get_full_name()} - آلرژی به پنی‌سیلین"
        self.assertEqual(str(record), expected_str)


class PrescriptionHistoryModelTests(TestCase):
    """تست‌های مدل تاریخچه نسخه‌ها"""
    
    def setUp(self):
        """آماده‌سازی داده‌های تست"""
        self.user = User.objects.create_user(
            username='09123456789',
            user_type='patient'
        )
        
        self.doctor = User.objects.create_user(
            username='09123456700',
            user_type='doctor'
        )
        
        self.patient = PatientProfile.objects.create(
            user=self.user,
            national_code='1234567890',
            first_name='احمد',
            last_name='احمدی',
            birth_date=date(1990, 1, 1),
            gender='male',
            emergency_contact_name='مریم احمدی',
            emergency_contact_phone='09123456788',
            emergency_contact_relation='همسر',
            address='تهران، خیابان آزادی',
            city='تهران',
            province='تهران',
            postal_code='1234567890',
            marital_status='married'
        )
        
        self.prescription_data = {
            'patient': self.patient,
            'prescribed_by': self.doctor,
            'medication_name': 'آموکسی‌سیلین',
            'dosage': '500 میلی‌گرم',
            'frequency': 'روزی 3 بار',
            'duration': '7 روز',
            'diagnosis': 'عفونت تنفسی',
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=7)
        }
    
    def test_prescription_creation(self):
        """تست ایجاد نسخه"""
        prescription = PrescriptionHistory.objects.create(**self.prescription_data)
        
        self.assertEqual(prescription.medication_name, 'آموکسی‌سیلین')
        self.assertEqual(prescription.status, 'active')
        self.assertIsNotNone(prescription.prescription_number)
    
    def test_prescription_number_generation(self):
        """تست تولید شماره نسخه"""
        prescription = PrescriptionHistory.objects.create(**self.prescription_data)
        
        # شماره نسخه باید با RX شروع شود
        self.assertTrue(prescription.prescription_number.startswith('RX'))
    
    def test_prescription_expiry(self):
        """تست انقضا نسخه"""
        # نسخه منقضی شده
        past_data = self.prescription_data.copy()
        past_data['end_date'] = date.today() - timedelta(days=1)
        prescription = PrescriptionHistory.objects.create(**past_data)
        
        self.assertTrue(prescription.is_expired)
        self.assertEqual(prescription.days_remaining, 0)
    
    def test_prescription_can_repeat(self):
        """تست امکان تکرار نسخه"""
        self.prescription_data['is_repeat_allowed'] = True
        self.prescription_data['max_repeats'] = 3
        prescription = PrescriptionHistory.objects.create(**self.prescription_data)
        
        self.assertTrue(prescription.can_repeat())


class MedicalConsentModelTests(TestCase):
    """تست‌های مدل رضایت‌نامه پزشکی"""
    
    def setUp(self):
        """آماده‌سازی داده‌های تست"""
        self.user = User.objects.create_user(
            username='09123456789',
            user_type='patient'
        )
        
        self.patient = PatientProfile.objects.create(
            user=self.user,
            national_code='1234567890',
            first_name='احمد',
            last_name='احمدی',
            birth_date=date(1990, 1, 1),
            gender='male',
            emergency_contact_name='مریم احمدی',
            emergency_contact_phone='09123456788',
            emergency_contact_relation='همسر',
            address='تهران، خیابان آزادی',
            city='تهران',
            province='تهران',
            postal_code='1234567890',
            marital_status='married'
        )
        
        self.consent_data = {
            'patient': self.patient,
            'consent_type': 'treatment',
            'title': 'رضایت‌نامه درمان',
            'description': 'رضایت برای انجام درمان‌های پزشکی',
            'consent_text': 'من با انجام درمان‌های لازم موافق هستم.',
            'expiry_date': date.today() + timedelta(days=30)
        }
    
    def test_consent_creation(self):
        """تست ایجاد رضایت‌نامه"""
        consent = MedicalConsent.objects.create(**self.consent_data)
        
        self.assertEqual(consent.title, 'رضایت‌نامه درمان')
        self.assertEqual(consent.consent_type, 'treatment')
        self.assertEqual(consent.status, 'pending')
    
    def test_consent_grant(self):
        """تست ثبت رضایت"""
        consent = MedicalConsent.objects.create(**self.consent_data)
        
        consent.grant_consent(
            digital_signature='sample_signature',
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
        
        self.assertEqual(consent.status, 'granted')
        self.assertIsNotNone(consent.consent_date)
        self.assertEqual(consent.ip_address, '127.0.0.1')
    
    def test_consent_validity(self):
        """تست اعتبار رضایت‌نامه"""
        consent = MedicalConsent.objects.create(**self.consent_data)
        
        # رضایت‌نامه در انتظار - نامعتبر
        self.assertFalse(consent.is_valid)
        
        # ثبت رضایت
        consent.grant_consent(
            digital_signature='sample_signature',
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
        
        # حالا باید معتبر باشد
        self.assertTrue(consent.is_valid)
    
    def test_consent_expiry(self):
        """تست انقضا رضایت‌نامه"""
        # رضایت‌نامه منقضی شده
        expired_data = self.consent_data.copy()
        expired_data['expiry_date'] = date.today() - timedelta(days=1)
        consent = MedicalConsent.objects.create(**expired_data)
        
        self.assertTrue(consent.is_expired)
        self.assertFalse(consent.is_valid)  # منقضی شده = نامعتبر