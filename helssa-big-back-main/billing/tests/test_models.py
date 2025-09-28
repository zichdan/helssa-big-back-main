"""
تست‌های مدل‌های سیستم مالی
Financial System Models Tests
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from ..models import (
    Wallet, Transaction, TransactionType, TransactionStatus,
    SubscriptionPlan, Subscription, SubscriptionStatus,
    Invoice, Commission
)

User = get_user_model()


class WalletModelTest(TestCase):
    """تست مدل کیف پول"""
    
    def setUp(self):
        """آماده‌سازی تست"""
        self.user = User.objects.create_user(
            phone_number='09123456789',
            user_type='patient'
        )
    
    def test_wallet_creation(self):
        """تست ایجاد کیف پول"""
        wallet = Wallet.objects.create(user=self.user)
        
        self.assertEqual(wallet.user, self.user)
        self.assertEqual(wallet.balance, Decimal('0'))
        self.assertTrue(wallet.is_active)
        self.assertIsNotNone(wallet.created_at)
    
    def test_wallet_unique_user(self):
        """تست یکتا بودن کیف پول برای هر کاربر"""
        Wallet.objects.create(user=self.user)
        
        with self.assertRaises(IntegrityError):
            Wallet.objects.create(user=self.user)
    
    def test_wallet_str_method(self):
        """تست متد __str__ کیف پول"""
        wallet = Wallet.objects.create(user=self.user)
        expected = f"کیف پول {self.user.phone_number}"
        self.assertEqual(str(wallet), expected)


class TransactionModelTest(TestCase):
    """تست مدل تراکنش"""
    
    def setUp(self):
        """آماده‌سازی تست"""
        self.user = User.objects.create_user(
            phone_number='09123456789',
            user_type='patient'
        )
        self.wallet = Wallet.objects.create(user=self.user)
    
    def test_transaction_creation(self):
        """تست ایجاد تراکنش"""
        transaction = Transaction.objects.create(
            wallet=self.wallet,
            amount=Decimal('10000'),
            transaction_type=TransactionType.DEPOSIT,
            status=TransactionStatus.PENDING,
            description='تست تراکنش'
        )
        
        self.assertEqual(transaction.wallet, self.wallet)
        self.assertEqual(transaction.amount, Decimal('10000'))
        self.assertEqual(transaction.transaction_type, TransactionType.DEPOSIT)
        self.assertEqual(transaction.status, TransactionStatus.PENDING)
    
    def test_transaction_str_method(self):
        """تست متد __str__ تراکنش"""
        transaction = Transaction.objects.create(
            wallet=self.wallet,
            amount=Decimal('10000'),
            transaction_type=TransactionType.DEPOSIT,
            status=TransactionStatus.PENDING
        )
        expected = f"تراکنش {transaction.amount} - {transaction.get_transaction_type_display()}"
        self.assertEqual(str(transaction), expected)
    
    def test_transaction_negative_amount(self):
        """تست مبلغ منفی تراکنش"""
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                wallet=self.wallet,
                amount=Decimal('-1000'),
                transaction_type=TransactionType.DEPOSIT,
                status=TransactionStatus.PENDING
            )
            transaction.full_clean()


class SubscriptionPlanModelTest(TestCase):
    """تست مدل پلن اشتراک"""
    
    def test_plan_creation(self):
        """تست ایجاد پلن"""
        plan = SubscriptionPlan.objects.create(
            name='پلن پایه',
            description='پلن پایه برای بیماران',
            price=Decimal('50000'),
            duration_days=30
        )
        
        self.assertEqual(plan.name, 'پلن پایه')
        self.assertEqual(plan.price, Decimal('50000'))
        self.assertEqual(plan.duration_days, 30)
        self.assertTrue(plan.is_active)
    
    def test_plan_str_method(self):
        """تست متد __str__ پلن"""
        plan = SubscriptionPlan.objects.create(
            name='پلن پایه',
            price=Decimal('50000'),
            duration_days=30
        )
        expected = f"پلن پایه - {plan.price} تومان"
        self.assertEqual(str(plan), expected)


class SubscriptionModelTest(TestCase):
    """تست مدل اشتراک"""
    
    def setUp(self):
        """آماده‌سازی تست"""
        self.user = User.objects.create_user(
            phone_number='09123456789',
            user_type='patient'
        )
        self.plan = SubscriptionPlan.objects.create(
            name='پلن تست',
            price=Decimal('50000'),
            duration_days=30
        )
    
    def test_subscription_creation(self):
        """تست ایجاد اشتراک"""
        subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            status=SubscriptionStatus.ACTIVE
        )
        
        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.plan, self.plan)
        self.assertEqual(subscription.status, SubscriptionStatus.ACTIVE)
        self.assertIsNotNone(subscription.start_date)
        self.assertIsNotNone(subscription.end_date)
    
    def test_subscription_str_method(self):
        """تست متد __str__ اشتراک"""
        subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            status=SubscriptionStatus.ACTIVE
        )
        expected = f"اشتراک {self.user.phone_number} - {self.plan.name}"
        self.assertEqual(str(subscription), expected)


class InvoiceModelTest(TestCase):
    """تست مدل فاکتور"""
    
    def setUp(self):
        """آماده‌سازی تست"""
        self.user = User.objects.create_user(
            phone_number='09123456789',
            user_type='patient'
        )
        self.plan = SubscriptionPlan.objects.create(
            name='پلن تست',
            price=Decimal('50000'),
            duration_days=30
        )
        self.subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            status=SubscriptionStatus.ACTIVE
        )
    
    def test_invoice_creation(self):
        """تست ایجاد فاکتور"""
        invoice = Invoice.objects.create(
            subscription=self.subscription,
            amount=self.plan.price,
            description='فاکتور تست'
        )
        
        self.assertEqual(invoice.subscription, self.subscription)
        self.assertEqual(invoice.amount, self.plan.price)
        self.assertFalse(invoice.is_paid)
        self.assertIsNotNone(invoice.created_at)
    
    def test_invoice_str_method(self):
        """تست متد __str__ فاکتور"""
        invoice = Invoice.objects.create(
            subscription=self.subscription,
            amount=self.plan.price
        )
        expected = f"فاکتور {invoice.amount} - {self.subscription.user.phone_number}"
        self.assertEqual(str(invoice), expected)


class CommissionModelTest(TestCase):
    """تست مدل کمیسیون"""
    
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
        self.plan = SubscriptionPlan.objects.create(
            name='پلن تست',
            price=Decimal('100000'),
            duration_days=30
        )
        self.subscription = Subscription.objects.create(
            user=self.patient,
            plan=self.plan,
            status=SubscriptionStatus.ACTIVE
        )
    
    def test_commission_creation(self):
        """تست ایجاد کمیسیون"""
        commission = Commission.objects.create(
            doctor=self.doctor,
            subscription=self.subscription,
            amount=Decimal('15000'),
            percentage=Decimal('15.0')
        )
        
        self.assertEqual(commission.doctor, self.doctor)
        self.assertEqual(commission.subscription, self.subscription)
        self.assertEqual(commission.amount, Decimal('15000'))
        self.assertEqual(commission.percentage, Decimal('15.0'))
        self.assertEqual(commission.status, 'pending')
    
    def test_commission_str_method(self):
        """تست متد __str__ کمیسیون"""
        commission = Commission.objects.create(
            doctor=self.doctor,
            subscription=self.subscription,
            amount=Decimal('15000'),
            percentage=Decimal('15.0')
        )
        expected = f"کمیسیون {self.doctor.phone_number} - {commission.amount}"
        self.assertEqual(str(commission), expected)