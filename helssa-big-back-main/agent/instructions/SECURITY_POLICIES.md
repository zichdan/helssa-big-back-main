# سیاست‌های امنیتی پلتفرم هلسا

## نمای کلی

این سند سیاست‌های امنیتی الزامی برای تمام اپلیکیشن‌های پلتفرم هلسا را تعریف می‌کند. این سیاست‌ها باید در تمام اپ‌ها بدون استثناء رعایت شوند.

## 1. احراز هویت یکپارچه (Unified Authentication)

### 1.1 مدل کاربر

- **الزامی**: استفاده از `unified_auth.UnifiedUser`
- **منع**: ایجاد مدل کاربر جدید
- **نوع کاربران**: patient, doctor, admin

```python
# صحیح
from unified_auth.models import UnifiedUser
from django.contrib.auth import get_user_model

User = get_user_model()  # UnifiedUser

# غلط
from django.contrib.auth.models import User  # منع
```

### 1.2 JWT Authentication

- **Access Token**: 5 دقیقه اعتبار
- **Refresh Token**: 7 روز اعتبار
- **Blacklist**: امکان باطل کردن توکن‌ها

```python
# تنظیمات الزامی
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

## 2. سیستم OTP و کاوه‌نگار

### 2.1 تولید OTP

- **طول کد**: 6 رقم عددی
- **الگوریتم**: Random number generation
- **منع**: کدهای متوالی یا قابل حدس

```python
import secrets

def generate_otp():
    return f"{secrets.randbelow(900000) + 100000:06d}"
```

### 2.2 اعتبار OTP

- **مدت زمان**: 3 دقیقه دقیقاً
- **تعداد تلاش**: حداکثر 3 بار
- **منع**: استفاده مجدد کد استفاده شده

### 2.3 Rate Limiting OTP

- **ارسال**: حداکثر 1 درخواست در دقیقه
- **روزانه**: حداکثر 5 درخواست در ساعت  
- **مسدودسازی**: 24 ساعت پس از 10 تلاش ناموفق

```python
# الگوی پیاده‌سازی
from django.core.cache import cache

def check_otp_rate_limit(phone_number):
    minute_key = f"otp_minute_{phone_number}"
    hour_key = f"otp_hour_{phone_number}"
    
    minute_count = cache.get(minute_key, 0)
    hour_count = cache.get(hour_key, 0)
    
    if minute_count >= 1:
        return False, "حداکثر 1 درخواست در دقیقه"
    if hour_count >= 5:
        return False, "حداکثر 5 درخواست در ساعت"
    
    return True, "OK"
```

### 2.4 یکپارچگی با کاوه‌نگار

- **API Key**: در متغیر محیطی `KAVENEGAR_API_KEY`
- **Template**: استفاده از template مشخص
- **خطاها**: لاگ تمام خطاهای ارسال

```python
# الگوی صحیح
from kavenegar import KavenegarAPI
from django.conf import settings

api = KavenegarAPI(settings.KAVENEGAR_API_KEY)
result = api.sms_send({
    'receptor': phone_number,
    'token': otp_code,
    'template': 'verify'  # template ثبت شده
})
```

## 3. تفکیک نقش‌ها (Role-Based Access Control)

### 3.1 نقش‌های تعریف شده

- **patient**: بیمار عادی
- **doctor**: پزشک معالج
- **admin**: مدیر سیستم

### 3.2 دسترسی‌های بیمار

```python
PATIENT_PERMISSIONS = [
    'view_own_profile',
    'update_own_profile', 
    'create_visit_request',
    'view_own_visits',
    'chat_with_ai',
    'generate_access_code',  # برای دسترسی پزشک
    'view_own_wallet',
    'charge_wallet'
]
```

### 3.3 دسترسی‌های پزشک

```python
DOCTOR_PERMISSIONS = [
    'view_own_profile',
    'update_own_profile',
    'view_patients_with_access',  # فقط با کد دسترسی
    'access_patient_data',        # موقت
    'create_prescription',
    'view_doctor_dashboard',
    'manage_visit_queue',
    'generate_medical_reports'
]
```

### 3.4 الگوی بررسی دسترسی

```python
from rest_framework.permissions import BasePermission

