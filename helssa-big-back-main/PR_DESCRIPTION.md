## خلاصه تغییرات

این PR اپ جدید scheduler را اضافه می‌کند که مسئول مدیریت و زمان‌بندی وظایف Celery در سیستم است.

## ویژگی‌های اضافه شده

### مدل‌ها
- **TaskDefinition**: تعریف وظایف قابل اجرا
- **ScheduledTask**: وظایف زمان‌بندی شده  
- **TaskExecution**: سوابق اجرای وظایف
- **TaskLog**: لاگ‌های جزئی اجرا
- **TaskAlert**: هشدارهای مربوط به وظایف

### قابلیت‌ها
- ✅ پشتیبانی از انواع زمان‌بندی: یکبار، بازه‌ای، کرون، روزانه، هفتگی، ماهانه
- ✅ مانیتورینگ و ثبت کامل اجراها
- ✅ سیستم هشدار هوشمند
- ✅ API کامل با DRF
- ✅ رابط admin قدرتمند
- ✅ مدیریت retry و error handling
- ✅ آمار و گزارشات عملکرد

### Celery Tasks
- `execute_task`: اجرای وظایف
- `run_scheduled_task`: اجرای وظایف زمان‌بندی شده
- `cleanup_old_executions`: پاکسازی سوابق قدیمی
- `check_missing_executions`: بررسی وظایف اجرا نشده
- `monitor_task_performance`: پایش عملکرد
- `send_task_alerts`: ارسال هشدارها

### API Endpoints
- `/api/scheduler/definitions/` - مدیریت تعاریف وظایف
- `/api/scheduler/scheduled/` - مدیریت وظایف زمان‌بندی شده
- `/api/scheduler/executions/` - مشاهده سوابق اجرا
- `/api/scheduler/alerts/` - مدیریت هشدارها
- `/api/scheduler/statistics/` - آمار و گزارشات

## فایل‌های اضافه شده
- `scheduler/models.py` - مدل‌های داده
- `scheduler/tasks.py` - وظایف Celery
- `scheduler/serializers.py` - سریالایزرهای API
- `scheduler/views.py` - ویوهای API
- `scheduler/urls.py` - مسیرهای URL
- `scheduler/admin.py` - رابط ادمین
- `scheduler/settings.py` - تنظیمات اپ
- `scheduler/README.md` - مستندات
- `helssa/celery.py` - پیکربندی Celery برای پروژه

## نکات فنی
- از django-celery-beat برای scheduler استفاده می‌شود (اختیاری)
- پشتیبانی از صف‌های مختلف برای اولویت‌بندی
- لاگ‌گیری کامل برای debugging
- هندل کردن خطاها و retry mechanism

## تست
برای تست این قابلیت:
1. مایگریشن‌ها را اجرا کنید
2. Celery worker و beat را راه‌اندازی کنید
3. از طریق admin یا API وظایف جدید تعریف کنید

## Checklist
- [x] کد تمیز و خوانا
- [x] Docstring فارسی برای تمام توابع و کلاس‌ها
- [x] رعایت استانداردهای PEP 8
- [x] Type hints
- [x] مستندات کامل
- [ ] تست‌های واحد (در PR بعدی)
- [ ] Integration با سایر اپ‌ها (در PR بعدی)