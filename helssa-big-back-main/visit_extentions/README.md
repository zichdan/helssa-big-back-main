# visit_extentions

اپ «visit_extentions» موتور تولید و مدیریت رسانه‌های مرتبط با ویزیت را فراهم می‌کند:

- تولید گواهی استعلاجی (PDF)
- تولید و مدیریت لینک/QR اعتبارسنجی عمومی
- ذخیره‌سازی فایل‌ها در MinIO/S3
- ارسال لینک دانلود از طریق کاوه‌نگار

نکته: این اپ صرفاً موتور تولید/ذخیره/اعتبارسنجی است و مدیریت ویزیت توسط اپ دیگر انجام می‌شود.

## نصب

1. وابستگی‌ها در `requirements.txt` موجود است: `weasyprint`, `qrcode`, `django-storages`, `kavenegar`.
2. تنظیمات پیشنهادی را از `visit_extentions/settings_sample.py` به `settings.py` اضافه کنید.
3. اپ را به `INSTALLED_APPS` اضافه کنید: `visit_extentions`.

## API ها

- POST `/api/v1/visit-ext/certificates/` ایجاد گواهی (JWT، فقط پزشک)
- GET `/api/v1/visit-ext/certificates/{id}/` دریافت جزئیات (پزشک/بیمار)
- POST `/api/v1/visit-ext/certificates/{id}/revoke/` ابطال گواهی (پزشک)
- GET `/verify/certificate/{token}/` صفحه اعتبارسنجی عمومی (بدون احراز هویت)

## مدل‌ها

- `Certificate`: نگه‌داری اطلاعات گواهی، وضعیت ابطال، لینک اعتبارسنجی، فایل PDF در MinIO

## تست

- تست‌ها در `visit_extentions/tests/` اضافه می‌شوند.