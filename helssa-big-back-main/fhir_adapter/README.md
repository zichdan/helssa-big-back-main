# FHIR Adapter

اپلیکیشن FHIR Adapter برای تبدیل داده‌های داخلی سیستم هلسا به استاندارد FHIR و بالعکس.

## ویژگی‌ها

- پشتیبانی از منابع اصلی FHIR (Patient، Practitioner، Encounter، Observation و...)
- تبدیل دوطرفه بین مدل‌های Django و منابع FHIR
- سیستم نقشه‌برداری انعطاف‌پذیر
- اعتبارسنجی منابع FHIR
- پشتیبانی از Bundle ها
- لاگ‌گیری کامل عملیات‌های صادرات و واردات
- API RESTful برای مدیریت منابع FHIR

## نصب و راه‌اندازی

1. اپلیکیشن را به `INSTALLED_APPS` اضافه کنید:
```python
INSTALLED_APPS = [
    ...
    'fhir_adapter',
]
```

2. URLها را در فایل اصلی urls.py اضافه کنید:
```python
urlpatterns = [
    ...
    path('api/fhir/', include('fhir_adapter.urls')),
]
```

3. مایگریشن‌ها را اجرا کنید:
```bash
python manage.py makemigrations fhir_adapter
python manage.py migrate fhir_adapter
```

## استفاده

### تبدیل داده به FHIR

```python
# POST /api/fhir/transform/
{
    "source_model": "patient.PatientProfile",
    "source_id": "123",
    "target_resource_type": "Patient",
    "include_related": true
}
```

### واردات منبع FHIR

```python
# POST /api/fhir/import/
{
    "resource_type": "Patient",
    "resource_content": {
        "resourceType": "Patient",
        "id": "example",
        "name": [{
            "family": "احمدی",
            "given": ["علی"]
        }]
    },
    "update_existing": true
}
```

### جستجوی منابع FHIR

```python
# POST /api/fhir/search/
{
    "resource_type": "Patient",
    "internal_model": "patient.PatientProfile",
    "page": 1,
    "page_size": 20
}
```

## API Endpoints

- `GET /api/fhir/resources/` - لیست منابع FHIR
- `POST /api/fhir/resources/` - ایجاد منبع جدید
- `GET /api/fhir/resources/{resource_id}/` - دریافت یک منبع
- `PUT /api/fhir/resources/{resource_id}/` - به‌روزرسانی منبع
- `DELETE /api/fhir/resources/{resource_id}/` - حذف منبع
- `GET /api/fhir/resources/{resource_id}/history/` - تاریخچه منبع
- `POST /api/fhir/resources/validate/` - اعتبارسنجی منبع

## نقشه‌برداری‌ها

برای تعریف نقشه‌برداری جدید:

```python
from fhir_adapter.models import FHIRMapping

mapping = FHIRMapping.objects.create(
    source_model='patient.PatientProfile',
    target_resource_type='Patient',
    field_mappings={
        'user.first_name': 'name.0.given.0',
        'user.last_name': 'name.0.family',
        'national_id': 'identifier.0.value',
        'phone_number': 'telecom.0.value'
    },
    transformation_rules={
        'telecom.0.system': 'phone',
        'identifier.0.system': 'http://example.ir/nationalid'
    }
)
```

## تنظیمات

در فایل `settings.py` پروژه:

```python
# تنظیمات FHIR
FHIR_BASE_URL = 'https://api.example.com/fhir/'
FHIR_VERSION = 'R4'
FHIR_VALIDATION_ENABLED = True
FHIR_BUNDLE_MAX_SIZE = 100
FHIR_DEFAULT_PAGE_SIZE = 20
```

## توسعه

برای اضافه کردن پشتیبانی از منبع جدید FHIR:

1. نوع منبع را به `RESOURCE_TYPES` در مدل اضافه کنید
2. متد اعتبارسنجی مربوطه را در `FHIRValidator` پیاده‌سازی کنید
3. نقشه‌برداری پیش‌فرض را تعریف کنید