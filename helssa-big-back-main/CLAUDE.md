# دستورالعمل‌های Claude برای پروژه هلسا

## نمای کلی پروژه
پروژه هلسا یک پلتفرم پزشکی دیجیتال است که بر اساس معماری میکروسرویس و Django طراحی شده است.

## اصول اساسی

### 1. زبان و فرهنگ
- **مستندات و کامنت‌ها**: فارسی
- **نام‌گذاری کد**: انگلیسی
- **پیام‌های کاربری**: فارسی
- **تاریخ**: شمسی با استفاده از `jdatetime`

### 2. معماری چهار هسته‌ای
هر اپلیکیشن باید شامل 4 هسته باشد:

```python
# app_name/cores/api_ingress.py
class APIIngressCore:
    """مدیریت ورودی و خروجی API"""
    pass

# app_name/cores/text_processor.py
class TextProcessorCore:
    """پردازش متن و NLP"""
    pass

# app_name/cores/speech_processor.py
class SpeechProcessorCore:
    """پردازش صوت (STT/TTS)"""
    pass

# app_name/cores/orchestrator.py
class CentralOrchestrator:
    """هماهنگی بین هسته‌ها"""
    pass
```

### 3. مدل‌های یکپارچه
```python
from unified_auth.models import UnifiedUser
from app_standards.models.base_models import BaseModel

# همیشه از UnifiedUser استفاده کنید
User = get_user_model()  # این UnifiedUser است

# همه مدل‌ها از BaseModel ارث‌بری کنند
class MyModel(BaseModel):
    pass
```

### 4. احراز هویت
```python
# OTP با کاوه‌نگار
from auth_otp.services import OTPService

# JWT tokens
from rest_framework_simplejwt.authentication import JWTAuthentication

# بررسی دسترسی
from unified_access.services import AccessService
```

### 5. پردازش AI
```python
from unified_ai.services import UnifiedAIService

ai_service = UnifiedAIService()
result = ai_service.process_text(
    text="متن ورودی",
    task="medical_summary",
    context={"patient_id": "123"}
)
```

## الگوهای کد

### API View Pattern
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def endpoint_name(request):
    """توضیح فارسی endpoint"""
    try:
        # 1. Validation
        serializer = InputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'validation_error',
                'details': serializer.errors
            }, status=400)
        
        # 2. Business Logic
        service = ServiceClass()
        success, result = service.process(serializer.validated_data)
        
        # 3. Response
        if success:
            return Response({
                'success': True,
                'data': result
            }, status=200)
        else:
            return Response({
                'success': False,
                'error': result.get('error'),
                'message': result.get('message')
            }, status=400)
            
    except Exception as e:
        logger.error(f"Error in {endpoint_name}: {str(e)}")
        return Response({
            'success': False,
            'error': 'internal_error',
            'message': 'خطای داخلی سرور'
        }, status=500)
```

### Service Pattern
```python
class ServiceName:
    """سرویس برای ..."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process(self, data: dict) -> Tuple[bool, dict]:
        """
        پردازش داده
        
        Returns:
            Tuple[bool, dict]: (موفقیت، نتیجه یا خطا)
        """
        try:
            # Validation
            if not self._validate(data):
                return False, {'error': 'invalid_data'}
            
            # Process
            result = self._do_process(data)
            
            # Log success
            self.logger.info(f"Process successful: {result.get('id')}")
            
            return True, result
            
        except Exception as e:
            self.logger.error(f"Process error: {str(e)}")
            return False, {
                'error': 'process_failed',
                'message': str(e)
            }
```

### Model Pattern
```python
class ModelName(BaseModel):
    """توضیح فارسی مدل"""
    
    # Relations
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='model_names',
        verbose_name='کاربر'
    )
    
    # Fields with Persian verbose_name
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان'
    )
    
    # Status with choices
    STATUS_CHOICES = [
        ('draft', 'پیش‌نویس'),
        ('published', 'منتشر شده'),
        ('archived', 'آرشیو شده'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='وضعیت'
    )
    
    class Meta:
        verbose_name = 'نام مدل'
        verbose_name_plural = 'نام‌های مدل'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user}"
```

## نکات امنیتی

### 1. Input Validation
```python
# همیشه از Serializer استفاده کنید
serializer = InputSerializer(data=request.data)
if not serializer.is_valid():
    return Response(error_response, status=400)
```

### 2. SQL Injection Prevention
```python
# خوب - استفاده از ORM
User.objects.filter(phone_number=phone)

# بد - Raw SQL
cursor.execute(f"SELECT * FROM users WHERE phone='{phone}'")
```

### 3. Rate Limiting
```python
from django.core.cache import cache

def check_rate_limit(key: str, limit: int, window: int) -> bool:
    count = cache.get(key, 0)
    if count >= limit:
        return False
    cache.set(key, count + 1, timeout=window)
    return True
```

### 4. Permission Checks
```python
# بررسی دسترسی به داده‌های بیمار
if request.user.user_type == 'doctor':
    has_access = AccessService.check_doctor_access(
        doctor=request.user,
        patient=patient
    )
    if not has_access:
        return Response({'error': 'دسترسی ندارید'}, status=403)
```

## تست‌نویسی

### Unit Test Pattern
```python
class ServiceTests(TestCase):
    """تست‌های سرویس"""
    
    def setUp(self):
        self.service = ServiceName()
        self.user = User.objects.create_user(
            username='09123456789',
            user_type='patient'
        )
    
    def test_process_success(self):
        """تست پردازش موفق"""
        data = {'field': 'value'}
        success, result = self.service.process(data)
        
        self.assertTrue(success)
        self.assertIn('id', result)
```

### API Test Pattern
```python
class APITests(APITestCase):
    """تست‌های API"""
    
    def test_endpoint_authenticated(self):
        """تست با احراز هویت"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            reverse('app:endpoint'),
            data={'field': 'value'},
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
```

## بهترین شیوه‌ها

### 1. Error Handling
- همیشه try/except داشته باشید
- خطاها را لاگ کنید
- پیام‌های کاربرپسند فارسی برگردانید

### 2. Database Optimization
```python
# استفاده از select_related برای ForeignKey
queryset = Model.objects.select_related('user', 'doctor')

# استفاده از prefetch_related برای ManyToMany
queryset = Model.objects.prefetch_related('tags', 'categories')
```

### 3. Caching
```python
from django.core.cache import cache

# ذخیره در کش
cache.set('key', value, timeout=3600)

# دریافت از کش
value = cache.get('key', default=None)
```

### 4. Async Tasks
```python
from celery import shared_task

@shared_task
def process_heavy_task(data_id: str):
    """پردازش سنگین در background"""
    pass
```

## چک‌لیست Code Review

- [ ] کد از استانداردهای PEP 8 پیروی می‌کند
- [ ] Type hints استفاده شده
- [ ] Docstring فارسی دارد
- [ ] معماری 4 هسته رعایت شده
- [ ] از UnifiedUser استفاده شده
- [ ] Validation ورودی‌ها انجام شده
- [ ] Error handling مناسب دارد
- [ ] تست نوشته شده
- [ ] Performance بهینه است
- [ ] امنیت رعایت شده