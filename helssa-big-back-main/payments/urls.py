"""
URLهای اپلیکیشن پرداخت
"""
from django.urls import path

from .views import (
    # ویوهای مشترک
    get_payment_methods,
    add_payment_method,
    get_payment_history,
    get_payment_detail,
)

from .views_patient import (
    # ویوهای بیمار
    patient_create_payment,
    patient_request_refund,
    patient_get_wallet,
    patient_charge_wallet,
    patient_payment_report,
)

from .views_doctor import (
    # ویوهای دکتر
    doctor_create_withdrawal,
    doctor_get_earnings,
    doctor_get_commissions,
    doctor_update_bank_info,
    doctor_get_wallet_transactions,
    doctor_financial_report,
)

app_name = 'payments'

urlpatterns = [
    # ==================== APIهای مشترک ====================
    # روش‌های پرداخت
    path('methods/', get_payment_methods, name='get_payment_methods'),
    path('methods/add/', add_payment_method, name='add_payment_method'),
    
    # تاریخچه و جزئیات
    path('history/', get_payment_history, name='get_payment_history'),
    path('detail/<uuid:payment_id>/', get_payment_detail, name='get_payment_detail'),
    
    # ==================== APIهای بیمار ====================
    # پرداخت و بازپرداخت
    path('patient/create/', patient_create_payment, name='patient_create_payment'),
    path('patient/refund/', patient_request_refund, name='patient_request_refund'),
    
    # کیف پول بیمار
    path('patient/wallet/', patient_get_wallet, name='patient_get_wallet'),
    path('patient/wallet/charge/', patient_charge_wallet, name='patient_charge_wallet'),
    
    # گزارش‌ها
    path('patient/report/', patient_payment_report, name='patient_payment_report'),
    
    # ==================== APIهای دکتر ====================
    # برداشت و درآمد
    path('doctor/withdrawal/', doctor_create_withdrawal, name='doctor_create_withdrawal'),
    path('doctor/earnings/', doctor_get_earnings, name='doctor_get_earnings'),
    
    # کمیسیون‌ها
    path('doctor/commissions/', doctor_get_commissions, name='doctor_get_commissions'),
    
    # اطلاعات بانکی
    path('doctor/bank-info/', doctor_update_bank_info, name='doctor_update_bank_info'),
    
    # کیف پول دکتر
    path('doctor/wallet/transactions/', doctor_get_wallet_transactions, name='doctor_wallet_transactions'),
    
    # گزارش مالی
    path('doctor/financial-report/', doctor_financial_report, name='doctor_financial_report'),
]