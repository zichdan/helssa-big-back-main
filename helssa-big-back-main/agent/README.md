# 🏥 سیستم یکپارچه ایجنت‌های توسعه پلتفرم هلسا

## 📋 فهرست مطالب

- [معرفی](## 🎯 معرفی)
- [ساختار پروژه](## 📁 ساختار پروژه)
- [نحوه استفاده](## 🚀 نحوه استفاده)
- [اپلیکیشن‌های سیستم](## 📱 اپلیکیشن‌های سیستم)
- [معماری چهار هسته‌ای](## 🏗️ معماری چهار هسته‌ای)
- [دستورالعمل ایجنت‌ها](## 📋 دستورالعمل ایجنت‌ها)
- [استانداردها و الگوها](## 🔧 استانداردها و الگوها)

## 🎯 معرفی

این مخزن حاوی ساختار یکپارچه و استاندارد برای ایجنت‌های توسعه‌دهنده پلتفرم هلسا است. هر ایجنت می‌تواند با استفاده از این ساختار، یک اپلیکیشن کامل و استاندارد برای پلتفرم ایجاد کند.

### ویژگی‌های کلیدی

- 🏗️ **معماری چهار هسته‌ای**: API Ingress, Text Processing, Speech Processing, Orchestration
- 🔐 **امنیت یکپارچه**: احراز هویت JWT، OTP، و کنترل دسترسی
- 🤖 **AI یکپارچه**: پردازش متن و صوت با OpenAI/Whisper
- 💰 **سیستم مالی**: یکپارچه‌سازی با درگاه‌های پرداخت
- 📱 **دو پلتفرم**: Medogram (بیماران) و SOAPify (پزشکان)

## 📁 ساختار پروژه

```bash
unified_agent/
├── 📚 docs/                      # مستندات کامل سیستم (18 فایل)
├── 📋 instructions/              # دستورالعمل‌های ایجنت‌ها
├── 📝 templates/                 # قالب‌های استاندارد
├── 🔧 app_standards/             # استانداردها و الگوها
│   ├── four_cores/              # الگوهای چهار هسته
│   ├── models/                  # الگوهای مدل
│   ├── views/                   # الگوهای view
│   └── serializers/             # الگوهای serializer
├── 📱 apps/                      # اپلیکیشن‌های سیستم
├── 🎯 unified_cores/             # هسته‌های یکپارچه
├── 🛠️ agent_tools/              # ابزارهای ایجنت
└── 💡 sample_codes/              # نمونه کدها
```

## 🚀 نحوه استفاده

### برای ایجنت‌های توسعه

1. **مطالعه مستندات اصلی**:

   ```bash
   # مطالعه معماری
   cat instructions/CORE_ARCHITECTURE.md
   
   # مطالعه سیاست‌های امنیتی
   cat instructions/SECURITY_POLICIES.md
   
   # مطالعه دستورالعمل‌ها
   cat instructions/AGENT_INSTRUCTIONS.md
   ```

2. **انتخاب اپلیکیشن برای توسعه**:
   - patient_chatbot
   - doctor_chatbot
   - soapify_v2
   - visit_management
   - prescription_system
   - telemedicine_core
   - patient_records
   - appointment_scheduler

3. **ایجاد ساختار اپ**:

   ```bash
   # ایجاد پوشه اپ
   mkdir -p apps/{app_name}
   
   # کپی قالب‌ها
   cp templates/* apps/{app_name}/
   ```

4. **پیاده‌سازی بر اساس الگوها**:
   - استفاده از `app_standards/` برای الگوها
   - پیروی از `sample_codes/` برای نمونه‌ها
   - رعایت `FINAL_CHECKLIST.json`

## 📱 اپلیکیشن‌های سیستم

### 1. patient_chatbot - چت‌بات بیمار

- **هدف**: سیستم چت هوشمند برای بیماران
- **APIs**: /chat/start, /chat/message, /chat/history
- **هسته‌های فعال**: API Ingress + Text Processing + Orchestration

### 2. doctor_chatbot - چت‌بات پزشک

- **هدف**: ابزار کمک تشخیص برای پزشکان
- **APIs**: /consult/start, /consult/query, /knowledge/search
- **هسته‌های فعال**: API Ingress + Text Processing + Orchestration

### 3. soapify_v2 - تولید گزارش SOAP

- **هدف**: تولید خودکار گزارش‌های پزشکی
- **APIs**: /encounter/create, /encounter/audio, /encounter/soap
- **هسته‌های فعال**: همه چهار هسته

### 4. visit_management - مدیریت ویزیت

- **هدف**: سیستم رزرو و مدیریت ویزیت‌ها
- **APIs**: /visit/book, /visit/available-times, /visit/reschedule
- **هسته‌های فعال**: API Ingress + Orchestration

### 5. prescription_system - سیستم نسخه‌نویسی

- **هدف**: ایجاد و مدیریت نسخه‌های دیجیتال
- **APIs**: /prescription/create, /drug/search, /drug/interaction-check
- **هسته‌های فعال**: API Ingress + Text Processing + Orchestration

## 🏗️ معماری چهار هسته‌ای

### 1. API Ingress Core

```python
from app_standards.four_cores import APIIngressCore

ingress = APIIngressCore()
# Validation
is_valid, data = ingress.validate_request(request.data, Serializer)
# Rate limiting
allowed = ingress.check_rate_limit(user_id, endpoint)
```

### 2. Text Processing Core

```python
from app_standards.four_cores import TextProcessorCore

processor = TextProcessorCore()
# پردازش متن پزشکی
result = processor.process_medical_text(text, context)
```

### 3. Speech Processing Core

```python
from app_standards.four_cores import SpeechProcessorCore

processor = SpeechProcessorCore()
# تبدیل صوت به متن
result = processor.transcribe_audio(audio_file, language='fa')
```

### 4. Central Orchestrator

```python
from app_standards.four_cores import CentralOrchestrator

orchestrator = CentralOrchestrator()
# اجرای workflow
result = orchestrator.execute_workflow('medical_chat', data, user)
```

## 📋 دستورالعمل ایجنت‌ها

### گام‌های اجرایی

1. **مطالعه (10%)**
   - خواندن CORE_ARCHITECTURE.md
   - خواندن SECURITY_POLICIES.md
   - بررسی app_standards/

2. **طراحی (20%)**
   - تکمیل PLAN.md
   - تعریف API endpoints
   - طراحی مدل‌ها

3. **پیاده‌سازی (50%)**
   - ایجاد Django app
   - پیاده‌سازی چهار هسته
   - نوشتن models, views, serializers

4. **یکپارچه‌سازی (10%)**
   - ادغام با unified_auth
   - ادغام با unified_billing
   - ادغام با unified_ai

5. **تست و مستندات (10%)**
   - نوشتن تست‌ها
   - تکمیل README
   - ایجاد API spec

## 🔧 استانداردها و الگوها

### الگوی Model

```python
from app_standards.models.base_models import BaseModel

class MyModel(BaseModel):
    # فیلدهای مدل
    pass
```

### الگوی View

```python
from app_standards.views.api_views import BaseAPIView

class MyView(BaseAPIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # پیاده‌سازی
        pass
```

### الگوی Serializer

```python
from app_standards.serializers.base_serializers import BaseModelSerializer

class MySerializer(BaseModelSerializer):
    class Meta:
        model = MyModel
        fields = '__all__'
```

## ⚠️ نکات مهم

### ✅ الزامات

- استفاده از UnifiedUser (هرگز User جدید نسازید)
- رعایت معماری چهار هسته‌ای
- پیاده‌سازی OTP با Kavenegar
- استفاده از JWT برای احراز هویت
- تفکیک دسترسی patient/doctor

### 🚫 ممنوعیت‌ها

- ایجاد user model جدید
- استفاده از Raw SQL
- Hard-coded values
- تغییر معماری
- نادیده گرفتن security policies

## 📊 وضعیت پروژه

- ✅ **مستندات**: کامل (18 فایل)
- ✅ **دستورالعمل‌ها**: کامل (5 فایل)
- ✅ **قالب‌ها**: کامل (5 فایل)
- ✅ **استانداردها**: کامل (8 فایل)
- ✅ **نمونه کدها**: کامل (2 فایل)
- 🔄 **اپلیکیشن‌ها**: آماده برای توسعه (8 اپ)

## 🤝 مشارکت

این پروژه توسط تیم ایجنت‌های هوشمند توسعه داده می‌شود. هر ایجنت مسئول توسعه یک اپلیکیشن است و باید دقیقاً طبق دستورالعمل‌ها عمل کند.

---

**نسخه**: 1.0.0  
**تاریخ**: 2024  
**تیم توسعه**: HELSSA AI Agents
