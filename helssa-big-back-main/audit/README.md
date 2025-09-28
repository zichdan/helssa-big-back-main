# اپ ممیزی (audit)

این اپ مسئول ثبت لاگ‌های ساختاریافته، Audit Trail و رویدادهای امنیتی طبق مستندات است.

## ویژگی‌ها
- مدل `AuditLog` برای ثبت رویدادها با فیلدهای: `timestamp`, `user`, `event_type`, `resource`, `action`, `result`, `ip_address`, `user_agent`, `session_id`, `metadata`
- مدل `SecurityEvent` برای رویدادهای امنیتی با فیلدهای: `event_type`, `severity`, `risk_score`, `result`, `details`
- سرویس‌های `AuditLogger` و `SecurityEventLogger`
- تنظیمات داخلی اپ در `audit/settings.py`

## استفاده

نمونه ثبت رویداد:
```python
from audit.services import AuditLogger

AuditLogger.log_event(
    event_type='authentication',
    action='LOGIN',
    result='success',
    resource='AUTH',
    user=request.user,
    request=request,
    metadata={'method': 'OTP'}
)
```

## تست

```bash
python manage.py test audit | cat
```

## نکات
- از `get_user_model()` برای ارجاع به `UnifiedUser` استفاده شده است.
- هیچ URL جدیدی اضافه نشده است.
- تنظیمات اپ درون خود اپ نگهداری می‌شود.