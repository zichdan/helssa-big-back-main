"""
تست‌های اپلیکیشن Doctor
Doctor Application Tests
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import datetime, time, date
from decimal import Decimal

from .models import (
    DoctorProfile,
    DoctorSchedule,
    DoctorShift,
    DoctorCertificate,
    DoctorRating,
    DoctorSettings
)
from .services.doctor_service import (
    DoctorProfileService,
    DoctorScheduleService
)

User = get_user_model()


class DoctorModelTests(TestCase):
    """تست‌های مدل‌های Doctor"""
    
    def setUp(self):
        """آماده‌سازی داده‌های تست"""
        self.user = User.objects.create_user(
            username='09123456789',
            password='testpassword'
        )
        
        # تنظیم نوع کاربر به پزشک اگر فیلد موجود باشد
        if hasattr(self.user, 'user_type'):
            self.user.user_type = 'doctor'
            self.user.save()
    
    def test_doctor_profile_creation(self):
        """تست ایجاد پروفایل پزشک"""
        profile = DoctorProfile.objects.create(
            user=self.user,
            first_name='محمد',
            last_name='احمدی',
            national_code='1234567890',
            medical_system_code='DOC12345',
            specialty='general',
            phone_number='09123456789',
            years_of_experience=5,
            visit_price=Decimal('200000')
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.get_full_name(), 'محمد احمدی')
        self.assertEqual(profile.specialty, 'general')
        self.assertFalse(profile.is_verified)
        self.assertEqual(profile.rating, 0.0)
        self.assertEqual(profile.total_reviews, 0)
    
    def test_doctor_profile_str(self):
        """تست متد __str__ پروفایل پزشک"""
        profile = DoctorProfile.objects.create(
            user=self.user,
            first_name='علی',
            last_name='رضایی',
            national_code='0987654321',
            medical_system_code='DOC54321',
            specialty='cardiology'
        )
        
        expected_str = 'دکتر علی رضایی - قلب'
        self.assertEqual(str(profile), expected_str)
    
    def test_doctor_schedule_creation(self):
        """تست ایجاد برنامه کاری پزشک"""
        schedule = DoctorSchedule.objects.create(
            doctor=self.user,
            weekday=0,  # شنبه
            start_time=time(8, 0),
            end_time=time(14, 0),
            visit_type='both',
            max_patients=20
        )
        
        self.assertEqual(schedule.doctor, self.user)
        self.assertEqual(schedule.weekday, 0)
        self.assertEqual(schedule.get_weekday_display(), 'شنبه')
        self.assertEqual(schedule.visit_type, 'both')


class DoctorServiceTests(TestCase):
    """تست‌های سرویس‌های Doctor"""
    
    def setUp(self):
        """آماده‌سازی داده‌های تست"""
        self.user = User.objects.create_user(
            username='09123456789',
            password='testpassword'
        )
        
        if hasattr(self.user, 'user_type'):
            self.user.user_type = 'doctor'
            self.user.save()
        
        self.profile_service = DoctorProfileService()
        self.schedule_service = DoctorScheduleService()
        
        self.profile_data = {
            'first_name': 'محمد',
            'last_name': 'احمدی',
            'national_code': '1234567890',
            'medical_system_code': 'DOC12345',
            'specialty': 'general',
            'phone_number': '09123456789',
            'years_of_experience': 5,
            'visit_price': Decimal('200000')
        }
    
    def test_get_doctor_profile_success(self):
        """تست موفق دریافت پروفایل پزشک"""
        # ایجاد پروفایل
        DoctorProfile.objects.create(user=self.user, **self.profile_data)
        
        success, result = self.profile_service.get_doctor_profile(self.user)
        
        self.assertTrue(success)
        self.assertIn('profile', result)
        self.assertIn('verification_status', result)
        self.assertIn('rating_info', result)
    
    def test_get_nonexistent_profile(self):
        """تست دریافت پروفایل غیرموجود"""
        success, result = self.profile_service.get_doctor_profile(self.user)
        
        self.assertFalse(success)
        self.assertIn('error', result)


class DoctorAPITests(APITestCase):
    """تست‌های API اپ Doctor"""
    
    def setUp(self):
        """آماده‌سازی داده‌های تست"""
        self.client = APIClient()
        
        self.doctor_user = User.objects.create_user(
            username='09123456789',
            password='testpassword'
        )
        
        if hasattr(self.doctor_user, 'user_type'):
            self.doctor_user.user_type = 'doctor'
            self.doctor_user.save()
    
    def test_search_doctors_api(self):
        """تست API جستجوی پزشکان"""
        # ایجاد پروفایل پزشک
        DoctorProfile.objects.create(
            user=self.doctor_user,
            first_name='محمد',
            last_name='احمدی',
            national_code='1234567890',
            medical_system_code='DOC12345',
            specialty='general',
            phone_number='09123456789',
            is_verified=True
        )
        
        url = reverse('doctor:search_doctors')
        response = self.client.get(url, {'specialty': 'general'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_unauthorized_access(self):
        """تست دسترسی غیرمجاز"""
        url = '/api/doctor/profile/create/'
        data = {'first_name': 'تست'}
        
        # بدون احراز هویت
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)