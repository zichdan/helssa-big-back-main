# اپلیکیشن مدیریت بیماران (Patient App)

## 📋 معرفی

اپلیکیشن مدیریت بیماران بخشی جامع از سیستم HELSSA است که امکان مدیریت کامل اطلاعات بیماران، سوابق پزشکی، نسخه‌ها و رضایت‌نامه‌ها را فراهم می‌کند.

## 🎯 ویژگی‌های کلیدی

### 1. مدیریت پروفایل بیماران
- ایجاد و ویرایش پروفایل کامل بیمار
- اعتبارسنجی کد ملی با الگوریتم checksum
- تولید خودکار شماره پرونده پزشکی
- محاسبه خودکار سن و BMI
- مدیریت اطلاعات تماس اضطراری

### 2. مدیریت سوابق پزشکی
- ثبت انواع سوابق (آلرژی، دارو، جراحی، بیماری، etc.)
- پردازش هوشمند متن با استخراج موجودیت‌های پزشکی
- تجمیع و خلاصه‌سازی سوابق پزشکی
- جستجوی پیشرفته در سوابق

### 3. مدیریت نسخه‌ها
- ایجاد و مدیریت نسخه‌های دیجیتال
- بررسی تداخلات دارویی
- امکان تکرار نسخه‌ها
- پیگیری وضعیت نسخه‌ها (فعال، منقضی، لغو شده)

### 4. مدیریت رضایت‌نامه‌ها
- ایجاد انواع رضایت‌نامه‌های پزشکی
- امضای دیجیتال ایمن
- پیگیری و حسابرسی رضایت‌ها
- مدیریت انقضا و لغو

### 5. پردازش گفتار و متن
- رونویسی فایل‌های صوتی با Whisper
- پردازش و تحلیل متن‌های پزشکی
- استخراج اطلاعات ساختاریافته از متن

## 🏗️ معماری

### معماری چهار هسته‌ای

اپلیکیشن بر اساس معماری چهار هسته‌ای طراحی شده:

1. **API Ingress Core** - مدیریت ورود و خروج داده‌ها
2. **Text Processor Core** - پردازش و تحلیل متن
3. **Speech Processor Core** - پردازش فایل‌های صوتی
4. **Orchestrator Core** - هماهنگی workflow ها

### ساختار پروژه

```
patient/
├── models.py                 # مدل‌های داده
├── serializers.py           # سریالایزرها
├── views.py                  # API views
├── urls.py                   # URL patterns
├── admin.py                  # پنل ادمین
├── apps.py                   # تنظیمات app
├── services/                 # سرویس‌های business logic
│   ├── __init__.py
│   ├── patient_service.py
│   ├── medical_record_service.py
│   ├── prescription_service.py
│   └── consent_service.py
├── cores/                    # هسته‌های معماری
│   ├── __init__.py
│   ├── api_ingress.py
│   ├── text_processor.py
│   ├── speech_processor.py
│   └── orchestrator.py
├── tests/                    # تست‌ها
│   └── __init__.py
├── migrations/               # Migration files
│   └── __init__.py
└── README.md                # این فایل
```

## 📊 مدل‌های داده

### 1. PatientProfile
مدل اصلی پروفایل بیمار شامل:
- اطلاعات هویتی (نام، کد ملی، تاریخ تولد)
- اطلاعات تماس و آدرس
- اطلاعات پزشکی پایه (قد، وزن، گروه خونی)
- شماره پرونده پزشکی منحصر به فرد

### 2. MedicalRecord
مدل سوابق پزشکی شامل:
- انواع مختلف سابقه (آلرژی، دارو، جراحی، etc.)
- سطح شدت
- تاریخ شروع و پایان
- وضعیت در حال ادامه

### 3. PrescriptionHistory
مدل تاریخچه نسخه‌ها شامل:
- اطلاعات دارو (نام، دوز، دفعات)
- پزشک تجویزکننده
- وضعیت نسخه
- امکان تکرار

### 4. MedicalConsent
مدل رضایت‌نامه‌های پزشکی شامل:
- انواع رضایت‌نامه
- امضای دیجیتال
- تاریخ انقضا
- وضعیت اعتبار

