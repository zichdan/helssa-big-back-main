"""
نمونه کدهای تست برای ایجنت‌ها
Sample Test Code Examples for Agents
"""

from django.test import TestCase, TransactionTestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, Mock
import json
from decimal import Decimal
from datetime import datetime, timedelta

User = get_user_model()


# ====================================
# نمونه 1: Model Tests
# ====================================

class PatientProfileModelTest(TestCase):
    """
    تست‌های مدل پروفایل بیمار
    """
    
    @classmethod
    def setUpTestData(cls):
        """داده‌های تست که یکبار ایجاد می‌شوند"""
        cls.user = User.objects.create_user(
            username='patient1',
            password='testpass123',
            first_name='علی',
            last_name='احمدی',
            user_type='patient'
        )
    
    def setUp(self):
        """اجرا قبل از هر تست"""
        from patient_records.models import PatientProfile
        self.profile = PatientProfile.objects.create(
            patient=self.user,
            national_code='1234567890',
            date_of_birth='1990-01-01',
            gender='male',
            phone_number='09123456789'
        )
    
    def test_profile_creation(self):
        """تست ایجاد پروفایل"""
        self.assertTrue(isinstance(self.profile, PatientProfile))
        self.assertEqual(self.profile.patient, self.user)
        self.assertEqual(str(self.profile), f"{self.user.get_full_name()} - 1234567890")
    
    def test_age_calculation(self):
        """تست محاسبه سن"""
        expected_age = timezone.now().year - 1990
        self.assertEqual(self.profile.age, expected_age)
    
    def test_unique_national_code(self):
        """تست یکتا بودن کد ملی"""
        from django.db import IntegrityError
        
        user2 = User.objects.create_user(
            username='patient2',
            password='testpass123',
            user_type='patient'
        )
        
        with self.assertRaises(IntegrityError):
            PatientProfile.objects.create(
                patient=user2,
                national_code='1234567890',  # کد ملی تکراری
                date_of_birth='1995-01-01',
                gender='female',
                phone_number='09123456780'
            )
    
    def test_model_validations(self):
        """تست اعتبارسنجی‌های مدل"""
        from django.core.exceptions import ValidationError
        
        # تست شماره تلفن نامعتبر
        self.profile.phone_number = '123'  # شماره نامعتبر
        with self.assertRaises(ValidationError):
            self.profile.full_clean()
    
    def tearDown(self):
        """پاکسازی بعد از هر تست"""
        # Django خودش transaction را rollback می‌کند


# ====================================
# نمونه 2: API View Tests
# ====================================

