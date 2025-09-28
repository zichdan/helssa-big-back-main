"""
تست‌های سیستم تریاژ پزشکی
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
import json

from .models import (
    SymptomCategory,
    Symptom,
    DifferentialDiagnosis,
    TriageSession,
    SessionSymptom,
    DiagnosisSymptom,
    TriageRule
)
from .services import TriageAnalysisService

User = get_user_model()


class SymptomCategoryModelTest(TestCase):
    """
    تست مدل دسته‌بندی علائم
    """
    
    def setUp(self):
        self.category = SymptomCategory.objects.create(
            name='علائم تنفسی',
            name_en='Respiratory Symptoms',
            description='علائم مربوط به سیستم تنفسی',
            priority_level=5
        )
    
    def test_category_creation(self):
        """تست ایجاد دسته‌بندی"""
        self.assertEqual(self.category.name, 'علائم تنفسی')
        self.assertEqual(self.category.priority_level, 5)
        self.assertTrue(self.category.is_active)
    
    def test_category_str_representation(self):
        """تست نمایش رشته‌ای دسته‌بندی"""
        expected = f"{self.category.name} ({self.category.priority_level})"
        self.assertEqual(str(self.category), expected)


class SymptomModelTest(TestCase):
    """
    تست مدل علائم
    """
    
    def setUp(self):
        self.category = SymptomCategory.objects.create(
            name='علائم تنفسی',
            name_en='Respiratory Symptoms',
            priority_level=5
        )
        self.symptom = Symptom.objects.create(
            name='تنگی نفس',
            name_en='Shortness of breath',
            category=self.category,
            description='مشکل در تنفس طبیعی',
            urgency_score=7,
            severity_levels=['خفیف', 'متوسط', 'شدید'],
            common_locations=['قفسه سینه', 'گلو']
        )
    
    def test_symptom_creation(self):
        """تست ایجاد علامت"""
        self.assertEqual(self.symptom.name, 'تنگی نفس')
        self.assertEqual(self.symptom.urgency_score, 7)
        self.assertEqual(self.symptom.category, self.category)
    
    def test_symptom_str_representation(self):
        """تست نمایش رشته‌ای علامت"""
        expected = f"{self.symptom.name} (اورژانس: {self.symptom.urgency_score})"
        self.assertEqual(str(self.symptom), expected)


class DifferentialDiagnosisModelTest(TestCase):
    """
    تست مدل تشخیص‌های افتراقی
    """
    
    def setUp(self):
        self.diagnosis = DifferentialDiagnosis.objects.create(
            name='آسم',
            name_en='Asthma',
            icd_10_code='J45',
            description='بیماری انسدادی راه‌های هوایی',
            urgency_level=6,
            recommended_actions=['استفاده از اسپری', 'مراجعه به پزشک'],
            red_flags=['تنگی نفس شدید', 'سیانوز']
        )
    
    def test_diagnosis_creation(self):
        """تست ایجاد تشخیص"""
        self.assertEqual(self.diagnosis.name, 'آسم')
        self.assertEqual(self.diagnosis.icd_10_code, 'J45')
        self.assertEqual(self.diagnosis.urgency_level, 6)


class TriageSessionModelTest(TestCase):
    """
    تست مدل جلسات تریاژ
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testpatient',
            email='patient@test.com',
            password='testpass123'
        )
        self.session = TriageSession.objects.create(
            patient=self.user,
            chief_complaint='تنگی نفس و سرفه',
            reported_symptoms=['تنگی نفس', 'سرفه خشک'],
            status='started'
        )
    
    def test_session_creation(self):
        """تست ایجاد جلسه تریاژ"""
        self.assertEqual(self.session.patient, self.user)
        self.assertEqual(self.session.status, 'started')
        self.assertIsNotNone(self.session.started_at)
    
    def test_calculate_urgency(self):
        """تست محاسبه سطح اورژانس"""
        # ایجاد علائم با اورژانس مختلف
        category = SymptomCategory.objects.create(name='تست', name_en='Test')
        
        symptom1 = Symptom.objects.create(
            name='علامت 1', name_en='Symptom 1',
            category=category, urgency_score=4
        )
        symptom2 = Symptom.objects.create(
            name='علامت 2', name_en='Symptom 2',
            category=category, urgency_score=8
        )
        
        # افزودن علائم به جلسه
        SessionSymptom.objects.create(
            session=self.session, symptom=symptom1, severity=5
        )
        SessionSymptom.objects.create(
            session=self.session, symptom=symptom2, severity=7
        )
        
        urgency = self.session.calculate_urgency()
        self.assertGreaterEqual(urgency, 1)
        self.assertLessEqual(urgency, 5)


