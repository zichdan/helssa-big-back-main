# اپلیکیشن SOAP

این اپ مسئول تولید و مدیریت گزارش‌های پزشکی استاندارد به فرمت SOAP است.

## وابستگی‌ها
- Django REST framework
- Simple JWT

توجه: طبق دستور، تنظیمات اپ در داخل اپ قرار دارد (`soap/settings.py`) و نیازی به تغییر `helssa/urls.py` نیست.

## Endpoints (درون اپ)
- POST `soap/generate/`: تولید گزارش SOAP
- GET `soap/formats/<report_id>/`: تولید خروجی Markdown از یک گزارش موجود

برای اتصال به روت پروژه می‌توانید در `helssa/urls.py`:

```python
from django.urls import include, path
urlpatterns += [ path('soap/', include('soap.urls')), ]
```

اما طبق دستور فعلاً تغییر در روت انجام نشده است.

## مدل‌ها
- `SOAPReport`: ذخیره گزارش‌های تولید شده

## امنیت و مجوز
- استفاده از `IsAuthenticated` و `IsDoctor` (محلی در `soap/permissions.py`)
- Rate limiting با دکوراتور `with_api_ingress`

## تست‌ها
تست‌های API به دلیل تناقضات زیر غیرفعال (skip) شده‌اند:
- عدم وجود `UnifiedUser` با فیلد `user_type`
- عدم افزودن DRF و SimpleJWT به `INSTALLED_APPS` در تنظیمات ریشه
- عدم درج مسیرهای اپ در `helssa/urls.py` (مطابق دستور)