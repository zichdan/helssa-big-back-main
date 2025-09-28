# {{APP_NAME}} - {{APP_DESCRIPTION}}

## نمای کلی

{{APP_OVERVIEW}}

## ویژگی‌ها

### برای بیماران
{{PATIENT_FEATURES_LIST}}

### برای پزشکان
{{DOCTOR_FEATURES_LIST}}

### مشترک
{{SHARED_FEATURES_LIST}}

## معماری

این اپلیکیشن بر اساس معماری چهار هسته‌ای پلتفرم هلسا طراحی شده است:

### هسته‌های پیاده‌سازی شده

#### 1. هسته‌ی ورودی API (API Ingress Core)
- مدیریت درخواست‌ها و پاسخ‌ها
- احراز هویت با Unified Auth
- اعتبارسنجی داده‌های ورودی
- Rate limiting و امنیت

#### 2. هسته‌ی پردازش متن (Text Processing Core)
{{#if USES_TEXT_PROCESSING}}
- یکپارچه‌سازی با unified_ai
- پردازش زبان طبیعی
- تولید محتوای هوشمند
{{else}}
- این اپ از پردازش متن استفاده نمی‌کند
{{/if}}

#### 3. هسته‌ی پردازش صوت (Speech Processing Core)
{{#if USES_SPEECH_PROCESSING}}
- تبدیل گفتار به متن (STT)
- پردازش فایل‌های صوتی
- یکپارچه‌سازی با Whisper
{{else}}
- این اپ از پردازش صوت استفاده نمی‌کند
{{/if}}

#### 4. هسته‌ی ارکستراسیون مرکزی (Central Orchestration Core)
- مدیریت جریان کار (workflow)
- منطق تجاری
- هماهنگی بین هسته‌ها

## API Endpoints

### احراز هویت
همه endpoints نیاز به احراز هویت دارند (JWT token):
```
Authorization: Bearer <access_token>
```

### Endpoints بیمار

{{PATIENT_API_ENDPOINTS}}

### Endpoints پزشک

{{DOCTOR_API_ENDPOINTS}}

### Endpoints مشترک

{{SHARED_API_ENDPOINTS}}

## نصب و راه‌اندازی

### پیش‌نیازها
- Django 4.2+
- Python 3.9+
- Redis (برای cache و rate limiting)
- MySQL/PostgreSQL
{{ADDITIONAL_REQUIREMENTS}}

### مراحل نصب

#### 1. اضافه کردن به INSTALLED_APPS
```python
# در فایل settings.py
INSTALLED_APPS = [
    # ...
    '{{APP_NAME}}.apps.{{APP_CLASS_NAME}}',
    # ...
]
```

#### 2. اضافه کردن URLs
```python
# در فایل urls.py اصلی
urlpatterns = [
    # ...
    path('{{URL_PREFIX}}/', include('{{APP_NAME}}.urls')),
    # ...
]
```

#### 3. اجرای Migrations
```bash
python manage.py makemigrations {{APP_NAME}}
python manage.py migrate {{APP_NAME}}
```

#### 4. تنظیم متغیرهای محیطی
```bash
{{ENVIRONMENT_VARIABLES}}
```

### تنظیمات اضافی Django

```python
# settings.py

{{ADDITIONAL_SETTINGS}}
```

## مدل‌های داده

{{DATA_MODELS_DOCUMENTATION}}

## احراز هویت و امنیت

### سیستم احراز هویت
- **unified_auth.UnifiedUser**: مدل کاربر یکپارچه
- **JWT Authentication**: برای API calls
- **OTP Verification**: برای عملیات حساس

### تفکیک نقش‌ها
```python
# بررسی نوع کاربر
if request.user.user_type == 'patient':
    # منطق بیمار
elif request.user.user_type == 'doctor':
    # منطق پزشک
```

### دسترسی موقت پزشک
```python
# استفاده از unified_access
from unified_access.decorators import require_patient_access

@require_patient_access
def view_patient_data(request, patient_id):
    # دسترسی تضمین شده
    pass
```

## یکپارچه‌سازی‌ها

### Unified Billing
{{BILLING_INTEGRATION_DOCS}}

### Unified Access
{{ACCESS_INTEGRATION_DOCS}}

### Kavenegar SMS
{{SMS_INTEGRATION_DOCS}}

### درگاه‌های پرداخت
{{PAYMENT_INTEGRATION_DOCS}}

## داشبورد پزشک

{{DOCTOR_DASHBOARD_DOCS}}

## مثال‌های کاربرد

### درخواست نمونه - بیمار
```bash
curl -X POST "{{API_BASE_URL}}/{{URL_PREFIX}}/patient/action/" \
  -H "Authorization: Bearer <patient_token>" \
  -H "Content-Type: application/json" \
  -d '{
    {{PATIENT_REQUEST_EXAMPLE}}
  }'
```

### پاسخ نمونه
```json
{{PATIENT_RESPONSE_EXAMPLE}}
```

### درخواست نمونه - پزشک
```bash
curl -X GET "{{API_BASE_URL}}/{{URL_PREFIX}}/doctor/dashboard/" \
  -H "Authorization: Bearer <doctor_token>"
```

### پاسخ نمونه
```json
{{DOCTOR_RESPONSE_EXAMPLE}}
```

## تست‌ها

### اجرای تست‌ها
```bash
# تست‌های واحد
python manage.py test {{APP_NAME}}.tests.unit

# تست‌های تلفیقی  
python manage.py test {{APP_NAME}}.tests.integration

# تست‌های End-to-End
python manage.py test {{APP_NAME}}.tests.e2e
```

### پوشش تست
هدف: حداقل 90% coverage

```bash
coverage run --source='{{APP_NAME}}' manage.py test {{APP_NAME}}
coverage report -m
```

## مانیتورینگ و لاگ‌گذاری

### Health Check
```bash
curl {{API_BASE_URL}}/{{URL_PREFIX}}/health/
```

### لاگ‌ها
{{LOGGING_CONFIGURATION}}

### Metrics
{{MONITORING_METRICS}}

## عیب‌یابی

### مشکلات رایج

#### خطای احراز هویت
```
{"error": "Authentication credentials were not provided."}
```
**راه‌حل**: JWT token را در header Authorization اضافه کنید

#### خطای دسترسی
```
{"error": "Permission denied for this user type."}
```
**راه‌حل**: نوع کاربر و permissions را بررسی کنید

#### خطای Rate Limiting  
```
{"error": "Rate limit exceeded. Try again later."}
```
**راه‌حل**: فاصله زمانی بین درخواست‌ها را افزایش دهید

### لاگ‌های سیستم
```bash
# مشاهده لاگ‌های اپ
tail -f logs/{{APP_NAME}}.log

# مشاهده لاگ‌های خطا
grep "ERROR" logs/{{APP_NAME}}.log
```

## مشارکت در توسعه

### قوانین کدنویسی
- کد باید PEP 8 compliant باشد
- تمام functions باید docstring داشته باشند
- تست‌ها باید برای کد جدید نوشته شوند

### فرآیند Review
1. ایجاد feature branch
2. نوشتن کد و تست‌ها
3. اجرای لینت و تست‌ها
4. ایجاد Pull Request
5. Code Review
6. Merge به main branch

## مجوز و قوانین

- این کد تحت مجوز اختصاصی HELSSA است
- تغییرات باید طبق دستورالعمل‌های مصوب باشد
- هیچ عمل سلیقه‌ای مجاز نیست

## پشتیبانی

- **مستندات**: [HELSSA Documentation]({{DOCS_URL}})
- **تیم توسعه**: {{SUPPORT_CONTACT}}
- **ایشوها**: [GitHub Issues]({{GITHUB_ISSUES_URL}})

---

**نسخه**: {{VERSION}}  
**آخرین به‌روزرسانی**: {{LAST_UPDATE}}  
**توسعه‌دهنده**: {{DEVELOPER_NAME}}