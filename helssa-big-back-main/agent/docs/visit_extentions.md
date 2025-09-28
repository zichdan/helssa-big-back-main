# visit_extentions

- نقش: موتور تولید خروجی‌های ویزیت (گواهی استعلاجی)، لینک/QR اعتبارسنجی، ذخیره‌سازی و ارسال لینک دانلود
- مصرف‌کننده: `visit_management`
- عدم شمول: مدیریت نسخه‌نویسی، لاجیک ویزیت

## مدل‌ها
- `Certificate`: نگهداری اطلاعات گواهی استعلاجی، وضعیت ابطال، فایل PDF و لینک/QR

## سرویس‌ها
- PDF: تولید PDF با WeasyPrint از قالب HTML
- QR: تولید QR به‌صورت PNG و درج در PDF (به‌صورت Base64)
- Storage: ذخیره در MinIO/S3 و ساخت URL عمومی
- SMS: ارسال لینک دانلود با کاوه‌نگار

## Endpoint ها
- POST `/api/v1/visit-ext/certificates/` ایجاد گواهی (JWT، فقط پزشک)
- GET `/api/v1/visit-ext/certificates/{id}/` جزئیات (پزشک/بیمار)
- POST `/api/v1/visit-ext/certificates/{id}/revoke/` ابطال (پزشک)
- GET `/verify/certificate/{token}/` صفحه عمومی اعتبارسنجی (معتبر/نامعتبر)

## تنظیمات داخل اپ
- فایل `visit_extentions/settings_sample.py` شامل تنظیمات MinIO، Kavenegar، Throttle های DRF

## امنیت و استانداردها
- استفاده از `AUTH_USER_MODEL` برای کاربران (UnifiedUser)
- JWT + Rate limiting روی APIها
- Validation با Serializer ها
- ذخیره‌سازی ایمن روی MinIO با URL عمومی کنترل‌شده