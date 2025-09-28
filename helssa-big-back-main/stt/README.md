# اپ STT (Speech-to-Text)

## معرفی
اپ STT برای تبدیل گفتار به متن در پلتفرم هلسا طراحی شده است. این اپ از مدل Whisper استفاده می‌کند و قابلیت‌های ویژه‌ای برای محیط پزشکی دارد.

## ویژگی‌ها

### ویژگی‌های عمومی
- تبدیل گفتار به متن با استفاده از Whisper
- پشتیبانی از زبان‌های فارسی و انگلیسی
- کنترل کیفیت خودکار
- تصحیح اصطلاحات پزشکی
- Rate limiting بر اساس نوع کاربر
- کش نتایج برای بهینه‌سازی

### API های ویژه بیمار
- **تبدیل صدای علائم**: بیماران می‌توانند علائم خود را به صورت صوتی ثبت کنند
- بهینه‌سازی برای شناسایی علائم پزشکی
- استخراج خودکار اطلاعات مهم مانند مدت و شدت علائم

### API های ویژه دکتر
- **دیکته نسخه**: امکان دیکته کردن نسخه‌های پزشکی
- **یادداشت‌های SOAP**: دیکته یادداشت‌های پزشکی
- دقت بالاتر با مدل‌های پیشرفته‌تر
- استخراج خودکار اطلاعات دارویی

## نصب و راه‌اندازی

### پیش‌نیازها
```bash
# نصب Whisper و وابستگی‌ها
pip install openai-whisper
pip install ffmpeg-python
pip install python-magic

# نصب ffmpeg (در سیستم)
# Ubuntu/Debian:
sudo apt update && sudo apt install ffmpeg

# macOS:
brew install ffmpeg
```

### تنظیمات
در فایل `settings.py` پروژه اصلی:

```python
INSTALLED_APPS = [
    # ...
    'stt',
]

# تنظیمات STT
STT_DEFAULT_MODEL = 'base'  # tiny, base, small, medium, large
STT_MAX_FILE_SIZE = 52428800  # 50MB
STT_RATE_LIMIT_PATIENT = 20  # در ساعت
STT_RATE_LIMIT_DOCTOR = 50  # در ساعت

# Celery
CELERY_BEAT_SCHEDULE = {
    'update-stt-daily-stats': {
        'task': 'stt.tasks.update_daily_statistics',
        'schedule': crontab(hour=0, minute=0),  # هر شب ساعت 00:00
    },
    'cleanup-old-stt-tasks': {
        'task': 'stt.tasks.cleanup_old_tasks',
        'schedule': crontab(hour=2, minute=0),  # هر شب ساعت 02:00
    },
}
```

### Migrations
```bash
python manage.py makemigrations stt
python manage.py migrate stt
```

## استفاده

### API عمومی تبدیل گفتار به متن
```bash
POST /api/stt/transcribe/
Authorization: Bearer <token>
Content-Type: multipart/form-data

audio_file: <file>
language: fa  # fa/en/auto
model: base  # tiny/base/small/medium/large
context_type: general  # general/medical/prescription/symptoms
```

### API ویژه بیمار
```bash
POST /api/stt/patient/voice-to-text/
Authorization: Bearer <token>
Content-Type: multipart/form-data

audio_file: <file>
language: fa
```

### API ویژه دکتر
```bash
POST /api/stt/doctor/dictation/
Authorization: Bearer <token>
Content-Type: multipart/form-data

audio_file: <file>
dictation_type: prescription  # prescription/soap_note/medical_report
language: fa
model: small  # توصیه می‌شود برای دقت بیشتر
```

### بررسی وضعیت
```bash
GET /api/stt/task/{task_id}/
Authorization: Bearer <token>
```

## معماری

### هسته‌های چهارگانه

1. **API Ingress Core**
   - اعتبارسنجی درخواست‌ها
   - Rate limiting
   - مدیریت کش

2. **Speech Processor Core**
   - تبدیل فرمت صوت
   - پیش‌پردازش (حذف نویز)
   - فراخوانی Whisper
   - تحلیل کیفیت صوت

3. **Text Processor Core**
   - نرمال‌سازی متن
   - تصحیح اصطلاحات پزشکی
   - استخراج موجودیت‌ها
   - بهبود علائم نگارشی

4. **Central Orchestrator**
   - هماهنگی بین هسته‌ها
   - مدیریت workflow
   - کنترل کیفیت
   - ذخیره نتایج

## مدل‌ها

### STTTask
وظیفه اصلی تبدیل گفتار به متن

### STTQualityControl
کنترل کیفیت و بررسی انسانی

### STTUsageStats
آمار استفاده روزانه کاربران

## کنترل کیفیت

### معیارهای بررسی خودکار
- امتیاز اطمینان کمتر از 50%
- کیفیت صوت پایین
- نویز پس‌زمینه زیاد
- متن بسیار کوتاه
- نسخه‌های پزشکی (برای دقت بیشتر)

### بررسی انسانی
کارمندان می‌توانند از طریق پنل ادمین یا API های مخصوص، نتایج را بررسی و اصلاح کنند.

## بهترین شیوه‌ها

### برای کاربران
1. در محیط آرام ضبط کنید
2. با صدای واضح و شمرده صحبت کنید
3. از فایل‌های با کیفیت مناسب استفاده کنید
4. برای نسخه‌های پزشکی، نام داروها را واضح بیان کنید

### برای توسعه‌دهندگان
1. همیشه context_type مناسب را مشخص کنید
2. برای دکترها از مدل‌های دقیق‌تر استفاده کنید
3. نتایج مهم را برای بررسی علامت‌گذاری کنید
4. از API های مخصوص هر نوع کاربر استفاده کنید

## عیب‌یابی

### خطاهای رایج

1. **Rate Limit Exceeded**
   - صبر کنید یا تعداد درخواست‌ها را کاهش دهید

2. **Low Audio Quality**
   - فایل را در محیط آرام‌تر ضبط کنید
   - از میکروفون بهتر استفاده کنید

3. **Processing Failed**
   - فرمت فایل را بررسی کنید
   - حجم فایل نباید بیش از 50MB باشد

## TODO
- [ ] پشتیبانی از زبان‌های بیشتر
- [ ] یکپارچه‌سازی با سرویس TTS
- [ ] Real-time transcription
- [ ] پشتیبانی از ویدیو
- [ ] دیکشنری اصطلاحات پزشکی کامل‌تر