class PatientChatAPITest(APITestCase):
    """
    تست‌های API چت بیمار
    """
    
    def setUp(self):
        """راه‌اندازی محیط تست"""
        # ایجاد کاربر بیمار
        self.patient = User.objects.create_user(
            username='patient_test',
            password='testpass123',
            user_type='patient'
        )
        
        # ایجاد کاربر پزشک
        self.doctor = User.objects.create_user(
            username='doctor_test',
            password='testpass123',
            user_type='doctor'
        )
        
        # Client برای درخواست‌ها
        self.client = APIClient()
        
        # URLs
        self.start_chat_url = reverse('patient_chatbot:chat-start')
        self.send_message_url = lambda chat_id: reverse(
            'patient_chatbot:chat-message',
            kwargs={'chat_id': chat_id}
        )
    
    def test_start_chat_authenticated(self):
        """تست شروع چت با احراز هویت"""
        self.client.force_authenticate(user=self.patient)
        
        response = self.client.post(self.start_chat_url, {
            'chief_complaint': 'سردرد شدید'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('chat_id', response.data)
        self.assertIn('message', response.data)
    
    def test_start_chat_unauthenticated(self):
        """تست شروع چت بدون احراز هویت"""
        response = self.client.post(self.start_chat_url, {
            'chief_complaint': 'سردرد'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_doctor_cannot_use_patient_chat(self):
        """تست عدم دسترسی پزشک به چت بیمار"""
        self.client.force_authenticate(user=self.doctor)
        
        response = self.client.post(self.start_chat_url, {
            'chief_complaint': 'تست'
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    @patch('unified_ai.services.UnifiedAIService.process_text')
    def test_send_message_with_ai_response(self, mock_ai):
        """تست ارسال پیام و دریافت پاسخ AI"""
        # Mock کردن پاسخ AI
        mock_ai.return_value = {
            'text': 'برای سردرد می‌توانید استامینوفن مصرف کنید',
            'confidence': 0.85
        }
        
        self.client.force_authenticate(user=self.patient)
        
        # ابتدا چت را شروع کنیم
        start_response = self.client.post(self.start_chat_url, {
            'chief_complaint': 'سردرد'
        })
        chat_id = start_response.data['chat_id']
        
        # ارسال پیام
        message_response = self.client.post(
            self.send_message_url(chat_id),
            {'message': 'سردردم از دیروز شروع شده'}
        )
        
        self.assertEqual(message_response.status_code, status.HTTP_200_OK)
        self.assertIn('response', message_response.data)
        self.assertTrue(mock_ai.called)
    
    def test_rate_limiting(self):
        """تست محدودیت نرخ درخواست"""
        self.client.force_authenticate(user=self.patient)
        
        # ارسال درخواست‌های متعدد
        responses = []
        for i in range(25):  # فرض کنیم محدودیت 20 در ساعت است
            response = self.client.post(self.start_chat_url, {
                'chief_complaint': f'تست {i}'
            })
            responses.append(response.status_code)
        
        # باید در نهایت 429 دریافت کنیم
        self.assertIn(status.HTTP_429_TOO_MANY_REQUESTS, responses)


# ====================================
# نمونه 3: Integration Tests
# ====================================

class PrescriptionIntegrationTest(TransactionTestCase):
    """
    تست‌های یکپارچگی سیستم نسخه‌نویسی
    """
    
    def setUp(self):
        """راه‌اندازی محیط تست یکپارچه"""
        # ایجاد کاربران
        self.doctor = User.objects.create_user(
            username='dr_test',
            password='testpass123',
            user_type='doctor'
        )
        
        self.patient = User.objects.create_user(
            username='patient_test',
            password='testpass123',
            user_type='patient'
        )
        
        # ایجاد ویزیت
        from visit_management.models import MedicalVisit
        self.visit = MedicalVisit.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            visit_date=timezone.now() + timedelta(days=1),
            visit_type='in_person',
            chief_complaint='سرماخوردگی',
            fee=500000,
            status='scheduled'
        )
    
    def test_complete_prescription_workflow(self):
        """تست فرآیند کامل نسخه‌نویسی"""
        from prescription_system.models import Prescription, PrescriptionItem
        
        # 1. تکمیل ویزیت
        self.visit.status = 'completed'
        self.visit.diagnosis = 'سرماخوردگی ویروسی'
        self.visit.treatment_plan = 'استراحت و مایعات فراوان'
        self.visit.save()
        
        # 2. ایجاد نسخه
        prescription = Prescription.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            visit=self.visit,
            notes='مصرف داروها با معده پر'
        )
        
        # 3. افزودن اقلام نسخه
        items = [
            {
                'drug_name': 'استامینوفن 500',
                'drug_type': 'tablet',
                'dosage': '500mg',
                'frequency': 'هر 6 ساعت',
                'duration': '3 روز',
                'quantity': 12
            },
            {
                'drug_name': 'ویتامین C',
                'drug_type': 'tablet',
                'dosage': '1000mg',
                'frequency': 'روزی یکبار',
                'duration': '7 روز',
                'quantity': 7
            }
        ]
        
        for item_data in items:
            PrescriptionItem.objects.create(
                prescription=prescription,
                **item_data
            )
        
        # 4. بررسی‌ها
        self.assertEqual(prescription.items.count(), 2)
        self.assertEqual(prescription.status, 'issued')
        self.assertFalse(prescription.is_expired)
        
        # 5. تست API endpoint
        client = APIClient()
        client.force_authenticate(user=self.patient)
        
        url = reverse('prescription_system:prescription-detail', kwargs={'pk': prescription.id})
        response = client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 2)


# ====================================
# نمونه 4: Serializer Tests
# ====================================

class ChatMessageSerializerTest(TestCase):
    """
    تست‌های سریالایزر پیام چت
    """
    
    def setUp(self):
        from patient_chatbot.serializers import ChatMessageSerializer
        self.serializer_class = ChatMessageSerializer
    
    def test_valid_message(self):
        """تست پیام معتبر"""
        data = {
            'message': 'سلام، من دیروز سردرد شدیدی داشتم'
        }
        serializer = self.serializer_class(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_empty_message(self):
        """تست پیام خالی"""
        data = {'message': ''}
        serializer = self.serializer_class(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('message', serializer.errors)
    
    def test_long_message(self):
        """تست پیام بسیار طولانی"""
        data = {'message': 'x' * 1001}  # بیش از حد مجاز
        serializer = self.serializer_class(data=data)
        self.assertFalse(serializer.is_valid())
    
    def test_message_with_attachments(self):
        """تست پیام با فایل پیوست"""
        # ایجاد فایل mock
        file1 = SimpleUploadedFile(
            "test.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        
        data = {
            'message': 'نتیجه آزمایش را پیوست کردم',
            'attachments': [file1]
        }
        
        serializer = self.serializer_class(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_inappropriate_content(self):
        """تست محتوای نامناسب"""
        data = {'message': 'این یک spam است'}
        serializer = self.serializer_class(data=data)
        self.assertFalse(serializer.is_valid())


# ====================================
# نمونه 5: Permission Tests
# ====================================

class PermissionTest(APITestCase):
    """
    تست‌های دسترسی‌ها
    """
    
    def setUp(self):
        # کاربران مختلف
        self.patient = User.objects.create_user(
            username='patient',
            password='pass',
            user_type='patient'
        )
        
        self.doctor = User.objects.create_user(
            username='doctor',
            password='pass',
            user_type='doctor'
        )
        
        self.admin = User.objects.create_user(
            username='admin',
            password='pass',
            user_type='admin',
            is_staff=True
        )
        
        # ایجاد رکورد پزشکی
        from patient_records.models import PatientRecord
        self.record = PatientRecord.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            title='معاینه عمومی',
            description='نتایج معاینه'
        )
        
        self.url = reverse('patient_records:record-detail', kwargs={'pk': self.record.id})
    
    def test_owner_can_access(self):
        """تست دسترسی مالک"""
        self.client.force_authenticate(user=self.patient)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_doctor_can_access(self):
        """تست دسترسی پزشک"""
        self.client.force_authenticate(user=self.doctor)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_other_patient_cannot_access(self):
        """تست عدم دسترسی بیمار دیگر"""
        other_patient = User.objects.create_user(
            username='other_patient',
            password='pass',
            user_type='patient'
        )
        
        self.client.force_authenticate(user=other_patient)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unauthenticated_cannot_access(self):
        """تست عدم دسترسی بدون احراز هویت"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ====================================
# نمونه 6: Mock External Services
# ====================================

class ExternalServiceTest(TestCase):
    """
    تست‌های سرویس‌های خارجی با Mock
    """
    
    @patch('requests.post')
    def test_sms_sending_with_kavenegar(self, mock_post):
        """تست ارسال SMS با Kavenegar"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'return': {
                'status': 200,
                'message': 'تایید شد'
            }
        }
        mock_post.return_value = mock_response
        
        # تست ارسال OTP
        from unified_auth.services import OTPService
        otp_service = OTPService()
        
        result = otp_service.send_otp('09123456789')
        
        self.assertTrue(result)
        self.assertTrue(mock_post.called)
        
        # بررسی پارامترهای ارسالی
        call_args = mock_post.call_args
        self.assertIn('receptor', call_args[1]['data'])
    
    @patch('unified_ai.services.openai.ChatCompletion.create')
    def test_ai_chat_response(self, mock_openai):
        """تست پاسخ AI"""
        # Mock پاسخ OpenAI
        mock_openai.return_value = {
            'choices': [{
                'message': {
                    'content': 'برای سردرد می‌توانید استامینوفن مصرف کنید'
                }
            }]
        }
        
        from unified_ai.services import UnifiedAIService
        ai_service = UnifiedAIService()
        
        response = ai_service.generate_medical_response(
            'سردرد دارم چه کنم؟',
            context={'patient_age': 30}
        )
        
        self.assertIn('استامینوفن', response)
        self.assertTrue(mock_openai.called)


# ====================================
# نمونه 7: Database Transaction Tests
# ====================================

class TransactionTest(TransactionTestCase):
    """
    تست‌های تراکنش دیتابیس
    """
    
    def test_prescription_creation_rollback(self):
        """تست rollback در صورت خطا"""
        from prescription_system.models import Prescription, PrescriptionItem
        from django.db import transaction
        
        doctor = User.objects.create_user(
            username='doctor',
            password='pass',
            user_type='doctor'
        )
        
        patient = User.objects.create_user(
            username='patient',
            password='pass',
            user_type='patient'
        )
        
        initial_prescription_count = Prescription.objects.count()
        initial_item_count = PrescriptionItem.objects.count()
        
        try:
            with transaction.atomic():
                # ایجاد نسخه
                prescription = Prescription.objects.create(
                    patient=patient,
                    doctor=doctor,
                    notes='تست'
                )
                
                # ایجاد آیتم با خطای عمدی
                PrescriptionItem.objects.create(
                    prescription=prescription,
                    drug_name='تست',
                    quantity=-1  # مقدار نامعتبر که باعث خطا می‌شود
                )
        except Exception:
            pass
        
        # بررسی rollback
        self.assertEqual(Prescription.objects.count(), initial_prescription_count)
        self.assertEqual(PrescriptionItem.objects.count(), initial_item_count)


# ====================================
# نمونه 8: File Upload Tests
# ====================================

class FileUploadTest(APITestCase):
    """
    تست‌های آپلود فایل
    """
    
    def setUp(self):
        self.patient = User.objects.create_user(
            username='patient',
            password='pass',
            user_type='patient'
        )
        self.client.force_authenticate(user=self.patient)
        self.url = reverse('patient_records:upload-document')
    
    def test_valid_file_upload(self):
        """تست آپلود فایل معتبر"""
        # ایجاد فایل تست
        file = SimpleUploadedFile(
            "test_report.pdf",
            b"PDF content here",
            content_type="application/pdf"
        )
        
        data = {
            'file': file,
            'document_type': 'lab_result',
            'description': 'نتیجه آزمایش خون'
        }
        
        response = self.client.post(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('file_url', response.data)
    
    def test_large_file_rejection(self):
        """تست رد فایل بزرگ"""
        # ایجاد فایل بزرگ (بیش از 10MB)
        large_content = b"x" * (11 * 1024 * 1024)
        file = SimpleUploadedFile(
            "large_file.pdf",
            large_content,
            content_type="application/pdf"
        )
        
        data = {
            'file': file,
            'document_type': 'other'
        }
        
        response = self.client.post(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('حجم فایل', str(response.data))
    
    def test_invalid_file_type(self):
        """تست نوع فایل نامعتبر"""
        file = SimpleUploadedFile(
            "test.exe",
            b"executable content",
            content_type="application/x-msdownload"
        )
        
        data = {
            'file': file,
            'document_type': 'other'
        }
        
        response = self.client.post(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ====================================
# نمونه 9: Performance Tests
# ====================================

class PerformanceTest(TestCase):
    """
    تست‌های عملکرد
    """
    
    def test_query_optimization(self):
        """تست بهینه‌سازی کوئری"""
        from django.test.utils import override_settings
        from django.db import connection
        from django.test import override_settings
        
        # ایجاد داده‌های تست
        doctor = User.objects.create_user(
            username='doctor',
            password='pass',
            user_type='doctor'
        )
        
        patients = []
        for i in range(10):
            patient = User.objects.create_user(
                username=f'patient{i}',
                password='pass',
                user_type='patient'
            )
            patients.append(patient)
        
        # ایجاد ویزیت‌ها
        from visit_management.models import MedicalVisit
        for patient in patients:
            for j in range(5):
                MedicalVisit.objects.create(
                    patient=patient,
                    doctor=doctor,
                    visit_date=timezone.now() + timedelta(days=j),
                    visit_type='online',
                    chief_complaint='تست',
                    fee=100000
                )
        
        # تست با select_related و prefetch_related
        with self.assertNumQueries(2):  # باید فقط 2 کوئری اجرا شود
            visits = MedicalVisit.objects.select_related(
                'patient', 'doctor'
            ).prefetch_related(
                'prescriptions'
            ).filter(doctor=doctor)
            
            # Force evaluation
            list(visits)
            
            # دسترسی به related objects نباید کوئری اضافی ایجاد کند
            for visit in visits:
                _ = visit.patient.username
                _ = visit.doctor.username


# ====================================
# نمونه 10: Custom Test Utilities
# ====================================

class TestUtilsMixin:
    """
    Mixin برای ابزارهای تست سفارشی
    """
    
    def create_authenticated_client(self, user_type='patient'):
        """ایجاد client احراز هویت شده"""
        user = User.objects.create_user(
            username=f'test_{user_type}',
            password='testpass',
            user_type=user_type
        )
        client = APIClient()
        client.force_authenticate(user=user)
        return client, user
    
    def assert_api_error(self, response, expected_error_code):
        """بررسی خطای API"""
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], expected_error_code)
    
    def create_test_file(self, filename='test.pdf', size=1024):
        """ایجاد فایل تست"""
        content = b'x' * size
        return SimpleUploadedFile(
            filename,
            content,
            content_type='application/pdf'
        )


class AppointmentTestWithUtils(APITestCase, TestUtilsMixin):
    """
    مثال استفاده از TestUtilsMixin
    """
    
    def test_create_appointment_with_utils(self):
        """تست ایجاد قرار با استفاده از utils"""
        client, patient = self.create_authenticated_client('patient')
        
        # ایجاد پزشک
        doctor = User.objects.create_user(
            username='doctor',
            password='pass',
            user_type='doctor'
        )
        
        url = reverse('appointment_scheduler:create-appointment')
        data = {
            'doctor_id': str(doctor.id),
            'appointment_date': (timezone.now() + timedelta(days=3)).date().isoformat(),
            'appointment_time': '14:30',
            'reason': 'معاینه عمومی'
        }
        
        response = client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('appointment_id', response.data)