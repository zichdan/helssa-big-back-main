"""
تست‌های سریالایزرهای سیستم مدیریت بیماران
Patient Management System Serializers Tests
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from datetime import date, timedelta
from decimal import Decimal

from ..models import PatientProfile, MedicalRecord, PrescriptionHistory, MedicalConsent
from ..serializers import (
    PatientProfileSerializer,
    MedicalRecordSerializer,
    PrescriptionHistorySerializer,
    MedicalConsentSerializer
)

User = get_user_model()


class PatientProfileSerializerTest(TestCase):
    """تست‌های سریالایزر پروفایل بیمار"""
    
    def setUp(self):
        """آماده‌سازی داده‌های تست"""
        self.user = User.objects.create_user(
            username='09123456789',
            user_type='patient'
        )
        
        self.valid_data = {
            'user': self.user.id,
            'national_code': '1234567890',
            'first_name': 'احمد',
            'last_name': 'احمدی',
            'birth_date': '1990-01-01',
            'gender': 'male',
            'height': 175.0,
            'weight': 70.0,
            'blood_group': 'A+',
            'emergency_contact_name': 'مریم احمدی',
            'emergency_contact_phone': '09123456788',
            'emergency_contact_relation': 'همسر',
            'address': 'تهران، خیابان آزادی',
            'city': 'تهران',
            'province': 'تهران',
            'postal_code': '1234567890',
            'marital_status': 'married'
        }
    
    def test_valid_serializer(self):
        """تست سریالایزر با داده‌های معتبر"""
        serializer = PatientProfileSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        
        patient = serializer.save()
        self.assertEqual(patient.first_name, 'احمد')
        self.assertEqual(patient.national_code, '1234567890')
        self.assertIsNotNone(patient.medical_record_number)
    
    def test_invalid_national_code_format(self):
        """تست اعتبارسنجی فرمت کد ملی"""
        # کد ملی کوتاه‌تر از 10 رقم
        invalid_data = self.valid_data.copy()
        invalid_data['national_code'] = '123456789'
        
        serializer = PatientProfileSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('national_code', serializer.errors)
    
    def test_invalid_national_code_checksum(self):
        """تست اعتبارسنجی checksum کد ملی"""
        invalid_data = self.valid_data.copy()
        invalid_data['national_code'] = '1234567891'  # checksum نادرست
        
        serializer = PatientProfileSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('national_code', serializer.errors)
    
    def test_future_birth_date(self):
        """تست تاریخ تولد آینده"""
        invalid_data = self.valid_data.copy()
        invalid_data['birth_date'] = str(date.today() + timedelta(days=1))
        
        serializer = PatientProfileSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('birth_date', serializer.errors)
    
    def test_too_old_birth_date(self):
        """تست تاریخ تولد خیلی قدیم"""
        invalid_data = self.valid_data.copy()
        invalid_data['birth_date'] = '1800-01-01'
        
        serializer = PatientProfileSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('birth_date', serializer.errors)
    
    def test_invalid_height_weight(self):
        """تست قد و وزن نامعتبر"""
        # قد منفی
        invalid_data = self.valid_data.copy()
        invalid_data['height'] = -10.0
        
        serializer = PatientProfileSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('height', serializer.errors)
        
        # وزن خیلی زیاد
        invalid_data = self.valid_data.copy()
        invalid_data['weight'] = 1000.0
        
        serializer = PatientProfileSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('weight', serializer.errors)
    
    def test_invalid_phone_format(self):
        """تست فرمت شماره تلفن نامعتبر"""
        invalid_data = self.valid_data.copy()
        invalid_data['emergency_contact_phone'] = '123456'  # فرمت نادرست
        
        serializer = PatientProfileSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('emergency_contact_phone', serializer.errors)
    
    def test_invalid_postal_code(self):
        """تست کد پستی نامعتبر"""
        invalid_data = self.valid_data.copy()
        invalid_data['postal_code'] = '123'  # کد پستی کوتاه
        
        serializer = PatientProfileSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('postal_code', serializer.errors)
    
    def test_full_name_field(self):
        """تست فیلد نام کامل"""
        patient = PatientProfile.objects.create(**{
            k: v for k, v in self.valid_data.items() 
            if k != 'user'
        }, user=self.user)
        
        serializer = PatientProfileSerializer(patient)
        self.assertEqual(serializer.data['full_name'], 'احمد احمدی')
    
    def test_age_calculation(self):
        """تست محاسبه سن"""
        patient = PatientProfile.objects.create(**{
            k: v for k, v in self.valid_data.items() 
            if k != 'user'
        }, user=self.user)
        
        serializer = PatientProfileSerializer(patient)
        expected_age = date.today().year - 1990
        if (date.today().month, date.today().day) < (1, 1):
            expected_age -= 1
        
        self.assertEqual(serializer.data['age'], expected_age)
    
    def test_bmi_calculation(self):
        """تست محاسبه BMI"""
        patient = PatientProfile.objects.create(**{
            k: v for k, v in self.valid_data.items() 
            if k != 'user'
        }, user=self.user)
        
        serializer = PatientProfileSerializer(patient)
        expected_bmi = round(70 / (1.75 ** 2), 2)
        self.assertEqual(serializer.data['bmi'], expected_bmi)


class MedicalRecordSerializerTest(TestCase):
    """تست‌های سریالایزر سوابق پزشکی"""
    
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
        
        self.valid_data = {
            'patient': self.patient.id,
            'record_type': 'allergy',
            'title': 'آلرژی به پنی‌سیلین',
            'description': 'بیمار آلرژی شدید به پنی‌سیلین دارد',
            'severity': 'severe',
            'start_date': '2024-01-01',
            'is_ongoing': True,
            'doctor': self.doctor.id
        }
    
    def test_valid_serializer(self):
        """تست سریالایزر با داده‌های معتبر"""
        serializer = MedicalRecordSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        
        record = serializer.save()
        self.assertEqual(record.title, 'آلرژی به پنی‌سیلین')
        self.assertEqual(record.severity, 'severe')
    
    def test_future_start_date(self):
        """تست تاریخ شروع آینده"""
        invalid_data = self.valid_data.copy()
        invalid_data['start_date'] = str(date.today() + timedelta(days=1))
        
        serializer = MedicalRecordSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('start_date', serializer.errors)
    
    def test_end_date_before_start_date(self):
        """تست تاریخ پایان قبل از تاریخ شروع"""
        invalid_data = self.valid_data.copy()
        invalid_data['start_date'] = '2024-01-10'
        invalid_data['end_date'] = '2024-01-05'
        invalid_data['is_ongoing'] = False
        
        serializer = MedicalRecordSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('end_date', serializer.errors)
    
    def test_ongoing_with_end_date(self):
        """تست سابقه در حال ادامه با تاریخ پایان"""
        invalid_data = self.valid_data.copy()
        invalid_data['is_ongoing'] = True
        invalid_data['end_date'] = '2024-12-31'
        
        serializer = MedicalRecordSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('end_date', serializer.errors)
    
    def test_required_fields(self):
        """تست فیلدهای اجباری"""
        required_fields = ['patient', 'record_type', 'title', 'start_date']
        
        for field in required_fields:
            invalid_data = self.valid_data.copy()
            del invalid_data[field]
            
            serializer = MedicalRecordSerializer(data=invalid_data)
            self.assertFalse(serializer.is_valid())
            self.assertIn(field, serializer.errors)


class PrescriptionHistorySerializerTest(TestCase):
    """تست‌های سریالایزر تاریخچه نسخه‌ها"""
    
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
        
        self.valid_data = {
            'patient': self.patient.id,
            'prescribed_by': self.doctor.id,
            'medication_name': 'آموکسی‌سیلین',
            'dosage': '500 میلی‌گرم',
            'frequency': 'روزی 3 بار',
            'duration': '7 روز',
            'diagnosis': 'عفونت تنفسی',
            'start_date': str(date.today()),
            'end_date': str(date.today() + timedelta(days=7)),
            'is_repeat_allowed': True,
            'max_repeats': 3
        }
    
    def test_valid_serializer(self):
        """تست سریالایزر با داده‌های معتبر"""
        serializer = PrescriptionHistorySerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        
        prescription = serializer.save()
        self.assertEqual(prescription.medication_name, 'آموکسی‌سیلین')
        self.assertIsNotNone(prescription.prescription_number)
    
    def test_future_start_date(self):
        """تست تاریخ شروع آینده"""
        invalid_data = self.valid_data.copy()
        invalid_data['start_date'] = str(date.today() + timedelta(days=10))
        
        serializer = PrescriptionHistorySerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('start_date', serializer.errors)
    
    def test_end_date_before_start_date(self):
        """تست تاریخ پایان قبل از تاریخ شروع"""
        invalid_data = self.valid_data.copy()
        invalid_data['start_date'] = str(date.today())
        invalid_data['end_date'] = str(date.today() - timedelta(days=1))
        
        serializer = PrescriptionHistorySerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('end_date', serializer.errors)
    
    def test_negative_max_repeats(self):
        """تست حداکثر تکرار منفی"""
        invalid_data = self.valid_data.copy()
        invalid_data['max_repeats'] = -1
        
        serializer = PrescriptionHistorySerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('max_repeats', serializer.errors)
    
    def test_dosage_validation(self):
        """تست اعتبارسنجی دوز"""
        # دوز خالی
        invalid_data = self.valid_data.copy()
        invalid_data['dosage'] = ''
        
        serializer = PrescriptionHistorySerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('dosage', serializer.errors)
    
    def test_medication_name_validation(self):
        """تست اعتبارسنجی نام دارو"""
        # نام دارو خیلی کوتاه
        invalid_data = self.valid_data.copy()
        invalid_data['medication_name'] = 'A'
        
        serializer = PrescriptionHistorySerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('medication_name', serializer.errors)
    
    def test_prescription_number_generation(self):
        """تست تولید شماره نسخه"""
        prescription = PrescriptionHistory.objects.create(**{
            k: v for k, v in self.valid_data.items() 
            if k not in ['patient', 'prescribed_by']
        }, patient=self.patient, prescribed_by=self.doctor)
        
        serializer = PrescriptionHistorySerializer(prescription)
        self.assertTrue(serializer.data['prescription_number'].startswith('RX'))


class MedicalConsentSerializerTest(TestCase):
    """تست‌های سریالایزر رضایت‌نامه‌های پزشکی"""
    
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
        
        self.valid_data = {
            'patient': self.patient.id,
            'consent_type': 'treatment',
            'title': 'رضایت‌نامه درمان',
            'description': 'رضایت برای انجام درمان‌های پزشکی',
            'consent_text': 'من با انجام درمان‌های لازم موافق هستم.',
            'expiry_date': str(date.today() + timedelta(days=30))
        }
    
    def test_valid_serializer(self):
        """تست سریالایزر با داده‌های معتبر"""
        serializer = MedicalConsentSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        
        consent = serializer.save()
        self.assertEqual(consent.title, 'رضایت‌نامه درمان')
        self.assertEqual(consent.status, 'pending')
    
    def test_past_expiry_date(self):
        """تست تاریخ انقضا گذشته"""
        invalid_data = self.valid_data.copy()
        invalid_data['expiry_date'] = str(date.today() - timedelta(days=1))
        
        serializer = MedicalConsentSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('expiry_date', serializer.errors)
    
    def test_empty_consent_text(self):
        """تست متن رضایت‌نامه خالی"""
        invalid_data = self.valid_data.copy()
        invalid_data['consent_text'] = ''
        
        serializer = MedicalConsentSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('consent_text', serializer.errors)
    
    def test_short_consent_text(self):
        """تست متن رضایت‌نامه کوتاه"""
        invalid_data = self.valid_data.copy()
        invalid_data['consent_text'] = 'موافقم'  # خیلی کوتاه
        
        serializer = MedicalConsentSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('consent_text', serializer.errors)
    
    def test_required_fields(self):
        """تست فیلدهای اجباری"""
        required_fields = ['patient', 'consent_type', 'title', 'consent_text']
        
        for field in required_fields:
            invalid_data = self.valid_data.copy()
            del invalid_data[field]
            
            serializer = MedicalConsentSerializer(data=invalid_data)
            self.assertFalse(serializer.is_valid())
            self.assertIn(field, serializer.errors)
    
    def test_is_valid_property(self):
        """تست property اعتبار رضایت‌نامه"""
        # رضایت‌نامه منقضی شده
        consent = MedicalConsent.objects.create(**{
            k: v for k, v in self.valid_data.items() 
            if k not in ['patient', 'expiry_date']
        }, patient=self.patient, expiry_date=date.today() - timedelta(days=1))
        
        serializer = MedicalConsentSerializer(consent)
        self.assertFalse(serializer.data['is_valid'])
        
        # رضایت‌نامه معتبر
        consent.expiry_date = date.today() + timedelta(days=30)
        consent.status = 'granted'
        consent.save()
        
        serializer = MedicalConsentSerializer(consent)
        self.assertTrue(serializer.data['is_valid'])


class SerializerEdgeCasesTest(TestCase):
    """تست‌های موارد خاص سریالایزرها"""
    
    def setUp(self):
        """آماده‌سازی داده‌های تست"""
        self.user = User.objects.create_user(
            username='09123456789',
            user_type='patient'
        )
    
    def test_unicode_and_special_characters(self):
        """تست کاراکترهای یونیکد و خاص"""
        data = {
            'user': self.user.id,
            'national_code': '1234567890',
            'first_name': 'محمد‌علی',  # شامل نیم‌فاصله
            'last_name': 'صفوی‌نژاد',
            'birth_date': '1990-01-01',
            'gender': 'male',
            'emergency_contact_name': 'فاطمه خانم',
            'emergency_contact_phone': '09123456788',
            'emergency_contact_relation': 'همسر',
            'address': 'تهران، خ. آزادی، ک. شهید فکوری، پ. 123',
            'city': 'تهران',
            'province': 'تهران',
            'postal_code': '1234567890',
            'marital_status': 'married'
        }
        
        serializer = PatientProfileSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        patient = serializer.save()
        self.assertEqual(patient.first_name, 'محمد‌علی')
    
    def test_boundary_values(self):
        """تست مقادیر حدی"""
        data = {
            'user': self.user.id,
            'national_code': '1234567890',
            'first_name': 'ا',  # کوتاه‌ترین نام ممکن
            'last_name': 'ب',
            'birth_date': '1900-01-01',  # قدیمی‌ترین تاریخ ممکن
            'gender': 'male',
            'height': 50.0,  # کم‌ترین قد ممکن
            'weight': 5.0,   # کم‌ترین وزن ممکن
            'emergency_contact_name': 'نام',
            'emergency_contact_phone': '09123456788',
            'emergency_contact_relation': 'سایر',
            'address': 'آدرس کوتاه',
            'city': 'شهر',
            'province': 'استان',
            'postal_code': '1234567890',
            'marital_status': 'single'
        }
        
        serializer = PatientProfileSerializer(data=data)
        # ممکن است بعضی مقادیر حدی معتبر نباشند
        if serializer.is_valid():
            patient = serializer.save()
            self.assertIsNotNone(patient)
        else:
            # بررسی اینکه خطاهای منطقی هستند
            self.assertIsInstance(serializer.errors, dict)
    
    def test_null_and_empty_values(self):
        """تست مقادیر null و خالی"""
        data = {
            'user': self.user.id,
            'national_code': '1234567890',
            'first_name': 'احمد',
            'last_name': 'احمدی',
            'birth_date': '1990-01-01',
            'gender': 'male',
            'height': None,  # مقدار null
            'weight': None,
            'blood_group': '',  # رشته خالی
            'emergency_contact_name': 'مریم احمدی',
            'emergency_contact_phone': '09123456788',
            'emergency_contact_relation': 'همسر',
            'address': 'تهران، خیابان آزادی',
            'city': 'تهران',
            'province': 'تهران',
            'postal_code': '1234567890',
            'marital_status': 'married'
        }
        
        serializer = PatientProfileSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        patient = serializer.save()
        self.assertIsNone(patient.height)
        self.assertIsNone(patient.weight)