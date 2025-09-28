# پنل ادمین هلسا (AdminPortal)

## معرفی

پنل ادمین هلسا یک سیستم کامل مدیریت و پشتیبانی داخلی برای پلتفرم هلسا است که شامل ابزارهای پیشرفته برای مدیریت کاربران، پشتیبانی، مانیتورینگ سیستم و عملیات ادمین می‌باشد.

## ویژگی‌ها

### 🔐 مدیریت کاربران ادمین
- ایجاد و مدیریت کاربران ادمین با نقش‌های مختلف
- سیستم دسترسی‌های پیشرفته و قابل تنظیم
- ردیابی فعالیت‌ها و نشست‌های ادمین
- مدیریت جلسات و کنترل دسترسی

### 🎫 مدیریت تیکت‌های پشتیبانی
- سیستم تیکت‌گذاری پیشرفته با اولویت‌بندی
- تخصیص خودکار و دستی تیکت‌ها
- ردیابی زمان پاسخ و حل مسئله
- گزارش‌گیری عملکرد پشتیبانی

### ⚙️ عملیات سیستمی
- مدیریت و نظارت بر عملیات سیستم
- اجرای وظایف پس‌زمینه
- مانیتورینگ منابع سیستم
- بک‌آپ و بازیابی داده‌ها

### 📊 گزارش‌گیری و تحلیل
- تولید گزارش‌های جامع از فعالیت‌های سیستم
- تحلیل عملکرد و آمارهای کاربری
- صادرات گزارش‌ها در فرمت‌های مختلف
- داشبورد تعاملی با چارت‌های زنده

### 🎤 پردازش صوت و متن
- تبدیل گفتار به متن برای یادداشت‌های ادمین
- تحلیل محتوای متنی و شناسایی کلمات کلیدی
- فیلترینگ محتوای حساس
- پردازش دستورات صوتی

### 🔍 جستجو و فیلترینگ
- جستجوی پیشرفته در تمام بخش‌های سیستم
- فیلترهای قابل تنظیم و ذخیره‌سازی
- جستجوی هوشمند با پردازش زبان طبیعی
- نتایج مرتب‌سازی شده بر اساس ارتباط

## معماری

### 🏗️ معماری چهار هسته‌ای

پنل ادمین بر اساس معماری چهار هسته‌ای طراحی شده است:

#### 1. API Ingress Core
- مدیریت ورودی و خروجی API
- اعتبارسنجی و امنیت درخواست‌ها
- Rate limiting و محدودیت‌های دسترسی
- لاگ‌گیری و حسابرسی

#### 2. Text Processor Core
- پردازش و تحلیل متن
- جستجوی هوشمند
- فیلترینگ محتوای حساس
- تولید خلاصه و کلمات کلیدی

#### 3. Speech Processor Core
- پردازش فایل‌های صوتی
- تبدیل گفتار به متن
- تحلیل دستورات صوتی
- پردازش یادداشت‌های صوتی

#### 4. Central Orchestrator
- هماهنگی بین سایر هسته‌ها
- مدیریت workflow ها
- عملیات دسته‌ای
- مانیتورینگ سیستم

## نصب و راه‌اندازی

### پیش‌نیازها
- Python 3.11+
- Django 5.2+
- PostgreSQL 14+
- Redis 6+
- Django REST Framework

### مراحل نصب

1. **اضافه کردن به INSTALLED_APPS**
```python
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'rest_framework_simplejwt',
    'adminportal',
    # ...
]
```

2. **تنظیم REST Framework**
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

3. **اضافه کردن URLs**
```python
urlpatterns = [
    # ...
    path('adminportal/', include('adminportal.urls')),
    # ...
]
```

4. **اجرای Migration**
```bash
python manage.py makemigrations adminportal
python manage.py migrate
```

5. **ایجاد کاربر ادمین اول**
```bash
python manage.py createsuperuser
```

## استفاده

### نقش‌های کاربری

#### Super Admin
- دسترسی کامل به تمام بخش‌ها
- مدیریت سایر ادمین‌ها
- تنظیمات سیستم

#### Support Admin
- مدیریت تیکت‌های پشتیبانی
- مشاهده کاربران
- تولید گزارش‌های پشتیبانی

#### Technical Admin
- مدیریت عملیات سیستمی
- مانیتورینگ سیستم
- بک‌آپ و بازیابی

#### Content Admin
- تحلیل محتوا
- پردازش متن و صوت
- مدیریت محتوای کاربران

#### Financial Admin
- مشاهده گزارش‌های مالی
- صادرات داده‌ها
- تحلیل عملکرد مالی

### API Endpoints

#### احراز هویت
```
POST /adminportal/auth/login/     # ورود
POST /adminportal/auth/refresh/   # تازه‌سازی توکن
POST /adminportal/auth/verify/    # تأیید توکن
```

#### مدیریت ادمین‌ها
```
GET    /adminportal/api/v1/admin-users/           # لیست ادمین‌ها
POST   /adminportal/api/v1/admin-users/           # ایجاد ادمین جدید
PUT    /adminportal/api/v1/admin-users/{id}/      # ویرایش ادمین
DELETE /adminportal/api/v1/admin-users/{id}/      # حذف ادمین
```

