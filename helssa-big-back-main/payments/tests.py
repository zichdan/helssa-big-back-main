"""
تست‌های اپلیکیشن پرداخت
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Payment, PaymentMethod, Wallet, WalletTransaction
from .services import PaymentService, WalletService

User = get_user_model()


class PaymentModelTests(TestCase):
    """
    تست‌های مدل پرداخت
    """
    
    def setUp(self):
        """راه‌اندازی داده‌های تست"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
    def test_create_payment(self):
        """تست ایجاد پرداخت جدید"""
        payment = Payment.objects.create(
            user=self.user,
            user_type='patient',
            payment_type='appointment',
            amount=Decimal('100000')
        )
        
        self.assertIsNotNone(payment.payment_id)
        self.assertIsNotNone(payment.tracking_code)
        self.assertEqual(payment.status, 'pending')
        self.assertEqual(payment.amount, Decimal('100000'))
        
    def test_tracking_code_generation(self):
        """تست تولید کد پیگیری یکتا"""
        payment1 = Payment.objects.create(
            user=self.user,
            user_type='patient',
            payment_type='appointment',
            amount=Decimal('50000')
        )
        
        payment2 = Payment.objects.create(
            user=self.user,
            user_type='patient',
            payment_type='consultation',
            amount=Decimal('75000')
        )
        
        self.assertNotEqual(payment1.tracking_code, payment2.tracking_code)
        self.assertTrue(payment1.tracking_code.startswith('PAY'))
        self.assertTrue(payment2.tracking_code.startswith('PAY'))


class WalletModelTests(TestCase):
    """
    تست‌های مدل کیف پول
    """
    
    def setUp(self):
        """راه‌اندازی داده‌های تست"""
        self.user = User.objects.create_user(
            username='walletuser',
            password='testpass123'
        )
        
    def test_create_wallet(self):
        """تست ایجاد کیف پول"""
        wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('0')
        )
        
        self.assertEqual(wallet.balance, Decimal('0'))
        self.assertEqual(wallet.blocked_balance, Decimal('0'))
        self.assertEqual(wallet.available_balance, Decimal('0'))
        
    def test_available_balance_calculation(self):
        """تست محاسبه موجودی قابل استفاده"""
        wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('100000'),
            blocked_balance=Decimal('30000')
        )
        
        self.assertEqual(wallet.available_balance, Decimal('70000'))


class PaymentServiceTests(TestCase):
    """
    تست‌های سرویس پرداخت
    """
    
    def setUp(self):
        """راه‌اندازی داده‌های تست"""
        self.user = User.objects.create_user(
            username='serviceuser',
            password='testpass123'
        )
        self.service = PaymentService()
        
    def test_create_payment_success(self):
        """تست ایجاد موفق پرداخت"""
        success, result = self.service.create_payment(
            user=self.user,
            payment_type='appointment',
            amount=Decimal('150000')
        )
        
        self.assertTrue(success)
        self.assertIn('payment', result)
        self.assertIn('payment_id', result)
        self.assertIn('tracking_code', result)
        
        # بررسی پرداخت ایجاد شده
        payment = result['payment']
        self.assertEqual(payment.user, self.user)
        self.assertEqual(payment.amount, Decimal('150000'))
        
    def test_create_payment_invalid_amount(self):
        """تست ایجاد پرداخت با مبلغ نامعتبر"""
        success, result = self.service.create_payment(
            user=self.user,
            payment_type='appointment',
            amount=Decimal('500')  # کمتر از حداقل
        )
        
        self.assertFalse(success)
        self.assertEqual(result['error'], 'invalid_amount')
        
    def test_calculate_commission(self):
        """تست محاسبه کمیسیون"""
        # کمیسیون نوبت (10%)
        commission = self.service.calculate_commission(
            'appointment',
            Decimal('100000')
        )
        self.assertEqual(commission, Decimal('10000'))
        
        # کمیسیون مشاوره (15%)
        commission = self.service.calculate_commission(
            'consultation',
            Decimal('200000')
        )
        self.assertEqual(commission, Decimal('30000'))


