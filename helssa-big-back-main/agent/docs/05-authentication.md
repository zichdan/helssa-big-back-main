# 🔐 احراز هویت یکپارچه HELSSA

## 📋 فهرست مطالب

- [معرفی سیستم احراز هویت](## 🎯 معرفی سیستم احراز هویت)
- [معماری احراز هویت](## 🏗️ معماری احراز هویت)
- [مدل‌های داده](## 📊 مدل‌های داده)
- [جریان احراز هویت](## 🔄 جریان احراز هویت)
- [پیاده‌سازی JWT](## 🔒 پیاده‌سازی JWT)
- [سیستم OTP](## 🔒 سیستم OTP)
- [مدیریت نقش‌ها (RBAC)](## 🔒 مدیریت نقش‌ها (RBAC))
- [امنیت و بهترین شیوه‌ها](## 🔒 امنیت و بهترین شیوه‌ها)

---

## 🎯 معرفی سیستم احراز هویت

سیستم احراز هویت یکپارچه HELSSA یک راهکار امن و مقیاس‌پذیر برای مدیریت هویت کاربران در تمام سرویس‌های پلتفرم است.

### ویژگی‌های کلیدی

- ✅ **ورود یکپارچه** برای بیماران و پزشکان
- ✅ **احراز هویت دو مرحله‌ای** با OTP
- ✅ **مدیریت نقش‌ها** (RBAC) پیشرفته
- ✅ **JWT Tokens** با Refresh Token
- ✅ **Rate Limiting** برای جلوگیری از حملات
- ✅ **Session Management** هوشمند
- ✅ **Audit Logging** کامل

## 🏗️ معماری احراز هویت

```python
graph TB
    subgraph "Client Layer"
        WEB[Web App]
        MOB[Mobile App]
        API[API Client]
    end
    
    subgraph "Auth Gateway"
        GW[API Gateway]
        MW[Auth Middleware]
        RL[Rate Limiter]
    end
    
    subgraph "Auth Services"
        LOGIN[Login Service]
        REG[Register Service]
        OTP[OTP Service]
        JWT[JWT Service]
        RBAC[RBAC Service]
    end
    
    subgraph "Data Layer"
        USER[(User DB)]
        REDIS[(Redis Cache)]
        AUDIT[(Audit Logs)]
    end
    
    WEB --> GW
    MOB --> GW
    API --> GW
    
    GW --> MW
    MW --> RL
    RL --> LOGIN
    RL --> REG
    
    LOGIN --> JWT
    LOGIN --> OTP
    REG --> OTP
    
    JWT --> REDIS
    OTP --> REDIS
    RBAC --> USER
    
    All --> AUDIT
```

## 📊 مدل‌های داده

### UnifiedUser Model

```python
# unified_auth/models.py
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
import uuid

class UnifiedUser(AbstractBaseUser, PermissionsMixin):
    """مدل کاربر یکپارچه برای بیماران و پزشکان"""
    
    # شناسه‌ها
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=11, unique=True, db_index=True)
    email = models.EmailField(unique=True, null=True, blank=True, db_index=True)
    national_id = models.CharField(max_length=10, unique=True, null=True, blank=True)
    
    # اطلاعات پایه
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=1,
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        null=True
    )
    
    # نقش‌ها
    USER_TYPES = [
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('admin', 'Admin'),
        ('staff', 'Staff')
    ]
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='patient')
    
    # وضعیت
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # تنظیمات امنیتی
    two_factor_enabled = models.BooleanField(default=False)
    failed_login_attempts = models.IntegerField(default=0)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_device = models.CharField(max_length=255, null=True, blank=True)
    
    # زمان‌ها
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'unified_users'
        indexes = [
            models.Index(fields=['phone_number', 'is_active']),
            models.Index(fields=['email', 'is_active']),
            models.Index(fields=['user_type', 'is_active']),
        ]
```

### UserProfile Models

```python
# unified_auth/models.py

class PatientProfile(models.Model):
    """پروفایل اختصاصی بیمار"""
    user = models.OneToOneField(UnifiedUser, on_delete=models.CASCADE, related_name='patient_profile')
    medical_record_number = models.CharField(max_length=20, unique=True)
    blood_type = models.CharField(max_length=5, null=True, blank=True)
    allergies = models.JSONField(default=list)
    chronic_conditions = models.JSONField(default=list)
    emergency_contact = models.JSONField(default=dict)
    insurance_info = models.JSONField(default=dict)

class DoctorProfile(models.Model):
    """پروفایل اختصاصی پزشک"""
    user = models.OneToOneField(UnifiedUser, on_delete=models.CASCADE, related_name='doctor_profile')
    medical_license_number = models.CharField(max_length=20, unique=True)
    specialty = models.CharField(max_length=100)
    sub_specialty = models.CharField(max_length=100, null=True, blank=True)
    medical_council_number = models.CharField(max_length=20)
    education = models.JSONField(default=list)
    experience_years = models.IntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=0)
    bio = models.TextField(null=True, blank=True)
    languages = models.JSONField(default=list)
    working_hours = models.JSONField(default=dict)
```

### Session & Token Models

```python
class UserSession(models.Model):
    """مدیریت نشست‌های کاربر"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(UnifiedUser, on_delete=models.CASCADE, related_name='sessions')
    
    # Token Info
    access_token = models.TextField()
    refresh_token = models.TextField()
    token_version = models.IntegerField(default=1)
    
    # Session Info
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=500)
    device_id = models.CharField(max_length=100, null=True, blank=True)
    device_type = models.CharField(max_length=50)  # web, ios, android
    
    # Security
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    # Metadata
    location = models.JSONField(null=True, blank=True)  # GeoIP data
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_sessions'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['expires_at']),
        ]
```

## 🔄 جریان احراز هویت

### 1. ثبت‌نام کاربر جدید

```python
# unified_auth/services/registration_service.py
from typing import Dict, Optional
import re

class RegistrationService:
    """سرویس ثبت‌نام کاربران"""
    
    def __init__(self):
        self.otp_service = OTPService()
        self.sms_service = SMSService()
        
    async def register_user(
        self,
        phone_number: str,
        email: Optional[str],
        first_name: str,
        last_name: str,
        user_type: str = 'patient',
        **extra_fields
    ) -> Dict:
        """ثبت‌نام کاربر جدید"""
        
        # اعتبارسنجی شماره تلفن
        if not self._validate_phone_number(phone_number):
            raise ValidationError("شماره تلفن نامعتبر است")
            
        # بررسی تکراری نبودن
        if await UnifiedUser.objects.filter(phone_number=phone_number).exists():
            raise ValidationError("این شماره تلفن قبلاً ثبت شده است")
            
        # ایجاد کاربر
        user = await UnifiedUser.objects.create(
            phone_number=phone_number,
            email=email,
            first_name=first_name,
            last_name=last_name,
            user_type=user_type,
            is_active=False,  # غیرفعال تا تایید OTP
            **extra_fields
        )
        
        # ارسال OTP
        otp_code = await self.otp_service.generate_otp(phone_number)
        await self.sms_service.send_otp(phone_number, otp_code)
        
        return {
            'user_id': str(user.id),
            'phone_number': phone_number,
            'message': 'کد تایید ارسال شد',
            'otp_expires_in': 120  # seconds
        }
        
    def _validate_phone_number(self, phone: str) -> bool:
        """اعتبارسنجی شماره موبایل ایران"""
        pattern = r'^09[0-9]{9}$'
        return bool(re.match(pattern, phone))
```

### 2. ورود با OTP

```python
# unified_auth/services/login_service.py
from datetime import datetime, timedelta
import jwt

class LoginService:
    """سرویس ورود کاربران"""
    
    def __init__(self):
        self.otp_service = OTPService()
        self.jwt_service = JWTService()
        self.session_service = SessionService()
        
    async def login_request(self, phone_number: str) -> Dict:
        """درخواست ورود و ارسال OTP"""
        
        # بررسی وجود کاربر
        try:
            user = await UnifiedUser.objects.get(
                phone_number=phone_number,
                is_active=True
            )
        except UnifiedUser.DoesNotExist:
            raise AuthenticationError("کاربر یافت نشد")
            
        # بررسی تعداد تلاش‌های ناموفق
        if user.failed_login_attempts >= 5:
            lockout_time = user.updated_at + timedelta(minutes=30)
            if datetime.now() < lockout_time:
                raise AuthenticationError(
                    f"حساب شما موقتاً قفل شده است. لطفاً {lockout_time} دوباره تلاش کنید"
                )
            else:
                user.failed_login_attempts = 0
                await user.save()
                
        # ارسال OTP
        otp_code = await self.otp_service.generate_otp(phone_number)
        await self.sms_service.send_otp(phone_number, otp_code)
        
        return {
            'phone_number': phone_number,
            'message': 'کد تایید ارسال شد',
            'otp_expires_in': 120
        }
        
    async def verify_login(
        self,
        phone_number: str,
        otp_code: str,
        device_info: Dict
    ) -> Dict:
        """تایید OTP و صدور توکن"""
        
        # تایید OTP
        if not await self.otp_service.verify_otp(phone_number, otp_code):
            user = await UnifiedUser.objects.get(phone_number=phone_number)
            user.failed_login_attempts += 1
            await user.save()
            raise AuthenticationError("کد تایید نامعتبر است")
            
        # بازیابی کاربر
        user = await UnifiedUser.objects.get(phone_number=phone_number)
        
        # به‌روزرسانی اطلاعات ورود
        user.last_login = datetime.now()
        user.last_login_ip = device_info.get('ip_address')
        user.last_login_device = device_info.get('user_agent')
        user.failed_login_attempts = 0
        
        if not user.is_verified:
            user.is_verified = True
            user.verified_at = datetime.now()
            
        await user.save()
        
        # ایجاد توکن‌ها
        tokens = await self.jwt_service.create_tokens(user)
        
        # ایجاد نشست
        session = await self.session_service.create_session(
            user=user,
            tokens=tokens,
            device_info=device_info
        )
        
        return {
            'user': self._serialize_user(user),
            'tokens': tokens,
            'session_id': str(session.id)
        }
```

## 🎫 پیاده‌سازی JWT

### JWT Service

```python
# unified_auth/services/jwt_service.py
from datetime import datetime, timedelta
import jwt
from django.conf import settings

class JWTService:
    """سرویس مدیریت JWT tokens"""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = 'HS256'
        self.access_token_lifetime = timedelta(minutes=15)
        self.refresh_token_lifetime = timedelta(days=7)
        
    async def create_tokens(self, user: UnifiedUser) -> Dict[str, str]:
        """ایجاد Access و Refresh tokens"""
        
        # Payload مشترک
        base_payload = {
            'user_id': str(user.id),
            'phone_number': user.phone_number,
            'user_type': user.user_type,
            'is_verified': user.is_verified,
            'iat': datetime.utcnow(),
        }
        
        # Access Token
        access_payload = {
            **base_payload,
            'type': 'access',
            'exp': datetime.utcnow() + self.access_token_lifetime,
            'permissions': await self._get_user_permissions(user)
        }
        access_token = jwt.encode(access_payload, self.secret_key, self.algorithm)
        
        # Refresh Token
        refresh_payload = {
            **base_payload,
            'type': 'refresh',
            'exp': datetime.utcnow() + self.refresh_token_lifetime,
            'token_version': await self._get_token_version(user)
        }
        refresh_token = jwt.encode(refresh_payload, self.secret_key, self.algorithm)
        
        # ذخیره در Redis برای blacklisting
        await self._store_tokens_in_cache(user.id, access_token, refresh_token)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': int(self.access_token_lifetime.total_seconds())
        }
        
    async def verify_token(self, token: str, token_type: str = 'access') -> Dict:
        """اعتبارسنجی توکن"""
        
        try:
            # Decode token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # بررسی نوع توکن
            if payload.get('type') != token_type:
                raise jwt.InvalidTokenError("Invalid token type")
                
            # بررسی blacklist
            if await self._is_token_blacklisted(token):
                raise jwt.InvalidTokenError("Token has been revoked")
                
            # بررسی token version برای refresh tokens
            if token_type == 'refresh':
                user_id = payload.get('user_id')
                current_version = await self._get_token_version(user_id)
                if payload.get('token_version') != current_version:
                    raise jwt.InvalidTokenError("Token version mismatch")
                    
            return payload
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("توکن منقضی شده است")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"توکن نامعتبر است: {str(e)}")
            
    async def refresh_tokens(self, refresh_token: str) -> Dict[str, str]:
        """تمدید توکن‌ها با استفاده از Refresh Token"""
        
        # اعتبارسنجی refresh token
        payload = await self.verify_token(refresh_token, 'refresh')
        
        # بازیابی کاربر
        user = await UnifiedUser.objects.get(id=payload['user_id'])
        
        # ایجاد توکن‌های جدید
        new_tokens = await self.create_tokens(user)
        
        # ابطال توکن‌های قدیمی
        await self._revoke_tokens(user.id)
        
        return new_tokens
```

### JWT Middleware

```python
# unified_auth/middleware/jwt_middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse

class JWTAuthenticationMiddleware(MiddlewareMixin):
    """Middleware برای احراز هویت JWT"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_service = JWTService()
        self.exempt_paths = [
            '/api/auth/login/',
            '/api/auth/register/',
            '/api/auth/verify-otp/',
            '/api/health/',
        ]
        
    def process_request(self, request):
        """بررسی و اعتبارسنجی JWT در هر درخواست"""
        
        # مسیرهای معاف از احراز هویت
        if any(request.path.startswith(path) for path in self.exempt_paths):
            return None
            
        # استخراج توکن از هدر
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse(
                {'error': 'Authorization header missing or invalid'},
                status=401
            )
            
        token = auth_header.split(' ')[1]
        
        try:
            # اعتبارسنجی توکن
            payload = self.jwt_service.verify_token(token)
            
            # افزودن اطلاعات کاربر به request
            request.jwt_payload = payload
            request.user_id = payload['user_id']
            request.user_type = payload['user_type']
            request.permissions = payload.get('permissions', [])
            
            # به‌روزرسانی last activity
            asyncio.create_task(
                self._update_last_activity(payload['user_id'])
            )
            
        except AuthenticationError as e:
            return JsonResponse(
                {'error': str(e)},
                status=401
            )
            
        return None
```

## 📱 سیستم OTP

### OTP Service

```python
# unified_auth/services/otp_service.py
import random
import string
from datetime import datetime, timedelta
from django.core.cache import cache

class OTPService:
    """سرویس مدیریت OTP"""
    
    def __init__(self):
        self.otp_length = 6
        self.otp_lifetime = 120  # seconds
        self.max_attempts = 3
        self.resend_cooldown = 60  # seconds
        
    async def generate_otp(self, phone_number: str) -> str:
        """تولید کد OTP"""
        
        # بررسی cooldown
        cooldown_key = f"otp_cooldown:{phone_number}"
        if cache.get(cooldown_key):
            raise ValidationError(
                f"لطفاً {self.resend_cooldown} ثانیه صبر کنید"
            )
            
        # تولید کد
        if settings.DEBUG:
            otp_code = "123456"  # برای محیط توسعه
        else:
            otp_code = ''.join(
                random.choices(string.digits, k=self.otp_length)
            )
            
        # ذخیره در کش
        cache_key = f"otp:{phone_number}"
        cache_data = {
            'code': otp_code,
            'attempts': 0,
            'created_at': datetime.utcnow().isoformat()
        }
        
        cache.set(cache_key, cache_data, self.otp_lifetime)
        cache.set(cooldown_key, True, self.resend_cooldown)
        
        # لاگ برای audit
        await self._log_otp_generation(phone_number)
        
        return otp_code
        
    async def verify_otp(
        self,
        phone_number: str,
        otp_code: str
    ) -> bool:
        """اعتبارسنجی کد OTP"""
        
        cache_key = f"otp:{phone_number}"
        cached_data = cache.get(cache_key)
        
        if not cached_data:
            return False
            
        # بررسی تعداد تلاش‌ها
        if cached_data['attempts'] >= self.max_attempts:
            cache.delete(cache_key)
            raise ValidationError("تعداد تلاش‌ها بیش از حد مجاز")
            
        # بررسی کد
        if cached_data['code'] != otp_code:
            cached_data['attempts'] += 1
            cache.set(cache_key, cached_data, self.otp_lifetime)
            return False
            
        # کد صحیح - حذف از کش
        cache.delete(cache_key)
        cache.delete(f"otp_cooldown:{phone_number}")
        
        # لاگ برای audit
        await self._log_otp_verification(phone_number, True)
        
        return True
```

### SMS Integration

```python
# unified_auth/services/sms_service.py
from kavenegar import KavenegarAPI

class SMSService:
    """سرویس ارسال پیامک"""
    
    def __init__(self):
        self.api = KavenegarAPI(settings.KAVENEGAR_API_KEY)
        self.sender = settings.KAVENEGAR_SENDER
        
    async def send_otp(self, phone_number: str, otp_code: str) -> bool:
        """ارسال پیامک OTP"""
        
        try:
            # استفاده از template کاوه‌نگار
            response = self.api.verify_lookup({
                'receptor': phone_number,
                'token': otp_code,
                'template': 'helssa-otp'
            })
            
            # لاگ ارسال موفق
            await self._log_sms_sent(
                phone_number,
                'otp',
                response['messageid']
            )
            
            return True
            
        except Exception as e:
            # لاگ خطا
            await self._log_sms_failed(phone_number, str(e))
            
            # Fallback به پیامک معمولی
            return await self._send_regular_sms(
                phone_number,
                f"کد تایید HELSSA: {otp_code}"
            )
```

## 👥 مدیریت نقش‌ها (RBAC)

### Role & Permission Models

```python
# unified_auth/models.py

class Role(models.Model):
    """نقش‌های سیستم"""
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    permissions = models.ManyToManyField('Permission', related_name='roles')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'auth_roles'

class Permission(models.Model):
    """مجوزهای سیستم"""
    name = models.CharField(max_length=100, unique=True)
    codename = models.CharField(max_length=100, unique=True)
    resource = models.CharField(max_length=50)  # e.g., 'patient_record'
    action = models.CharField(max_length=50)    # e.g., 'read', 'write'
    description = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'auth_permissions'
        unique_together = [['resource', 'action']]

class UserRole(models.Model):
    """ارتباط کاربر و نقش"""
    user = models.ForeignKey(UnifiedUser, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(
        UnifiedUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_roles'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'user_roles'
        unique_together = [['user', 'role']]
```

### RBAC Service

```python
# unified_auth/services/rbac_service.py

class RBACService:
    """سرویس مدیریت دسترسی‌ها"""
    
    def __init__(self):
        self.cache = get_redis_client()
        
    async def check_permission(
        self,
        user_id: str,
        resource: str,
        action: str
    ) -> bool:
        """بررسی دسترسی کاربر"""
        
        # بررسی کش
        cache_key = f"perms:{user_id}:{resource}:{action}"
        cached_result = await self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result == '1'
            
        # بازیابی نقش‌های کاربر
        user_roles = await UserRole.objects.filter(
            user_id=user_id,
            role__is_active=True
        ).select_related('role').all()
        
        # بررسی expire date
        active_roles = [
            ur.role for ur in user_roles
            if not ur.expires_at or ur.expires_at > timezone.now()
        ]
        
        # بررسی مجوزها
        has_permission = await Permission.objects.filter(
            roles__in=active_roles,
            resource=resource,
            action=action
        ).exists()
        
        # ذخیره در کش
        await self.cache.setex(
            cache_key,
            300,  # 5 minutes
            '1' if has_permission else '0'
        )
        
        return has_permission
        
    async def assign_role(
        self,
        user_id: str,
        role_name: str,
        assigned_by_id: str,
        expires_at: Optional[datetime] = None
    ) -> UserRole:
        """اختصاص نقش به کاربر"""
        
        role = await Role.objects.get(name=role_name)
        
        user_role, created = await UserRole.objects.update_or_create(
            user_id=user_id,
            role=role,
            defaults={
                'assigned_by_id': assigned_by_id,
                'expires_at': expires_at
            }
        )
        
        # پاک کردن کش
        await self._clear_user_permission_cache(user_id)
        
        # Audit log
        await self._log_role_assignment(
            user_id,
            role_name,
            assigned_by_id,
            created
        )
        
        return user_role
```

### Permission Decorators

```python
# unified_auth/decorators.py

def require_permission(resource: str, action: str):
    """دکوراتور بررسی دسترسی"""
    
    def decorator(view_func):
        @wraps(view_func)
        async def wrapped_view(request, *args, **kwargs):
            # بررسی احراز هویت
            if not hasattr(request, 'user_id'):
                return JsonResponse(
                    {'error': 'Authentication required'},
                    status=401
                )
                
            # بررسی دسترسی
            rbac_service = RBACService()
            has_permission = await rbac_service.check_permission(
                request.user_id,
                resource,
                action
            )
            
            if not has_permission:
                return JsonResponse(
                    {'error': f'Permission denied: {resource}.{action}'},
                    status=403
                )
                
            return await view_func(request, *args, **kwargs)
            
        return wrapped_view
    return decorator

# مثال استفاده
@require_permission('patient_record', 'read')
async def view_patient_record(request, patient_id):
    # کد مشاهده پرونده بیمار
    pass
```

## 🔒 امنیت و بهترین شیوه‌ها

### 1. Rate Limiting

```python
# unified_auth/middleware/rate_limiter.py
from django.core.cache import cache
from django.http import JsonResponse

class RateLimitMiddleware:
    """محدودیت نرخ درخواست"""
    
    LIMITS = {
        '/api/auth/login/': (5, 300),      # 5 requests per 5 minutes
        '/api/auth/register/': (3, 3600),  # 3 requests per hour
        '/api/auth/verify-otp/': (10, 300), # 10 requests per 5 minutes
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # بررسی rate limit
        if request.path in self.LIMITS:
            limit, window = self.LIMITS[request.path]
            
            # کلید بر اساس IP
            ip = self.get_client_ip(request)
            cache_key = f"rate_limit:{request.path}:{ip}"
            
            # بررسی تعداد درخواست‌ها
            current = cache.get(cache_key, 0)
            if current >= limit:
                return JsonResponse(
                    {
                        'error': 'Rate limit exceeded',
                        'retry_after': window
                    },
                    status=429
                )
                
            # افزایش شمارنده
            cache.set(cache_key, current + 1, window)
            
        response = self.get_response(request)
        return response
```

### 2. Session Security

```python
# unified_auth/services/session_service.py

class SessionService:
    """مدیریت امن نشست‌ها"""
    
    async def create_session(
        self,
        user: UnifiedUser,
        tokens: Dict,
        device_info: Dict
    ) -> UserSession:
        """ایجاد نشست امن"""
        
        # حذف نشست‌های قدیمی در همان دستگاه
        device_id = device_info.get('device_id')
        if device_id:
            await UserSession.objects.filter(
                user=user,
                device_id=device_id,
                is_active=True
            ).update(is_active=False)
            
        # ایجاد نشست جدید
        session = await UserSession.objects.create(
            user=user,
            access_token=tokens['access_token'],
            refresh_token=tokens['refresh_token'],
            ip_address=device_info['ip_address'],
            user_agent=device_info['user_agent'],
            device_id=device_id,
            device_type=self._detect_device_type(device_info['user_agent']),
            expires_at=datetime.utcnow() + timedelta(days=7),
            location=await self._get_location_from_ip(device_info['ip_address'])
        )
        
        # اطلاع‌رسانی ورود جدید
        if user.two_factor_enabled:
            await self._notify_new_login(user, session)
            
        return session
        
    async def validate_session(self, session_id: str) -> bool:
        """اعتبارسنجی نشست"""
        
        try:
            session = await UserSession.objects.get(
                id=session_id,
                is_active=True
            )
            
            # بررسی انقضا
            if session.expires_at < datetime.utcnow():
                session.is_active = False
                await session.save()
                return False
                
            # بررسی عدم فعالیت
            inactivity_limit = timedelta(hours=2)
            if datetime.utcnow() - session.last_activity > inactivity_limit:
                session.is_active = False
                await session.save()
                return False
                
            # به‌روزرسانی last activity
            session.last_activity = datetime.utcnow()
            await session.save()
            
            return True
            
        except UserSession.DoesNotExist:
            return False
```

### 3. Audit Logging

```python
# unified_auth/models.py

class AuthAuditLog(models.Model):
    """لاگ‌های امنیتی احراز هویت"""
    
    EVENT_TYPES = [
        ('login_success', 'Login Success'),
        ('login_failed', 'Login Failed'),
        ('logout', 'Logout'),
        ('register', 'Registration'),
        ('password_change', 'Password Change'),
        ('role_assigned', 'Role Assigned'),
        ('permission_denied', 'Permission Denied'),
        ('session_expired', 'Session Expired'),
        ('suspicious_activity', 'Suspicious Activity'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(
        UnifiedUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='auth_logs'
    )
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    
    # Event details
    success = models.BooleanField(default=True)
    error_message = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'auth_audit_logs'
        indexes = [
            models.Index(fields=['user', 'event_type', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
        ]
```

### 4. Security Headers

```python
# unified_auth/middleware/security_headers.py

class SecurityHeadersMiddleware:
    """افزودن هدرهای امنیتی"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        
        # Security headers
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # CSP برای API
        if request.path.startswith('/api/'):
            response['Content-Security-Policy'] = "default-src 'none'; frame-ancestors 'none';"
            
        return response
```

---

[ELEMENT: div align="center"]

[→ قبلی: تکنولوژی و وابستگی‌ها](04-technology-stack.md) | [بعدی: سیستم‌های هوش مصنوعی ←](06-ai-systems.md)

</div>
