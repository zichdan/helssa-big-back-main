# اپلیکیشن Doctor - مدیریت پزشکان

این اپلیکیشن مسئول مدیریت کامل پزشکان در سیستم هلسا است و شامل پروفایل، برنامه کاری، مدارک، امتیازدهی و قابلیت‌های تولید نسخه و گواهی PDF می‌باشد.

## ویژگی‌های کلیدی

### 1. مدیریت پروفایل پزشک
- ایجاد و ویرایش پروفایل کامل پزشک
- اطلاعات شخصی، تخصص، تجربه کاری
- مدیریت تصویر پروفایل
- سیستم تایید و احراز هویت پزشکان
- امتیازدهی و نظرات بیماران

### 2. مدیریت برنامه کاری و شیفت‌ها
- برنامه‌ریزی هفتگی کار پزشک
- تعریف شیفت‌های خاص و اورژانسی
- مدیریت ساعات کاری و استراحت
- تنظیم حداکثر تعداد بیماران
- پشتیبانی از ویزیت حضوری و آنلاین

### 3. مدیریت مدارک و گواهی‌نامه‌ها
- آپلود و مدیریت مدارک پزشکی
- سیستم تایید مدارک توسط ادمین
- بررسی انقضای مدارک
- دسته‌بندی انواع مختلف مدارک

### 4. سیستم امتیازدهی
- امتیازدهی بیماران به پزشکان
- محاسبه میانگین امتیازات
- مدیریت نظرات و بازخوردها
- سیستم تایید نظرات

### 5. تولید اسناد PDF
- تولید خودکار نسخه‌های PDF
- صدور گواهی‌های پزشکی
- امضای دیجیتال اسناد
- قالب‌های استاندارد و قابل تنظیم

## معماری چهار هسته‌ای

### 1. API Ingress Core
- مدیریت ورودی و خروجی API
- اعتبارسنجی درخواست‌ها
- Rate limiting اختصاصی پزشک
- لاگ‌گیری عملیات

### 2. Text Processor Core
- پردازش متن‌های پزشکی
- استخراج علائم و داروها
- تولید خلاصه پزشکی
- استخراج اجزای SOAP

### 3. Speech Processor Core
- رونویسی صوت پزشکی
- تحلیل گفتگوی پزشک-بیمار
- استخراج اطلاعات از فایل‌های صوتی
- کیفیت‌سنجی فایل‌های صوتی

### 4. Central Orchestrator
- هماهنگی بین هسته‌ها
- مدیریت workflow های پیچیده
- پردازش غیرهمزمان
- مدیریت خطاها و retry

## مدل‌های داده

### DoctorProfile
پروفایل کامل پزشک شامل:
```python
- user: رابطه با کاربر
- first_name, last_name: نام و نام خانوادگی
- national_code: کد ملی
- medical_system_code: کد نظام پزشکی
- specialty: تخصص اصلی
- sub_specialty: فوق تخصص
- phone_number: شماره تماس
- clinic_address: آدرس مطب
- biography: بیوگرافی
- years_of_experience: سال‌های تجربه
- visit_duration: مدت ویزیت
- visit_price: هزینه ویزیت
- is_verified: وضعیت تایید
- rating: امتیاز میانگین
- total_reviews: تعداد نظرات
```

### DoctorSchedule
برنامه کاری هفتگی:
```python
- doctor: پزشک
- weekday: روز هفته (0-6)
- start_time, end_time: ساعت شروع و پایان
- visit_type: نوع ویزیت (حضوری/آنلاین/هردو)
- max_patients: حداکثر بیمار
- break_start, break_end: زمان استراحت
```

### DoctorShift
شیفت‌های خاص:
```python
- doctor: پزشک
- date: تاریخ
- start_time, end_time: ساعت کاری
- shift_type: نوع شیفت (عادی/اورژانس/ویژه/مرخصی)
- notes: یادداشت‌ها
```

### DoctorCertificate
مدارک و گواهی‌نامه‌ها:
```python
- doctor: پزشک
- certificate_type: نوع مدرک
- title: عنوان مدرک
- issuer: مرجع صادرکننده
- issue_date: تاریخ صدور
- expiry_date: تاریخ انقضا
- file: فایل مدرک
- is_verified: وضعیت تایید
```

### DoctorRating
امتیازدهی و نظرات:
```python
- doctor: پزشک
- patient: بیمار
- rating: امتیاز (1-5)
- comment: نظر
- visit_date: تاریخ ویزیت
- is_approved: وضعیت تایید
```

### DoctorSettings
تنظیمات شخصی:
```python
- doctor: پزشک
- email_notifications: اعلان ایمیل
- sms_notifications: اعلان پیامک
- auto_generate_prescription: تولید خودکار نسخه
- preferred_language: زبان ترجیحی
```

## API Endpoints

### مدیریت پروفایل
- `POST /api/doctor/profile/create/` - ایجاد پروفایل
- `GET /api/doctor/profile/` - دریافت پروفایل
- `PUT /api/doctor/profile/update/` - بروزرسانی پروفایل

### مدیریت برنامه کاری
- `POST /api/doctor/schedule/create/` - ایجاد برنامه کاری
- `GET /api/doctor/schedule/` - دریافت برنامه کاری

