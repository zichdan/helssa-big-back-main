# دستورالعمل‌های ایجنت‌های اپلیکیشن

## نمای کلی

این سند دستورالعمل‌های جامع برای ایجنت‌هایی است که اپلیکیشن‌های مختلف پلتفرم هلسا را بر اساس معماری چهار هسته‌ای می‌سازند.

## اپلیکیشن‌های مورد نیاز

بر اساس تحلیل پروژه، اپلیکیشن‌های زیر باید توسط ایجنت‌های فرعی ساخته شوند:

### 1. **patient_chatbot** - چت‌بات بیمار

- **هدف**: سیستم چت هوشمند برای بیماران
- **هسته‌های فعال**: API Ingress + Text Processing + Orchestration
- **اولویت**: بالا (استفاده روزانه بالا)

### 2. **doctor_chatbot** - چت‌بات پزشک  

- **هدف**: ابزار کمک تشخیص برای پزشکان
- **هسته‌های فعال**: API Ingress + Text Processing + Orchestration
- **اولویت**: بالا (ابزار اصلی پزشکان)

### 3. **soapify_v2** - تولید گزارش‌های SOAP

- **هدف**: تولید خودکار گزارش‌های پزشکی استاندارد
- **هسته‌های فعال**: همه چهار هسته
- **اولویت**: بالا (ضروری برای پزشکان)

### 4. **visit_management** - مدیریت ویزیت‌ها

- **هدف**: سیستم رزرو و مدیریت ویزیت‌های آنلاین
- **هسته‌های فعال**: API Ingress + Orchestration
- **اولویت**: متوسط

### 5. **prescription_system** - سیستم نسخه‌نویسی

- **هدف**: ایجاد و مدیریت نسخه‌های دیجیتال
- **هسته‌های فعال**: API Ingress + Text Processing + Orchestration
- **اولویت**: بالا

### 6. **telemedicine_core** - هسته طب از راه دور

- **هدف**: ارتباط ویدئویی و صوتی بین بیمار و پزشک
- **هسته‌های فعال**: API Ingress + Speech Processing + Orchestration
- **اولویت**: متوسط

### 7. **patient_records** - مدیریت پرونده بیمار

- **هدف**: سیستم جامع پرونده‌های پزشکی
- **هسته‌های فعال**: API Ingress + Orchestration
- **اولویت**: بالا

### 8. **appointment_scheduler** - زمان‌بندی قرارها

- **هدف**: سیستم رزرو نوبت پیشرفته
- **هسته‌های فعال**: API Ingress + Orchestration  
- **اولویت**: متوسط

## الگوی کلی ایجاد اپلیکیشن

هر ایجنت باید مراحل زیر را دنبال کند:

### مرحله 1: آماده‌سازی

1. خواندن کامل CORE_ARCHITECTURE.md
2. خواندن کامل SECURITY_POLICIES.md  
3. بررسی الگوهای موجود در کد پایه
4. ایجاد پوشه اپ در `agent/<app_name>/`

### مرحله 2: طراحی

1. تکمیل PLAN.md بر اساس template
2. تعریف API endpoints
3. طراحی مدل‌های داده
4. تعیین dependencies

### مرحله 3: پیاده‌سازی

1. ایجاد Django app
2. نوشتن models و migrations
3. پیاده‌سازی چهار هسته
4. ایجاد serializers و views
5. پیکربندی URLs

### مرحله 4: یکپارچه‌سازی

1. ادغام با unified_auth
2. ادغام با unified_billing
3. ادغام با unified_access
4. پیکربندی Kavenegar

### مرحله 5: تست و مستندسازی

1. نوشتن تست‌ها (بدون اجرا)
2. تکمیل README.md
3. به‌روزرسانی PROGRESS.json
4. ثبت در LOG.md

## ساختار استاندارد اپلیکیشن

```bash
agent/<app_name>/
├── PLAN.md                    # برنامه تفصیلی
├── CHECKLIST.json             # چک‌لیست اجرا
├── PROGRESS.json              # گزارش پیشرفت
├── LOG.md                     # لاگ تصمیم‌ها
├── README.md                  # مستندات اپ
├── charts/
│   └── progress_doughnut.svg  # نمودار پیشرفت
├── app_code/                  # کد اپلیکیشن
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py
│   ├── admin.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── permissions.py
│   ├── cores/                 # چهار هسته
│   │   ├── __init__.py
│   │   ├── api_ingress.py
│   │   ├── text_processor.py
│   │   ├── speech_processor.py
│   │   └── orchestrator.py
│   ├── migrations/
│   │   └── __init__.py
│   └── tests/                 # تست‌ها (نوشته شده، اجرا نشده)
│       ├── __init__.py
│       ├── test_models.py
│       ├── test_views.py
│       ├── test_serializers.py
│       └── test_integration.py
├── deployment/
│   ├── settings_additions.py  # تنظیمات اضافی Django
│   ├── urls_additions.py      # اضافات URL
│   └── requirements_additions.txt
└── docs/
    ├── api_spec.yaml          # OpenAPI spec
    ├── user_manual.md         # راهنمای کاربر
    └── admin_guide.md         # راهنمای مدیر
```