class PatientOnlyPermission(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.user_type == 'patient'
        )

class DoctorOnlyPermission(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.user_type == 'doctor'
        )
```

## 4. دسترسی موقت پزشک (Unified Access)

### 4.1 تولید کد دسترسی

- **فقط بیمار**: می‌تواند کد تولید کند
- **محدودیت**: حداکثر 3 کد فعال همزمان
- **QR Code**: برای راحتی استفاده

### 4.2 تایید کد توسط پزشک

- **بررسی**: کد معتبر و منقضی نشده
- **Session**: ایجاد session با UUID منحصر به فرد
- **محدودیت زمانی**: حداکثر 24 ساعت

### 4.3 مدیریت Session

```python
class AccessSession:
    # خصوصیات الزامی
    session_id = models.UUIDField(unique=True)
    doctor = models.ForeignKey(UnifiedUser, related_name='doctor_sessions')
    patient = models.ForeignKey(UnifiedUser, related_name='patient_sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    # Audit fields
    doctor_ip = models.GenericIPAddressField()
    user_agent = models.TextField()
```

### 4.4 Audit Logging

```python
# ثبت اجباری تمام دسترسی‌ها
class AccessLog:
    session = models.ForeignKey(AccessSession)
    action = models.CharField(max_length=100)  # 'view_profile', 'access_chats'
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField()
    ip_address = models.GenericIPAddressField()
```

## 5. اعتبارسنجی و Validation

### 5.1 ورودی‌های API

```python
# الگوی استاندارد
from rest_framework import serializers

class StandardAPISerializer(serializers.Serializer):
    def validate(self, data):
        # بررسی‌های امنیتی
        if not self.context['request'].user.is_authenticated:
            raise serializers.ValidationError("Authentication required")
        
        return data
```

### 5.2 SQL Injection Prevention

- **الزامی**: استفاده از Django ORM
- **منع**: Raw SQL queries
- **استثناء**: فقط با Prepared Statements

```python
# صحیح
User.objects.filter(phone_number=phone)

# غلط
cursor.execute(f"SELECT * FROM users WHERE phone='{phone}'")
```

### 5.3 XSS Prevention

- **Template**: auto-escape فعال
- **JSON**: استفاده از safe serializers
- **Headers**: CSP headers

```python
# تنظیمات الزامی
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
```

## 6. رمزنگاری داده‌ها

### 6.1 داده‌های حساس

- **فیلدهای پزشکی**: رمزنگاری در دیتابیس
- **شماره موبایل**: هش شده ذخیره
- **پیام‌ها**: End-to-End encryption

```python
from cryptography.fernet import Fernet

class EncryptedField(models.TextField):
    def get_prep_value(self, value):
        if value is None:
            return value
        return encrypt_data(value)
    
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return decrypt_data(value)
```

### 6.2 API Communications

- **HTTPS**: اجباری در production
- **TLS 1.3**: حداقل نسخه
- **Certificate Pinning**: برای mobile apps

## 7. Rate Limiting و DDoS Protection

### 7.1 API Rate Limits

```python
# تنظیمات rate limiting
RATE_LIMITS = {
    'login': '5/minute',
    'otp_send': '1/minute', 
    'api_calls': '100/minute',
    'chat_ai': '20/minute',
    'file_upload': '10/minute'
}
```

### 7.2 IP-based Protection

- **Failed Login**: مسدودسازی IP پس از 10 تلاش ناموفق
- **Suspicious Activity**: تشخیص الگوهای مشکوک
- **Whitelist**: IP های مجاز برای admin

## 8. Session Management

### 8.1 خصوصیات Session

- **Timeout**: 30 دقیقه عدم فعالیت
- **Concurrent Sessions**: حداکثر 3 session همزمان
- **Device Tracking**: ثبت device و location

### 8.2 Logout Policies

- **Manual Logout**: باطل کردن همه sessions
- **Automatic**: logout در تغییر password
- **Remote Logout**: امکان logout از دستگاه‌های دیگر

## 9. File Upload Security

### 9.1 محدودیت‌های فایل

```python
ALLOWED_FILE_TYPES = {
    'image': ['jpg', 'jpeg', 'png'],
    'audio': ['mp3', 'wav', 'ogg'],
    'document': ['pdf']
}

MAX_FILE_SIZE = {
    'image': 5 * 1024 * 1024,    # 5MB
    'audio': 50 * 1024 * 1024,   # 50MB  
    'document': 10 * 1024 * 1024  # 10MB
}
```

### 9.2 Virus Scanning

- **اجباری**: اسکن تمام فایل‌های آپلود شده
- **Quarantine**: فایل‌های مشکوک
- **Cleanup**: حذف خودکار فایل‌های قدیمی

## 10. Compliance و Standards

### 10.1 HIPAA Compliance

- **Data Encryption**: At rest and in transit
- **Access Controls**: Role-based access
- **Audit Logs**: تمام دسترسی‌ها ثبت شود
- **Backup**: رمزنگاری شده

### 10.2 GDPR Compliance

- **Right to Delete**: حذف کامل داده‌ها
- **Data Portability**: امکان export داده‌ها
- **Consent Management**: ثبت رضایت‌ها

## 11. Monitoring و Incident Response

### 11.1 Security Monitoring

```python
# Events قابل نظارت
SECURITY_EVENTS = [
    'failed_login_attempts',
    'privilege_escalation', 
    'unusual_api_usage',
    'data_access_violations',
    'suspicious_file_uploads'
]
```

### 11.2 Incident Response

1. **Detection**: تشخیص خودکار
2. **Alert**: اطلاع‌رسانی فوری
3. **Isolation**: جداسازی سیستم آلوده
4. **Investigation**: بررسی علت
5. **Recovery**: بازیابی سیستم
6. **Documentation**: گزارش کامل

## 12. Security Headers

### 12.1 الزامی برای تمام responses

```python
SECURE_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Content-Security-Policy': "default-src 'self'",
    'Referrer-Policy': 'strict-origin-when-cross-origin'
}
```

## 13. Password Policies (فقط برای admin users)

### 13.1 الزامات رمز عبور

- **طول**: حداقل 12 کاراکتر
- **پیچیدگی**: ترکیب حروف، اعداد، نمادها
- **History**: عدم تکرار 5 رمز قبلی
- **Expiry**: تغییر هر 90 روز

## اجرای سیاست‌ها

### چک‌لیست اجرا

- [ ] تمام endpoints از unified_auth استفاده می‌کنند
- [ ] OTP rate limiting پیاده‌سازی شده
- [ ] Role-based permissions تعریف شده
- [ ] Session management صحیح است
- [ ] Audit logging فعال است
- [ ] Security headers تنظیم شده
- [ ] File upload restrictions اعمال شده
- [ ] Error handling امن است

### نکات مهم

1. **عدم انحراف**: هیچ انحراف از این سیاست‌ها مجاز نیست
2. **ثبت تغییرات**: هر تغیری در LOG.md ثبت شود
3. **Security Review**: کد قبل از deploy بررسی شود
4. **Regular Updates**: سیاست‌ها به‌طور مداوم به‌روزرسانی شوند

---

**نسخه**: 1.0.0  
**تاریخ ایجاد**: {{CREATION_DATE}}  
**تأیید شده توسط**: Mother Agent
**وضعیت**: الزامی برای تمام اپ‌ها
