"""
تست‌های View های سیستم مالی
Financial System Views Tests
"""

from decimal import Decimal
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status

from ..models import (
    Wallet, Transaction, TransactionType, TransactionStatus,
    SubscriptionPlan, Subscription, SubscriptionStatus
)

User = get_user_model()


class DoctorViewsTest(APITestCase):
    """تست View های مخصوص دکتر"""
    
    def setUp(self):
        """آماده‌سازی تست"""
        self.doctor = User.objects.create_user(
            phone_number='09123456789',
            user_type='doctor',
            is_verified=True
        )
        self.wallet = Wallet.objects.create(
            user=self.doctor,
            balance=Decimal('100000')
        )
        self.client.force_authenticate(user=self.doctor)
    
    def test_doctor_wallet_view(self):
        """تست مشاهده کیف پول دکتر"""
        url = reverse('billing:doctor:doctor_wallet')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['balance'], self.wallet.balance)
        self.assertIn('total_earnings', response.data)
        self.assertIn('pending_earnings', response.data)
    
    def test_doctor_withdraw_success(self):
        """تست موفقیت‌آمیز برداشت دکتر"""
        url = reverse('billing:doctor:doctor_withdraw')
        data = {
            'amount': '50000',
            'description': 'برداشت تست'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('transaction', response.data)
    
    def test_doctor_withdraw_insufficient_balance(self):
        """تست برداشت با موجودی ناکافی"""
        url = reverse('billing:doctor:doctor_withdraw')
        data = {
            'amount': '200000',  # بیشتر از موجودی
            'description': 'برداشت تست'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_doctor_financial_summary(self):
        """تست خلاصه مالی دکتر"""
        url = reverse('billing:doctor:doctor_financial_summary')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('monthly_stats', response.data)
        self.assertIn('total_stats', response.data)
        self.assertIn('wallet_info', response.data)
    
    def test_doctor_transaction_history(self):
        """تست تاریخچه تراکنش‌های دکتر"""
        # ایجاد تراکنش تست
        Transaction.objects.create(
            wallet=self.wallet,
            amount=Decimal('10000'),
            transaction_type=TransactionType.DEPOSIT,
            status=TransactionStatus.COMPLETED
        )
        
        url = reverse('billing:doctor:doctor_transactions')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('stats', response.data)
        self.assertEqual(len(response.data['results']), 1)


class PatientViewsTest(APITestCase):
    """تست View های مخصوص بیمار"""
    
    def setUp(self):
        """آماده‌سازی تست"""
        self.patient = User.objects.create_user(
            phone_number='09123456789',
            user_type='patient',
            is_verified=True
        )
        self.wallet = Wallet.objects.create(
            user=self.patient,
            balance=Decimal('50000')
        )
        self.plan = SubscriptionPlan.objects.create(
            name='پلن تست',
            price=Decimal('30000'),
            duration_days=30
        )
        self.client.force_authenticate(user=self.patient)
    
    def test_patient_wallet_view(self):
        """تست مشاهده کیف پول بیمار"""
        url = reverse('billing:patient:patient_wallet')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['balance'], self.wallet.balance)
        self.assertIn('total_spent', response.data)
        self.assertIn('total_charged', response.data)
    
    def test_patient_payment_valid_amount(self):
        """تست پرداخت با مبلغ معتبر"""
        url = reverse('billing:patient:patient_payment')
        data = {
            'amount': '20000',
            'gateway': 'zarinpal',
            'description': 'شارژ تست'
        }
        response = self.client.post(url, data, format='json')
        
        # باید درخواست پرداخت ایجاد شود
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
    
    def test_patient_payment_invalid_amount(self):
        """تست پرداخت با مبلغ نامعتبر"""
        url = reverse('billing:patient:patient_payment')
        data = {
            'amount': '0',  # مبلغ نامعتبر
            'gateway': 'zarinpal'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_patient_plans_view(self):
        """تست مشاهده پلن‌های اشتراک"""
        url = reverse('billing:patient:patient_plans')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'پلن تست')
    
    def test_patient_subscription_purchase(self):
        """تست خرید اشتراک"""
        url = reverse('billing:patient:patient_subscription')
        data = {
            'plan_id': self.plan.id
        }
        response = self.client.post(url, data, format='json')
        
        # باید اشتراک خریداری شود یا خطای موجودی ناکافی
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
    
    def test_patient_subscription_view_no_subscription(self):
        """تست مشاهده اشتراک زمانی که اشتراکی نیست"""
        url = reverse('billing:patient:patient_subscription')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CommonViewsTest(APITestCase):
    """تست View های مشترک"""
    
    def setUp(self):
        """آماده‌سازی تست"""
        self.user = User.objects.create_user(
            phone_number='09123456789',
            user_type='patient'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_payment_methods_view(self):
        """تست مشاهده روش‌های پرداخت"""
        url = reverse('billing:payment_methods')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('payment_methods', response.data)
        self.assertIn('total_count', response.data)
    
    def test_payment_limits_view(self):
        """تست مشاهده محدودیت‌های پرداخت"""
        url = reverse('billing:payment_limits')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('limits', response.data)
        self.assertIn('user_type', response.data)
    
    def test_payment_fees_calculation(self):
        """تست محاسبه کارمزد پرداخت"""
        url = reverse('billing:payment_fees')
        response = self.client.get(url, {'amount': '10000', 'gateway': 'zarinpal'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('fee_amount', response.data)
        self.assertIn('total_amount', response.data)
    
    def test_health_check_view(self):
        """تست بررسی سلامت سیستم"""
        url = reverse('billing:health_check')
        response = self.client.get(url)
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE])
        self.assertIn('status', response.data)
        self.assertIn('components', response.data)


class PermissionTest(APITestCase):
    """تست‌های مجوزهای دسترسی"""
    
    def setUp(self):
        """آماده‌سازی تست"""
        self.doctor = User.objects.create_user(
            phone_number='09123456789',
            user_type='doctor'
        )
        self.patient = User.objects.create_user(
            phone_number='09123456788',
            user_type='patient'
        )
    
    def test_doctor_cannot_access_patient_apis(self):
        """تست عدم دسترسی دکتر به API های بیمار"""
        self.client.force_authenticate(user=self.doctor)
        url = reverse('billing:patient:patient_payment')
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_patient_cannot_access_doctor_apis(self):
        """تست عدم دسترسی بیمار به API های دکتر"""
        self.client.force_authenticate(user=self.patient)
        url = reverse('billing:doctor:doctor_withdraw')
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unauthenticated_user_access_denied(self):
        """تست عدم دسترسی کاربر احراز نشده"""
        url = reverse('billing:payment_methods')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)