## الگوهای اجباری

### 1. Import Pattern

```python
# الگوی صحیح imports
from django.contrib.auth import get_user_model
from rest_framework import status, serializers, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

# Unified integrations
from unified_auth.models import UnifiedUser
from unified_billing.services import UnifiedBillingService
from unified_access.decorators import require_patient_access

User = get_user_model()
```

### 2. View Pattern

```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def standard_endpoint(request):
    """
    Standard API endpoint pattern
    """
    try:
        # 1. Validation
        serializer = RequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid input', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 2. Permission check
        if not request.user.has_permission_for_action():
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 3. Process through orchestrator
        orchestrator = CentralOrchestrator()
        result = orchestrator.execute_workflow(
            'workflow_name',
            serializer.validated_data,
            request.user
        )
        
        # 4. Return response
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Endpoint error: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

### 3. Model Pattern

```python
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class StandardModel(models.Model):
    """
    الگوی استاندارد برای تمام مدل‌ها
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='%(class)s_created'
    )
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
```

## پیکربندی اجباری

### 1. Settings Additions

هر اپ باید این تنظیمات را اضافه کند:

```python
# در فایل deployment/settings_additions.py
INSTALLED_APPS += [
    '<app_name>.apps.<AppName>Config',
]

# Rate limiting برای اپ
RATE_LIMIT_<APP_NAME> = {
    'api_calls': '100/minute',
    'ai_requests': '20/minute',
}

# Logging configuration
LOGGING['loggers']['<app_name>'] = {
    'handlers': ['file', 'console'],
    'level': 'INFO',
    'propagate': False,
}
```

### 2. URLs Addition

```python
# در فایل deployment/urls_additions.py
urlpatterns += [
    path('api/<app_name>/', include('<app_name>.urls')),
]
```

## چک‌لیست اجرای ایجنت

هر ایجنت باید این موارد را تأیید کند:

### ✅ اجباری برای همه

- [ ] PLAN.md کامل شده
- [ ] معماری چهار هسته‌ای رعایت شده
- [ ] سیاست‌های امنیتی پیاده‌سازی شده
- [ ] unified_auth integration انجام شده
- [ ] OTP/Kavenegar پیکربندی شده
- [ ] تفکیک patient/doctor رعایت شده
- [ ] تست‌ها نوشته شده (بدون اجرا)
- [ ] README.md تکمیل شده
- [ ] PROGRESS.json به‌روزرسانی شده
- [ ] LOG.md ثبت تغییرات شده

### ✅ شرطی بر اساس نیاز

- [ ] unified_ai integration (اگر از AI استفاده می‌کند)
- [ ] Speech processing (اگر صوت دارد)
- [ ] unified_billing integration (اگر پولی است)
- [ ] File upload handling (اگر فایل می‌گیرد)

## قوانین مهم اجرا

### 🚫 ممنوعیت‌ها

1. **هیچ عمل سلیقه‌ای**: فقط طبق دستورالعمل
2. **تغییر معماری**: چهار هسته‌ای اجباری
3. **ایجاد user model جدید**: فقط UnifiedUser
4. **Raw SQL**: فقط Django ORM  
5. **Hard-coded values**: همه چیز configurable

### ✅ الزامات

1. **ثبت همه تغییرات**: در LOG.md
2. **پیروی از الگوها**: در تمام کدها
3. **Error handling**: استاندارد و کامل
4. **Security first**: امنیت در اولویت
5. **Documentation**: کامل و دقیق

## نحوه تعامل ایجنت‌ها

### اولویت‌بندی

1. **patient_chatbot** - شروع فوری
2. **doctor_chatbot** - همزمان با patient
3. **soapify_v2** - پس از chatbots
4. **prescription_system** - پس از soapify
5. سایر اپ‌ها بر اساس نیاز

### هماهنگی

- هر ایجنت مستقل کار می‌کند
- تداخل در کدها ممنوع
- استفاده از shared utilities مجاز
- هماهنگی از طریق Mother Agent

## خروجی نهایی

هر ایجنت باید این خروجی‌ها را تحویل دهد:

1. **کد کامل** در `agent/<app_name>/app_code/`
2. **مستندات کامل** شامل README و API spec
3. **تست‌های نوشته شده** (بدون اجرا)
4. **فایل‌های deployment** برای integration
5. **گزارش پیشرفت** با نمودار SVG
6. **لاگ تصمیم‌ها** کامل و مستند

## QA نهایی

پس از تکمیل همه اپ‌ها، ایجنت QA:

1. بررسی یکنواختی کدها
2. تأیید رعایت سیاست‌های امنیتی  
3. تست integration بین اپ‌ها
4. تهیه گزارش نهایی
5. آماده‌سازی برای انتقال به helssa-big_back

---

**نکته**: این دستورالعمل الزامی و بدون استثناء است. هر ایجنت باید دقیقاً طبق این راهنما عمل کند.
