"""
تست‌های اپلیکیشن Checklist
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import Mock, patch

from .models import (
    ChecklistCatalog,
    ChecklistTemplate,
    ChecklistEval,
    ChecklistAlert
)
from .services import ChecklistService, ChecklistEvaluationService

User = get_user_model()


class ChecklistCatalogModelTest(TestCase):
    """
    تست‌های مدل ChecklistCatalog
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testdoctor',
            password='testpass123'
        )
        
        self.catalog_item = ChecklistCatalog.objects.create(
            title='بررسی فشار خون',
            description='اندازه‌گیری و ثبت فشار خون بیمار',
            category='physical_exam',
            priority='high',
            keywords=['فشار خون', 'blood pressure', 'BP'],
            question_template='آیا فشار خون بیمار اندازه‌گیری شده است؟',
            created_by=self.user
        )
    
    def test_catalog_item_creation(self):
        """تست ایجاد آیتم کاتالوگ"""
        self.assertEqual(self.catalog_item.title, 'بررسی فشار خون')
        self.assertEqual(self.catalog_item.category, 'physical_exam')
        self.assertEqual(self.catalog_item.priority, 'high')
        self.assertEqual(len(self.catalog_item.keywords), 3)
        self.assertTrue(self.catalog_item.is_active)
    
    def test_catalog_item_str(self):
        """تست نمایش رشته‌ای آیتم کاتالوگ"""
        expected = 'بررسی فشار خون (معاینه فیزیکی)'
        self.assertEqual(str(self.catalog_item), expected)


class ChecklistTemplateModelTest(TestCase):
    """
    تست‌های مدل ChecklistTemplate
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # ایجاد چند آیتم کاتالوگ
        self.catalog_items = []
        for i in range(3):
            item = ChecklistCatalog.objects.create(
                title=f'آیتم {i+1}',
                category='history',
                created_by=self.user
            )
            self.catalog_items.append(item)
        
        # ایجاد قالب
        self.template = ChecklistTemplate.objects.create(
            name='قالب ویزیت عمومی',
            description='قالب استاندارد برای ویزیت‌های عمومی',
            created_by=self.user
        )
        self.template.catalog_items.set(self.catalog_items)
    
    def test_template_creation(self):
        """تست ایجاد قالب"""
        self.assertEqual(self.template.name, 'قالب ویزیت عمومی')
        self.assertEqual(self.template.catalog_items.count(), 3)
        self.assertTrue(self.template.is_active)
    
    def test_template_str(self):
        """تست نمایش رشته‌ای قالب"""
        self.assertEqual(str(self.template), 'قالب ویزیت عمومی')


class ChecklistEvaluationServiceTest(TestCase):
    """
    تست‌های سرویس ارزیابی چک‌لیست
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testdoctor',
            password='testpass123'
        )
        
        # ایجاد آیتم کاتالوگ
        self.catalog_item = ChecklistCatalog.objects.create(
            title='بررسی علائم حیاتی',
            category='physical_exam',
            priority='high',
            keywords=['فشار خون', 'نبض', 'تنفس', 'دما'],
            question_template='آیا علائم حیاتی بیمار بررسی شده است؟',
            created_by=self.user
        )
        
        self.service = ChecklistEvaluationService()
    
    def test_keyword_based_evaluation_covered(self):
        """تست ارزیابی کلمات کلیدی - پوشش کامل"""
        transcript = "فشار خون بیمار 120/80 است. نبض 72 و منظم. تعداد تنفس 16 در دقیقه. دمای بدن 37 درجه."
        
        result = self.service._keyword_based_evaluation(self.catalog_item, transcript)
        
        self.assertEqual(result['status'], 'covered')
        self.assertGreater(result['confidence_score'], 0.8)
        self.assertIn('فشار خون', result['evidence_text'])
    
    def test_keyword_based_evaluation_partial(self):
        """تست ارزیابی کلمات کلیدی - پوشش جزئی"""
        transcript = "فشار خون بیمار 120/80 است. نبض نرمال."
        
        result = self.service._keyword_based_evaluation(self.catalog_item, transcript)
        
        self.assertEqual(result['status'], 'partial')
        self.assertGreater(result['confidence_score'], 0.4)
        self.assertLess(result['confidence_score'], 0.8)
    
    def test_keyword_based_evaluation_missing(self):
        """تست ارزیابی کلمات کلیدی - عدم پوشش"""
        transcript = "بیمار درد شکم دارد. معاینه شکم انجام شد."
        
        result = self.service._keyword_based_evaluation(self.catalog_item, transcript)
        
        self.assertEqual(result['status'], 'missing')
        self.assertEqual(result['confidence_score'], 0.0)
        self.assertEqual(result['evidence_text'], '')
    
    def test_extract_context(self):
        """تست استخراج context"""
        text = "این یک متن تست است که در آن کلمه مهم وجود دارد."
        start = text.find('کلمه مهم')
        end = start + len('کلمه مهم')
        
        context = self.service._extract_context(text, start, end, context_length=10)
        
        self.assertIn('کلمه مهم', context)
        self.assertIn('...', context)  # باید ... داشته باشد چون متن بریده شده


