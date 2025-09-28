# {{APP_NAME}} - برنامه پیاده‌سازی

## هدف و دامنه

### هدف کلی
{{APP_OBJECTIVE}}

### دامنه عملکرد
{{APP_SCOPE}}

### مصرف‌کنندگان هدف
- **بیماران**: {{PATIENT_FEATURES}}
- **پزشکان**: {{DOCTOR_FEATURES}}

## معماری کلی

### ادغام با هسته‌های مرکزی

#### 1. هسته‌ی ورودی API (API Ingress Core)
- **Endpoints**: {{API_ENDPOINTS}}
- **Authentication**: Unified Auth با JWT
- **Validation**: {{VALIDATION_RULES}}
- **Rate Limiting**: {{RATE_LIMITS}}

#### 2. هسته‌ی پردازش متن (Text Processing Core)
{{#if USES_TEXT_PROCESSING}}
- **AI Integration**: {{AI_FEATURES}}
- **NLP Tasks**: {{NLP_TASKS}}
- **Language Support**: فارسی، انگلیسی
{{else}}
- این اپ از پردازش متن استفاده نمی‌کند
{{/if}}

#### 3. هسته‌ی پردازش صوت (Speech Processing Core)
{{#if USES_SPEECH_PROCESSING}}
- **STT Integration**: {{STT_FEATURES}}
- **Audio Processing**: {{AUDIO_FEATURES}}
- **File Support**: {{AUDIO_FORMATS}}
{{else}}
- این اپ از پردازش صوت استفاده نمی‌کند
{{/if}}

#### 4. هسته‌ی ارکستراسیون مرکزی (Central Orchestration Core)
- **Workflows**: {{WORKFLOWS}}
- **Business Logic**: {{BUSINESS_LOGIC}}
- **Background Tasks**: {{CELERY_TASKS}}

## API سطح بالا

### Endpoints بیمار (Patient)
```
{{PATIENT_ENDPOINTS}}
```

### Endpoints پزشک (Doctor)
```
{{DOCTOR_ENDPOINTS}}
```

### Endpoints مشترک
```
{{SHARED_ENDPOINTS}}
```

## وابستگی‌ها

### هسته‌های داخلی
- `unified_auth`: احراز هویت و مدیریت کاربران
- `unified_billing`: پرداخت و اشتراک
- `unified_access`: دسترسی موقت پزشک به بیمار
{{#if USES_AI}}
- `unified_ai`: سرویس‌های هوش مصنوعی
{{/if}}

### کتابخانه‌های خارجی
{{EXTERNAL_DEPENDENCIES}}

## مدل‌های داده

### مدل‌های اصلی
{{DATA_MODELS}}

### روابط با سیستم‌های موجود
{{MODEL_RELATIONSHIPS}}

## امنیت و دسترسی

### احراز هویت
- **روش ورود**: OTP از طریق Kavenegar
- **نگهداری session**: JWT tokens
- **انقضای token**: Access 5 دقیقه، Refresh 7 روز

### سطوح دسترسی
- **بیمار**: {{PATIENT_PERMISSIONS}}
- **پزشک**: {{DOCTOR_PERMISSIONS}}
- **مدیر**: {{ADMIN_PERMISSIONS}}

### حفاظت از داده‌ها
- **رمزنگاری**: End-to-End برای داده‌های حساس
- **Audit Logging**: ثبت تمام دسترسی‌ها
- **Rate Limiting**: {{SECURITY_LIMITS}}

### سیاست‌های OTP
- **مدت اعتبار**: 3 دقیقه
- **تعداد تلاش**: حداکثر 3 بار
- **محدودیت ارسال**: 1 در دقیقه، 5 در ساعت
- **Provider**: Kavenegar SMS service

## مشاهده‌پذیری

### لاگ‌گذاری
- **سطح**: INFO برای عملیات عادی، ERROR برای خطاها
- **فرمت**: JSON structured logs
- **محتوا**: {{LOG_CONTENT}}

### Metrics
- **Performance**: Response time, throughput
- **Business**: {{BUSINESS_METRICS}}
- **Error Rate**: 4xx/5xx responses

### Monitoring
- **Health Checks**: {{HEALTH_CHECKS}}
- **Alerts**: {{ALERT_CONDITIONS}}

## تست‌ها

### تست‌های واحد (Unit Tests)
- **Coverage Target**: حداقل 90%
- **Test Files**: {{UNIT_TEST_FILES}}

### تست‌های تلفیقی (Integration Tests)
- **API Tests**: {{API_TEST_SCENARIOS}}
- **Database Tests**: {{DB_TEST_SCENARIOS}}

### تست‌های End-to-End
- **User Journeys**: {{E2E_SCENARIOS}}

## انتشار

### متغیرهای محیطی
```bash
{{ENVIRONMENT_VARIABLES}}
```

### تنظیمات Django
{{DJANGO_SETTINGS}}

### URL Routing
{{URL_CONFIGURATION}}

## داشبورد پزشک

### ویژگی‌های اختصاصی
{{DOCTOR_DASHBOARD_FEATURES}}

### گزارش‌ها
{{DOCTOR_REPORTS}}

### مدیریت صف
{{QUEUE_MANAGEMENT}}

## یکپارچگی با پرداخت

### درگاه‌های پرداخت
{{PAYMENT_GATEWAYS}}

### مدیریت کیف پول
{{WALLET_INTEGRATION}}

### سیاست‌های قیمت‌گذاری
{{PRICING_POLICIES}}

## یکپارچگی با پیام‌رسانی

### Kavenegar SMS
- **API Key**: تنظیم در متغیر محیطی
- **Templates**: {{SMS_TEMPLATES}}
- **Error Handling**: {{SMS_ERROR_HANDLING}}

### اطلاع‌رسانی‌ها
{{NOTIFICATION_TYPES}}

## مراحل پیاده‌سازی

### فاز 1: ساختار پایه
- [ ] ایجاد Django app
- [ ] تعریف models
- [ ] پیکربندی admin
- [ ] ایجاد migrations

### فاز 2: API و هسته‌ها
- [ ] پیاده‌سازی چهار هسته
- [ ] ایجاد serializers
- [ ] پیاده‌سازی views
- [ ] پیکربندی URLs

### فاز 3: امنیت و دسترسی
- [ ] ادغام با unified_auth
- [ ] پیاده‌سازی permissions
- [ ] تست‌های امنیتی

### فاز 4: تست و مستندسازی
- [ ] نوشتن تست‌ها
- [ ] تکمیل مستندات
- [ ] بررسی coverage

### فاز 5: آماده‌سازی انتشار
- [ ] تنظیمات production
- [ ] Performance optimization
- [ ] Security audit

## ملاحظات خاص

{{SPECIAL_CONSIDERATIONS}}

## نکات مهم

1. **عدم استثناء**: هیچ عمل سلیقه‌ای مجاز نیست
2. **دستورالعمل‌محوری**: فقط طبق این سند عمل شود
3. **ثبت تغییرات**: هر انحراف در LOG.md ثبت شود
4. **تست‌ها**: نوشته شوند اما اجرا نشوند
5. **مستندسازی**: تمام تغییرات در README مستند شوند

---
**نسخه**: {{VERSION}}
**تاریخ ایجاد**: {{CREATION_DATE}}
**آخرین به‌روزرسانی**: {{LAST_UPDATE}}