# 📝 Feedback App - سیستم بازخورد و نظرسنجی

اپلیکیشن feedback برای مدیریت بازخورد کاربران، امتیازدهی جلسات و نظرسنجی‌ها در پلتفرم هلسا طراحی شده است.

## 🎯 امکانات

### امتیازدهی جلسات (Session Rating)
- امتیازدهی کلی از 1 تا 5
- امتیازدهی تفکیکی (کیفیت پاسخ، سرعت، مفید بودن)
- نظرات متنی و پیشنهادات بهبود
- توصیه به دیگران

### بازخورد پیام‌ها (Message Feedback)
- انواع مختلف بازخورد (مفید، غیرمفید، نادرست، ناکامل، نامناسب، عالی)
- بازخورد تفصیلی متنی
- بازخورد صوتی
- تحلیل احساسات

### نظرسنجی‌ها (Surveys)
- ایجاد نظرسنجی‌های سفارشی
- انواع مختلف سوالات (متن، عدد، امتیاز، چندگزینه‌ای)
- زمان‌بندی نظرسنجی‌ها
- نظرسنجی ناشناس
- آمار و گزارش‌گیری

### تحلیل و آنالیتیک
- آمار کلی و تفصیلی
- تحلیل احساسات
- تشخیص نگرانی‌های پزشکی
- داشبورد مدیریتی

## 🏗️ معماری

اپلیکیشن بر اساس معماری 4 هسته‌ای هلسا طراحی شده:

### 1. API Ingress Core
- اعتبارسنجی داده‌های ورودی
- فرمت کردن پاسخ‌ها
- مدیریت خطاها

### 2. Text Processor Core
- تحلیل احساسات متن فارسی
- استخراج کلمات کلیدی
- تشخیص پیشنهادات بهبود
- تشخیص نگرانی‌های پزشکی

### 3. Speech Processor Core
- تبدیل صدا به متن
- تولید صدا از متن
- پردازش بازخورد صوتی
- اعتبارسنجی فایل‌های صوتی

### 4. Central Orchestrator
- هماهنگی بین هسته‌ها
- مدیریت workflow
- پردازش async

## 📊 مدل‌های داده

### SessionRating
امتیازدهی جلسات چت

```python
- session_id: شناسه جلسه
- user: کاربر امتیازدهنده
- overall_rating: امتیاز کلی (1-5)
- response_quality: امتیاز کیفیت پاسخ
- response_speed: امتیاز سرعت پاسخ
- helpfulness: امتیاز مفید بودن
- comment: نظر متنی
- suggestions: پیشنهادات بهبود
- would_recommend: توصیه به دیگران
```

### MessageFeedback
بازخورد پیام‌های چت

```python
- message_id: شناسه پیام
- user: کاربر بازخورددهنده
- feedback_type: نوع بازخورد
- is_helpful: مفید بودن
- detailed_feedback: بازخورد تفصیلی
- expected_response: پاسخ مورد انتظار
```

### Survey
نظرسنجی‌ها

```python
- title: عنوان نظرسنجی
- description: توضیحات
- survey_type: نوع نظرسنجی
- target_users: کاربران هدف
- questions: سوالات (JSON)
- start_date/end_date: زمان‌بندی
- max_responses: حداکثر پاسخ
- allow_anonymous: پاسخ ناشناس
```

### SurveyResponse
پاسخ‌های نظرسنجی

```python
- survey: نظرسنجی مرتبط
- user: کاربر پاسخ‌دهنده
- answers: پاسخ‌ها (JSON)
- overall_score: امتیاز کلی
- completion_time: زمان تکمیل
```

### FeedbackSettings
تنظیمات اپ

```python
- key: کلید تنظیمات
- value: مقدار (JSON)
- setting_type: نوع تنظیمات
- description: توضیحات
```

## 🔗 API Endpoints

### امتیازدهی جلسات
```
GET    /feedback/api/ratings/          # فهرست امتیازدهی‌ها
POST   /feedback/api/ratings/          # ایجاد امتیازدهی جدید
GET    /feedback/api/ratings/{id}/     # جزئیات امتیازدهی
PUT    /feedback/api/ratings/{id}/     # ویرایش امتیازدهی
DELETE /feedback/api/ratings/{id}/     # حذف امتیازدهی
GET    /feedback/api/ratings/stats/    # آمار امتیازدهی‌ها
```

### بازخورد پیام‌ها
```
GET    /feedback/api/feedbacks/        # فهرست بازخوردها
POST   /feedback/api/feedbacks/        # ایجاد بازخورد جدید
GET    /feedback/api/feedbacks/{id}/   # جزئیات بازخورد
PUT    /feedback/api/feedbacks/{id}/   # ویرایش بازخورد
DELETE /feedback/api/feedbacks/{id}/   # حذف بازخورد
GET    /feedback/api/feedbacks/stats/  # آمار بازخوردها
```

