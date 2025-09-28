# سیستم احراز هویت OTP با کاوه‌نگار

## معرفی

این اپلیکیشن یک سیستم کامل احراز هویت مبتنی بر OTP (One-Time Password) با استفاده از سرویس پیامک کاوه‌نگار است که شامل موارد زیر می‌باشد:

- ارسال و تأیید کد OTP
- مدیریت توکن‌های JWT
- محدودیت نرخ (Rate Limiting)
- مدیریت نشست‌ها
- پنل ادمین کامل

## ویژگی‌ها

### 1. ارسال OTP
- ارسال کد 6 رقمی به شماره موبایل
- پشتیبانی از ارسال پیامک و تماس صوتی
- محدودیت نرخ: 1 در دقیقه، 5 در ساعت، 10 در روز
- مسدودسازی خودکار بعد از 10 تلاش ناموفق

### 2. تأیید OTP
- اعتبار 3 دقیقه‌ای برای هر کد
- حداکثر 3 تلاش برای هر کد
- ایجاد خودکار کاربر جدید در صورت عدم وجود

### 3. مدیریت توکن
- JWT با access token (5 دقیقه) و refresh token (7 روز)
- Blacklist برای توکن‌های باطل شده
- Refresh token rotation

### 4. مدیریت نشست
- مشاهده نشست‌های فعال
- امکان خروج از یک یا همه دستگاه‌ها
- ذخیره اطلاعات دستگاه و IP

## نصب و راه‌اندازی

### 1. افزودن به INSTALLED_APPS

```python
INSTALLED_APPS = [
    # ...
    'auth_otp',
    'rest_framework',
    'rest_framework_simplejwt',
    # ...
]
```

### 2. تنظیمات کاوه‌نگار

```python
# settings.py

# کاوه‌نگار
KAVENEGAR_API_KEY = 'your-api-key'
KAVENEGAR_SENDER = '10004346'  # شماره ارسال (اختیاری)
KAVENEGAR_OTP_TEMPLATE = 'verify'  # نام قالب در کاوه‌نگار

# JWT
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    'JTI_CLAIM': 'jti',
}
```

### 3. افزودن URLs

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    # ...
    path('api/auth/', include('auth_otp.urls')),
    # ...
]
```

### 4. اجرای Migration

```bash
python manage.py makemigrations auth_otp
python manage.py migrate
```

## API Endpoints

### ارسال OTP

```
POST /api/auth/otp/send/
```

Request Body:
```json
{
    "phone_number": "09123456789",
    "purpose": "login",  // login, register, reset_password, verify_phone
    "sent_via": "sms"    // sms, call
}
```

Response:
```json
{
    "success": true,
    "data": {
        "otp_id": "uuid",
        "expires_at": "2024-01-01T12:00:00Z",
        "expires_in": 180,
        "message": "کد تأیید با موفقیت ارسال شد"
    }
}
```

### تأیید OTP

```
POST /api/auth/otp/verify/
```

Request Body:
```json
{
    "phone_number": "09123456789",
    "otp_code": "123456",
    "purpose": "login",
    "device_id": "optional-device-id",
    "device_name": "iPhone 12"
}
```

Response:
```json
{
    "success": true,
    "data": {
        "tokens": {
            "access": "jwt-access-token",
            "refresh": "jwt-refresh-token",
            "token_type": "Bearer",
            "expires_in": 300
        },
        "user": {
            "id": "uuid",
            "username": "09123456789",
            "user_type": "patient",
            "full_name": ""
        },
        "is_new_user": true,
        "message": "ورود موفقیت‌آمیز"
    }
}
```

### تازه‌سازی توکن

```
POST /api/auth/token/refresh/
```

Request Body:
```json
{
    "refresh": "jwt-refresh-token"
}
```

### خروج

```
POST /api/auth/logout/
```

Headers:
```
Authorization: Bearer jwt-access-token
```

Request Body:
```json
{
    "refresh": "jwt-refresh-token",
    "logout_all_devices": false
}
```

### وضعیت OTP

```
GET /api/auth/otp/status/{otp_id}/
```

### محدودیت نرخ

```
GET /api/auth/rate-limit/{phone_number}/
```

### نشست‌های کاربر

```
GET /api/auth/sessions/
```

Headers:
```
Authorization: Bearer jwt-access-token
```

### لغو نشست

```
POST /api/auth/sessions/{session_id}/revoke/
```

Headers:
```
Authorization: Bearer jwt-access-token
```

## مدل‌های دیتابیس

### OTPRequest
- ذخیره درخواست‌های ارسال OTP
- شامل کد، زمان انقضا، تعداد تلاش

### OTPVerification
- ذخیره تأییدیه‌های موفق
- شامل توکن‌ها و اطلاعات دستگاه

### OTPRateLimit
- مدیریت محدودیت نرخ برای هر شماره
- شمارنده‌های دقیقه، ساعت و روز

### TokenBlacklist
- لیست سیاه توکن‌های باطل شده

## دستورات مدیریت

### پاکسازی داده‌های منقضی

```bash
# پاکسازی واقعی
python manage.py cleanup_otp

# نمایش تعداد بدون حذف
python manage.py cleanup_otp --dry-run

# تنظیم سن OTP برای حذف
python manage.py cleanup_otp --otp-age-hours 48
```

پیشنهاد می‌شود این دستور را با cron job روزانه اجرا کنید:

```bash
# crontab -e
0 3 * * * cd /path/to/project && python manage.py cleanup_otp
```

## پنل ادمین

همه مدل‌ها در پنل ادمین Django قابل مدیریت هستند:

- مشاهده درخواست‌های OTP
- مدیریت محدودیت‌های نرخ
- رفع مسدودیت شماره‌ها
- مشاهده نشست‌های فعال
- مدیریت توکن‌های مسدود

## تست‌ها

اجرای تست‌ها:

```bash
python manage.py test auth_otp
```

پوشش تست:
- مدل‌ها و خصوصیات آنها
- سرویس OTP و rate limiting
- سرویس احراز هویت و توکن
- API endpoints
- دستورات پاکسازی

## نکات امنیتی

1. **محافظت از API Key کاوه‌نگار**: از متغیرهای محیطی استفاده کنید
2. **HTTPS الزامی**: همیشه از HTTPS در production استفاده کنید
3. **Rate Limiting**: محدودیت‌های پیش‌فرض را بررسی و تنظیم کنید
4. **Token Lifetime**: زمان اعتبار توکن‌ها را متناسب با نیاز تنظیم کنید
5. **Logging**: لاگ‌های امنیتی را فعال و مانیتور کنید

## Troubleshooting

### خطای ارسال پیامک
- API Key کاوه‌نگار را بررسی کنید
- اعتبار حساب کاوه‌نگار را چک کنید
- لاگ‌ها را برای جزئیات خطا بررسی کنید

### خطای Rate Limit
- محدودیت‌ها در مدل OTPRateLimit قابل تنظیم هستند
- برای رفع مسدودیت از پنل ادمین استفاده کنید

### توکن نامعتبر
- مطمئن شوید SECRET_KEY در تنظیمات تغییر نکرده
- زمان سرور را بررسی کنید (برای انقضای توکن)

## مشارکت

برای گزارش باگ یا پیشنهاد بهبود، لطفاً issue ایجاد کنید.