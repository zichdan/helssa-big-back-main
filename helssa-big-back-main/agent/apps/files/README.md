# اپلیکیشن Files

مدیریت فایل‌های آپلود شده توسط کاربران بر اساس استانداردهای HELSSA.

## Endpoints
- `POST /api/files/stored-files/`: آپلود فایل جدید (multipart/form-data)
- `GET /api/files/stored-files/`: لیست فایل‌های کاربر
- `GET /api/files/stored-files/{id}/`: جزئیات فایل
- `DELETE /api/files/stored-files/{id}/`: حذف (soft delete)

## نصب
- افزودن `files.apps.FilesConfig` در تنظیمات (در `deployment/settings_additions.py` این اپ موجود است)
- افزودن URL ها از `deployment/urls_additions.py`

## امنیت
- نیازمند JWT (`IsAuthenticated`)
- محدودیت نرخ `StandardUserThrottle`

## مدل‌ها
- `StoredFile` بر پایه `FileAttachmentModel`