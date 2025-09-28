# 📚 فهرست کامل پروژه unified_agent

## 🗂️ ساختار دایرکتوری‌ها

### 📁 /docs - مستندات سیستم

- `01-system-overview.md` - نمای کلی سیستم HELSSA
- `02-centralized-architecture.md` - معماری متمرکز
- `03-project-tree.md` - نمودار درختی پروژه
- `04-technology-stack.md` - پشته تکنولوژی
- `05-authentication.md` - سیستم احراز هویت
- `06-ai-systems.md` - سیستم‌های هوش مصنوعی
- `07-billing-system.md` - سیستم مالی و پرداخت
- `08-visits-encounters.md` - مدیریت ویزیت‌ها
- `09-doctor-access.md` - دسترسی پزشکان
- `10-chatbot-system.md` - سیستم چت‌بات
- `11-audio-processing.md` - پردازش صوت
- `12-output-generation.md` - تولید خروجی
- `13-infrastructure.md` - زیرساخت
- `14-api-reference.md` - مرجع API
- `15-security-compliance.md` - امنیت و انطباق
- `16-deployment-guide.md` - راهنمای استقرار
- `17-quick-start.md` - شروع سریع
- `18-examples.md` - نمونه‌ها

### 📁 /instructions - دستورالعمل‌های ایجنت

- `AGENT_INSTRUCTIONS.md` - دستورالعمل اصلی ایجنت‌ها
- `QA_AGENT_INSTRUCTIONS.md` - دستورالعمل ایجنت QA
- `CORE_ARCHITECTURE.md` - معماری چهار هسته‌ای
- `SECURITY_POLICIES.md` - سیاست‌های امنیتی
- `ARCHITECTURE_CONVENTIONS.md` - قراردادهای معماری

### 📁 /templates - قالب‌های استاندارد

- `PLAN.md.template` - قالب برنامه‌ریزی
- `CHECKLIST.json.template` - قالب چک‌لیست
- `PROGRESS.json.template` - قالب گزارش پیشرفت
- `LOG.md.template` - قالب لاگ تصمیمات
- `README.md.template` - قالب مستندات اپ

### 📁 /app_standards - استانداردها و الگوها

#### 📁 /four_cores - الگوهای چهار هسته

- `__init__.py` - ماژول چهار هسته
- `api_ingress.py` - هسته ورودی API
- `text_processor.py` - هسته پردازش متن
- `speech_processor.py` - هسته پردازش صوت
- `orchestrator.py` - هماهنگ‌کننده مرکزی

#### 📁 /models - الگوهای مدل

- `base_models.py` - مدل‌های پایه
- `unified_models.py` - مدل‌های یکپارچه

#### 📁 /views - الگوهای view

- `api_views.py` - الگوهای API view
- `permissions.py` - الگوهای permission

#### 📁 /serializers - الگوهای serializer

- `base_serializers.py` - serializer‌های پایه

### 📁 /apps - اپلیکیشن‌های سیستم

- `patient_chatbot/` - چت‌بات بیمار
- `doctor_chatbot/` - چت‌بات پزشک
- `soapify_v2/` - تولید گزارش SOAP
- `visit_management/` - مدیریت ویزیت
- `prescription_system/` - سیستم نسخه‌نویسی
- `telemedicine_core/` - طب از راه دور
- `patient_records/` - پرونده بیمار
- `appointment_scheduler/` - زمان‌بندی قرارها

### 📁 /unified_cores - هسته‌های یکپارچه

- `unified_auth/` - احراز هویت یکپارچه
- `unified_billing/` - سیستم مالی یکپارچه
- `unified_ai/` - AI یکپارچه
- `unified_access/` - کنترل دسترسی یکپارچه

### 📁 /agent_tools - ابزارهای ایجنت

- `code_generator.py` - تولیدکننده کد
- `structure_validator.py` - اعتبارسنج ساختار
- `progress_tracker.py` - ردیاب پیشرفت
- `chart_generator.py` - تولیدکننده نمودار

### 📁 /sample_codes - نمونه کدها

- `view_examples.py` - نمونه‌های view (9 مثال)
- `model_examples.py` - نمونه‌های model (8 مثال)

## 📄 فایل‌های اصلی

### در ریشه پروژه

- `README.md` - مستندات اصلی پروژه
- `PROJECT_TREE.md` - نمودار درختی کامل
- `AGENT_PROMPT.md` - پرامپت اصلی ایجنت‌ها
- `FINAL_CHECKLIST.json` - چک‌لیست نهایی
- `INDEX.md` - این فایل

## 🔗 لینک‌های سریع

### مستندات مهم

- [معماری چهار هسته‌ای](instructions/CORE_ARCHITECTURE.md)
- [سیاست‌های امنیتی](instructions/SECURITY_POLICIES.md)
- [دستورالعمل ایجنت‌ها](instructions/AGENT_INSTRUCTIONS.md)
- [نمودار درختی](PROJECT_TREE.md)

### شروع سریع

1. [مطالعه سیستم](docs/01-system-overview.md)
2. [بررسی معماری](docs/02-centralized-architecture.md)
3. [مطالعه دستورالعمل‌ها](instructions/AGENT_INSTRUCTIONS.md)
4. [استفاده از قالب‌ها](templates/)

### برای توسعه‌دهندگان

- [الگوهای کد](app_standards/)
- [نمونه کدها](sample_codes/)
- [ابزارهای کمکی](agent_tools/)

## 📊 آمار پروژه

- **تعداد فایل‌های مستندات**: 18
- **تعداد دستورالعمل‌ها**: 5
- **تعداد قالب‌ها**: 5
- **تعداد الگوهای کد**: 8
- **تعداد نمونه کدها**: 17+ مثال
- **تعداد اپلیکیشن‌ها**: 8
- **تعداد هسته‌های یکپارچه**: 4

## 🎯 هدف این ساختار

این ساختار یکپارچه طراحی شده تا:

1. **ایجنت‌ها** بتوانند به سرعت و با کیفیت بالا اپلیکیشن بسازند
2. **استانداردها** در تمام پروژه رعایت شوند
3. **امنیت** از ابتدا در نظر گرفته شود
4. **یکپارچگی** بین اپلیکیشن‌ها حفظ شود
5. **کیفیت کد** در بالاترین سطح باشد

---

تولید شده در تاریخ: 2024  
نسخه: 1.0.0
