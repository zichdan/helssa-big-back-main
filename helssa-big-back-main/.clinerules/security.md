# قوانین امنیتی پروژه هلسا

## احراز هویت (Authentication)

### استفاده از UnifiedUser
```python
# همیشه از UnifiedUser استفاده کنید
from django.contrib.auth import get_user_model

User = get_user_model()  # این UnifiedUser است

# بررسی نوع کاربر
if request.user.user_type == 'patient':
    # منطق بیمار
elif request.user.user_type == 'doctor':
    # منطق پزشک
```

### JWT Authentication
```python
# در settings.py
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
}

# در views
from rest_framework_simplejwt.authentication import JWTAuthentication

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def protected_view(request):
    pass
```

### OTP System
```python
from auth_otp.services import OTPService

# ارسال OTP
otp_service = OTPService()
success, result = otp_service.send_otp(
    phone_number='09123456789',
    purpose='login',
    ip_address=request.META.get('REMOTE_ADDR')
)

# تأیید OTP
success, result = otp_service.verify_otp(
    phone_number='09123456789',
    otp_code='123456',
    purpose='login'
)
```

## مجوزها (Authorization)

### Permission Classes
```python
from rest_framework.permissions import BasePermission

class IsPatient(BasePermission):
    """فقط بیماران"""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.user_type == 'patient'
        )

class IsDoctor(BasePermission):
    """فقط پزشکان"""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.user_type == 'doctor'
        )

class IsOwnerOrReadOnly(BasePermission):
    """مالک یا فقط خواندن"""
    def has_object_permission(self, request, view, obj):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return obj.user == request.user
```

### دسترسی پزشک به بیمار
```python
from unified_access.services import AccessService

# بررسی دسترسی
has_access = AccessService.check_doctor_access(
    doctor=request.user,
    patient=patient_user
)

if not has_access:
    return Response(
        {'error': 'شما به اطلاعات این بیمار دسترسی ندارید'},
        status=403
    )

# دریافت بیماران با دسترسی
patients = AccessService.get_accessible_patients(doctor=request.user)
```

## اعتبارسنجی ورودی (Input Validation)

### استفاده از Serializers
```python
from rest_framework import serializers

class SecureInputSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=11,
        validators=[
            RegexValidator(r'^09\d{9}$', 'شماره موبایل نامعتبر')
        ]
    )
    
    text_input = serializers.CharField(
        max_length=1000,
        help_text='حداکثر 1000 کاراکتر'
    )
    
    def validate_phone_number(self, value):
        # Sanitize input
        value = value.strip().replace(' ', '')
        
        # Additional validation
        if BlacklistedPhone.objects.filter(phone=value).exists():
            raise serializers.ValidationError('این شماره مسدود شده است')
        
        return value
    
    def validate(self, data):
        # Cross-field validation
        return data
```

### SQL Injection Prevention
```python
# ❌ بد - هرگز این کار را نکنید
query = f"SELECT * FROM users WHERE phone = '{phone}'"
cursor.execute(query)

# ✅ خوب - از ORM استفاده کنید
users = User.objects.filter(phone_number=phone)

# ✅ در صورت نیاز به raw SQL
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute(
        "SELECT * FROM users WHERE phone = %s",
        [phone]
    )
```

### XSS Prevention
```python
# در templates - auto-escape فعال است
{{ user_input }}

# اگر نیاز به HTML دارید
{{ trusted_html|safe }}  # فقط برای محتوای قابل اعتماد

# در API responses
from django.utils.html import escape
safe_text = escape(user_input)
```

## Rate Limiting

### محدودیت نرخ API
```python
from django.core.cache import cache
from functools import wraps

def rate_limit(key_prefix: str, limit: int, window: int):
    """
    محدودیت نرخ decorator
    
    Args:
        key_prefix: پیشوند کلید cache
        limit: تعداد مجاز
        window: پنجره زمانی (ثانیه)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # تولید کلید یکتا
            user_id = request.user.id if request.user.is_authenticated else 'anon'
            ip = request.META.get('REMOTE_ADDR', '')
            key = f"{key_prefix}:{user_id}:{ip}"
            
            # بررسی تعداد
            count = cache.get(key, 0)
            if count >= limit:
                return Response(
                    {
                        'error': 'rate_limit_exceeded',
                        'message': f'حداکثر {limit} درخواست در {window} ثانیه'
                    },
                    status=429
                )
            
            # افزایش شمارنده
            cache.set(key, count + 1, timeout=window)
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator

# استفاده
@api_view(['POST'])
@rate_limit('send_otp', limit=1, window=60)  # 1 در دقیقه
def send_otp(request):
    pass
```

