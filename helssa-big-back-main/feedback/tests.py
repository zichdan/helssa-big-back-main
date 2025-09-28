"""
تست‌های feedback app
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
import uuid

from .models import SessionRating, MessageFeedback, Survey, SurveyResponse, FeedbackSettings

User = get_user_model()


class SessionRatingModelTest(TestCase):
    """تست‌های مدل SessionRating"""
    
    def setUp(self):
        """تنظیمات اولیه"""
        try:
            self.user = User.objects.create_user(
                username='09123456789',
                password='testpass123'
            )
        except:
            self.user = User.objects.create(
                username='testuser',
                email='test@example.com'
            )
        
        self.session_id = uuid.uuid4()
    
    def test_create_session_rating(self):
        """تست ایجاد امتیازدهی جلسه"""
        rating = SessionRating.objects.create(
            session_id=self.session_id,
            user=self.user,
            overall_rating=4,
            response_quality=4,
            response_speed=5,
            helpfulness=3,
            comment='خوب بود',
            would_recommend=True
        )
        
        self.assertEqual(rating.overall_rating, 4)
        self.assertEqual(rating.user, self.user)
        self.assertEqual(str(rating.session_id), str(self.session_id))
        self.assertTrue(rating.would_recommend)
        self.assertTrue(rating.is_active)
    
    def test_session_rating_str(self):
        """تست نمایش string مدل"""
        rating = SessionRating.objects.create(
            session_id=self.session_id,
            user=self.user,
            overall_rating=5
        )
        
        expected_str = f"امتیاز 5/5 - جلسه {self.session_id} - {self.user}"
        self.assertEqual(str(rating), expected_str)


class MessageFeedbackModelTest(TestCase):
    """تست‌های مدل MessageFeedback"""
    
    def setUp(self):
        try:
            self.user = User.objects.create_user(
                username='09123456789',
                password='testpass123'
            )
        except:
            self.user = User.objects.create(
                username='testuser',
                email='test@example.com'
            )
        
        self.message_id = uuid.uuid4()
    
    def test_create_message_feedback(self):
        """تست ایجاد بازخورد پیام"""
        feedback = MessageFeedback.objects.create(
            message_id=self.message_id,
            user=self.user,
            feedback_type='helpful',
            is_helpful=True,
            detailed_feedback='پاسخ مفیدی بود'
        )
        
        self.assertEqual(feedback.feedback_type, 'helpful')
        self.assertTrue(feedback.is_helpful)
        self.assertEqual(feedback.detailed_feedback, 'پاسخ مفیدی بود')
        self.assertTrue(feedback.is_active)


class SurveyModelTest(TestCase):
    """تست‌های مدل Survey"""
    
    def setUp(self):
        try:
            self.user = User.objects.create_user(
                username='09123456789',
                password='testpass123'
            )
        except:
            self.user = User.objects.create(
                username='testuser',
                email='test@example.com'
            )
    
    def test_create_survey(self):
        """تست ایجاد نظرسنجی"""
        questions = [
            {
                'id': 'q1',
                'text': 'چقدر راضی هستید؟',
                'type': 'rating',
                'min_value': 1,
                'max_value': 5
            }
        ]
        
        survey = Survey.objects.create(
            title='نظرسنجی رضایت',
            description='نظرسنجی رضایت کاربران',
            survey_type='satisfaction',
            target_users='all',
            questions=questions
        )
        
        self.assertEqual(survey.title, 'نظرسنجی رضایت')
        self.assertEqual(survey.survey_type, 'satisfaction')
        self.assertEqual(len(survey.questions), 1)
        self.assertTrue(survey.is_active)


class FeedbackAPITest(APITestCase):
    """تست‌های API feedback"""
    
    def setUp(self):
        """تنظیمات اولیه API"""
        try:
            self.user = User.objects.create_user(
                username='09123456789',
                password='testpass123'
            )
        except:
            self.user = User.objects.create(
                username='testuser',
                email='test@example.com'
            )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.session_id = uuid.uuid4()
        self.message_id = uuid.uuid4()
    
    def test_create_session_rating_api(self):
        """تست API ایجاد امتیازدهی جلسه"""
        url = reverse('feedback:session-rating-list')
        data = {
            'session_id': str(self.session_id),
            'overall_rating': 4,
            'response_quality': 4,
            'comment': 'خوب بود'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('message', response.data)
        
        # بررسی ایجاد در دیتابیس
        rating = SessionRating.objects.get(session_id=self.session_id)
        self.assertEqual(rating.overall_rating, 4)
        self.assertEqual(rating.user, self.user)
    
    def test_analytics_dashboard_api(self):
        """تست API داشبورد آنالیتیک"""
        url = reverse('feedback:analytics-dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('data', response.data)
        self.assertIn('summary', response.data['data'])
    
    def test_unauthorized_access(self):
        """تست دسترسی غیرمجاز"""
        self.client.force_authenticate(user=None)
        
        url = reverse('feedback:session-rating-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class FeedbackSettingsTest(TestCase):
    """تست‌های تنظیمات feedback"""
    
    def test_create_feedback_setting(self):
        """تست ایجاد تنظیمات"""
        setting = FeedbackSettings.objects.create(
            key='test_setting',
            value={'enabled': True, 'max_value': 5},
            description='تنظیمات تست',
            setting_type='general'
        )
        
        self.assertEqual(setting.key, 'test_setting')
        self.assertTrue(setting.value['enabled'])
        self.assertEqual(setting.setting_type, 'general')