class ChecklistAPITest(APITestCase):
    """
    تست‌های API چک‌لیست
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testdoctor',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # ایجاد داده‌های تست
        self.catalog_item = ChecklistCatalog.objects.create(
            title='تست API',
            category='history',
            priority='medium',
            created_by=self.user
        )
    
    def test_catalog_list_api(self):
        """تست API لیست آیتم‌های کاتالوگ"""
        url = reverse('checklist:checklist-catalog-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_catalog_create_api(self):
        """تست API ایجاد آیتم کاتالوگ"""
        url = reverse('checklist:checklist-catalog-list')
        data = {
            'title': 'آیتم جدید',
            'category': 'diagnosis',
            'priority': 'high',
            'keywords': ['کلمه1', 'کلمه2']
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ChecklistCatalog.objects.count(), 2)
    
    def test_catalog_filter_api(self):
        """تست فیلتر کردن آیتم‌های کاتالوگ"""
        # ایجاد آیتم دیگر با دسته متفاوت
        ChecklistCatalog.objects.create(
            title='آیتم دیگر',
            category='treatment',
            created_by=self.user
        )
        
        url = reverse('checklist:checklist-catalog-list')
        response = self.client.get(url, {'category': 'history'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['category'], 'history')
    
    def test_unauthenticated_access(self):
        """تست دسترسی بدون احراز هویت"""
        self.client.force_authenticate(user=None)
        url = reverse('checklist:checklist-catalog-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ChecklistSignalsTest(TestCase):
    """
    تست‌های سیگنال‌های چک‌لیست
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Mock encounter
        self.mock_encounter = Mock()
        self.mock_encounter.id = 1
        
        # ایجاد آیتم کاتالوگ بحرانی
        self.critical_item = ChecklistCatalog.objects.create(
            title='آیتم بحرانی',
            category='red_flags',
            priority='critical',
            created_by=self.user
        )
    
    @patch('checklist.models.ChecklistEval.encounter')
    def test_critical_alert_signal(self, mock_encounter):
        """تست سیگنال ایجاد هشدار برای آیتم‌های بحرانی"""
        mock_encounter.return_value = self.mock_encounter
        
        # ایجاد ارزیابی با وضعیت missing
        evaluation = ChecklistEval(
            encounter=self.mock_encounter,
            catalog_item=self.critical_item,
            status='missing',
            created_by=self.user
        )
        
        # ذخیره باید سیگنال را فعال کند
        with patch.object(ChecklistAlert.objects, 'create') as mock_create:
            evaluation.save()
            
            # بررسی ایجاد هشدار
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            self.assertEqual(call_args['alert_type'], 'missing_critical')
            self.assertIn('آیتم بحرانی', call_args['message'])