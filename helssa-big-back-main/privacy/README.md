# ماژول Privacy - مدیریت حریم خصوصی

## توضیحات

ماژول Privacy مسئول پیاده‌سازی سیستم‌های حفاظت از حریم خصوصی در پلتفرم هلسا است. این ماژول شامل سرویس‌های پنهان‌سازی داده‌های حساس (PII/PHI)، مدیریت رضایت‌های کاربر و نظارت بر دسترسی‌ها می‌باشد.

## ویژگی‌ها

### 🔒 پنهان‌سازی داده‌های حساس
- شناسایی و پنهان‌سازی خودکار اطلاعات شخصی (PII)
- پنهان‌سازی اطلاعات سلامت محافظت‌شده (PHI)
- پشتیبانی از الگوهای سفارشی regex
- سطوح مختلف پنهان‌سازی (none, standard, strict)

### 👤 مدیریت رضایت‌های کاربر
- ثبت و مدیریت رضایت‌های کاربر
- پشتیبانی از انواع مختلف رضایت
- امکان پس‌گیری رضایت
- مدیریت انقضای رضایت‌ها

### 📊 طبقه‌بندی و مدیریت داده‌ها
- طبقه‌بندی داده‌ها بر اساس حساسیت
- تعریف سیاست‌های نگهداری
- مدیریت فیلدهای داده

### 📈 نظارت و گزارش‌گیری
- لاگ تمام دسترسی‌ها به داده‌های حساس
- آمار و گزارش‌های حریم خصوصی
- تحلیل ریسک‌های حریم خصوصی

## نصب و راه‌اندازی

### 1. اضافه کردن به INSTALLED_APPS

```python
INSTALLED_APPS = [
    # ...
    'privacy',
    'rest_framework',
    # ...
]
```

### 2. Migration
```bash
python manage.py makemigrations privacy
python manage.py migrate
```

### 3. URL Configuration
```python
# در helssa/urls.py
urlpatterns = [
    # ...
    path('api/privacy/', include('privacy.urls')),
    # ...
]
```

## استفاده

### پنهان‌سازی متن
```python
from privacy.services.redactor import default_redactor

text = "شماره تماس من 09123456789 است"
redacted_text, matches = default_redactor.redact_text(text)
print(redacted_text)  # "شماره تماس من [شماره تلفن حذف شده] است"
```

### مدیریت رضایت
```python
from privacy.services.consent_manager import default_consent_manager

# اعطای رضایت
consent = default_consent_manager.grant_consent(
    user_id="user-uuid",
    consent_type="data_processing",
    purpose="پردازش اطلاعات برای ارائه خدمات",
    data_categories=["pii-category-uuid"],
    legal_basis="رضایت آگاهانه کاربر"
)

# بررسی رضایت
has_consent = default_consent_manager.check_consent(
    user_id="user-uuid",
    consent_type="data_processing"
)
```

### تحلیل ریسک حریم خصوصی
```python
from privacy.cores.text_processor import privacy_text_processor

analysis = privacy_text_processor.analyze_text_privacy_risks(
    text="متن حاوی اطلاعات حساس",
    include_suggestions=True
)
print(f"امتیاز ریسک: {analysis['risk_score']}")
```

## API Endpoints

### پنهان‌سازی متن
```
POST /api/privacy/redact-text/
```

### تحلیل ریسک
```
POST /api/privacy/analyze-risks/
```

### مدیریت رضایت‌ها
```
GET /api/privacy/consents/
POST /api/privacy/consents/grant_consent/
POST /api/privacy/consents/withdraw_consent/
```

### مدیریت طبقه‌بندی‌ها
```
GET /api/privacy/classifications/
POST /api/privacy/classifications/
```

### مدیریت فیلدهای داده
```
GET /api/privacy/fields/
POST /api/privacy/fields/
```

### لاگ‌های دسترسی
```
GET /api/privacy/access-logs/
```

## مدل‌های داده

### DataClassification
طبقه‌بندی انواع داده‌ها بر اساس حساسیت

### DataField
تعریف فیلدهای داده‌ای که نیاز به حفاظت دارند

### ConsentRecord
رکوردهای رضایت کاربران

### DataAccessLog
لاگ دسترسی به داده‌های حساس

### DataRetentionPolicy
سیاست‌های نگهداری داده‌ها

## تنظیمات

```python
# در settings.py

# مدت زمان کش الگوهای پنهان‌سازی (ثانیه)
PRIVACY_CACHE_TIMEOUT = 3600

# فعال‌سازی لاگ‌گیری پیش‌فرض
PRIVACY_DEFAULT_LOGGING = True

# سطح پنهان‌سازی پیش‌فرض
PRIVACY_DEFAULT_REDACTION_LEVEL = 'standard'
```

## امنیت

### نکات مهم امنیتی:
- همه دسترسی‌ها به داده‌های حساس لاگ می‌شوند
- فقط کاربران مجاز می‌توانند به API های مدیریتی دسترسی داشته باشند
- رضایت‌های کاربر قبل از هر عملیات بررسی می‌شوند
- الگوهای پنهان‌سازی در کش ذخیره می‌شوند

### کنترل دسترسی:
- API های عمومی: نیاز به احراز هویت
- API های مدیریتی: نیاز به دسترسی admin
- لاگ‌های دسترسی: کاربران فقط لاگ‌های خود را می‌بینند

## تست

```bash
# اجرای تمام تست‌ها
python manage.py test privacy

# اجرای تست‌های خاص
python manage.py test privacy.tests.PIIRedactorTestCase
```

## نمونه‌های استفاده

### پنهان‌سازی پیشرفته
```python
from privacy.services.redactor import PHIRedactor

phi_redactor = PHIRedactor()
result = phi_redactor.redact_medical_text(
    text="بیمار با شماره پرونده MR123456 مراجعه کرد",
    patient_id="patient-uuid",
    doctor_id="doctor-uuid"
)
```

### تحلیل کامل حریم خصوصی
```python
from privacy.cores.text_processor import privacy_text_processor

result = privacy_text_processor.process_medical_text(
    text="متن پزشکی",
    context={"encounter_id": "encounter-uuid"},
    redaction_level="strict"
)

print(f"امتیاز حریم خصوصی: {result.privacy_score}")
print(f"حاوی داده حساس: {result.contains_sensitive_data}")
```

## مجوز

این کد تحت مجوز اختصاصی هلسا/مدوگرام قرار دارد.