# Compliance App - مدیریت امنیت و رعایت مقررات

## معرفی
اپ Compliance مسئول مدیریت امنیت، احراز هویت چندعامله (MFA)، کنترل دسترسی (RBAC)، رعایت استانداردهای HIPAA و مدیریت حوادث امنیتی در پلتفرم HELSSA است.

## ویژگی‌ها

### 1. لایه‌های امنیتی (Security Layers)
- مدیریت لایه‌های مختلف امنیتی: Network, Application, Data, Audit
- قابلیت تست و پیکربندی هر لایه
- اولویت‌بندی و فعال/غیرفعال‌سازی

### 2. احراز هویت چندعامله (MFA)
- پشتیبانی از TOTP (Time-based One-Time Password)
- تولید QR Code برای تنظیم در Google Authenticator
- کدهای پشتیبان برای مواقع اضطراری

### 3. کنترل دسترسی بر اساس نقش (RBAC)
- نقش‌های از پیش تعریف شده: بیمار، پزشک، ادمین، پرستار، کارمند
- مدیریت مجوزها برای هر نقش
- دسترسی‌های موقت برای پزشکان

### 4. رعایت HIPAA
- ممیزی خودکار compliance
- گزارش‌گیری از وضعیت رعایت استانداردها
- پیشنهادات بهبود

### 5. مدیریت حوادث امنیتی
- تشخیص و ثبت حوادث امنیتی
- سیستم پاسخ خودکار به حوادث
- پیگیری وضعیت و حل حوادث

### 6. Audit و Logging
- ثبت تمام فعالیت‌های حساس
- قابلیت جستجو و فیلتر در لاگ‌ها
- گزارش‌گیری و آنالیز

## نصب و راه‌اندازی

### 1. افزودن به INSTALLED_APPS
```python
INSTALLED_APPS = [
    ...
    'compliance',
    ...
]
```

### 2. افزودن تنظیمات
در فایل settings.py پروژه:
```python
from compliance.settings import *
```

### 3. افزودن URLs
در urls.py اصلی:
```python
urlpatterns = [
    ...
    path('compliance/', include('compliance.urls')),
    ...
]
```

### 4. اجرای migrations
```bash
python manage.py makemigrations compliance
python manage.py migrate compliance
```

## API Endpoints

### Security Layers
- `GET /compliance/api/security-layers/` - لیست لایه‌های امنیتی
- `POST /compliance/api/security-layers/` - ایجاد لایه جدید
- `POST /compliance/api/security-layers/{id}/test_layer/` - تست لایه

### MFA
- `POST /compliance/api/mfa/enable/` - فعال‌سازی MFA
- `POST /compliance/api/mfa/verify/` - تایید توکن
- `POST /compliance/api/mfa/disable/` - غیرفعال‌سازی MFA
- `GET /compliance/api/mfa/status/` - وضعیت MFA کاربر

### Roles & Access
- `GET /compliance/api/roles/` - لیست نقش‌ها
- `POST /compliance/api/roles/{id}/assign_to_user/` - اختصاص نقش به کاربر
- `GET /compliance/api/temporary-access/` - دسترسی‌های موقت
- `POST /compliance/api/temporary-access/{id}/revoke/` - لغو دسترسی

### HIPAA Compliance
- `POST /compliance/api/hipaa-compliance/run_audit/` - اجرای ممیزی
- `GET /compliance/api/hipaa-compliance/latest/` - آخرین گزارش

### Security Dashboard
- `GET /compliance/api/dashboard/` - داشبورد امنیت

## وابستگی‌ها

### وابستگی‌های نصب شده
- Django
- Django REST Framework
- pyotp (برای MFA)
- cryptography (برای رمزنگاری)

### وابستگی‌های در انتظار پیاده‌سازی
- **unified_auth**: برای مدل UnifiedUser و احراز هویت یکپارچه
- **medical**: برای مدل‌های Encounter و سایر داده‌های پزشکی
- **MinIO**: برای ذخیره‌سازی امن فایل‌ها

## نکات مهم

### 1. امنیت
- تمام داده‌های حساس باید رمزنگاری شوند
- دسترسی‌ها باید بر اساس اصل Least Privilege باشد
- تمام فعالیت‌ها باید در audit log ثبت شوند

### 2. Performance
- استفاده از index برای فیلدهای پرکاربرد
- cache کردن نتایج محاسبات سنگین
- استفاده از select_related برای کاهش query ها

### 3. توسعه آینده
- پیاده‌سازی ML برای تشخیص anomaly
- یکپارچه‌سازی با SIEM خارجی
- پشتیبانی از WebAuthn/FIDO2

## تست‌ها
```bash
python manage.py test compliance
```

## مستندات بیشتر
برای اطلاعات بیشتر به فایل‌های زیر مراجعه کنید:
- `/agent/docs/15-security-compliance.md` - مستندات کامل امنیت و compliance
- `/agent/instructions/SECURITY_POLICIES.md` - سیاست‌های امنیتی