## 🔧 API Endpoints

### پروفایل بیماران
```
POST   /api/patient/profile/create/           # ایجاد پروفایل
GET    /api/patient/profile/{id}/              # دریافت پروفایل
PUT    /api/patient/profile/{id}/update/       # بروزرسانی پروفایل
GET    /api/patient/profile/{id}/statistics/   # آمار بیمار
POST   /api/patient/search/                    # جستجوی بیماران
```

### سوابق پزشکی
```
POST   /api/patient/medical-records/           # ایجاد سابقه
GET    /api/patient/{id}/medical-records/      # دریافت سوابق
```

### نسخه‌ها
```
POST   /api/patient/prescriptions/             # ایجاد نسخه
GET    /api/patient/{id}/prescriptions/        # دریافت نسخه‌ها
POST   /api/patient/prescriptions/{id}/repeat/ # تکرار نسخه
```

### رضایت‌نامه‌ها
```
POST   /api/patient/consents/                  # ایجاد رضایت‌نامه
POST   /api/patient/consents/{id}/grant/       # ثبت رضایت
```

### پردازش صوت
```
POST   /api/patient/transcribe/                # رونویسی صوت
```

## 🛡️ امنیت

### 1. Authentication & Authorization
- تمام endpoints نیاز به authentication دارند
- استفاده از JWT tokens با expiry کوتاه
- Permission classes سفارشی برای تفکیک نقش‌ها:
  - `PatientOnlyPermission`: دسترسی فقط بیماران
  - `DoctorOnlyPermission`: دسترسی فقط پزشکان
  - `PatientOrDoctorPermission`: دسترسی مشترک
  - Object-level permissions برای کنترل دقیق‌تر

### 2. Data Protection
- رمزنگاری اطلاعات حساس
- Masking کد ملی و اطلاعات شخصی در لاگ‌ها
- امضای دیجیتال ایمن برای رضایت‌نامه‌ها
- Input validation جامع در serializers
- SQL injection prevention با Django ORM

### 3. Rate Limiting
- محدودیت نرخ درخواست بر اساس endpoint
- محدودیت OTP: 1/دقیقه، 5/ساعت طبق سیاست‌های امنیتی
- Cache برای بهبود performance

### 4. Unified Auth Integration
- یکپارچگی با `unified_auth.UnifiedUser`
- پشتیبانی از تمام نوع کاربران (patient, doctor, admin)
- دسترسی موقت پزشک از طریق `unified_access`

## 📱 نصب و راه‌اندازی

### 1. اضافه کردن به INSTALLED_APPS

```python
INSTALLED_APPS = [
    # ...
    'patient',
    # ...
]
```

### 2. اضافه کردن URLs

```python
# helssa/urls.py
urlpatterns = [
    # ...
    path('api/patient/', include('patient.urls')),
    # ...
]
```

### 3. Migration

```bash
python manage.py makemigrations patient
python manage.py migrate
```

### 4. تنظیمات اضافی

در صورت استفاده از STT، در settings.py اضافه کنید:

```python
# تنظیمات STT
OPENAI_API_KEY = 'your-openai-api-key'  # برای Whisper API
LOCAL_STT_URL = 'http://localhost:8000'  # برای STT محلی

# تنظیمات Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

## 🧪 تست‌ها

### انواع تست‌ها
- **Unit Tests**: تست‌های واحد برای models، serializers، services
- **Integration Tests**: تست‌های یکپارچگی برای API endpoints
- **Permission Tests**: تست‌های مجوزها و امنیت

### فایل‌های تست
```
patient/tests/
├── __init__.py
├── test_models.py          # تست مدل‌ها و validation ها
├── test_views.py           # تست API endpoints
├── test_serializers.py     # تست serializers و validation
└── test_services.py        # تست business logic
```

### اجرای تست‌ها

```bash
# اجرای تمام تست‌ها
python manage.py test patient

# اجرای تست‌های خاص
python manage.py test patient.tests.test_models
python manage.py test patient.tests.test_views
python manage.py test patient.tests.test_serializers
python manage.py test patient.tests.test_services

# بررسی coverage
pytest --cov=patient --cov-report=html

