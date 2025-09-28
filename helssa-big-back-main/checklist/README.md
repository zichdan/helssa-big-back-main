# اپلیکیشن Checklist

## معرفی
اپلیکیشن Checklist برای مدیریت چک‌لیست‌های پویا در طول ویزیت‌های پزشکی و ایجاد هشدارهای real-time طراحی شده است. این اپ به پزشکان کمک می‌کند تا اطمینان حاصل کنند که تمام موارد مهم در طول ویزیت بررسی شده‌اند.

## ویژگی‌ها

### 1. کاتالوگ چک‌لیست
- تعریف آیتم‌های استاندارد چک‌لیست
- دسته‌بندی آیتم‌ها (تاریخچه، معاینه، تشخیص، درمان و...)
- تعیین اولویت (پایین، متوسط، بالا، بحرانی)
- کلمات کلیدی برای تشخیص خودکار

### 2. قالب‌های چک‌لیست
- ایجاد قالب‌های قابل استفاده مجدد
- تخصیص به تخصص‌ها و شکایات خاص
- امکان کپی و ویرایش قالب‌ها

### 3. ارزیابی خودکار
- تحلیل متن transcript ویزیت
- تشخیص پوشش آیتم‌ها بر اساس کلمات کلیدی
- محاسبه امتیاز اطمینان
- استخراج متن شاهد

### 4. هشدارهای Real-time
- هشدار برای آیتم‌های بحرانی پوشش داده نشده
- هشدار برای امتیازهای اطمینان پایین
- تشخیص و هشدار علائم خطر (Red Flags)
- امکان رد کردن هشدارها

## مدل‌های داده

### ChecklistCatalog
آیتم‌های کاتالوگ چک‌لیست که شامل:
- عنوان و توضیحات
- دسته‌بندی و اولویت
- کلمات کلیدی
- قالب سوال

### ChecklistTemplate
قالب‌های چک‌لیست برای استفاده در موارد خاص:
- نام و توضیحات
- آیتم‌های کاتالوگ مرتبط
- تخصص و شکایت اصلی

### ChecklistEval
ارزیابی چک‌لیست برای هر ویزیت:
- وضعیت پوشش (covered, partial, missing, unclear)
- امتیاز اطمینان
- متن شاهد
- پاسخ پزشک

### ChecklistAlert
هشدارهای سیستم:
- نوع هشدار
- پیام
- وضعیت رد شدن

## API Endpoints

### کاتالوگ
- `GET /api/checklist/catalogs/` - لیست آیتم‌های کاتالوگ
- `POST /api/checklist/catalogs/` - ایجاد آیتم جدید
- `GET /api/checklist/catalogs/{id}/` - جزئیات آیتم
- `PUT /api/checklist/catalogs/{id}/` - ویرایش آیتم
- `DELETE /api/checklist/catalogs/{id}/` - حذف آیتم
- `GET /api/checklist/catalogs/by_category/` - آیتم‌ها بر اساس دسته

### قالب‌ها
- `GET /api/checklist/templates/` - لیست قالب‌ها
- `POST /api/checklist/templates/` - ایجاد قالب
- `POST /api/checklist/templates/{id}/duplicate/` - کپی قالب

### ارزیابی‌ها
- `GET /api/checklist/evaluations/` - لیست ارزیابی‌ها
- `POST /api/checklist/evaluations/bulk_evaluate/` - ارزیابی دسته‌ای
- `GET /api/checklist/evaluations/summary/` - خلاصه وضعیت
- `GET /api/checklist/evaluations/pending_questions/` - سوالات در انتظار
- `POST /api/checklist/evaluations/{id}/answer_question/` - پاسخ به سوال

### هشدارها
- `GET /api/checklist/alerts/` - لیست هشدارها
- `POST /api/checklist/alerts/{id}/dismiss/` - رد کردن هشدار
- `POST /api/checklist/alerts/dismiss_bulk/` - رد کردن دسته‌ای

## نحوه استفاده

### 1. تعریف آیتم‌های کاتالوگ
```python
catalog_item = ChecklistCatalog.objects.create(
    title="بررسی فشار خون",
    category="physical_exam",
    priority="high",
    keywords=["فشار خون", "blood pressure", "BP"],
    question_template="آیا فشار خون بیمار اندازه‌گیری شده است؟"
)
```

### 2. ایجاد قالب
```python
template = ChecklistTemplate.objects.create(
    name="ویزیت عمومی",
    specialty="عمومی"
)
template.catalog_items.add(catalog_item)
```

### 3. ارزیابی ویزیت
```python
service = ChecklistEvaluationService()
results = service.evaluate_encounter(
    encounter_id=123,
    template_id=template.id
)
```

### 4. دریافت خلاصه وضعیت
```python
service = ChecklistService()
summary = service.get_evaluation_summary(encounter_id=123)
```

## تنظیمات

در فایل `settings_additions.py`:

```python
CHECKLIST_SETTINGS = {
    'CONFIDENCE_THRESHOLD': 0.6,
    'MAX_KEYWORDS_PER_ITEM': 20,
    'EVIDENCE_CONTEXT_LENGTH': 100,
    'ALERTS': {
        'ENABLE_REALTIME_ALERTS': True,
        'CRITICAL_ITEM_THRESHOLD': 0.3,
    }
}
```

## مجوزها

- `IsHealthcareProvider`: فقط کادر درمان
- `IsDoctor`: فقط پزشکان
- `CanManageChecklists`: مدیریت چک‌لیست‌ها
- `CanEvaluateChecklists`: ارزیابی چک‌لیست‌ها
- `IsEncounterParticipant`: شرکت‌کنندگان ویزیت
- `CanDismissAlerts`: رد کردن هشدارها

## وابستگی‌ها

- Django >= 3.2
- Django REST Framework
- PostgreSQL (برای ArrayField)
- اپ encounters (برای مدل Encounter)

## نکات مهم

1. این اپ به اپ `encounters` وابسته است و نیاز به وجود مدل `Encounter` دارد
2. از `ArrayField` PostgreSQL استفاده می‌کند، بنابراین نیاز به دیتابیس PostgreSQL است
3. برای عملکرد بهینه، از cache برای نتایج ارزیابی استفاده می‌شود
4. هشدارها به صورت real-time از طریق websocket قابل ارسال هستند