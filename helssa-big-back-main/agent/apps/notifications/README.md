# Notifications App

این اپلیکیشن یک API برای ارسال اعلان‌ها فراهم می‌کند.

## نصب
- فایل `deployment/settings_additions.py` را در تنظیمات پروژه merge کنید.
- فایل `deployment/urls_additions.py` را به `urls.py` پروژه merge کنید.

## API
- POST `/api/notifications/send/`

## امنیت
- احراز هویت JWT (Simple JWT)
- Rate limiting و permission `CanSendNotification`