# اپلیکیشن مدیریت پرداخت‌ها

## معرفی
اپلیکیشن payments مسئول مدیریت تمامی عملیات مالی و پرداخت در پلتفرم پزشکی هلسا است. این اپلیکیشن با معماری 4 هسته‌ای طراحی شده و APIهای جداگانه‌ای برای بیماران و پزشکان ارائه می‌دهد.

## ویژگی‌ها

### ویژگی‌های عمومی
- پشتیبانی از انواع روش‌های پرداخت (آنلاین، کارت به کارت، کیف پول، بیمه)
- سیستم کیف پول یکپارچه
- مدیریت تراکنش‌ها و رسیدها
- گزارش‌گیری جامع مالی
- پشتیبانی از بازپرداخت
- معماری 4 هسته‌ای (API Ingress, Text Processing, Speech Processing, Orchestration)

### ویژگی‌های بیمار
- پرداخت نوبت، مشاوره، دارو، آزمایش و تصویربرداری
- شارژ کیف پول
- درخواست بازپرداخت
- مشاهده تاریخچه پرداخت‌ها
- مدیریت روش‌های پرداخت

### ویژگی‌های پزشک
- درخواست برداشت از کیف پول
- مشاهده گزارش درآمد و کمیسیون
- مدیریت اطلاعات بانکی
- گزارش مالی جامع
- مشاهده تراکنش‌های کیف پول

## نصب و راه‌اندازی

### 1. افزودن به INSTALLED_APPS
```python
INSTALLED_APPS = [
    ...
    'payments',
]
```

### 2. اجرای migration
```bash
python manage.py makemigrations payments
python manage.py migrate payments
```

### 3. افزودن URLs
در فایل `urls.py` اصلی پروژه:
```python
urlpatterns = [
    ...
    path('api/payments/', include('payments.urls')),
]
```

### 4. تنظیمات (اختیاری)
می‌توانید تنظیمات زیر را در `settings.py` پروژه اضافه کنید:

```python
# تنظیمات پرداخت
PAYMENT_SETTINGS = {
    'MIN_PAYMENT_AMOUNT': 1000,  # حداقل مبلغ پرداخت (ریال)
    'MAX_PAYMENT_AMOUNT': 500000000,  # حداکثر مبلغ پرداخت (ریال)
    'APPOINTMENT_COMMISSION_RATE': 10,  # درصد کمیسیون نوبت
    'CONSULTATION_COMMISSION_RATE': 15,  # درصد کمیسیون مشاوره
}

# تنظیمات درگاه‌ها
PAYMENT_GATEWAYS = {
    'zarinpal': {
        'merchant_id': 'YOUR_MERCHANT_ID',
        'sandbox': True,
    }
}

# درگاه پیش‌فرض
DEFAULT_PAYMENT_GATEWAY = 'zarinpal'
```

## مدل‌ها

### Payment
مدل اصلی پرداخت‌ها که شامل اطلاعات:
- کاربر و نوع کاربر (بیمار/پزشک)
- نوع پرداخت
- مبلغ
- وضعیت
- کد پیگیری
- اطلاعات درگاه

### PaymentMethod
روش‌های پرداخت ذخیره شده کاربران:
- نوع روش (آنلاین، کارت، کیف پول، بیمه)
- جزئیات روش
- پیش‌فرض بودن

### Wallet
کیف پول کاربران:
- موجودی کل
- موجودی مسدود شده
- موجودی قابل استفاده

### Transaction
تراکنش‌های مالی:
- نوع تراکنش
- مبلغ
- شماره مرجع
- وضعیت

### WalletTransaction
تراکنش‌های کیف پول:
- نوع تراکنش
- تغییرات موجودی
- توضیحات

## API Endpoints

### endpoints مشترک
- `GET /api/payments/methods/` - دریافت روش‌های پرداخت
- `POST /api/payments/methods/add/` - افزودن روش پرداخت
- `GET /api/payments/history/` - تاریخچه پرداخت‌ها
- `GET /api/payments/detail/<payment_id>/` - جزئیات پرداخت