class TriageAnalysisServiceTest(TestCase):
    """
    تست سرویس تحلیل تریاژ
    """
    
    def setUp(self):
        self.service = TriageAnalysisService()
        self.user = User.objects.create_user(
            username='testpatient',
            email='patient@test.com',
            password='testpass123'
        )
        
        # ایجاد دیتای تست
        self.category = SymptomCategory.objects.create(
            name='علائم عمومی', name_en='General Symptoms'
        )
        
        self.symptom = Symptom.objects.create(
            name='تب', name_en='Fever',
            category=self.category, urgency_score=5
        )
        
        self.diagnosis = DifferentialDiagnosis.objects.create(
            name='عفونت ویروسی', name_en='Viral Infection',
            urgency_level=3
        )
        
        DiagnosisSymptom.objects.create(
            diagnosis=self.diagnosis,
            symptom=self.symptom,
            weight=2.0
        )
    
    def test_extract_symptoms_from_text(self):
        """تست استخراج علائم از متن"""
        text = "من تب دارم و سردرد شدیدی دارم"
        symptoms = self.service._extract_symptoms_from_text(text)
        
        # بررسی که علائم استخراج شده‌اند
        self.assertIsInstance(symptoms, list)
    
    def test_calculate_initial_urgency(self):
        """تست محاسبه اورژانس اولیه"""
        symptoms = [self.symptom]
        urgency = self.service._calculate_initial_urgency(symptoms)
        
        self.assertGreaterEqual(urgency, 1)
        self.assertLessEqual(urgency, 5)
    
    def test_analyze_symptoms_standalone(self):
        """تست تحلیل مستقل علائم"""
        symptoms = ['تب', 'سردرد']
        severity_scores = {'تب': 7, 'سردرد': 5}
        
        result = self.service.analyze_symptoms_standalone(
            symptoms=symptoms,
            severity_scores=severity_scores,
            patient_age=30,
            patient_gender='male'
        )
        
        self.assertIn('urgency_level', result)
        self.assertIn('possible_diagnoses', result)
        self.assertIn('red_flags', result)
        self.assertIn('confidence_score', result)


class TriageAPITest(APITestCase):
    """
    تست‌های API تریاژ
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testpatient',
            email='patient@test.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # ایجاد دیتای تست
        self.category = SymptomCategory.objects.create(
            name='علائم عمومی', name_en='General Symptoms'
        )
        
        self.symptom = Symptom.objects.create(
            name='تب', name_en='Fever',
            category=self.category, urgency_score=5
        )
    
    def test_create_triage_session(self):
        """تست ایجاد جلسه تریاژ"""
        url = reverse('triage:triage-sessions-list')
        data = {
            'chief_complaint': 'تب و سردرد شدید',
            'reported_symptoms': ['تب', 'سردرد']
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TriageSession.objects.count(), 1)
    
    def test_list_symptoms(self):
        """تست لیست علائم"""
        url = reverse('triage:symptoms-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_search_symptoms(self):
        """تست جستجوی علائم"""
        url = reverse('triage:search-symptoms')
        response = self.client.get(url, {'q': 'تب'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_analyze_symptoms_api(self):
        """تست API تحلیل علائم"""
        url = reverse('triage:analyze-symptoms')
        data = {
            'symptoms': ['تب', 'سردرد'],
            'severity_scores': {'تب': 7, 'سردرد': 5},
            'patient_age': 30
        }
        
        with patch.object(TriageAnalysisService, 'analyze_symptoms_standalone') as mock_analyze:
            mock_analyze.return_value = {
                'urgency_level': 3,
                'possible_diagnoses': [],
                'red_flags': [],
                'confidence_score': 0.7
            }
            
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            mock_analyze.assert_called_once()
    
    def test_add_symptom_to_session(self):
        """تست افزودن علامت به جلسه"""
        session = TriageSession.objects.create(
            patient=self.user,
            chief_complaint='تست',
            status='started'
        )
        
        url = reverse('triage:triage-sessions-add-symptom', kwargs={'pk': session.pk})
        data = {
            'symptom_id': str(self.symptom.id),
            'severity': 7,
            'duration_hours': 24,
            'location': 'سر'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SessionSymptom.objects.count(), 1)
    
    def test_complete_triage(self):
        """تست تکمیل تریاژ"""
        session = TriageSession.objects.create(
            patient=self.user,
            chief_complaint='تست',
            status='in_progress'
        )
        
        # افزودن علامت
        SessionSymptom.objects.create(
            session=session,
            symptom=self.symptom,
            severity=5
        )
        
        url = reverse('triage:triage-sessions-complete-triage', kwargs={'pk': session.pk})
        
        with patch.object(TriageAnalysisService, 'complete_triage_analysis') as mock_complete:
            mock_complete.return_value = {
                'urgency_score': 3,
                'possible_diagnoses': [],
                'confidence_score': 0.8
            }
            
            response = self.client.post(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            session.refresh_from_db()
            self.assertEqual(session.status, 'completed')
    
    def test_get_triage_statistics(self):
        """تست دریافت آمار تریاژ"""
        # ایجاد چند جلسه تست
        TriageSession.objects.create(
            patient=self.user,
            chief_complaint='تست 1',
            status='completed'
        )
        TriageSession.objects.create(
            patient=self.user,
            chief_complaint='تست 2',
            status='in_progress'
        )
        
        url = reverse('triage:statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_sessions', response.data)
        self.assertIn('completed_sessions', response.data)
        self.assertEqual(response.data['total_sessions'], 2)
        self.assertEqual(response.data['completed_sessions'], 1)


class TriageRuleTest(TestCase):
    """
    تست قوانین تریاژ
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        
        self.rule = TriageRule.objects.create(
            name='قانون اورژانس تنفسی',
            description='افزایش اورژانس برای مشکلات تنفسی شدید',
            conditions={
                'required_symptoms': ['تنگی نفس شدید'],
                'min_severity': 8
            },
            actions={
                'set_urgency': 5,
                'require_immediate_attention': True,
                'add_recommendations': ['مراجعه فوری به اورژانس']
            },
            priority=10,
            created_by=self.user
        )
    
    def test_rule_creation(self):
        """تست ایجاد قانون"""
        self.assertEqual(self.rule.name, 'قانون اورژانس تنفسی')
        self.assertEqual(self.rule.priority, 10)
        self.assertTrue(self.rule.is_active)
    
    def test_rule_str_representation(self):
        """تست نمایش رشته‌ای قانون"""
        expected = f"{self.rule.name} (اولویت: {self.rule.priority})"
        self.assertEqual(str(self.rule), expected)