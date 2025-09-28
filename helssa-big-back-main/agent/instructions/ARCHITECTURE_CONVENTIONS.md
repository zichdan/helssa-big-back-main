# 🏛️ قراردادهای معماری HELSSA

## 📋 خلاصه

این سند حاوی قراردادها و الگوهای استخراج شده از پروژه HELSSA-MAIN است که همه ایجنت‌ها باید از آن پیروی کنند.

## 🔧 قراردادهای فنی

### نام‌گذاری

1. **مدل‌ها**: PascalCase (مثال: `UnifiedUser`, `PatientProfile`)
2. **سرویس‌ها**: PascalCase + Service (مثال: `OTPService`, `JWTService`)
3. **URL patterns**: kebab-case (مثال: `/api/v1/auth/login-otp/`)
4. **متغیرهای محیطی**: UPPER_SNAKE_CASE (مثال: `KAVENEGAR_API_KEY`)

### ساختار پوشه‌ها

```bash
app_name/
├── models/
│   ├── __init__.py
│   └── model_name.py
├── services/
│   ├── __init__.py
│   └── service_name.py
├── api/
│   ├── __init__.py
│   ├── serializers.py
│   └── views.py
├── tasks.py
├── utils/
├── tests/
├── migrations/
└── apps.py
```

### API Response Format

#### موفقیت (200 OK)

```json
{
  "data": {
    // داده‌های اصلی
  },
  "meta": {
    "request_id": "req_uuid",
    "timestamp": "2024-01-20T10:30:00Z"
  }
}
```

#### خطا

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "پیام خطا به زبان فارسی",
    "details": {
      // جزئیات اضافی
    },
    "request_id": "req_uuid",
    "timestamp": "2024-01-20T10:30:00Z"
  }
}
```

## 🔐 احراز هویت و امنیت

### OTP Flow

1. **درخواست OTP**:
   - مسیر: `POST /api/v1/auth/login/otp/`
   - ارسال از طریق کاوه‌نگار
   - مدت اعتبار: 120 ثانیه
   - حداکثر تلاش: 3 بار

2. **تایید OTP**:
   - مسیر: `POST /api/v1/auth/verify/otp/`
   - بازگشت JWT tokens
   - ثبت در Audit logs

### JWT Structure

```python
{
    'user_id': str(user.id),
    'phone_number': user.phone_number,
    'user_type': user.user_type,  # patient/doctor/admin/staff
    'is_verified': user.is_verified,
    'permissions': [...],
    'iat': datetime.utcnow(),
    'exp': datetime.utcnow() + timedelta(minutes=15)
}
```

### تفکیک نقش‌ها

1. **Patient Routes**: `/api/v1/patients/*`
2. **Doctor Routes**: `/api/v1/doctors/*`
3. **Admin Routes**: `/api/v1/admin/*`

## 💳 سیستم پرداخت

### درگاه‌های پرداخت

1. **ایرانی**:
   - BitPay.ir (اولویت اول)
   - ZarinPal
   - IDPay

2. **بین‌المللی**:
   - Stripe
   - PayPal

### Transaction States

```python
TRANSACTION_STATES = [
    ('pending', 'در انتظار'),
    ('processing', 'در حال پردازش'),
    ('completed', 'تکمیل شده'),
    ('failed', 'ناموفق'),
    ('refunded', 'بازگشت داده شده'),
    ('cancelled', 'لغو شده')
]
```

## 📱 سیستم پیام‌رسانی

### کاوه‌نگار (SMS)

```python
# تنظیمات
KAVENEGAR_API_KEY = os.getenv('KAVENEGAR_API_KEY')
KAVENEGAR_SENDER = os.getenv('KAVENEGAR_SENDER', '10004346')

# Template Names
TEMPLATES = {
    'otp': 'verify',
    'welcome': 'welcome',
    'appointment': 'appointment',
    'reminder': 'reminder'
}
```

### Rate Limiting

```python
RATE_LIMITS = {
    'otp_request': '5/hour',
    'api_anonymous': '100/hour',
    'api_authenticated': '1000/hour',
    'api_premium': '10000/hour'
}
```

## 🏥 مراکز کنترل (Control Centers)

### لیست مراکز

1. **AUTH CENTER** - احراز هویت و مدیریت کاربران
2. **VISIT CENTER** - ویزیت‌ها و ملاقات‌ها
3. **AI CENTER** - چت‌بات و پردازش AI
4. **BILLING CENTER** - کیف پول و اشتراک‌ها
5. **ACCESS CENTER** - دسترسی موقت با OTP
6. **CHAT CENTER** - پیام‌رسانی و تاریخچه
7. **COMM CENTER** - SMS/Email/Push
8. **TASK CENTER** - Celery Tasks
9. **AGENT CENTER** - AI Agents و Workflows

## 📊 لاگ و Monitoring

### Audit Log Format

```python
{
    'timestamp': datetime.utcnow(),
    'user_id': user.id,
    'action': 'LOGIN_SUCCESS',
    'resource': 'AUTH',
    'ip_address': request.META.get('REMOTE_ADDR'),
    'user_agent': request.META.get('HTTP_USER_AGENT'),
    'metadata': {
        'method': 'OTP',
        'device_type': 'mobile'
    }
}
```

### Log Levels

- **DEBUG**: اطلاعات توسعه
- **INFO**: رویدادهای عادی
- **WARNING**: هشدارها
- **ERROR**: خطاهای قابل بازیابی
- **CRITICAL**: خطاهای بحرانی

## 🔄 Celery Tasks

### Task Naming

```python
@shared_task(name='billing.process_payment')
def process_payment(transaction_id):
    pass
```

### Queue Names

- `default`: تسک‌های عمومی
- `critical`: تسک‌های حیاتی (OTP, Payment)
- `notifications`: ارسال اعلان‌ها
- `reports`: تولید گزارش‌ها
- `ai_processing`: پردازش‌های AI

## 🧪 تست‌نویسی

### ساختار تست‌ها

```python
# tests/test_models.py
class TestUnifiedUser(TestCase):
    def setUp(self):
        self.user = UnifiedUserFactory()
    
    def test_user_creation(self):
        self.assertEqual(self.user.user_type, 'patient')
```

### Coverage Requirements

- حداقل پوشش: 80%
- Critical paths: 95%
- Models: 90%
- Services: 85%

## 📝 مستندسازی

### Docstring Format

```python
def send_otp(phone_number: str) -> bool:
    """
    ارسال کد OTP به شماره موبایل کاربر.
    
    Args:
        phone_number: شماره موبایل با فرمت +98...
        
    Returns:
        bool: True در صورت موفقیت
        
    Raises:
        ValidationError: شماره موبایل نامعتبر
        RateLimitError: تعداد درخواست بیش از حد
    """
```

### API Documentation

استفاده از drf-yasg برای تولید خودکار مستندات Swagger/OpenAPI.

---

این قراردادها بر اساس تحلیل کامل HELSSA-MAIN استخراج شده و باید بدون تغییر رعایت شوند.
