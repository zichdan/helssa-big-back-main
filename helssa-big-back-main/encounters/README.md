# اپ Encounters - مدیریت ملاقات‌های پزشکی

## معرفی

اپ encounters مسئول مدیریت کامل ملاقات‌های پزشکی در سیستم هلسا است. این اپ امکانات زیر را فراهم می‌کند:

- زمان‌بندی و مدیریت ویزیت‌ها
- ویدیو کنفرانس برای ویزیت‌های آنلاین
- ضبط و پردازش صوت ملاقات‌ها
- رونویسی خودکار با Whisper
- تولید گزارش SOAP با هوش مصنوعی
- نسخه‌نویسی الکترونیک
- مدیریت فایل‌های پزشکی

## مدل‌های اصلی

### Encounter
مدل اصلی برای ذخیره اطلاعات ملاقات شامل:
- اطلاعات بیمار و پزشک
- نوع و وضعیت ویزیت
- زمان‌بندی
- اطلاعات پرداخت
- لینک‌های اتصال ویدیو

### AudioChunk
ذخیره قطعات صوتی ضبط شده از ملاقات

### Transcript
رونویسی متنی قطعات صوتی

### SOAPReport
گزارش SOAP شامل چهار بخش:
- Subjective (شرح حال)
- Objective (معاینه)
- Assessment (ارزیابی)
- Plan (برنامه درمان)

### Prescription
نسخه‌های الکترونیک صادر شده

### EncounterFile
فایل‌های مرتبط با ملاقات (تصاویر، آزمایشات و...)

## API Endpoints

### مدیریت ملاقات‌ها
- `POST /api/v1/encounters/schedule/` - زمان‌بندی ملاقات جدید
- `GET /api/v1/encounters/` - لیست ملاقات‌ها
- `GET /api/v1/encounters/{id}/` - جزئیات ملاقات
- `POST /api/v1/encounters/{id}/status/` - تغییر وضعیت
- `POST /api/v1/encounters/{id}/start/` - شروع ویزیت
- `POST /api/v1/encounters/{id}/end/` - پایان ویزیت

### پردازش صوت
- `POST /api/v1/encounters/{id}/upload-audio/` - آپلود قطعه صوتی
- `GET /api/v1/audio-chunks/` - لیست قطعات صوتی
- `GET /api/v1/transcripts/` - لیست رونویسی‌ها
- `GET /api/v1/transcripts/full_transcript/` - رونویسی کامل

### گزارش‌ها
- `POST /api/v1/encounters/{id}/generate-soap/` - تولید گزارش SOAP
- `GET /api/v1/soap-reports/` - لیست گزارش‌ها
- `POST /api/v1/soap-reports/{id}/approve/` - تایید گزارش
- `POST /api/v1/soap-reports/{id}/share/` - اشتراک با بیمار

### نسخه‌نویسی
- `GET /api/v1/prescriptions/` - لیست نسخه‌ها
- `POST /api/v1/prescriptions/` - ایجاد نسخه جدید
- `POST /api/v1/prescriptions/{id}/add_medication/` - افزودن دارو
- `POST /api/v1/prescriptions/{id}/issue/` - صدور نسخه

## تنظیمات

برای استفاده از این اپ، تنظیمات زیر را به `settings.py` پروژه اضافه کنید:

```python
# در INSTALLED_APPS
INSTALLED_APPS = [
    # ...
    'encounters',
    # ...
]

# تنظیمات Jitsi
JITSI_DOMAIN = 'meet.jit.si'
JITSI_JWT_SECRET = 'your-secret'

# تنظیمات MinIO
MINIO_ENDPOINT = 'minio.helssa.ir'
MINIO_ACCESS_KEY = 'your-key'
MINIO_SECRET_KEY = 'your-secret'

# تنظیمات STT
WHISPER_API_URL = 'http://whisper-api:8000'
WHISPER_API_KEY = 'your-key'

# سایر تنظیمات در encounters/settings.py
```

## نیازمندی‌ها

```
django>=4.2
djangorestframework>=3.14
celery>=5.3
django-filter>=23.0
pyjwt>=2.8
cryptography>=41.0
aiohttp>=3.9
```

## Celery Tasks

### صف‌های مورد نیاز:
- `stt` - پردازش تبدیل گفتار به متن
- `nlp` - پردازش زبان طبیعی
- `video` - پردازش ویدیو

### Task های اصلی:
- `process_audio_chunk_stt` - پردازش STT قطعات صوتی
- `extract_medical_entities` - استخراج موجودیت‌های پزشکی
- `merge_encounter_transcripts` - ادغام رونویسی‌ها
- `generate_soap_report_async` - تولید گزارش SOAP

## مجوزها و دسترسی‌ها

### Permission Classes:
- `IsPatientOrDoctor` - دسترسی برای بیمار یا پزشک ملاقات
- `IsDoctorOfEncounter` - دسترسی فقط برای پزشک
- `CanStartEncounter` - بررسی امکان شروع ملاقات
- `CanModifySOAPReport` - دسترسی تغییر گزارش SOAP

## نکات امنیتی

1. تمام فایل‌های صوتی و تصویری رمزنگاری می‌شوند
2. هر ملاقات کلید رمزنگاری منحصر به فرد دارد
3. دسترسی به فایل‌ها با توکن موقت انجام می‌شود
4. رونویسی‌ها و گزارش‌ها قابل ویرایش توسط غیر پزشک نیستند

## مثال استفاده

### زمان‌بندی ملاقات:

```python
import requests

response = requests.post(
    'http://api.helssa.ir/v1/encounters/schedule/',
    headers={'Authorization': 'Bearer YOUR_TOKEN'},
    json={
        'patient': 'patient-uuid',
        'doctor': 'doctor-uuid',
        'type': 'video',
        'scheduled_at': '2024-01-20T10:00:00Z',
        'duration_minutes': 30,
        'chief_complaint': 'سردرد مزمن',
        'fee_amount': 500000
    }
)
```

### شروع ویزیت:

```python
response = requests.post(
    f'http://api.helssa.ir/v1/encounters/{encounter_id}/start/',
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)

# دریافت لینک اتصال
join_url = response.json()['visit_info']['join_url']
```

## توسعه

برای توسعه این اپ:

1. مدل‌های جدید را در `models/` اضافه کنید
2. سرویس‌های جدید را در `services/` پیاده‌سازی کنید
3. API views را در `api/views/` اضافه کنید
4. برای پردازش‌های سنگین از Celery tasks استفاده کنید

## پشتیبانی

در صورت بروز مشکل یا سوال، با تیم توسعه تماس بگیرید.