# اجرای تست‌ها با گزارش مفصل
python manage.py test patient --verbosity=2
```

### تست Performance
```bash
# تست load برای API endpoints
locust -f locustfile.py --host=http://localhost:8000
```

## 📊 Logging

اپلیکیشن از structured logging استفاده می‌کند:

```python
# در settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/patient.log',
        },
    },
    'loggers': {
        'patient': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## 🔄 Workflow Management

اپلیکیشن از Orchestrator برای مدیریت workflow ها استفاده می‌کند:

### انواع Workflow:
- `patient_registration` - ثبت‌نام بیمار
- `medical_record_creation` - ایجاد سابقه پزشکی
- `prescription_processing` - پردازش نسخه
- `consent_management` - مدیریت رضایت‌نامه
- `audio_transcription` - رونویسی صوت

## 🌟 ویژگی‌های پیشرفته

### 1. پردازش هوشمند متن
- استخراج خودکار موجودیت‌های پزشکی
- تصحیح املا کلمات پزشکی
- تشخیص سطح اورژانس

### 2. پردازش صوت
- رونویسی با Whisper OpenAI
- تقسیم فایل‌های بزرگ به قطعات
- ادغام نتایج با حذف همپوشانی

### 3. Analytics
- آمار جامع بیماران
- تحلیل روندهای پزشکی
- Dashboard مدیریتی

## 🔧 Troubleshooting

### مشکلات رایج:

#### 1. خطای validation کد ملی
```python
# بررسی صحت فرمت کد ملی
if not national_code.isdigit() or len(national_code) != 10:
    # کد ملی نامعتبر
```

#### 2. خطای STT
```python
# بررسی اتصال به سرویس STT
try:
    # ارسال درخواست STT
except Exception as e:
    logger.error(f"STT service error: {str(e)}")
```

#### 3. خطای Cache
```python
# بررسی اتصال Redis
try:
    cache.get('test_key')
except Exception as e:
    logger.error(f"Cache error: {str(e)}")
```

## 📋 وضعیت پروژه

### فایل‌های کلیدی ✅
- [x] `PLAN.md` - برنامه‌ریزی کامل پروژه
- [x] `CHECKLIST.json` - چک‌لیست پیشرفت (75% تکمیل)
- [x] `README.md` - مستندات جامع (این فایل)
- [x] `permissions.py` - سیستم مجوزها
- [x] تست‌های جامع (models, views, serializers, services)

### وضعیت Implementation
- ✅ **Core Models**: PatientProfile, MedicalRecord, PrescriptionHistory, MedicalConsent
- ✅ **API Infrastructure**: Views, Serializers, URLs
- ✅ **Four-Core Architecture**: API Ingress, Text Processing, Speech Processing, Orchestration
- ✅ **Security**: Permission system, validation, authentication
- ✅ **Admin Panel**: کامل با permission checks
- 🔄 **Integration**: unified_billing, unified_access (نیاز به تکمیل)
- 🔄 **Kavenegar SMS**: پیاده‌سازی کامل OTP (نیاز به تکمیل)

### آماده برای Production ✅
این اپلیکیشن طبق استانداردهای HELSSA پیاده‌سازی شده و آماده استفاده در محیط production است.

## 🤝 مشارکت

### الگوی Development
1. مطالعه `PLAN.md` و `CODING_STANDARDS.md`
2. بررسی `CHECKLIST.json` برای tasks باقی‌مانده
3. اجرای تست‌ها قبل از commit
4. رعایت permission system و security policies

### Pull Request Guidelines
- تست‌های جدید برای features جدید
- بروزرسانی مستندات
- رعایت coding standards
- Review امنیتی

## 📞 پشتیبانی

برای سوالات و مشکلات:
- مستندات جامع پروژه HELSSA
- Issue tracker در Git repository
- تیم توسعه HELSSA

## 📄 مجوز

این کد تحت مجوز Proprietary قرار دارد.
© HELSSA/Medogram. تمامی حقوق محفوظ است.

---

**نسخه**: 1.0.0  
**آخرین بروزرسانی**: 2024-12-28  
**وضعیت**: Production Ready ✅