### endpoints بیمار
- `POST /api/payments/patient/create/` - ایجاد پرداخت جدید
- `POST /api/payments/patient/refund/` - درخواست بازپرداخت
- `GET /api/payments/patient/wallet/` - اطلاعات کیف پول
- `POST /api/payments/patient/wallet/charge/` - شارژ کیف پول
- `GET /api/payments/patient/report/` - گزارش پرداخت‌ها

### endpoints پزشک
- `POST /api/payments/doctor/withdrawal/` - درخواست برداشت
- `GET /api/payments/doctor/earnings/` - گزارش درآمد
- `GET /api/payments/doctor/commissions/` - گزارش کمیسیون
- `POST /api/payments/doctor/bank-info/` - بروزرسانی اطلاعات بانکی
- `GET /api/payments/doctor/wallet/transactions/` - تراکنش‌های کیف پول
- `GET /api/payments/doctor/financial-report/` - گزارش مالی جامع

## نمونه استفاده

### ایجاد پرداخت (بیمار)
```python
POST /api/payments/patient/create/
{
    "payment_type": "appointment",
    "amount": "150000",
    "payment_method_id": 1,
    "appointment_id": "123",
    "doctor_id": "456"
}
```

پاسخ:
```json
{
    "success": true,
    "data": {
        "payment_id": "uuid-here",
        "tracking_code": "PAY202401011234567890",
        "status": "pending",
        "payment_url": "/payments/gateway/uuid-here",
        "amount": "150000"
    }
}
```

### درخواست برداشت (پزشک)
```python
POST /api/payments/doctor/withdrawal/
{
    "amount": "1000000",
    "bank_account": "IR123456789012345678901234"
}
```

پاسخ:
```json
{
    "success": true,
    "data": {
        "payment_id": "uuid-here",
        "tracking_code": "PAY202401011234567891",
        "amount": "1000000",
        "status": "pending",
        "message": "درخواست برداشت با موفقیت ثبت شد و در حال بررسی است"
    }
}
```

## تست‌ها

برای اجرای تست‌ها:
```bash
python manage.py test payments
```

تست‌های موجود:
- تست‌های مدل (ایجاد، اعتبارسنجی، محاسبات)
- تست‌های سرویس (پرداخت، کیف پول، درگاه)
- تست‌های API (endpoints، دسترسی‌ها، خطاها)

## نکات امنیتی

1. **احراز هویت**: تمام APIها نیاز به احراز هویت دارند
2. **بررسی دسترسی**: APIهای بیمار و پزشک از هم جدا هستند
3. **رمزنگاری**: اطلاعات حساس مانند شماره کارت رمزنگاری می‌شوند
4. **Rate Limiting**: محدودیت تعداد درخواست برای جلوگیری از سوءاستفاده
5. **لاگ‌گیری**: تمام تراکنش‌ها و عملیات مهم لاگ می‌شوند

## توسعه

### افزودن درگاه جدید
1. در `services/gateway_service.py` متد مربوط به درگاه را اضافه کنید
2. تنظیمات درگاه را در `settings.py` اضافه کنید
3. در صورت نیاز middleware یا utils خاص درگاه را پیاده‌سازی کنید

### افزودن نوع پرداخت جدید
1. در `models.py` در `PAYMENT_TYPE_CHOICES` نوع جدید را اضافه کنید
2. logic مربوطه را در `cores/orchestrator.py` پیاده‌سازی کنید
3. در صورت نیاز serializer و view مخصوص ایجاد کنید

## پشتیبانی

در صورت بروز مشکل یا سوال:
1. لاگ‌ها را در `logs/payments.log` بررسی کنید
2. مستندات API را مطالعه کنید
3. تست‌های مربوطه را اجرا کنید
4. با تیم توسعه تماس بگیرید

## مجوز
این اپلیکیشن بخشی از پلتفرم پزشکی هلسا است و تحت مجوز اختصاصی قرار دارد.