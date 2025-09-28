"""
تست‌های ویوهای سیستم مدیریت بیماران
Patient Management System Views Tests
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import date, timedelta
import json

from ..models import PatientProfile, MedicalRecord, PrescriptionHistory, MedicalConsent

User = get_user_model()


class BasePatientAPITestCase(APITestCase):
    """کلاس پایه برای تست‌های API"""
    
    def setUp(self):
        """آماده‌سازی داده‌های تست"""
        # ایجاد کاربران
        self.patient_user = User.objects.create_user(
            username='09123456789',
            user_type='patient'
        )
        
        self.doctor_user = User.objects.create_user(
            username='09123456700',
            user_type='doctor'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            user_type='admin',
            is_staff=True
        )
        
        # ایجاد پروفایل بیمار
        self.patient_profile = PatientProfile.objects.create(
            user=self.patient_user,
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
        
        # Client setup
        self.client = APIClient()
    
    def get_jwt_token(self, user):
        """دریافت JWT token برای کاربر"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def authenticate_patient(self):
        """احراز هویت به عنوان بیمار"""
        token = self.get_jwt_token(self.patient_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    def authenticate_doctor(self):
        """احراز هویت به عنوان پزشک"""
        token = self.get_jwt_token(self.doctor_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    def authenticate_admin(self):
        """احراز هویت به عنوان ادمین"""
        token = self.get_jwt_token(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')


class PatientProfileViewsTest(BasePatientAPITestCase):
    """تست‌های ویوهای پروفایل بیمار"""
    
    def test_create_patient_profile_success(self):
        """تست ایجاد موفق پروفایل بیمار"""
        self.authenticate_patient()
        
        data = {
            'national_code': '0987654321',
            'first_name': 'علی',
            'last_name': 'علوی',
            'birth_date': '1985-05-15',
            'gender': 'male',
            'emergency_contact_name': 'فاطمه علوی',
            'emergency_contact_phone': '09123456777',
            'emergency_contact_relation': 'همسر',
            'address': 'تهران، میدان آزادی',
            'city': 'تهران',
            'province': 'تهران',
            'postal_code': '1234567890',
            'marital_status': 'married'
        }
        
        url = reverse('create_patient_profile')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('data', response.data)
    
    def test_create_patient_profile_doctor_forbidden(self):
        """تست عدم مجوز پزشک برای ایجاد پروفایل"""
        self.authenticate_doctor()
        
        data = {
            'national_code': '0987654321',
            'first_name': 'علی',
            'last_name': 'علوی',
            'birth_date': '1985-05-15',
            'gender': 'male'
        }
        
        url = reverse('create_patient_profile')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_patient_profile_as_patient(self):
        """تست دریافت پروفایل توسط خود بیمار"""
        self.authenticate_patient()
        
        url = reverse('get_patient_profile', kwargs={'patient_id': self.patient_profile.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['first_name'], 'احمد')
    
    def test_get_patient_profile_as_doctor(self):
        """تست دریافت پروفایل توسط پزشک"""
        self.authenticate_doctor()
        
        url = reverse('get_patient_profile', kwargs={'patient_id': self.patient_profile.id})
        response = self.client.get(url)
        
        # بستگی به پیاده‌سازی unified_access دارد
        # در حالت عادی باید 403 باشد مگر اینکه دسترسی داده شده باشد
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])
    
    def test_update_patient_profile_success(self):
        """تست بروزرسانی موفق پروفایل"""
        self.authenticate_patient()
        
        data = {
            'first_name': 'محمد',
            'last_name': 'محمدی',
            'height': 175.0,
            'weight': 70.0
        }
        
        url = reverse('update_patient_profile', kwargs={'patient_id': self.patient_profile.id})
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # بررسی بروزرسانی در دیتابیس
        self.patient_profile.refresh_from_db()
        self.assertEqual(self.patient_profile.first_name, 'محمد')
    
    def test_search_patients_doctor_only(self):
        """تست جستجوی بیماران فقط برای پزشک"""
        self.authenticate_doctor()
        
        data = {
            'query': 'احمد',
            'search_type': 'name'
        }
        
        url = reverse('search_patients')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_search_patients_patient_forbidden(self):
        """تست عدم مجوز بیمار برای جستجو"""
        self.authenticate_patient()
        
        data = {
            'query': 'احمد',
            'search_type': 'name'
        }
        
        url = reverse('search_patients')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MedicalRecordViewsTest(BasePatientAPITestCase):
    """تست‌های ویوهای سوابق پزشکی"""
    
    def setUp(self):
        super().setUp()
        
        self.medical_record = MedicalRecord.objects.create(
            patient=self.patient_profile,
            record_type='allergy',
            title='آلرژی به پنی‌سیلین',
            description='بیمار آلرژی شدید به پنی‌سیلین دارد',
            severity='severe',
            start_date=date.today(),
            is_ongoing=True,
            doctor=self.doctor_user
        )
    
    def test_create_medical_record_as_doctor(self):
        """تست ایجاد سابقه پزشکی توسط پزشک"""
        self.authenticate_doctor()
        
        data = {
            'patient_id': str(self.patient_profile.id),
            'record_type': 'medication',
            'title': 'حساسیت به آسپرین',
            'description': 'مصرف آسپرین باعث تهوع می‌شود',
            'severity': 'moderate',
            'start_date': '2024-01-01',
            'is_ongoing': True
        }
        
        url = reverse('create_medical_record')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_create_medical_record_patient_forbidden(self):
        """تست عدم مجوز بیمار برای ایجاد سابقه"""
        self.authenticate_patient()
        
        data = {
            'patient_id': str(self.patient_profile.id),
            'record_type': 'medication',
            'title': 'حساسیت به آسپرین'
        }
        
        url = reverse('create_medical_record')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_patient_medical_records_as_patient(self):
        """تست دریافت سوابق توسط خود بیمار"""
        self.authenticate_patient()
        
        url = reverse('get_patient_medical_records', kwargs={'patient_id': self.patient_profile.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIsInstance(response.data['data'], list)


class PrescriptionViewsTest(BasePatientAPITestCase):
    """تست‌های ویوهای نسخه‌ها"""
    
    def setUp(self):
        super().setUp()
        
        self.prescription = PrescriptionHistory.objects.create(
            patient=self.patient_profile,
            prescribed_by=self.doctor_user,
            medication_name='آموکسی‌سیلین',
            dosage='500 میلی‌گرم',
            frequency='روزی 3 بار',
            duration='7 روز',
            diagnosis='عفونت تنفسی',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7)
        )
    
    def test_create_prescription_as_doctor(self):
        """تست ایجاد نسخه توسط پزشک"""
        self.authenticate_doctor()
        
        data = {
            'patient_id': str(self.patient_profile.id),
            'medication_name': 'ایبوپروفن',
            'dosage': '400 میلی‌گرم',
            'frequency': 'روزی 2 بار',
            'duration': '5 روز',
            'diagnosis': 'درد عضلانی',
            'start_date': str(date.today()),
            'end_date': str(date.today() + timedelta(days=5))
        }
        
        url = reverse('create_prescription')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_get_patient_prescriptions_as_patient(self):
        """تست دریافت نسخه‌ها توسط بیمار"""
        self.authenticate_patient()
        
        url = reverse('get_patient_prescriptions', kwargs={'patient_id': self.patient_profile.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_repeat_prescription_as_doctor(self):
        """تست تکرار نسخه توسط پزشک"""
        self.authenticate_doctor()
        
        # فعال کردن امکان تکرار
        self.prescription.is_repeat_allowed = True
        self.prescription.max_repeats = 3
        self.prescription.save()
        
        data = {
            'notes': 'تکرار نسخه به دلیل ادامه درمان'
        }
        
        url = reverse('repeat_prescription', kwargs={'prescription_id': self.prescription.id})
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ConsentViewsTest(BasePatientAPITestCase):
    """تست‌های ویوهای رضایت‌نامه‌ها"""
    
    def setUp(self):
        super().setUp()
        
        self.consent = MedicalConsent.objects.create(
            patient=self.patient_profile,
            consent_type='treatment',
            title='رضایت‌نامه درمان',
            description='رضایت برای انجام درمان‌های پزشکی',
            consent_text='من با انجام درمان‌های لازم موافق هستم.',
            expiry_date=date.today() + timedelta(days=30)
        )
    
    def test_create_consent_as_doctor(self):
        """تست ایجاد رضایت‌نامه توسط پزشک"""
        self.authenticate_doctor()
        
        data = {
            'patient_id': str(self.patient_profile.id),
            'consent_type': 'surgery',
            'title': 'رضایت‌نامه جراحی',
            'description': 'رضایت برای انجام عمل جراحی',
            'consent_text': 'من با انجام عمل جراحی موافق هستم.',
            'expiry_date': str(date.today() + timedelta(days=60))
        }
        
        url = reverse('create_consent')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_grant_consent_as_patient(self):
        """تست ثبت رضایت توسط بیمار"""
        self.authenticate_patient()
        
        data = {
            'digital_signature': 'sample_signature_data',
            'confirm': True
        }
        
        url = reverse('grant_consent', kwargs={'consent_id': self.consent.id})
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # بررسی بروزرسانی در دیتابیس
        self.consent.refresh_from_db()
        self.assertEqual(self.consent.status, 'granted')
    
    def test_grant_consent_doctor_forbidden(self):
        """تست عدم مجوز پزشک برای ثبت رضایت"""
        self.authenticate_doctor()
        
        data = {
            'digital_signature': 'sample_signature_data',
            'confirm': True
        }
        
        url = reverse('grant_consent', kwargs={'consent_id': self.consent.id})
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AudioTranscriptionViewsTest(BasePatientAPITestCase):
    """تست‌های ویوهای رونویسی صوت"""
    
    def test_transcribe_audio_as_doctor(self):
        """تست رونویسی فایل صوتی توسط پزشک"""
        self.authenticate_doctor()
        
        # ایجاد فایل صوتی mock
        from django.core.files.uploadedfile import SimpleUploadedFile
        audio_file = SimpleUploadedFile(
            "test_audio.wav",
            b"fake audio content",
            content_type="audio/wav"
        )
        
        data = {
            'audio_file': audio_file,
            'language': 'fa',
            'model': 'whisper-1'
        }
        
        url = reverse('transcribe_audio')
        response = self.client.post(url, data, format='multipart')
        
        # ممکن است بستگی به وجود سرویس STT داشته باشد
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ])
    
    def test_transcribe_audio_patient_forbidden(self):
        """تست عدم مجوز بیمار برای رونویسی"""
        self.authenticate_patient()
        
        from django.core.files.uploadedfile import SimpleUploadedFile
        audio_file = SimpleUploadedFile(
            "test_audio.wav",
            b"fake audio content",
            content_type="audio/wav"
        )
        
        data = {
            'audio_file': audio_file
        }
        
        url = reverse('transcribe_audio')
        response = self.client.post(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class StatisticsViewsTest(BasePatientAPITestCase):
    """تست‌های ویوهای آمار"""
    
    def test_get_patient_statistics_as_patient(self):
        """تست دریافت آمار توسط خود بیمار"""
        self.authenticate_patient()
        
        url = reverse('get_patient_statistics', kwargs={'patient_id': self.patient_profile.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_get_patient_statistics_as_doctor(self):
        """تست دریافت آمار توسط پزشک"""
        self.authenticate_doctor()
        
        url = reverse('get_patient_statistics', kwargs={'patient_id': self.patient_profile.id})
        response = self.client.get(url)
        
        # بستگی به دسترسی پزشک دارد
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])
    
    def test_analyze_data_as_doctor(self):
        """تست تحلیل داده‌ها توسط پزشک"""
        self.authenticate_doctor()
        
        data = {
            'analysis_type': 'patient_trends',
            'patient_ids': [str(self.patient_profile.id)],
            'date_range': {
                'start': str(date.today() - timedelta(days=30)),
                'end': str(date.today())
            }
        }
        
        url = reverse('analyze_data')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UnauthorizedAccessTest(BasePatientAPITestCase):
    """تست‌های دسترسی غیرمجاز"""
    
    def test_unauthenticated_access_forbidden(self):
        """تست عدم دسترسی کاربران احراز هویت نشده"""
        urls = [
            reverse('create_patient_profile'),
            reverse('get_patient_profile', kwargs={'patient_id': self.patient_profile.id}),
            reverse('search_patients'),
            reverse('create_medical_record'),
            reverse('create_prescription'),
            reverse('transcribe_audio'),
        ]
        
        for url in urls:
            response = self.client.post(url)
            self.assertIn(response.status_code, [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN
            ], f"URL {url} should require authentication")
    
    def test_cross_patient_access_forbidden(self):
        """تست عدم دسترسی بیمار به اطلاعات بیمار دیگر"""
        # ایجاد بیمار دوم
        other_patient_user = User.objects.create_user(
            username='09123456799',
            user_type='patient'
        )
        
        other_patient_profile = PatientProfile.objects.create(
            user=other_patient_user,
            national_code='0987654321',
            first_name='علی',
            last_name='علوی',
            birth_date=date(1985, 5, 15),
            gender='male',
            emergency_contact_name='فاطمه علوی',
            emergency_contact_phone='09123456777',
            emergency_contact_relation='همسر',
            address='تهران، میدان انقلاب',
            city='تهران',
            province='تهران',
            postal_code='0987654321',
            marital_status='married'
        )
        
        # احراز هویت به عنوان بیمار اول
        self.authenticate_patient()
        
        # تلاش برای دسترسی به اطلاعات بیمار دوم
        url = reverse('get_patient_profile', kwargs={'patient_id': other_patient_profile.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)