#### مدیریت تیکت‌ها
```
GET  /adminportal/api/v1/support-tickets/           # لیست تیکت‌ها
POST /adminportal/api/v1/support-tickets/{id}/assign-to-me/  # تخصیص به خودم
POST /adminportal/api/v1/support-tickets/{id}/resolve/      # حل تیکت
```

#### عملیات سیستمی
```
GET  /adminportal/api/v1/system-operations/         # لیست عملیات
POST /adminportal/api/v1/system-operations/{id}/start/     # شروع عملیات
POST /adminportal/api/v1/system-operations/{id}/complete/  # تکمیل عملیات
```

#### ابزارهای پیشرفته
```
POST /adminportal/api/v1/search/              # جستجوی محتوا
POST /adminportal/api/v1/bulk-operations/     # عملیات دسته‌ای
POST /adminportal/api/v1/generate-report/     # تولید گزارش
POST /adminportal/api/v1/process-voice/       # پردازش صوت
POST /adminportal/api/v1/analyze-content/     # تحلیل محتوا
```

### نمونه کد

#### ایجاد کاربر ادمین
```python
from adminportal.models import AdminUser
from django.contrib.auth import get_user_model

User = get_user_model()

# ایجاد کاربر
user = User.objects.create_user(
    username='support_admin',
    email='support@helssa.com'
)

# ایجاد پروفایل ادمین
admin_user = AdminUser.objects.create(
    user=user,
    role='support_admin',
    department='پشتیبانی',
    permissions=['view_tickets', 'manage_tickets']
)
```

#### بررسی دسترسی
```python
from adminportal.permissions import AdminPermissions

# بررسی دسترسی
if AdminPermissions.has_permission(admin_user, 'manage_tickets'):
    # کاربر دسترسی دارد
    pass
```

#### پردازش صوت
```python
from adminportal.cores import SpeechProcessorCore

processor = SpeechProcessorCore()
result = processor.process_voice_command(audio_data, 'wav')

if result['success']:
    transcription = result['transcription']['text']
    command = result['command_analysis']['command']
```

## تنظیمات

### تنظیمات اصلی
```python
# settings.py

# فعال‌سازی adminportal
ADMINPORTAL_ENABLED = True

# سطح لاگ
ADMINPORTAL_LOG_LEVEL = 'INFO'

# تنظیمات امنیتی
ADMINPORTAL_REQUIRE_HTTPS = True
ADMINPORTAL_RATE_LIMIT_REQUESTS = 100

# تنظیمات پردازش صوت
ADMINPORTAL_MAX_AUDIO_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ADMINPORTAL_SUPPORTED_AUDIO_FORMATS = ['wav', 'mp3', 'ogg']
```

### متغیرهای محیطی
```bash
# .env
ADMINPORTAL_ENABLED=true
ADMINPORTAL_DEBUG=false
ADMINPORTAL_LOG_LEVEL=INFO
ADMINPORTAL_REQUIRE_HTTPS=true
```

## مانیتورینگ و لاگ‌گیری

### لاگ‌های سیستم
- تمام عملیات ادمین لاگ می‌شوند
- جزئیات کامل تغییرات ثبت می‌شود
- لاگ‌های امنیتی جداگانه

### متریک‌های عملکرد
- زمان پاسخ API ها
- تعداد درخواست‌ها
- استفاده از منابع سیستم
- نرخ موفقیت عملیات

## امنیت

### احراز هویت و مجوزها
- JWT token برای احراز هویت
- سیستم نقش‌محور دسترسی‌ها
- Rate limiting برای پیشگیری از حملات
- لاگ‌گیری کامل فعالیت‌ها

### حفاظت از داده‌ها
- فیلترینگ اطلاعات حساس
- رمزنگاری داده‌های حساس
- Audit trail کامل
- Backup خودکار

## عملکرد

### بهینه‌سازی‌ها
- Cache کردن دسترسی‌ها
- Pagination برای لیست‌های بزرگ
- Lazy loading برای داده‌های سنگین
- Database indexing

### مقیاس‌پذیری
- پردازش موازی عملیات دسته‌ای
- Queue برای تسک‌های سنگین
- Horizontal scaling قابلیت

## تست‌ها

### اجرای تست‌ها
```bash
# تست‌های واحد
python manage.py test adminportal

# تست‌های API
python manage.py test adminportal.tests.AdminPortalAPITest

# تست‌های یکپارچگی
python manage.py test adminportal.tests.AdminPortalIntegrationTest
```

### پوشش تست
- تست‌های مدل‌ها
- تست‌های API
- تست‌های دسترسی‌ها
- تست‌های هسته‌ها

## مشارکت

برای مشارکت در توسعه پنل ادمین:

1. کد را Fork کنید
2. برنچ feature ایجاد کنید
3. تغییرات را commit کنید
4. تست‌ها را اجرا کنید
5. Pull Request ارسال کنید

## پشتیبانی

برای دریافت پشتیبانی:
- ایمیل: support@helssa.com
- مستندات: `/adminportal/docs/`
- لاگ‌ها: `/logs/adminportal.log`

## مجوز

این پروژه تحت مجوز اختصاصی هلسا/مدوگرام است.
© 2024 Helssa/Medogram. All rights reserved.