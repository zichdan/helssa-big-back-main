"""
تست‌های پنل ادمین
AdminPortal Tests
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
import json
import uuid

from .models import (
    AdminUser, SystemOperation, SupportTicket, 
    SystemMetrics, AdminAuditLog, AdminSession
)
from .permissions import AdminPermissions
from .cores import (
    APIIngressCore, TextProcessorCore, 
    SpeechProcessorCore, CentralOrchestrator
)

User = get_user_model()


class AdminUserModelTest(TestCase):
    """تست مدل AdminUser"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com'
        )
    
    def test_create_admin_user(self):
        """تست ایجاد کاربر ادمین"""
        admin_user = AdminUser.objects.create(
            user=self.user,
            role='support_admin',
            department='پشتیبانی'
        )
        
        self.assertEqual(admin_user.user, self.user)
        self.assertEqual(admin_user.role, 'support_admin')
        self.assertEqual(admin_user.department, 'پشتیبانی')
        self.assertTrue(admin_user.is_active)
        self.assertEqual(str(admin_user), f"{self.user.username} - ادمین پشتیبانی")
    
    def test_update_last_activity(self):
        """تست بروزرسانی آخرین فعالیت"""
        admin_user = AdminUser.objects.create(
            user=self.user,
            role='support_admin'
        )
        
        old_activity = admin_user.last_activity
        admin_user.update_last_activity()
        
        self.assertIsNotNone(admin_user.last_activity)
        self.assertNotEqual(old_activity, admin_user.last_activity)