### جستجو
- `GET /api/doctor/search/` - جستجوی پزشکان

## سرویس‌ها

### DoctorProfileService
مدیریت پروفایل پزشک:
```python
- create_doctor_profile()
- update_doctor_profile()
- get_doctor_profile()
- search_doctors()
```

### DoctorScheduleService
مدیریت برنامه کاری:
```python
- create_schedule()
- get_doctor_schedule()
- update_schedule()
- delete_schedule()
```

### DoctorCertificateService
مدیریت مدارک:
```python
- add_certificate()
- get_doctor_certificates()
```

### DoctorRatingService
مدیریت امتیازدهی:
```python
- add_rating()
- get_doctor_ratings()
```

### DoctorAnalyticsService
آنالیتیکس و گزارش‌ها:
```python
- get_doctor_dashboard_stats()
```

## Workflow ها

### ایجاد پروفایل پزشک
1. اعتبارسنجی داده‌های پروفایل
2. بررسی یکتا بودن کد نظام پزشکی
3. ایجاد پروفایل
4. تنظیم پیکربندی‌های پیش‌فرض

### ایجاد برنامه کاری
1. اعتبارسنجی داده‌های برنامه
2. بررسی تداخل برنامه کاری
3. ایجاد برنامه
4. ارسال اعلان

### پردازش صوت پزشکی
1. اعتبارسنجی فایل صوتی
2. رونویسی صوت
3. استخراج اطلاعات پزشکی
4. تولید SOAP از صوت
5. ذخیره تحلیل

### تولید نسخه PDF
1. اعتبارسنجی داده‌های نسخه
2. بررسی تداخل دارویی
3. تولید PDF
4. افزودن امضای دیجیتال
5. ذخیره رکورد نسخه

## امنیت و دسترسی

### احراز هویت
- JWT authentication
- بررسی نوع کاربر (پزشک)
- سیستم تایید پزشک

### مجوزها
- `@doctor_required` - نیاز به پزشک بودن
- `@doctor_rate_limit` - محدودیت درخواست
- بررسی تایید پزشک برای عملیات حساس

### اعتبارسنجی
- Serializer validation
- بررسی یکتایی کد ملی و کد نظام پزشکی
- اعتبارسنجی زمان‌بندی برنامه کاری
- بررسی انقضای مدارک

## تنظیمات Django Admin

پنل مدیریت کامل با قابلیت‌های:
- مدیریت پروفایل پزشکان
- تایید/لغو تایید پزشکان
- مدیریت برنامه کاری و شیفت‌ها
- بررسی و تایید مدارک
- مدیریت امتیازات و نظرات
- تنظیمات شخصی پزشکان

## تست‌ها

### انواع تست‌ها
- Unit Tests: تست مدل‌ها و سرویس‌ها
- API Tests: تست endpoint ها
- Integration Tests: تست یکپارچگی
- Workflow Tests: تست فرآیندها

### پوشش تست
- تست ایجاد و مدیریت پروفایل
- تست برنامه‌ریزی کاری
- تست امتیازدهی
- تست دسترسی‌ها و مجوزها

## استفاده

### نصب
1. اپ را به `INSTALLED_APPS` اضافه کنید
2. Migration ها را اجرا کنید
3. URL ها را به پروژه اصلی اضافه کنید

### پیکربندی
```python
# settings.py
INSTALLED_APPS = [
    ...
    'doctor',
    'rest_framework',
]

# urls.py
urlpatterns = [
    ...
    path('api/doctor/', include('doctor.urls')),
]
```

### مثال استفاده API

#### ایجاد پروفایل پزشک
```python
POST /api/doctor/profile/create/
{
    "first_name": "محمد",
    "last_name": "احمدی",
    "national_code": "1234567890",
    "medical_system_code": "DOC12345",
    "specialty": "general",
    "phone_number": "09123456789",
    "years_of_experience": 5,
    "visit_price": "200000"
}
```

#### جستجوی پزشکان
```python
GET /api/doctor/search/?specialty=general&verified_only=true
```

## نکات توسعه

### بهترین شیوه‌ها
- همیشه از UnifiedUser استفاده کنید
- Type hints را رعایت کنید
- کامنت‌ها و docstring ها را فارسی بنویسید
- از معماری چهار هسته‌ای پیروی کنید

### قوانین امنیتی
- هرگز اطلاعات حساس را لاگ نکنید
- همیشه input validation انجام دهید
- از ORM برای جلوگیری از SQL injection استفاده کنید
- Rate limiting را رعایت کنید

### Performance
- از select_related و prefetch_related استفاده کنید
- Cache را برای داده‌های مکرر به کار ببرید
- Pagination را فراموش نکنید
- Database index ها را بررسی کنید

## ترک اپ
این اپ بخشی از سیستم جامع هلسا است و با سایر اپ‌ها ارتباط دارد:
- `auth_otp`: برای احراز هویت
- `patient`: برای ارتباط با بیماران  
- `encounters`: برای مدیریت ویزیت‌ها
- `soap`: برای یادداشت‌های پزشکی
- `notifications`: برای ارسال اعلان‌ها

## مجوز
© Helssa/Medogram. All rights reserved.