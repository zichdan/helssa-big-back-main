"""
URL Configuration برای سیستم مالی
Financial System URL Configuration
"""

from django.urls import path, include
from .views import (
    # Doctor Views
    DoctorWalletView, DoctorCommissionView, DoctorFinancialSummaryView,
    DoctorWithdrawView, DoctorTransactionHistoryView,
    
    # Patient Views
    PatientWalletView, PatientPaymentView, PatientSubscriptionView,
    PatientPlansView, PatientTransactionHistoryView,
    
    # Common Views
    PaymentMethodsView, PaymentStatusView, RefundPaymentView
)
from .views.doctor_views import doctor_commission_stats
from .views.patient_views import patient_spending_stats
from .views.common_views import payment_limits, payment_fees, health_check

app_name = 'billing'

# URL های مخصوص دکتر
doctor_patterns = [
    path('wallet/', DoctorWalletView.as_view(), name='doctor_wallet'),
    path('commission/', DoctorCommissionView.as_view(), name='doctor_commission'),
    path('commission/stats/', doctor_commission_stats, name='doctor_commission_stats'),
    path('financial-summary/', DoctorFinancialSummaryView.as_view(), name='doctor_financial_summary'),
    path('withdraw/', DoctorWithdrawView.as_view(), name='doctor_withdraw'),
    path('transactions/', DoctorTransactionHistoryView.as_view(), name='doctor_transactions'),
]

# URL های مخصوص بیمار
patient_patterns = [
    path('wallet/', PatientWalletView.as_view(), name='patient_wallet'),
    path('payment/', PatientPaymentView.as_view(), name='patient_payment'),
    path('subscription/', PatientSubscriptionView.as_view(), name='patient_subscription'),
    path('plans/', PatientPlansView.as_view(), name='patient_plans'),
    path('transactions/', PatientTransactionHistoryView.as_view(), name='patient_transactions'),
    path('spending-stats/', patient_spending_stats, name='patient_spending_stats'),
]

# URL های مشترک
common_patterns = [
    path('payment-methods/', PaymentMethodsView.as_view(), name='payment_methods'),
    path('payment-status/<str:transaction_id>/', PaymentStatusView.as_view(), name='payment_status'),
    path('refund/', RefundPaymentView.as_view(), name='refund_payment'),
    path('payment-limits/', payment_limits, name='payment_limits'),
    path('payment-fees/', payment_fees, name='payment_fees'),
    path('health/', health_check, name='health_check'),
]

# URL های اصلی
urlpatterns = [
    # API های دکتر
    path('doctor/', include((doctor_patterns, 'doctor'), namespace='doctor')),
    
    # API های بیمار
    path('patient/', include((patient_patterns, 'patient'), namespace='patient')),
    
    # API های مشترک
    path('', include(common_patterns)),
]