### محدودیت OTP
```python
# در auth_otp محدودیت‌های زیر پیاده‌سازی شده:
# - 1 درخواست در دقیقه
# - 5 درخواست در ساعت
# - 10 درخواست در روز
# - مسدودسازی 24 ساعته بعد از 10 تلاش ناموفق
```

## مدیریت توکن

### Blacklist Management
```python
from auth_otp.services import AuthService

# مسدود کردن توکن
AuthService.blacklist_token(
    token=refresh_token,
    token_type='refresh',
    user=request.user,
    reason='User logout'
)

# بررسی blacklist
from auth_otp.models import TokenBlacklist
is_blacklisted = TokenBlacklist.is_blacklisted(token)
```

### Logout
```python
# خروج از یک دستگاه
AuthService.logout(
    user=request.user,
    refresh_token=refresh_token
)

# خروج از همه دستگاه‌ها
AuthService.logout(
    user=request.user,
    logout_all=True
)
```

## رمزنگاری

### رمزنگاری فیلدهای حساس
```python
from cryptography.fernet import Fernet
from django.conf import settings

class EncryptedField(models.TextField):
    """فیلد رمزنگاری شده"""
    
    def __init__(self, *args, **kwargs):
        self.cipher = Fernet(settings.ENCRYPTION_KEY)
        super().__init__(*args, **kwargs)
    
    def get_prep_value(self, value):
        if value is None:
            return value
        # رمزنگاری
        encrypted = self.cipher.encrypt(value.encode())
        return encrypted.decode()
    
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        # رمزگشایی
        decrypted = self.cipher.decrypt(value.encode())
        return decrypted.decode()

# استفاده
class PatientRecord(models.Model):
    sensitive_data = EncryptedField()
```

### هش کردن
```python
from django.contrib.auth.hashers import make_password, check_password

# هش کردن
hashed = make_password('sensitive_value')

# بررسی
is_valid = check_password('sensitive_value', hashed)
```

## Security Headers

```python
# در middleware
class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # HSTS (فقط در production)
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response
```

## File Upload Security

```python
import os
from django.core.exceptions import ValidationError

def validate_file_upload(file):
    """اعتبارسنجی فایل آپلود شده"""
    
    # بررسی حجم (حداکثر 10MB)
    max_size = 10 * 1024 * 1024
    if file.size > max_size:
        raise ValidationError('حجم فایل نباید بیشتر از 10 مگابایت باشد')
    
    # بررسی نوع فایل
    allowed_types = {
        'image': ['jpg', 'jpeg', 'png', 'gif'],
        'document': ['pdf', 'doc', 'docx'],
        'audio': ['mp3', 'wav', 'ogg']
    }
    
    ext = os.path.splitext(file.name)[1][1:].lower()
    if not any(ext in types for types in allowed_types.values()):
        raise ValidationError(f'فرمت {ext} مجاز نیست')
    
    # بررسی محتوا (Magic bytes)
    file_signatures = {
        b'\xFF\xD8\xFF': 'jpg',
        b'\x89\x50\x4E\x47': 'png',
        b'%PDF': 'pdf'
    }
    
    file.seek(0)
    file_header = file.read(8)
    file.seek(0)
    
    valid_signature = False
    for signature, file_type in file_signatures.items():
        if file_header.startswith(signature):
            valid_signature = True
            break
    
    if not valid_signature:
        raise ValidationError('فایل معتبر نیست')
    
    return True
```

## Audit Logging

```python
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType

def log_user_action(user, obj, action_flag, message=''):
    """ثبت فعالیت کاربر"""
    LogEntry.objects.create(
        user=user,
        content_type=ContentType.objects.get_for_model(obj),
        object_id=str(obj.pk),
        object_repr=str(obj),
        action_flag=action_flag,
        change_message=message
    )

# مثال استفاده
log_user_action(
    user=request.user,
    obj=patient_record,
    action_flag=CHANGE,
    message='دسترسی به سوابق پزشکی'
)
```

## چک‌لیست امنیتی

- [ ] از UnifiedUser استفاده شده
- [ ] JWT authentication اعمال شده
- [ ] Permission classes تعریف شده
- [ ] Input validation با serializer
- [ ] Rate limiting اعمال شده
- [ ] SQL injection prevention (ORM)
- [ ] XSS prevention
- [ ] CSRF protection فعال
- [ ] Security headers تنظیم شده
- [ ] File upload validation
- [ ] Sensitive data encrypted
- [ ] Audit logging فعال
- [ ] Error messages امن (بدون افشای اطلاعات)