class WalletServiceTests(TestCase):
    """
    تست‌های سرویس کیف پول
    """
    
    def setUp(self):
        """راه‌اندازی داده‌های تست"""
        self.user = User.objects.create_user(
            username='walletserviceuser',
            password='testpass123'
        )
        self.service = WalletService()
        
    def test_charge_wallet(self):
        """تست شارژ کیف پول"""
        success, result = self.service.charge_wallet(
            user=self.user,
            amount=Decimal('50000')
        )
        
        self.assertTrue(success)
        self.assertEqual(result['balance'], Decimal('50000'))
        self.assertEqual(result['charged_amount'], Decimal('50000'))
        
        # بررسی تراکنش
        transaction = WalletTransaction.objects.get(wallet__user=self.user)
        self.assertEqual(transaction.transaction_type, 'deposit')
        self.assertEqual(transaction.amount, Decimal('50000'))
        
    def test_withdraw_insufficient_balance(self):
        """تست برداشت با موجودی ناکافی"""
        # ایجاد کیف پول با موجودی کم
        wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('10000')
        )
        
        success, result = self.service.withdraw_from_wallet(
            user=self.user,
            amount=Decimal('20000')
        )
        
        self.assertFalse(success)
        self.assertEqual(result['error'], 'insufficient_balance')
        
    def test_block_and_unblock_amount(self):
        """تست مسدود کردن و رفع مسدودی"""
        # ایجاد کیف پول با موجودی
        wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal('100000')
        )
        
        # مسدود کردن
        success, result = self.service.block_amount(
            user=self.user,
            amount=Decimal('30000')
        )
        
        self.assertTrue(success)
        wallet.refresh_from_db()
        self.assertEqual(wallet.blocked_balance, Decimal('30000'))
        self.assertEqual(wallet.available_balance, Decimal('70000'))
        
        # رفع مسدودی
        success, result = self.service.unblock_amount(
            user=self.user,
            amount=Decimal('30000')
        )
        
        self.assertTrue(success)
        wallet.refresh_from_db()
        self.assertEqual(wallet.blocked_balance, Decimal('0'))
        self.assertEqual(wallet.available_balance, Decimal('100000'))


class PaymentAPITests(APITestCase):
    """
    تست‌های API پرداخت
    """
    
    def setUp(self):
        """راه‌اندازی داده‌های تست"""
        self.patient_user = User.objects.create_user(
            username='patient',
            password='testpass123'
        )
        # فرض می‌کنیم user_type در مدل User وجود دارد
        if hasattr(self.patient_user, 'user_type'):
            self.patient_user.user_type = 'patient'
            self.patient_user.save()
            
        self.doctor_user = User.objects.create_user(
            username='doctor',
            password='testpass123'
        )
        if hasattr(self.doctor_user, 'user_type'):
            self.doctor_user.user_type = 'doctor'
            self.doctor_user.save()
            
    def test_patient_create_payment(self):
        """تست ایجاد پرداخت توسط بیمار"""
        self.client.force_authenticate(user=self.patient_user)
        
        data = {
            'payment_type': 'appointment',
            'amount': '100000',
            'description': 'پرداخت نوبت دکتر'
        }
        
        response = self.client.post(
            reverse('payments:patient_create_payment'),
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('payment_id', response.data['data'])
        self.assertIn('tracking_code', response.data['data'])
        
    def test_doctor_unauthorized_patient_api(self):
        """تست عدم دسترسی دکتر به API بیمار"""
        self.client.force_authenticate(user=self.doctor_user)
        
        data = {
            'payment_type': 'appointment',
            'amount': '100000'
        }
        
        response = self.client.post(
            reverse('payments:patient_create_payment'),
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])
        
    def test_get_payment_history(self):
        """تست دریافت تاریخچه پرداخت‌ها"""
        # ایجاد چند پرداخت
        for i in range(3):
            Payment.objects.create(
                user=self.patient_user,
                user_type='patient',
                payment_type='appointment',
                amount=Decimal(f'{(i+1)*50000}'),
                status='success'
            )
            
        self.client.force_authenticate(user=self.patient_user)
        
        response = self.client.get(reverse('payments:get_payment_history'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['count'], 3)
        
    def test_add_payment_method(self):
        """تست افزودن روش پرداخت"""
        self.client.force_authenticate(user=self.patient_user)
        
        data = {
            'method_type': 'card',
            'title': 'کارت ملت',
            'details': {
                'card_number': '6219861012345678'
            }
        }
        
        response = self.client.post(
            reverse('payments:add_payment_method'),
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # بررسی ایجاد روش پرداخت
        payment_method = PaymentMethod.objects.get(
            user=self.patient_user,
            title='کارت ملت'
        )
        self.assertEqual(payment_method.method_type, 'card')