"""
تنظیمات اپلیکیشن پرداخت
"""
from django.conf import settings
from decimal import Decimal

# تنظیمات عمومی پرداخت
PAYMENT_SETTINGS = {
    # حداقل و حداکثر مبالغ
    'MIN_PAYMENT_AMOUNT': Decimal('1000'),  # 1,000 ریال
    'MAX_PAYMENT_AMOUNT': Decimal('500000000'),  # 500 میلیون ریال
    'MIN_WITHDRAWAL_AMOUNT': Decimal('100000'),  # 100 هزار ریال
    'MIN_WALLET_CHARGE': Decimal('10000'),  # 10 هزار ریال
    
    # کمیسیون‌ها (درصد)
    'APPOINTMENT_COMMISSION_RATE': Decimal('10'),  # 10%
    'CONSULTATION_COMMISSION_RATE': Decimal('15'),  # 15%
    'DEFAULT_COMMISSION_RATE': Decimal('10'),  # 10%
    
    # محدودیت‌ها
    'MAX_DAILY_WITHDRAWAL': Decimal('50000000'),  # 50 میلیون ریال
    'MAX_MONTHLY_WITHDRAWAL': Decimal('500000000'),  # 500 میلیون ریال
    'MAX_REFUND_DAYS': 7,  # حداکثر 7 روز برای درخواست بازپرداخت
    
    # تایم‌اوت‌ها (ثانیه)
    'PAYMENT_TIMEOUT': 600,  # 10 دقیقه
    'GATEWAY_TIMEOUT': 30,  # 30 ثانیه
    
    # Rate Limiting
    'PAYMENT_RATE_LIMIT': '10/hour',  # 10 پرداخت در ساعت
    'WITHDRAWAL_RATE_LIMIT': '3/day',  # 3 برداشت در روز
    'REFUND_RATE_LIMIT': '5/day',  # 5 درخواست بازپرداخت در روز
}

# تنظیمات درگاه‌های پرداخت
PAYMENT_GATEWAYS = {
    'zarinpal': {
        'merchant_id': getattr(settings, 'ZARINPAL_MERCHANT_ID', ''),
        'sandbox': getattr(settings, 'ZARINPAL_SANDBOX', True),
        'webgate': 'https://sandbox.zarinpal.com/pg/v4/payment/request.json' if getattr(settings, 'ZARINPAL_SANDBOX', True) else 'https://api.zarinpal.com/pg/v4/payment/request.json',
        'gateway': 'https://sandbox.zarinpal.com/pg/StartPay/' if getattr(settings, 'ZARINPAL_SANDBOX', True) else 'https://www.zarinpal.com/pg/StartPay/',
        'verify_url': 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json' if getattr(settings, 'ZARINPAL_SANDBOX', True) else 'https://api.zarinpal.com/pg/v4/payment/verify.json',
    },
    'mellat': {
        'terminal_id': getattr(settings, 'MELLAT_TERMINAL_ID', ''),
        'username': getattr(settings, 'MELLAT_USERNAME', ''),
        'password': getattr(settings, 'MELLAT_PASSWORD', ''),
        'wsdl': 'https://bpm.shaparak.ir/pgwchannel/services/pgw?wsdl',
    },
    'saman': {
        'merchant_id': getattr(settings, 'SAMAN_MERCHANT_ID', ''),
        'password': getattr(settings, 'SAMAN_PASSWORD', ''),
        'terminal_id': getattr(settings, 'SAMAN_TERMINAL_ID', ''),
        'gateway_url': 'https://sep.shaparak.ir/MobilePG/MobilePayment',
        'verify_url': 'https://sep.shaparak.ir/verifyTxnRandomSessionkey/ipg/VerifyTransaction',
    },
}

# تنظیمات کیف پول
WALLET_SETTINGS = {
    'AUTO_CREATE': True,  # ایجاد خودکار کیف پول برای کاربران جدید
    'INITIAL_BALANCE': Decimal('0'),  # موجودی اولیه
    'MAX_BALANCE': Decimal('1000000000'),  # حداکثر موجودی: 1 میلیارد ریال
    'TRANSACTION_HISTORY_LIMIT': 100,  # حداکثر تعداد تراکنش‌های نمایش داده شده
}

