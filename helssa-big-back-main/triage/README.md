# اپلیکیشن تریاژ پزشکی - Helssa

## 📋 مقدمه

اپلیکیشن تریاژ پزشکی بخشی از پلتفرم هلسا است که برای ارزیابی اولیه علائم بیماران و تشخیص افتراقی طراحی شده است. این سیستم با استفاده از الگوریتم‌های هوشمند، سطح اورژانس بیماران را تعیین کرده و اقدامات مناسب را پیشنهاد می‌دهد.

## 🎯 ویژگی‌های کلیدی

### 🔍 تحلیل علائم
- شناسایی خودکار علائم از متن
- محاسبه سطح اورژانس بر اساس علائم
- تشخیص افتراقی بر اساس پایگاه دانش پزشکی
- شناسایی علائم خطر (Red Flags)

### 📊 مدیریت جلسات تریاژ
- ایجاد و مدیریت جلسات تریاژ
- ثبت علائم با جزئیات کامل
- پیگیری وضعیت بیماران
- تولید گزارش‌های جامع

### 🧠 هوش مصنوعی
- تحلیل هوشمند علائم
- محاسبه احتمال تشخیص‌های مختلف
- اعمال قوانین تریاژ خودکار
- ارائه توصیه‌های مبتنی بر شواهد

### 📈 آمار و گزارش‌دهی
- آمار عملکرد سیستم تریاژ
- گزارش‌های تحلیلی
- نمودارهای تعاملی
- صادرات داده‌ها

## 🏗️ ساختار پروژه

```
triage/
├── models.py              # مدل‌های دیتابیس
├── serializers.py         # سریالایزرهای API
├── views.py              # ویوها و APIها
├── services.py           # سرویس‌های تحلیل
├── admin.py              # پنل مدیریت
├── urls.py               # مسیرهای URL
├── tests.py              # تست‌ها
├── apps.py               # تنظیمات اپ
├── settings_sample.py    # نمونه تنظیمات
└── README.md             # مستندات
```

## 📦 مدل‌های داده

### SymptomCategory
دسته‌بندی علائم پزشکی (تنفسی، قلبی، عصبی و...)

### Symptom  
علائم پزشکی با جزئیات کامل شامل سطح اورژانس

### DifferentialDiagnosis
تشخیص‌های افتراقی با کدهای ICD-10

### TriageSession
جلسات تریاژ بیماران با تمام اطلاعات

### TriageRule
قوانین خودکار تریاژ قابل تنظیم

## 🔌 API Endpoints

### علائم
```
GET /api/symptoms/                    # لیست علائم
GET /api/symptoms/{id}/               # جزئیات علامت
GET /api/symptoms/{id}/related/       # علائم مرتبط
GET /api/search-symptoms/?q=تب        # جستجوی علائم
```

### جلسات تریاژ
```
GET /api/sessions/                    # لیست جلسات
POST /api/sessions/                   # ایجاد جلسه جدید
GET /api/sessions/{id}/               # جزئیات جلسه
PUT /api/sessions/{id}/               # به‌روزرسانی جلسه
POST /api/sessions/{id}/add-symptom/  # افزودن علامت
POST /api/sessions/{id}/complete/     # تکمیل تریاژ
GET /api/sessions/{id}/analysis/      # تحلیل جلسه
```

### تحلیل
```
POST /api/analyze-symptoms/           # تحلیل مستقل علائم
GET /api/statistics/                  # آمار تریاژ
GET /api/emergency-symptoms/          # علائم اورژانسی
GET /api/common-diagnoses/            # تشخیص‌های رایج
```

## 🔧 نصب و راه‌اندازی

### 1. افزودن به INSTALLED_APPS
```python
INSTALLED_APPS = [
    # ...
    'triage',
    # ...
]
```

### 2. افزودن URLها
```python
# urls.py اصلی پروژه
urlpatterns = [
    # ...
    path('triage/', include('triage.urls')),
    # ...
]
```

### 3. اجرای Migration
```bash
python manage.py makemigrations triage
python manage.py migrate
```

### 4. ایجاد دیتای اولیه
```python
# در Django shell
from triage.models import SymptomCategory, Symptom

# ایجاد دسته‌بندی‌ها
respiratory = SymptomCategory.objects.create(
    name='علائم تنفسی',
    name_en='Respiratory Symptoms',
    priority_level=8
)

# ایجاد علائم
Symptom.objects.create(
    name='تنگی نفس',
    name_en='Shortness of breath',
    category=respiratory,
    urgency_score=7,
    severity_levels=['خفیف', 'متوسط', 'شدید'],
    common_locations=['قفسه سینه', 'گلو']
)
```

## 📝 استفاده

### ایجاد جلسه تریاژ
```python
# POST /api/sessions/
{
    "chief_complaint": "تنگی نفس و سرفه",
    "reported_symptoms": ["تنگی نفس", "سرفه خشک", "تب"]
}
```

### افزودن علامت به جلسه
```python
# POST /api/sessions/{id}/add-symptom/
{
    "symptom_id": "uuid-here",
    "severity": 7,
    "duration_hours": 24,
    "location": "قفسه سینه",
    "additional_details": "درد با تنفس عمیق بدتر می‌شود"
}
```

### تحلیل مستقل علائم
```python
# POST /api/analyze-symptoms/
{
    "symptoms": ["تب", "سردرد", "گلودرد"],
    "severity_scores": {
        "تب": 8,
        "سردرد": 6,
        "گلودرد": 4
    },
    "patient_age": 35,
    "patient_gender": "male"
}
```

## ⚙️ تنظیمات

تنظیمات مربوط به اپ تریاژ را در فایل `settings_sample.py` مشاهده کنید و آن‌ها را به settings اصلی پروژه اضافه کنید.

### متغیرهای محیطی
```bash
TRIAGE_AI_API_KEY=your_ai_api_key
TRIAGE_ENABLE_ML=True
TRIAGE_DEBUG_MODE=False
TRIAGE_CACHE_ENABLED=True
```

## 🧪 تست‌ها

```bash
# اجرای تمام تست‌ها
python manage.py test triage

# اجرای تست‌های خاص
python manage.py test triage.tests.TriageSessionModelTest
python manage.py test triage.tests.TriageAPITest

# تست با پوشش کد
coverage run --source='.' manage.py test triage
coverage report
```

## 📊 مانیتورینگ و لاگ‌ها

سیستم تریاژ رویدادهای مختلفی را لاگ می‌کند:

- ایجاد و تکمیل جلسات
- نتایج تحلیل علائم  
- اعمال قوانین تریاژ
- تشخیص علائم خطر
- خطاهای سیستم

## 🔒 امنیت

- احراز هویت کاربران الزامی
- Rate limiting برای APIها
- اعتبارسنجی دقیق ورودی‌ها
- لاگ کامل عملیات
- رمزنگاری اطلاعات حساس

## 🚀 بهینه‌سازی عملکرد

- کش کردن نتایج جستجو
- Index گذاری مناسب دیتابیس
- Pagination برای لیست‌ها
- Lazy loading برای روابط
- Background tasks برای تحلیل‌های سنگین

## 🤝 مشارکت

برای مشارکت در توسعه:

1. Fork کردن پروژه
2. ایجاد branch جدید
3. اعمال تغییرات
4. نوشتن تست
5. ارسال Pull Request

## 📄 مجوز

این پروژه تحت مجوز Proprietary شرکت هلسا/مدوگرام است.

---

**نکته مهم:** این اپ بخشی از سیستم جامع هلسا بوده و باید همراه با سایر اپ‌ها استفاده شود.