### نظرسنجی‌ها
```
GET    /feedback/api/surveys/              # فهرست نظرسنجی‌ها
POST   /feedback/api/surveys/              # ایجاد نظرسنجی جدید
GET    /feedback/api/surveys/{id}/         # جزئیات نظرسنجی
PUT    /feedback/api/surveys/{id}/         # ویرایش نظرسنجی
DELETE /feedback/api/surveys/{id}/         # حذف نظرسنجی
POST   /feedback/api/surveys/{id}/submit_response/  # ارسال پاسخ
```

### آنالیتیک
```
GET    /feedback/api/analytics/        # داشبورد آنالیتیک
```

### تنظیمات
```
GET    /feedback/api/settings/         # فهرست تنظیمات
POST   /feedback/api/settings/         # ایجاد تنظیمات جدید
GET    /feedback/api/settings/config/  # تنظیمات جامع
```

## 🛠️ نصب و راه‌اندازی

### 1. اضافه کردن به INSTALLED_APPS

```python
INSTALLED_APPS = [
    ...
    'feedback',
    ...
]
```

### 2. تنظیمات اضافی

```python
# تنظیمات امتیازدهی
FEEDBACK_RATING_SETTINGS = {
    'ENABLED': True,
    'SCALE_MAX': 5,
    'REQUIRED_FIELDS': ['overall_rating'],
    'ALLOW_EDIT': True,
    'EDIT_TIME_LIMIT': 24 * 60,
}

# تنظیمات بازخورد پیام
FEEDBACK_MESSAGE_SETTINGS = {
    'ENABLED': True,
    'VOICE_FEEDBACK_ENABLED': True,
    'MAX_TEXT_LENGTH': 500,
    'SENTIMENT_ANALYSIS_ENABLED': True,
    'AUTO_FOLLOWUP_ENABLED': True,
}

# تنظیمات نظرسنجی
FEEDBACK_SURVEY_SETTINGS = {
    'ENABLED': True,
    'ANONYMOUS_ALLOWED': False,
    'MAX_QUESTIONS': 20,
    'AUTO_ACTIVATION': True,
    'COMPLETION_TRACKING': True,
}
```

### 3. URLs

```python
# در urls.py اصلی
urlpatterns = [
    ...
    path('feedback/', include('feedback.urls')),
    ...
]
```

### 4. Migration

```bash
python manage.py makemigrations feedback
python manage.py migrate
```

## 📱 نحوه استفاده

### ایجاد امتیازدهی

```python
from feedback.models import SessionRating

rating = SessionRating.objects.create(
    session_id=session_uuid,
    user=user,
    overall_rating=4,
    response_quality=4,
    comment='پاسخ‌های خوبی بود',
    would_recommend=True
)
```

### ایجاد بازخورد پیام

```python
from feedback.models import MessageFeedback

feedback = MessageFeedback.objects.create(
    message_id=message_uuid,
    user=user,
    feedback_type='helpful',
    is_helpful=True,
    detailed_feedback='پاسخ مفیدی بود'
)
```

### استفاده از API

```javascript
// ایجاد امتیازدهی
const response = await fetch('/feedback/api/ratings/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
    },
    body: JSON.stringify({
        session_id: sessionId,
        overall_rating: 4,
        comment: 'خوب بود'
    })
});

// دریافت آمار
const stats = await fetch('/feedback/api/ratings/stats/')
    .then(res => res.json());
```

## 🧪 تست‌ها

```bash
# اجرای تمام تست‌ها
python manage.py test feedback

# اجرای تست‌های خاص
python manage.py test feedback.tests.SessionRatingModelTest
python manage.py test feedback.tests.FeedbackAPITest
```

## 🔧 تنظیمات پیشرفته

### تحلیل احساسات سفارشی

```python
from feedback.cores import FeedbackTextProcessorCore

processor = FeedbackTextProcessorCore()
result = processor.analyze_feedback_sentiment("متن بازخورد")
print(result['sentiment'])  # positive/negative/neutral
```

### پردازش صوت

```python
from feedback.cores import FeedbackSpeechProcessorCore

speech_processor = FeedbackSpeechProcessorCore()
result = speech_processor.transcribe_feedback_audio(audio_data, "wav")
print(result.text)
```

## 📈 مانیتورینگ

### Logging

لاگ‌های اپ در فایل `logs/feedback.log` ذخیره می‌شوند:

```python
import logging

logger = logging.getLogger('feedback')
logger.info('Feedback processed successfully')
```

### آمار

آمار کلی از طریق admin panel یا API قابل دسترسی است:

- تعداد کل امتیازدهی‌ها
- میانگین امتیازات
- توزیع انواع بازخورد
- نرخ تکمیل نظرسنجی‌ها

## 🤝 مشارکت

برای مشارکت در توسعه:

1. رعایت استانداردهای کدنویسی فارسی
2. نوشتن تست برای کدهای جدید
3. استفاده از معماری 4 هسته‌ای
4. مستندسازی تغییرات

## 📄 مجوز

این پروژه تحت مجوز [LICENSE] منتشر شده است.