# تنظیمات امنیتی
PAYMENT_SECURITY = {
    'ENABLE_3D_SECURE': True,  # فعال‌سازی 3D Secure
    'REQUIRE_CVV': True,  # الزامی بودن CVV
    'MASK_CARD_NUMBER': True,  # ماسک کردن شماره کارت
    'LOG_TRANSACTIONS': True,  # ثبت تمام تراکنش‌ها
    'ENCRYPT_SENSITIVE_DATA': True,  # رمزنگاری داده‌های حساس
}

# تنظیمات اعلان‌ها
PAYMENT_NOTIFICATIONS = {
    'SEND_SMS': True,  # ارسال پیامک
    'SEND_EMAIL': True,  # ارسال ایمیل
    'SEND_PUSH': True,  # ارسال نوتیفیکیشن
    'SMS_TEMPLATES': {
        'payment_success': 'پرداخت شما به مبلغ {amount} ریال با کد پیگیری {tracking_code} با موفقیت انجام شد.',
        'payment_failed': 'پرداخت شما به مبلغ {amount} ریال ناموفق بود. لطفاً مجدداً تلاش کنید.',
        'withdrawal_request': 'درخواست برداشت {amount} ریال ثبت شد. کد پیگیری: {tracking_code}',
        'withdrawal_success': 'برداشت {amount} ریال به حساب شما واریز شد.',
        'refund_success': 'مبلغ {amount} ریال به حساب شما بازگشت داده شد.',
    }
}

# تنظیمات Cache
PAYMENT_CACHE = {
    'CACHE_PAYMENT_METHODS': True,
    'CACHE_TIMEOUT': 3600,  # 1 ساعت
    'CACHE_KEY_PREFIX': 'payment_',
}

# تنظیمات صف‌ها (Celery)
PAYMENT_CELERY = {
    'PROCESS_PAYMENT_QUEUE': 'payment_processing',
    'WITHDRAWAL_QUEUE': 'withdrawal_processing',
    'NOTIFICATION_QUEUE': 'payment_notifications',
    'REPORT_QUEUE': 'payment_reports',
}

# تنظیمات گزارش‌گیری
PAYMENT_REPORTING = {
    'DAILY_REPORT_TIME': '00:00',  # زمان تولید گزارش روزانه
    'MONTHLY_REPORT_DAY': 1,  # روز تولید گزارش ماهانه
    'REPORT_RECIPIENTS': getattr(settings, 'PAYMENT_REPORT_RECIPIENTS', []),
}

# درگاه پیش‌فرض
DEFAULT_PAYMENT_GATEWAY = getattr(settings, 'DEFAULT_PAYMENT_GATEWAY', 'zarinpal')

# تنظیمات لاگ
PAYMENT_LOGGING = {
    'LOG_LEVEL': 'INFO',
    'LOG_FILE': 'payments.log',
    'LOG_MAX_SIZE': 10 * 1024 * 1024,  # 10 MB
    'LOG_BACKUP_COUNT': 5,
}

# Import تنظیمات از settings اصلی (در صورت وجود)
try:
    from django.conf import settings
    
    # Override با تنظیمات پروژه
    if hasattr(settings, 'PAYMENT_SETTINGS'):
        PAYMENT_SETTINGS.update(settings.PAYMENT_SETTINGS)
    
    if hasattr(settings, 'PAYMENT_GATEWAYS'):
        PAYMENT_GATEWAYS.update(settings.PAYMENT_GATEWAYS)
        
    if hasattr(settings, 'WALLET_SETTINGS'):
        WALLET_SETTINGS.update(settings.WALLET_SETTINGS)
        
    if hasattr(settings, 'PAYMENT_SECURITY'):
        PAYMENT_SECURITY.update(settings.PAYMENT_SECURITY)
        
    if hasattr(settings, 'PAYMENT_NOTIFICATIONS'):
        PAYMENT_NOTIFICATIONS.update(settings.PAYMENT_NOTIFICATIONS)
        
except ImportError:
    pass