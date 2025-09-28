# استانداردهای کدنویسی پروژه هلسا

## 1. استانداردهای Python/Django

### 1.1 Style Guide
- **PEP 8**: رعایت کامل PEP 8
- **خط‌ها**: حداکثر 88 کاراکتر (Black formatter)
- **Import**: ترتیب standard > third-party > local

```python
# صحیح
import os
import sys
from datetime import datetime

from django.db import models
from rest_framework import serializers

from .models import CustomModel
from .utils import helper_function
```

### 1.2 Type Hints
```python
from typing import Dict, List, Optional, Tuple

def process_data(
    data: Dict[str, any],
    user_id: str,
    options: Optional[Dict] = None
) -> Tuple[bool, Dict[str, any]]:
    """پردازش داده‌های ورودی"""
    pass
```

### 1.3 مدل‌ها
```python
class PatientProfile(models.Model):
    """پروفایل بیمار"""
    
    # فیلدها با verbose_name فارسی
    national_code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name='کد ملی'
    )
    
    class Meta:
        verbose_name = 'پروفایل بیمار'
        verbose_name_plural = 'پروفایل بیماران'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['national_code']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.national_code}"
```

## 2. معماری چهار هسته‌ای

### 2.1 ساختار پوشه‌ها
```
app_name/
├── models.py
├── serializers.py
├── views.py
├── urls.py
├── admin.py
├── services/
│   ├── __init__.py
│   ├── core_service.py
│   └── helpers.py
├── cores/
│   ├── __init__.py
│   ├── api_ingress.py
│   ├── text_processor.py
│   ├── speech_processor.py
│   └── orchestrator.py
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_views.py
    └── test_services.py
```

### 2.2 API Views
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_endpoint(request):
    """
    توضیحات endpoint
    
    Request Body:
        - field1: توضیح
        - field2: توضیح
        
    Returns:
        200: موفق
        400: خطای validation
        500: خطای سرور
    """
    try:
        # Validation
        serializer = RequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid input', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process
        result = service.process(serializer.validated_data)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in api_endpoint: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

## 3. سرویس‌ها

### 3.1 ساختار سرویس
```python
class ServiceName:
    """توضیحات سرویس"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process(self, data: dict) -> Tuple[bool, dict]:
        """
        پردازش داده
        
        Args:
            data: داده ورودی
            
        Returns:
            Tuple[bool, dict]: (موفقیت، نتیجه/خطا)
        """
        try:
            # Business logic
            result = self._internal_process(data)
            
            self.logger.info(f"Process successful: {result['id']}")
            return True, result
            
        except Exception as e:
            self.logger.error(f"Process error: {str(e)}")
            return False, {'error': str(e)}
    
    def _internal_process(self, data: dict) -> dict:
        """متد internal - با _ شروع می‌شود"""
        pass
```

## 4. تست‌نویسی

### 4.1 ساختار تست
```python
class ModelNameTests(TestCase):
    """تست‌های مدل"""
    
    def setUp(self):
        """آماده‌سازی داده‌های تست"""
        self.user = User.objects.create_user(
            username='09123456789',
            user_type='patient'
        )
    
    def test_model_creation(self):
        """تست ایجاد مدل"""
        instance = ModelName.objects.create(
            user=self.user,
            field1='value1'
        )
        
        self.assertEqual(instance.field1, 'value1')
        self.assertTrue(instance.is_active)
    
    def test_model_validation(self):
        """تست validation"""
        with self.assertRaises(ValidationError):
            instance = ModelName.objects.create(
                user=self.user,
                field1='invalid_value'
            )
```

### 4.2 تست API
```python
class APITests(APITestCase):
    """تست‌های API"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='09123456789',
            user_type='patient'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_endpoint_success(self):
        """تست موفق endpoint"""
        url = reverse('app_name:endpoint_name')
        data = {
            'field1': 'value1',
            'field2': 'value2'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
```

## 5. امنیت

### 5.1 Validation
```python
# همیشه از serializer استفاده کنید
class InputSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=11,
        validators=[
            RegexValidator(r'^09\d{9}$', 'شماره موبایل نامعتبر')
        ]
    )
    
    def validate_phone_number(self, value):
        # Validation اضافی
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('این شماره قبلاً ثبت شده')
        return value
```

### 5.2 Permissions
```python
from rest_framework.permissions import BasePermission

class IsPatientOrReadOnly(BasePermission):
    """فقط بیماران می‌توانند ایجاد/ویرایش کنند"""
    
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        return (
            request.user.is_authenticated and 
            request.user.user_type == 'patient'
        )
```

## 6. لاگینگ

### 6.1 استفاده از Logger
```python
import logging

logger = logging.getLogger(__name__)

# سطوح مختلف
logger.debug('Debug message')
logger.info('Info message')
logger.warning('Warning message')
logger.error('Error message')
logger.critical('Critical message')

# با context
logger.info(
    'User action',
    extra={
        'user_id': user.id,
        'action': 'login',
        'ip': request.META.get('REMOTE_ADDR')
    }
)
```

## 7. مستندات

### 7.1 Docstring Format
```python
def function_name(param1: str, param2: int = 0) -> dict:
    """
    توضیح کوتاه تابع
    
    توضیحات تفصیلی در صورت نیاز
    
    Args:
        param1: توضیح پارامتر اول
        param2: توضیح پارامتر دوم (پیش‌فرض: 0)
        
    Returns:
        dict: توضیح خروجی
        
    Raises:
        ValueError: زمانی که ورودی نامعتبر است
        
    Example:
        >>> result = function_name("test", 5)
        >>> print(result)
        {'status': 'success', 'count': 5}
    """
    pass
```

## 8. Git Workflow

### 8.1 Commit Messages
```bash
# فرمت
<type>: <subject>

<body>

<footer>

# مثال‌ها
feat: افزودن سیستم OTP با کاوه‌نگار

- پیاده‌سازی ارسال و تأیید OTP
- افزودن rate limiting
- ایجاد مدل‌های مربوطه

Closes #123

fix: رفع مشکل timeout در ارسال پیامک

مشکل timeout در ارتباط با کاوه‌نگار برطرف شد
```

### 8.2 Branch Naming
```bash
feature/otp-authentication
bugfix/sms-timeout
hotfix/critical-security-issue
refactor/clean-models
```

## 9. Performance

### 9.1 Database Queries
```python
# بد - N+1 query
for patient in Patient.objects.all():
    print(patient.visits.count())

# خوب - با select_related/prefetch_related
patients = Patient.objects.prefetch_related('visits').all()
for patient in patients:
    print(patient.visits.count())
```

### 9.2 Caching
```python
from django.core.cache import cache

def get_user_stats(user_id: str) -> dict:
    cache_key = f'user_stats_{user_id}'
    stats = cache.get(cache_key)
    
    if stats is None:
        stats = calculate_user_stats(user_id)
        cache.set(cache_key, stats, timeout=3600)  # 1 hour
    
    return stats
```

## 10. چک‌لیست Code Review

- [ ] کد PEP 8 را رعایت می‌کند
- [ ] Type hints دارد
- [ ] Docstring فارسی دارد
- [ ] تست نوشته شده
- [ ] مستندات بروز شده
- [ ] امنیت رعایت شده
- [ ] Performance بهینه است
- [ ] لاگ مناسب دارد
- [ ] Error handling کامل است
- [ ] معماری 4 هسته رعایت شده