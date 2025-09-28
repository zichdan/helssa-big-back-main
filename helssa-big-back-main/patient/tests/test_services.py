"""
تست‌های سرویس‌های سیستم مدیریت بیماران
Patient Management System Services Tests
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from unittest.mock import patch, MagicMock
from datetime import date, timedelta
import asyncio

from ..models import PatientProfile, MedicalRecord, PrescriptionHistory, MedicalConsent
from ..services import (
    PatientService,
    MedicalRecordService,
    PrescriptionService,
    ConsentService
)

User = get_user_model()


class AsyncTestCase(TestCase):
    """کلاس پایه برای تست‌های async"""
    
    def setUp(self):
        """آماده‌سازی cache و user data"""
        cache.clear()
        super().setUp()
    
    def run_async(self, coro):
        """اجرای کد async در تست‌ها"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


class PatientServiceTest(AsyncTestCase):
    """تست‌های سرویس بیمار"""
    
    def setUp(self):
        super().setUp()
        
        self.user = User.objects.create_user(
            username='09123456789',
            user_type='patient'
        )
        
        self.doctor = User.objects.create_user(
            username='09123456700',
            user_type='doctor'
        )
        
        self.patient_profile = PatientProfile.objects.create(
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
        
        self.service = PatientService()
    
    def test_generate_medical_record_number(self):
        """تست تولید شماره پرونده پزشکی"""
        number = self.service.generate_medical_record_number()
        
        self.assertIsInstance(number, str)
        self.assertTrue(number.startswith(f'P{date.today().year}'))
        self.assertEqual(len(number), 12)  # P + 4 رقم سال + 7 رقم
    
    def test_generate_unique_medical_record_numbers(self):
        """تست تولید شماره‌های یکتا"""
        numbers = set()
        for _ in range(100):
            number = self.service.generate_medical_record_number()
            self.assertNotIn(number, numbers)
            numbers.add(number)
    
    def test_create_patient_profile_success(self):
        """تست ایجاد موفق پروفایل بیمار"""
        async def test():
            data = {
                'user': self.user,
                'national_code': '0987654321',
                'first_name': 'علی',
                'last_name': 'علوی',
                'birth_date': date(1985, 5, 15),
                'gender': 'male',
                'emergency_contact_name': 'فاطمه علوی',
                'emergency_contact_phone': '09123456777',
                'emergency_contact_relation': 'همسر',
                'address': 'تهران، میدان انقلاب',
                'city': 'تهران',
                'province': 'تهران',
                'postal_code': '0987654321',
                'marital_status': 'married'
            }
            
            success, result = await self.service.create_patient_profile(data)
            
            self.assertTrue(success)
            self.assertIn('patient', result)
            self.assertEqual(result['patient']['first_name'], 'علی')
            self.assertIsNotNone(result['patient']['medical_record_number'])
        
        self.run_async(test())
    
    def test_create_patient_profile_duplicate_national_code(self):
        """تست ایجاد پروفایل با کد ملی تکراری"""
        async def test():
            data = {
                'user': self.user,
                'national_code': '1234567890',  # کد ملی موجود
                'first_name': 'علی',
                'last_name': 'علوی',
                'birth_date': date(1985, 5, 15),
                'gender': 'male',
                'emergency_contact_name': 'فاطمه علوی',
                'emergency_contact_phone': '09123456777',
                'emergency_contact_relation': 'همسر',
                'address': 'تهران، میدان انقلاب',
                'city': 'تهران',
                'province': 'تهران',
                'postal_code': '0987654321',
                'marital_status': 'married'
            }
            
            success, result = await self.service.create_patient_profile(data)
            
            self.assertFalse(success)
            self.assertIn('error', result)
            self.assertIn('کد ملی', result['message'])
        
        self.run_async(test())
    
    def test_get_patient_profile_success(self):
        """تست دریافت موفق پروفایل بیمار"""
        async def test():
            success, result = await self.service.get_patient_profile(
                self.patient_profile.id, include_statistics=True
            )
            
            self.assertTrue(success)
            self.assertIn('patient', result)
            self.assertEqual(result['patient']['first_name'], 'احمد')
            self.assertIn('statistics', result)
        
        self.run_async(test())
    
    def test_get_patient_profile_not_found(self):
        """تست دریافت پروفایل غیرموجود"""
        async def test():
            import uuid
            fake_id = uuid.uuid4()
            
            success, result = await self.service.get_patient_profile(fake_id)
            
            self.assertFalse(success)
            self.assertEqual(result['error'], 'patient_not_found')
        
        self.run_async(test())
    
    def test_update_patient_profile_success(self):
        """تست بروزرسانی موفق پروفایل"""
        async def test():
            update_data = {
                'first_name': 'محمد',
                'height': 175.0,
                'weight': 70.0
            }
            
            success, result = await self.service.update_patient_profile(
                self.patient_profile.id, update_data, self.user
            )
            
            self.assertTrue(success)
            self.assertEqual(result['patient']['first_name'], 'محمد')
            
            # بررسی بروزرسانی در دیتابیس
            self.patient_profile.refresh_from_db()
            self.assertEqual(self.patient_profile.first_name, 'محمد')
        
        self.run_async(test())
    
    def test_validate_patient_access_success(self):
        """تست اعتبارسنجی موفق دسترسی"""
        async def test():
            # بیمار به اطلاعات خودش دسترسی دارد
            has_access = await self.service.validate_patient_access(
                self.user, self.patient_profile.id, 'view'
            )
            
            self.assertTrue(has_access)
        
        self.run_async(test())
    
    def test_validate_patient_access_denied(self):
        """تست عدم دسترسی"""
        async def test():
            other_user = User.objects.create_user(
                username='09123456799',
                user_type='patient'
            )
            
            # بیمار دیگر نباید دسترسی داشته باشد
            has_access = await self.service.validate_patient_access(
                other_user, self.patient_profile.id, 'view'
            )
            
            self.assertFalse(has_access)
        
        self.run_async(test())
    
    def test_get_patient_statistics(self):
        """تست دریافت آمار بیمار"""
        async def test():
            # ایجاد داده‌های نمونه
            MedicalRecord.objects.create(
                patient=self.patient_profile,
                record_type='allergy',
                title='آلرژی تست',
                description='توضیحات',
                severity='mild',
                start_date=date.today(),
                is_ongoing=True
            )
            
            success, result = await self.service.get_patient_statistics(
                self.patient_profile.id
            )
            
            self.assertTrue(success)
            self.assertIn('medical_records_count', result)
            self.assertIn('prescriptions_count', result)
            self.assertIn('consents_count', result)
            self.assertEqual(result['medical_records_count'], 1)
        
        self.run_async(test())


class MedicalRecordServiceTest(AsyncTestCase):
    """تست‌های سرویس سوابق پزشکی"""
    
    def setUp(self):
        super().setUp()
        
        self.user = User.objects.create_user(
            username='09123456789',
            user_type='patient'
        )
        
        self.doctor = User.objects.create_user(
            username='09123456700',
            user_type='doctor'
        )
        
        self.patient_profile = PatientProfile.objects.create(
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
        
        self.service = MedicalRecordService()
    
    def test_add_medical_record_success(self):
        """تست افزودن موفق سابقه پزشکی"""
        async def test():
            data = {
                'patient': self.patient_profile,
                'record_type': 'allergy',
                'title': 'آلرژی به آسپرین',
                'description': 'حساسیت شدید به آسپرین',
                'severity': 'severe',
                'start_date': date.today(),
                'is_ongoing': True,
                'doctor': self.doctor
            }
            
            success, result = await self.service.add_medical_record(data)
            
            self.assertTrue(success)
            self.assertIn('record', result)
            self.assertEqual(result['record']['title'], 'آلرژی به آسپرین')
        
        self.run_async(test())
    
    def test_get_patient_medical_records(self):
        """تست دریافت سوابق پزشکی بیمار"""
        async def test():
            # ایجاد چند سابقه نمونه
            MedicalRecord.objects.create(
                patient=self.patient_profile,
                record_type='allergy',
                title='آلرژی 1',
                description='توضیحات',
                severity='mild',
                start_date=date.today(),
                is_ongoing=True
            )
            
            MedicalRecord.objects.create(
                patient=self.patient_profile,
                record_type='medication',
                title='دارو 1',
                description='توضیحات',
                severity='moderate',
                start_date=date.today() - timedelta(days=30),
                end_date=date.today() - timedelta(days=15),
                is_ongoing=False
            )
            
            success, result = await self.service.get_patient_medical_records(
                self.patient_profile.id
            )
            
            self.assertTrue(success)
            self.assertIn('records', result)
            self.assertEqual(len(result['records']), 2)
        
        self.run_async(test())
    
    def test_get_medical_records_by_type(self):
        """تست دریافت سوابق بر اساس نوع"""
        async def test():
            # ایجاد سوابق مختلف
            MedicalRecord.objects.create(
                patient=self.patient_profile,
                record_type='allergy',
                title='آلرژی',
                description='توضیحات',
                severity='mild',
                start_date=date.today(),
                is_ongoing=True
            )
            
            MedicalRecord.objects.create(
                patient=self.patient_profile,
                record_type='surgery',
                title='جراحی',
                description='توضیحات',
                severity='high',
                start_date=date.today() - timedelta(days=30),
                end_date=date.today() - timedelta(days=15),
                is_ongoing=False
            )
            
            success, result = await self.service.get_patient_medical_records(
                self.patient_profile.id, record_type='allergy'
            )
            
            self.assertTrue(success)
            self.assertEqual(len(result['records']), 1)
            self.assertEqual(result['records'][0]['record_type'], 'allergy')
        
        self.run_async(test())
    
    def test_update_medical_record_success(self):
        """تست بروزرسانی موفق سابقه پزشکی"""
        async def test():
            record = MedicalRecord.objects.create(
                patient=self.patient_profile,
                record_type='allergy',
                title='آلرژی اولیه',
                description='توضیحات اولیه',
                severity='mild',
                start_date=date.today(),
                is_ongoing=True
            )
            
            update_data = {
                'title': 'آلرژی بروزرسانی شده',
                'severity': 'severe',
                'description': 'توضیحات جدید'
            }
            
            success, result = await self.service.update_medical_record(
                record.id, update_data, self.doctor
            )
            
            self.assertTrue(success)
            self.assertEqual(result['record']['title'], 'آلرژی بروزرسانی شده')
            
            # بررسی بروزرسانی در دیتابیس
            record.refresh_from_db()
            self.assertEqual(record.title, 'آلرژی بروزرسانی شده')
        
        self.run_async(test())


class PrescriptionServiceTest(AsyncTestCase):
    """تست‌های سرویس نسخه‌ها"""
    
    def setUp(self):
        super().setUp()
        
        self.user = User.objects.create_user(
            username='09123456789',
            user_type='patient'
        )
        
        self.doctor = User.objects.create_user(
            username='09123456700',
            user_type='doctor'
        )
        
        self.patient_profile = PatientProfile.objects.create(
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
        
        self.service = PrescriptionService()
    
    def test_add_prescription_success(self):
        """تست افزودن موفق نسخه"""
        async def test():
            data = {
                'patient': self.patient_profile,
                'prescribed_by': self.doctor,
                'medication_name': 'آموکسی‌سیلین',
                'dosage': '500 میلی‌گرم',
                'frequency': 'روزی 3 بار',
                'duration': '7 روز',
                'diagnosis': 'عفونت تنفسی',
                'start_date': date.today(),
                'end_date': date.today() + timedelta(days=7)
            }
            
            success, result = await self.service.add_prescription(data)
            
            self.assertTrue(success)
            self.assertIn('prescription', result)
            self.assertEqual(result['prescription']['medication_name'], 'آموکسی‌سیلین')
            self.assertIsNotNone(result['prescription']['prescription_number'])
        
        self.run_async(test())
    
    def test_get_patient_prescriptions(self):
        """تست دریافت نسخه‌های بیمار"""
        async def test():
            # ایجاد چند نسخه نمونه
            PrescriptionHistory.objects.create(
                patient=self.patient_profile,
                prescribed_by=self.doctor,
                medication_name='دارو 1',
                dosage='250mg',
                frequency='روزی 2 بار',
                duration='5 روز',
                diagnosis='بیماری 1',
                start_date=date.today(),
                end_date=date.today() + timedelta(days=5),
                status='active'
            )
            
            PrescriptionHistory.objects.create(
                patient=self.patient_profile,
                prescribed_by=self.doctor,
                medication_name='دارو 2',
                dosage='500mg',
                frequency='روزی 1 بار',
                duration='10 روز',
                diagnosis='بیماری 2',
                start_date=date.today() - timedelta(days=20),
                end_date=date.today() - timedelta(days=10),
                status='completed'
            )
            
            success, result = await self.service.get_patient_prescriptions(
                self.patient_profile.id
            )
            
            self.assertTrue(success)
            self.assertIn('prescriptions', result)
            self.assertEqual(len(result['prescriptions']), 2)
        
        self.run_async(test())
    
    def test_get_prescriptions_by_status(self):
        """تست دریافت نسخه‌ها بر اساس وضعیت"""
        async def test():
            PrescriptionHistory.objects.create(
                patient=self.patient_profile,
                prescribed_by=self.doctor,
                medication_name='دارو فعال',
                dosage='250mg',
                frequency='روزی 2 بار',
                duration='5 روز',
                diagnosis='بیماری',
                start_date=date.today(),
                end_date=date.today() + timedelta(days=5),
                status='active'
            )
            
            PrescriptionHistory.objects.create(
                patient=self.patient_profile,
                prescribed_by=self.doctor,
                medication_name='دارو منقضی',
                dosage='500mg',
                frequency='روزی 1 بار',
                duration='10 روز',
                diagnosis='بیماری',
                start_date=date.today() - timedelta(days=20),
                end_date=date.today() - timedelta(days=10),
                status='expired'
            )
            
            success, result = await self.service.get_patient_prescriptions(
                self.patient_profile.id, prescription_status='active'
            )
            
            self.assertTrue(success)
            self.assertEqual(len(result['prescriptions']), 1)
            self.assertEqual(result['prescriptions'][0]['status'], 'active')
        
        self.run_async(test())
    
    def test_repeat_prescription_success(self):
        """تست تکرار موفق نسخه"""
        async def test():
            original_prescription = PrescriptionHistory.objects.create(
                patient=self.patient_profile,
                prescribed_by=self.doctor,
                medication_name='آموکسی‌سیلین',
                dosage='500mg',
                frequency='روزی 3 بار',
                duration='7 روز',
                diagnosis='عفونت',
                start_date=date.today() - timedelta(days=10),
                end_date=date.today() - timedelta(days=3),
                status='completed',
                is_repeat_allowed=True,
                max_repeats=3,
                repeat_count=0
            )
            
            success, result = await self.service.repeat_prescription(
                original_prescription.id, self.doctor, 'تکرار برای ادامه درمان'
            )
            
            self.assertTrue(success)
            self.assertIn('new_prescription', result)
            
            # بررسی نسخه جدید
            new_prescription = PrescriptionHistory.objects.get(
                id=result['new_prescription']['id']
            )
            self.assertEqual(new_prescription.medication_name, 'آموکسی‌سیلین')
            self.assertNotEqual(new_prescription.prescription_number, 
                               original_prescription.prescription_number)
            
            # بررسی بروزرسانی نسخه اصلی
            original_prescription.refresh_from_db()
            self.assertEqual(original_prescription.repeat_count, 1)
        
        self.run_async(test())
    
    def test_repeat_prescription_not_allowed(self):
        """تست تکرار نسخه‌ای که مجاز نیست"""
        async def test():
            prescription = PrescriptionHistory.objects.create(
                patient=self.patient_profile,
                prescribed_by=self.doctor,
                medication_name='دارو',
                dosage='250mg',
                frequency='روزی 2 بار',
                duration='5 روز',
                diagnosis='بیماری',
                start_date=date.today() - timedelta(days=10),
                end_date=date.today() - timedelta(days=5),
                status='completed',
                is_repeat_allowed=False
            )
            
            success, result = await self.service.repeat_prescription(
                prescription.id, self.doctor
            )
            
            self.assertFalse(success)
            self.assertIn('error', result)
        
        self.run_async(test())


class ConsentServiceTest(AsyncTestCase):
    """تست‌های سرویس رضایت‌نامه‌ها"""
    
    def setUp(self):
        super().setUp()
        
        self.user = User.objects.create_user(
            username='09123456789',
            user_type='patient'
        )
        
        self.patient_profile = PatientProfile.objects.create(
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
        
        self.service = ConsentService()
    
    def test_create_consent_success(self):
        """تست ایجاد موفق رضایت‌نامه"""
        async def test():
            data = {
                'patient': self.patient_profile,
                'consent_type': 'treatment',
                'title': 'رضایت‌نامه درمان',
                'description': 'رضایت برای انجام درمان‌های پزشکی',
                'consent_text': 'من با انجام درمان‌های لازم موافق هستم.',
                'expiry_date': date.today() + timedelta(days=30)
            }
            
            success, result = await self.service.create_consent(data)
            
            self.assertTrue(success)
            self.assertIn('consent', result)
            self.assertEqual(result['consent']['title'], 'رضایت‌نامه درمان')
            self.assertEqual(result['consent']['status'], 'pending')
        
        self.run_async(test())
    
    def test_get_patient_consents(self):
        """تست دریافت رضایت‌نامه‌های بیمار"""
        async def test():
            # ایجاد چند رضایت‌نامه نمونه
            MedicalConsent.objects.create(
                patient=self.patient_profile,
                consent_type='treatment',
                title='رضایت‌نامه 1',
                description='توضیحات',
                consent_text='متن رضایت‌نامه',
                expiry_date=date.today() + timedelta(days=30),
                status='pending'
            )
            
            MedicalConsent.objects.create(
                patient=self.patient_profile,
                consent_type='surgery',
                title='رضایت‌نامه 2',
                description='توضیحات',
                consent_text='متن رضایت‌نامه جراحی',
                expiry_date=date.today() + timedelta(days=60),
                status='granted'
            )
            
            success, result = await self.service.get_patient_consents(
                self.patient_profile.id
            )
            
            self.assertTrue(success)
            self.assertIn('consents', result)
            self.assertEqual(len(result['consents']), 2)
        
        self.run_async(test())
    
    def test_sign_consent_success(self):
        """تست ثبت موفق رضایت"""
        async def test():
            consent = MedicalConsent.objects.create(
                patient=self.patient_profile,
                consent_type='treatment',
                title='رضایت‌نامه درمان',
                description='توضیحات',
                consent_text='متن رضایت‌نامه',
                expiry_date=date.today() + timedelta(days=30),
                status='pending'
            )
            
            sign_data = {
                'digital_signature': 'sample_signature_data',
                'confirm': True
            }
            
            client_info = {
                'ip_address': '127.0.0.1',
                'user_agent': 'Test Agent'
            }
            
            success, result = await self.service.sign_consent(
                consent.id, sign_data, client_info
            )
            
            self.assertTrue(success)
            self.assertIn('consent', result)
            self.assertEqual(result['consent']['status'], 'granted')
            
            # بررسی بروزرسانی در دیتابیس
            consent.refresh_from_db()
            self.assertEqual(consent.status, 'granted')
            self.assertIsNotNone(consent.consent_date)
            self.assertEqual(consent.ip_address, '127.0.0.1')
        
        self.run_async(test())
    
    def test_sign_expired_consent(self):
        """تست ثبت رضایت برای رضایت‌نامه منقضی"""
        async def test():
            consent = MedicalConsent.objects.create(
                patient=self.patient_profile,
                consent_type='treatment',
                title='رضایت‌نامه منقضی',
                description='توضیحات',
                consent_text='متن رضایت‌نامه',
                expiry_date=date.today() - timedelta(days=1),  # منقضی شده
                status='pending'
            )
            
            sign_data = {
                'digital_signature': 'sample_signature_data',
                'confirm': True
            }
            
            client_info = {
                'ip_address': '127.0.0.1',
                'user_agent': 'Test Agent'
            }
            
            success, result = await self.service.sign_consent(
                consent.id, sign_data, client_info
            )
            
            self.assertFalse(success)
            self.assertIn('error', result)
        
        self.run_async(test())
    
    def test_revoke_consent_success(self):
        """تست لغو موفق رضایت"""
        async def test():
            consent = MedicalConsent.objects.create(
                patient=self.patient_profile,
                consent_type='treatment',
                title='رضایت‌نامه',
                description='توضیحات',
                consent_text='متن رضایت‌نامه',
                expiry_date=date.today() + timedelta(days=30),
                status='granted'
            )
            
            revoke_data = {
                'reason': 'تغییر نظر بیمار'
            }
            
            success, result = await self.service.revoke_consent(
                consent.id, revoke_data
            )
            
            self.assertTrue(success)
            self.assertIn('consent', result)
            self.assertEqual(result['consent']['status'], 'revoked')
            
            # بررسی بروزرسانی در دیتابیس
            consent.refresh_from_db()
            self.assertEqual(consent.status, 'revoked')
        
        self.run_async(test())


class CacheIntegrationTest(AsyncTestCase):
    """تست‌های یکپارچگی cache"""
    
    def setUp(self):
        super().setUp()
        
        self.user = User.objects.create_user(
            username='09123456789',
            user_type='patient'
        )
        
        self.patient_profile = PatientProfile.objects.create(
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
        
        self.service = PatientService()
    
    def test_patient_profile_cache(self):
        """تست cache پروفایل بیمار"""
        async def test():
            # دریافت اول - از دیتابیس
            success1, result1 = await self.service.get_patient_profile(
                self.patient_profile.id
            )
            
            # دریافت دوم - از cache
            success2, result2 = await self.service.get_patient_profile(
                self.patient_profile.id
            )
            
            self.assertTrue(success1)
            self.assertTrue(success2)
            self.assertEqual(result1['patient']['id'], result2['patient']['id'])
            
            # بررسی وجود در cache
            cache_key = f"patient_profile:{self.patient_profile.id}"
            cached_data = cache.get(cache_key)
            self.assertIsNotNone(cached_data)
        
        self.run_async(test())
    
    def test_cache_invalidation_on_update(self):
        """تست invalidation cache هنگام بروزرسانی"""
        async def test():
            # دریافت و ذخیره در cache
            await self.service.get_patient_profile(self.patient_profile.id)
            
            # بروزرسانی
            update_data = {'first_name': 'علی'}
            await self.service.update_patient_profile(
                self.patient_profile.id, update_data, self.user
            )
            
            # بررسی invalidation cache
            cache_key = f"patient_profile:{self.patient_profile.id}"
            cached_data = cache.get(cache_key)
            # باید null باشد یا داده‌های جدید داشته باشد
            if cached_data is not None:
                self.assertEqual(cached_data['first_name'], 'علی')
        
        self.run_async(test())


class ServiceErrorHandlingTest(AsyncTestCase):
    """تست‌های مدیریت خطا در سرویس‌ها"""
    
    def setUp(self):
        super().setUp()
        self.service = PatientService()
    
    def test_database_error_handling(self):
        """تست مدیریت خطای دیتابیس"""
        async def test():
            with patch('patient.models.PatientProfile.objects.create') as mock_create:
                mock_create.side_effect = Exception("Database error")
                
                data = {
                    'national_code': '1234567890',
                    'first_name': 'تست',
                    'last_name': 'خطا'
                }
                
                success, result = await self.service.create_patient_profile(data)
                
                self.assertFalse(success)
                self.assertIn('error', result)
        
        self.run_async(test())
    
    def test_validation_error_handling(self):
        """تست مدیریت خطای اعتبارسنجی"""
        async def test():
            # داده‌های نامعتبر
            data = {
                'national_code': '123',  # کوتاه
                'first_name': '',  # خالی
                'birth_date': 'invalid_date'
            }
            
            success, result = await self.service.create_patient_profile(data)
            
            self.assertFalse(success)
            self.assertIn('validation_errors', result)
        
        self.run_async(test())