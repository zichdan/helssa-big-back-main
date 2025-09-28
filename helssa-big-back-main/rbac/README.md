# RBAC (Role-Based Access Control) App

## معرفی
اپلیکیشن RBAC مسئول مدیریت کاربران یکپارچه، نقش‌ها و دسترسی‌ها در پروژه هلسا است. این اپ شامل:
- مدل کاربر یکپارچه (UnifiedUser) برای همه انواع کاربران
- پروفایل‌های اختصاصی برای بیماران و پزشکان
- سیستم مدیریت نقش‌ها و دسترسی‌ها
- مدیریت نشست‌ها و توکن‌های JWT
- سیستم audit log برای ثبت فعالیت‌های امنیتی

## نصب و راه‌اندازی

### 1. اضافه کردن به INSTALLED_APPS
```python
INSTALLED_APPS = [
    # ...
    'rbac',
    # ...
]
```

### 2. تنظیم AUTH_USER_MODEL
```python
AUTH_USER_MODEL = 'rbac.UnifiedUser'
```

### 3. اجرای migrations
```bash
python manage.py makemigrations rbac
python manage.py migrate rbac
```

## مدل‌ها

### UnifiedUser
مدل کاربر اصلی که جایگزین User پیش‌فرض Django می‌شود:
- احراز هویت با شماره موبایل
- پشتیبانی از انواع کاربر: بیمار، پزشک، ادمین، کارمند
- فیلدهای امنیتی مثل two_factor_enabled و failed_login_attempts

### PatientProfile
پروفایل اختصاصی بیماران:
- شماره پرونده پزشکی
- اطلاعات پزشکی (گروه خونی، حساسیت‌ها، سوابق)
- محاسبه خودکار BMI
- تنظیمات حریم خصوصی

### DoctorProfile
پروفایل اختصاصی پزشکان:
- شماره پروانه و نظام پزشکی
- تخصص و سوابق تحصیلی
- ساعات کاری و هزینه ویزیت
- آمار عملکرد و نرخ موفقیت

### Role & Permission
سیستم RBAC کامل:
- نقش‌های پیش‌فرض: patient_basic, doctor_basic, admin, etc.
- مجوزها بر اساس resource و action
- امکان اختصاص نقش با تاریخ انقضا

### UserSession
مدیریت نشست‌های کاربران:
- ذخیره امن توکن‌ها (به صورت هش)
- اطلاعات دستگاه و IP
- مدیریت انقضای نشست

### AuthAuditLog
ثبت تمام فعالیت‌های امنیتی:
- انواع رویداد: login, logout, permission_denied, etc.
- ذخیره IP و User Agent
- متادیتای اضافی

## استفاده

### ایجاد کاربر جدید
```python
from django.contrib.auth import get_user_model

User = get_user_model()

# ایجاد بیمار
patient = User.objects.create_user(
    phone_number='09123456789',
    first_name='علی',
    last_name='احمدی',
    user_type='patient',
    password='secure_password'
)

# ایجاد پروفایل بیمار
patient_profile = PatientProfile.objects.create(
    user=patient,
    medical_record_number='MRN123456',
    blood_type='A+'
)
```

### اختصاص نقش به کاربر
```python
from rbac.models import Role, UserRole

# دریافت نقش
role = Role.objects.get(name='patient_basic')

# اختصاص به کاربر
user_role = UserRole.objects.create(
    user=patient,
    role=role,
    assigned_by=admin_user,
    reason='ثبت‌نام اولیه'
)
```

### بررسی دسترسی
```python
# بررسی نوع کاربر
if user.is_patient:
    # عملیات مخصوص بیمار
    pass

# بررسی نقش فعال
active_roles = user.user_roles.filter(
    is_active=True,
    expires_at__gt=timezone.now()
).select_related('role')

# بررسی مجوز خاص
has_permission = user.user_roles.filter(
    role__permissions__codename='view_medical_records',
    is_active=True
).exists()
```

### ثبت لاگ امنیتی
```python
from rbac.models import AuthAuditLog

AuthAuditLog.objects.create(
    user=user,
    event_type='login_success',
    ip_address=request.META.get('REMOTE_ADDR'),
    user_agent=request.META.get('HTTP_USER_AGENT'),
    success=True,
    metadata={'login_method': 'otp'}
)
```

## تنظیمات

در فایل `rbac/settings.py` تنظیمات زیر قابل استفاده است:

### تنظیمات OTP
- `OTP_LENGTH`: طول کد OTP (پیش‌فرض: 6)
- `OTP_LIFETIME`: مدت اعتبار OTP به ثانیه (پیش‌فرض: 120)
- `OTP_MAX_ATTEMPTS`: حداکثر تلاش برای OTP (پیش‌فرض: 3)

### تنظیمات JWT
- `ACCESS_TOKEN_LIFETIME`: مدت اعتبار access token (پیش‌فرض: 15 دقیقه)
- `REFRESH_TOKEN_LIFETIME`: مدت اعتبار refresh token (پیش‌فرض: 7 روز)

### تنظیمات نشست
- `SESSION_TIMEOUT`: مدت عدم فعالیت تا انقضای نشست (پیش‌فرض: 2 ساعت)
- `MAX_SESSIONS_PER_USER`: حداکثر نشست همزمان (پیش‌فرض: 5)

## تست‌ها

برای اجرای تست‌ها:
```bash
python manage.py test rbac
```

تست‌های موجود:
- تست‌های مدل UnifiedUser
- تست‌های PatientProfile و DoctorProfile
- تست‌های سیستم RBAC
- تست‌های UserSession
- تست‌های AuthAuditLog

## نکات امنیتی

1. **توکن‌ها**: همیشه به صورت هش ذخیره می‌شوند
2. **Rate Limiting**: برای جلوگیری از حملات brute force
3. **Audit Logging**: تمام فعالیت‌های حساس ثبت می‌شوند
4. **Session Management**: امکان مدیریت و خاتمه نشست‌ها
5. **Two-Factor Auth**: پشتیبانی از احراز هویت دو مرحله‌ای

## مشارکت

برای مشارکت در توسعه:
1. Fork کنید
2. Branch جدید ایجاد کنید
3. تغییرات خود را commit کنید
4. Pull Request ارسال کنید

## لایسنس

این پروژه تحت لایسنس پروژه هلسا قرار دارد.