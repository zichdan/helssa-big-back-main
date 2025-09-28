# API Gateway App

اپ API Gateway برای پروژه هلسا - دروازه ورودی تمام درخواست‌های API

## معرفی

این اپ به عنوان دروازه اصلی برای تمام درخواست‌های API سیستم هلسا عمل می‌کند و شامل موارد زیر است:

- **API Ingress**: دریافت و اعتبارسنجی اولیه درخواست‌ها
- **Text Processing**: پردازش متن‌ها شامل تحلیل زبان، احساسات و استخراج کلیدواژه
- **Speech Processing**: پردازش فایل‌های صوتی، STT و TTS
- **Orchestrator**: مدیریت workflow های پیچیده و اجرای موازی تسک‌ها

## معماری چهار هسته‌ای

### 1. API Ingress Core
- اعتبارسنجی درخواست‌ها
- استخراج metadata
- تشخیص نوع پردازش مورد نیاز
- Rate limiting

### 2. Text Processor Core
- تشخیص زبان متن
- پاکسازی و نرمال‌سازی
- استخراج کلیدواژه‌ها
- تحلیل احساسات
- تولید خلاصه

### 3. Speech Processor Core
- پردازش فایل‌های صوتی
- تبدیل گفتار به متن (STT)
- تبدیل متن به گفتار (TTS)
- تحلیل صوتی

### 4. Orchestrator Core
- اجرای workflow های چندمرحله‌ای
- اجرای موازی تسک‌ها
- مانیتورینگ و کنترل فرآیندها

## مدل‌های دیتابیس

### UnifiedUser
کاربر یکپارچه برای تمام نوع کاربران سیستم

### APIRequest
لاگ تمام درخواست‌های API برای مانیتورینگ و آنالیز

### Workflow
مدیریت workflow های پیچیده و چندمرحله‌ای

### RateLimitTracker
ردگیری محدودیت نرخ درخواست‌ها

## API Endpoints

### عمومی
- `GET /api/health/` - بررسی سلامت سیستم
- `POST /api/auth/register/` - ثبت‌نام کاربر جدید

### پردازش متن
- `POST /api/text/process/` - پردازش کامل متن

### پردازش صدا
- `POST /api/speech/process/` - پردازش فایل صوتی
- `POST /api/speech/stt/` - تبدیل گفتار به متن
- `POST /api/speech/tts/` - تبدیل متن به گفتار

### مدیریت Workflow
- `POST /api/workflow/execute/` - اجرای workflow
- `POST /api/workflow/parallel/` - اجرای موازی تسک‌ها
- `GET /api/workflow/{id}/status/` - وضعیت workflow
- `POST /api/workflow/{id}/cancel/` - لغو workflow

### کاربر
- `GET /api/auth/requests/` - لیست درخواست‌های کاربر

## نصب و راه‌اندازی

### 1. افزودن به INSTALLED_APPS
```python
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'corsheaders',
    'api_gateway',
    # ...
]
```

### 2. اضافه کردن URLs
```python
urlpatterns = [
    # ...
    path('api/v1/', include('api_gateway.urls')),
    path('api/', include('api_gateway.urls')),
]
```

### 3. اجرای migrations
```bash
python manage.py makemigrations api_gateway
python manage.py migrate
```

### 4. ایجاد superuser
```bash
python manage.py createsuperuser
```

## تنظیمات

تنظیمات اپ در فایل `api_gateway/settings.py` قرار دارد:

```python
from api_gateway.settings import API_GATEWAY_SETTINGS

# دسترسی به تنظیمات
rate_limit = API_GATEWAY_SETTINGS['DEFAULT_RATE_LIMIT']
max_text_length = API_GATEWAY_SETTINGS['MAX_TEXT_LENGTH']
```

## تست‌ها

اجرای تست‌ها:

```bash
# تست تمام اپ
python manage.py test api_gateway

# تست کلاس خاص
python manage.py test api_gateway.tests.APIGatewayCoreTests

# تست با coverage
coverage run --source='.' manage.py test api_gateway
coverage report
```

## استفاده

### پردازش متن
```python
from api_gateway.services import APIGatewayService

service = APIGatewayService()
success, result = service.process_text(
    text="این یک متن نمونه است",
    options={'include_stats': True},
    user=user
)
```

### اجرای Workflow
```python
workflow_config = {
    'steps': [
        {
            'name': 'Process Text',
            'type': 'text_processing',
            'params': {'text': 'sample text'}
        }
    ]
}

success, result = service.execute_workflow(
    workflow_config=workflow_config,
    user=user
)
```

## امنیت

- تمام endpoint ها دارای rate limiting
- اعتبارسنجی کامل داده‌های ورودی
- لاگ کامل درخواست‌ها
- پوشاندن داده‌های حساس در لاگ‌ها

## مانیتورینگ

- لاگ تمام درخواست‌ها در دیتابیس
- متریک‌های performance
- Health check endpoint
- Dashboard مدیریت در Django Admin

## مشارکت

لطفاً استانداردهای کدنویسی پروژه هلسا را رعایت کنید:

1. کامنت‌ها و مستندات به فارسی
2. نام متغیرها و توابع به انگلیسی
3. Type hints برای تمام توابع
4. تست برای تمام functionality ها
5. رعایت معماری چهار هسته‌ای

## لایسنس

© Helssa/Medogram. All rights reserved.