class SystemOperationModelTest(TestCase):
    """تست مدل SystemOperation"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='operator')
        self.admin_user = AdminUser.objects.create(
            user=self.user,
            role='technical_admin'
        )
    
    def test_create_system_operation(self):
        """تست ایجاد عملیات سیستمی"""
        operation = SystemOperation.objects.create(
            title='تست عملیات',
            operation_type='system_maintenance',
            description='تست توضیحات',
            operator=self.admin_user,
            priority=3
        )
        
        self.assertEqual(operation.title, 'تست عملیات')
        self.assertEqual(operation.status, 'pending')
        self.assertEqual(operation.priority, 3)
    
    def test_start_operation(self):
        """تست شروع عملیات"""
        operation = SystemOperation.objects.create(
            title='تست عملیات',
            operation_type='system_maintenance'
        )
        
        operation.start_operation(self.admin_user)
        
        self.assertEqual(operation.status, 'in_progress')
        self.assertEqual(operation.operator, self.admin_user)
        self.assertIsNotNone(operation.started_at)
    
    def test_complete_operation(self):
        """تست تکمیل عملیات"""
        operation = SystemOperation.objects.create(
            title='تست عملیات',
            operation_type='system_maintenance',
            status='in_progress'
        )
        
        result_data = {'success': True, 'message': 'تکمیل شد'}
        operation.complete_operation(result_data)
        
        self.assertEqual(operation.status, 'completed')
        self.assertEqual(operation.result, result_data)
        self.assertIsNotNone(operation.completed_at)


class SupportTicketModelTest(TestCase):
    """تست مدل SupportTicket"""
    
    def setUp(self):
        self.customer = User.objects.create_user(username='customer')
        self.admin_user = AdminUser.objects.create(
            user=User.objects.create_user(username='support'),
            role='support_admin'
        )
    
    def test_create_support_ticket(self):
        """تست ایجاد تیکت پشتیبانی"""
        ticket = SupportTicket.objects.create(
            user=self.customer,
            subject='مشکل در سیستم',
            description='توضیحات مشکل',
            category='technical',
            priority='high'
        )
        
        self.assertEqual(ticket.user, self.customer)
        self.assertEqual(ticket.status, 'open')
        self.assertIsNotNone(ticket.ticket_number)
        self.assertTrue(ticket.ticket_number.startswith('TK-'))
    
    def test_assign_to_admin(self):
        """تست تخصیص تیکت به ادمین"""
        ticket = SupportTicket.objects.create(
            user=self.customer,
            subject='تست تیکت',
            description='توضیحات'
        )
        
        ticket.assign_to_admin(self.admin_user)
        
        self.assertEqual(ticket.assigned_to, self.admin_user)
        self.assertEqual(ticket.status, 'in_progress')
    
    def test_resolve_ticket(self):
        """تست حل تیکت"""
        ticket = SupportTicket.objects.create(
            user=self.customer,
            subject='تست تیکت',
            description='توضیحات',
            status='in_progress'
        )
        
        resolution = 'مشکل حل شد'
        ticket.resolve_ticket(resolution, self.admin_user)
        
        self.assertEqual(ticket.status, 'resolved')
        self.assertEqual(ticket.resolution, resolution)
        self.assertIsNotNone(ticket.resolved_at)


class AdminPermissionsTest(TestCase):
    """تست سیستم دسترسی‌ها"""
    
    def setUp(self):
        self.super_admin_user = User.objects.create_user(username='super_admin')
        self.super_admin = AdminUser.objects.create(
            user=self.super_admin_user,
            role='super_admin'
        )
        
        self.support_user = User.objects.create_user(username='support_admin')
        self.support_admin = AdminUser.objects.create(
            user=self.support_user,
            role='support_admin'
        )
    
    def test_super_admin_permissions(self):
        """تست دسترسی‌های super admin"""
        permissions = AdminPermissions.get_user_permissions(self.super_admin)
        
        # super admin باید تمام دسترسی‌ها را داشته باشد
        self.assertTrue(len(permissions) > 0)
        self.assertTrue(AdminPermissions.has_permission(self.super_admin, 'manage_users'))
        self.assertTrue(AdminPermissions.has_permission(self.super_admin, 'system_admin'))
    
    def test_support_admin_permissions(self):
        """تست دسترسی‌های support admin"""
        permissions = AdminPermissions.get_user_permissions(self.support_admin)
        
        # support admin باید دسترسی‌های محدود داشته باشد
        self.assertTrue(AdminPermissions.has_permission(self.support_admin, 'view_users'))
        self.assertTrue(AdminPermissions.has_permission(self.support_admin, 'manage_tickets'))
        self.assertFalse(AdminPermissions.has_permission(self.support_admin, 'system_admin'))
    
    def test_custom_permissions(self):
        """تست دسترسی‌های سفارشی"""
        # اضافه کردن دسترسی سفارشی
        self.support_admin.permissions = ['content_analysis']
        self.support_admin.save()
        
        self.assertTrue(AdminPermissions.has_permission(self.support_admin, 'content_analysis'))
    
    def test_inactive_admin_permissions(self):
        """تست دسترسی‌های ادمین غیرفعال"""
        self.support_admin.is_active = False
        self.support_admin.save()
        
        permissions = AdminPermissions.get_user_permissions(self.support_admin)
        self.assertEqual(len(permissions), 0)


class APIIngressCoreTest(TestCase):
    """تست هسته API Ingress"""
    
    def setUp(self):
        self.api_ingress = APIIngressCore()
        self.user = User.objects.create_user(username='test_admin')
        self.admin_user = AdminUser.objects.create(
            user=self.user,
            role='support_admin'
        )
    
    def test_validate_admin_request(self):
        """تست اعتبارسنجی درخواست ادمین"""
        # ایجاد mock request
        request = MagicMock()
        request.user = self.user
        request.user.admin_profile = self.admin_user
        
        result = self.api_ingress.validate_admin_request(request)
        
        self.assertTrue(result[0])
        self.assertEqual(result[1]['admin_user'], self.admin_user)
    
    def test_check_rate_limit(self):
        """تست محدودیت نرخ"""
        request = MagicMock()
        request.user = self.user
        request.user.admin_profile = self.admin_user
        
        result = self.api_ingress.check_rate_limit(request, limit=5, window=60)
        
        self.assertTrue(result[0])
        self.assertIn('remaining', result[1])
    
    def test_format_api_response(self):
        """تست فرمت پاسخ API"""
        response = self.api_ingress.format_api_response(
            True, 
            data={'test': 'data'},
            message='موفق'
        )
        
        self.assertTrue(response['success'])
        self.assertEqual(response['data'], {'test': 'data'})
        self.assertIn('timestamp', response)


class TextProcessorCoreTest(TestCase):
    """تست هسته پردازش متن"""
    
    def setUp(self):
        self.text_processor = TextProcessorCore()
    
    def test_process_search_query(self):
        """تست پردازش query جستجو"""
        query = "جستجوی کاربر تست"
        result = self.text_processor.process_search_query(query, 'user')
        
        self.assertEqual(result['original_query'], query)
        self.assertIn('keywords', result)
        self.assertIn('patterns', result)
    
    def test_analyze_admin_content(self):
        """تست تحلیل محتوای ادمین"""
        content = "این یک تیکت فوری است. مشکل جدی در سیستم وجود دارد."
        result = self.text_processor.analyze_admin_content(content, 'ticket')
        
        self.assertEqual(result['content_type'], 'ticket')
        self.assertIn('keywords', result)
        self.assertIn('priority_indicators', result)
        self.assertIn('sentiment', result)
    
    def test_filter_sensitive_content(self):
        """تست فیلتر محتوای حساس"""
        content = "شماره کارت: 1234 5678 9012 3456 و تلفن: 09123456789"
        result = self.text_processor.filter_sensitive_content(content, 'medium')
        
        self.assertTrue(result['is_sensitive'])
        self.assertGreater(len(result['detected_items']), 0)
        self.assertNotEqual(result['filtered_content'], content)


class SpeechProcessorCoreTest(TestCase):
    """تست هسته پردازش صوت"""
    
    def setUp(self):
        self.speech_processor = SpeechProcessorCore()
    
    def test_validate_audio_input(self):
        """تست اعتبارسنجی ورودی صوتی"""
        audio_data = b'fake_audio_data' * 100  # داده نمونه
        result = self.speech_processor._validate_audio_input(audio_data, 'wav')
        
        self.assertTrue(result['valid'])
        self.assertIn('duration', result)
    
    def test_process_voice_command(self):
        """تست پردازش دستور صوتی"""
        audio_data = b'fake_audio_data' * 100
        result = self.speech_processor.process_voice_command(audio_data, 'wav')
        
        self.assertTrue(result['success'])
        self.assertIn('transcription', result)
        self.assertIn('command_analysis', result)


class CentralOrchestratorTest(TestCase):
    """تست هسته هماهنگی مرکزی"""
    
    def setUp(self):
        self.orchestrator = CentralOrchestrator()
        self.user = User.objects.create_user(username='orchestrator_test')
        self.admin_user = AdminUser.objects.create(
            user=self.user,
            role='super_admin'
        )
    
    def test_handle_admin_request(self):
        """تست مدیریت درخواست ادمین"""
        request = MagicMock()
        request.user = self.user
        request.user.admin_profile = self.admin_user
        request.META = {'REMOTE_ADDR': '127.0.0.1'}
        request.method = 'GET'
        request.path = '/test/'
        
        with patch.object(self.orchestrator.api_ingress, 'validate_admin_request') as mock_validate:
            mock_validate.return_value = (True, {'admin_user': self.admin_user})
            
            with patch.object(self.orchestrator.api_ingress, 'check_rate_limit') as mock_rate_limit:
                mock_rate_limit.return_value = (True, {'remaining': 99})
                
                result = self.orchestrator.handle_admin_request(
                    request, 
                    'search_users', 
                    {'query': 'test'}
                )
                
                self.assertIn('success', result)


class AdminPortalAPITest(APITestCase):
    """تست API های adminportal"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='api_test',
            email='api@test.com'
        )
        self.admin_user = AdminUser.objects.create(
            user=self.user,
            role='super_admin'
        )
        
        # احراز هویت
        self.client.force_authenticate(user=self.user)
    
    def test_admin_users_list(self):
        """تست لیست کاربران ادمین"""
        url = reverse('adminportal:admin-users-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_admin_users_create(self):
        """تست ایجاد کاربر ادمین"""
        new_user = User.objects.create_user(
            username='new_admin',
            email='new@test.com'
        )
        
        url = reverse('adminportal:admin-users-list')
        data = {
            'user': new_user.id,
            'role': 'support_admin',
            'department': 'پشتیبانی'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_support_tickets_list(self):
        """تست لیست تیکت‌های پشتیبانی"""
        # ایجاد تیکت نمونه
        customer = User.objects.create_user(username='customer')
        SupportTicket.objects.create(
            user=customer,
            subject='تست تیکت',
            description='توضیحات تست'
        )
        
        url = reverse('adminportal:support-tickets-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_dashboard_overview(self):
        """تست نمای کلی داشبورد"""
        url = reverse('adminportal:dashboard_overview')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('overview', response.data)
        self.assertIn('recent_activities', response.data)
    
    def test_search_content(self):
        """تست جستجوی محتوا"""
        url = reverse('adminportal:search_content')
        data = {
            'query': 'test search',
            'search_type': 'general'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_system_monitoring(self):
        """تست مانیتورینگ سیستم"""
        url = reverse('adminportal:system_monitoring')
        data = {
            'scope': 'basic'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_generate_report(self):
        """تست تولید گزارش"""
        url = reverse('adminportal:generate_report')
        data = {
            'report_type': 'users',
            'format': 'json'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_unauthorized_access(self):
        """تست دسترسی غیرمجاز"""
        # خروج از احراز هویت
        self.client.force_authenticate(user=None)
        
        url = reverse('adminportal:admin-users-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_non_admin_access(self):
        """تست دسترسی کاربر غیرادمین"""
        regular_user = User.objects.create_user(username='regular')
        self.client.force_authenticate(user=regular_user)
        
        url = reverse('adminportal:admin-users-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminPortalIntegrationTest(TransactionTestCase):
    """تست‌های یکپارچگی adminportal"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='integration_test')
        self.admin_user = AdminUser.objects.create(
            user=self.user,
            role='super_admin'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_complete_workflow(self):
        """تست workflow کامل"""
        # 1. ایجاد تیکت
        customer = User.objects.create_user(username='workflow_customer')
        ticket = SupportTicket.objects.create(
            user=customer,
            subject='تست workflow',
            description='توضیحات تست',
            priority='high'
        )
        
        # 2. تخصیص تیکت
        url = reverse('adminportal:support_ticket_assign_to_me', kwargs={'pk': ticket.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 3. حل تیکت
        url = reverse('adminportal:support_ticket_resolve', kwargs={'pk': ticket.pk})
        data = {'resolution': 'مشکل حل شد'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 4. بررسی audit log
        audit_logs = AdminAuditLog.objects.filter(
            admin_user=self.admin_user,
            resource_type='support_ticket'
        )
        self.assertGreater(audit_logs.count(), 0)
    
    def test_bulk_operations_workflow(self):
        """تست workflow عملیات دسته‌ای"""
        # ایجاد چند تیکت
        customer = User.objects.create_user(username='bulk_customer')
        tickets = []
        for i in range(3):
            ticket = SupportTicket.objects.create(
                user=customer,
                subject=f'تیکت {i}',
                description=f'توضیحات {i}'
            )
            tickets.append(ticket)
        
        # عملیات دسته‌ای
        url = reverse('adminportal:bulk_operations')
        data = {
            'operation_type': 'update',
            'item_ids': [str(ticket.id) for ticket in tickets],
            'options': {'status': 'resolved'}
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])


class AdminPortalPerformanceTest(TestCase):
    """تست‌های عملکرد adminportal"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='performance_test')
        self.admin_user = AdminUser.objects.create(
            user=self.user,
            role='super_admin'
        )
    
    def test_large_dataset_query(self):
        """تست query روی dataset بزرگ"""
        # ایجاد تعداد زیادی متریک
        metrics = []
        for i in range(100):
            metric = SystemMetrics(
                metric_name=f'test_metric_{i}',
                metric_type='performance',
                value=i * 10.5,
                unit='ms'
            )
            metrics.append(metric)
        
        SystemMetrics.objects.bulk_create(metrics)
        
        # تست query
        import time
        start_time = time.time()
        
        queryset = SystemMetrics.objects.filter(metric_type='performance')
        count = queryset.count()
        
        end_time = time.time()
        query_time = end_time - start_time
        
        self.assertEqual(count, 100)
        self.assertLess(query_time, 1.0)  # باید کمتر از 1 ثانیه باشد
    
    def test_permissions_cache(self):
        """تست cache دسترسی‌ها"""
        from .permissions import PermissionCacheManager
        
        # اولین بار محاسبه دسترسی‌ها
        import time
        start_time = time.time()
        
        permissions1 = AdminPermissions.get_user_permissions(self.admin_user)
        
        first_query_time = time.time() - start_time
        
        # دومین بار (باید از cache استفاده کند)
        start_time = time.time()
        
        permissions2 = AdminPermissions.get_user_permissions(self.admin_user)
        
        second_query_time = time.time() - start_time
        
        self.assertEqual(permissions1, permissions2)
        # query دوم باید سریع‌تر باشد (اگر cache فعال باشد)


if __name__ == '__main__':
    import unittest
    unittest.main()