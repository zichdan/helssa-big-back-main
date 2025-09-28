# قوانین عمومی پروژه هلسا

## زبان و فرهنگ
- کامنت‌ها و docstring: فارسی
- نام متغیرها و توابع: انگلیسی
- پیام‌های کاربری: فارسی
- لاگ‌ها: انگلیسی

## استانداردهای کد

### Python Style
```python
# PEP 8 compliant
# حداکثر 88 کاراکتر در هر خط (Black formatter)
# Type hints الزامی

from typing import Dict, List, Optional, Tuple

def process_data(
    data: Dict[str, any],
    options: Optional[Dict] = None
) -> Tuple[bool, Dict[str, any]]:
    """
    پردازش داده‌های ورودی
    
    Args:
        data: دیکشنری داده‌ها
        options: تنظیمات اختیاری
        
    Returns:
        Tuple[bool, dict]: (موفقیت، نتیجه)
    """
    pass
```

### Import Order
```python
# 1. Standard library
import os
import sys
from datetime import datetime

# 2. Third-party
from django.db import models
from rest_framework import serializers

# 3. Local application
from .models import MyModel
from .utils import helper_function
```

### نام‌گذاری
- متغیرها و توابع: `snake_case`
- کلاس‌ها: `PascalCase`
- ثابت‌ها: `UPPER_SNAKE_CASE`
- Private methods: `_method_name`

## Django Specific

### مدل‌ها
```python
class ModelName(BaseModel):
    """توضیح فارسی مدل"""
    
    # همیشه verbose_name فارسی
    field = models.CharField(
        max_length=100,
        verbose_name='نام فیلد'
    )
    
    class Meta:
        verbose_name = 'نام مدل'
        verbose_name_plural = 'نام‌های مدل'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.meaningful_field
```

### Views
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def view_name(request):
    """توضیح endpoint"""
    try:
        # Logic here
        return Response({'success': True, 'data': {}})
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return Response(
            {'success': False, 'error': 'خطای سرور'},
            status=500
        )
```

## مستندسازی

### Docstring Format
```python
def function_name(param1: str, param2: int = 0) -> dict:
    """
    توضیح مختصر (یک خط)
    
    توضیح تفصیلی در صورت نیاز که می‌تواند
    چند خط باشد.
    
    Args:
        param1: توضیح پارامتر اول
        param2: توضیح پارامتر دوم (پیش‌فرض: 0)
        
    Returns:
        dict: توضیح دیکشنری خروجی
        
    Raises:
        ValueError: زمانی که param1 خالی است
        
    Example:
        >>> result = function_name("test", 5)
        >>> print(result)
        {'status': 'success'}
    """
    pass
```

### API Documentation
```python
@api_view(['POST'])
def endpoint(request):
    """
    عنوان endpoint
    
    این endpoint برای ... استفاده می‌شود
    
    Request Body:
        {
            "field1": "string - اجباری",
            "field2": "integer - اختیاری"
        }
        
    Response:
        Success (200):
        {
            "success": true,
            "data": {
                "id": "uuid",
                "field": "value"
            }
        }
        
        Error (400):
        {
            "success": false,
            "error": "validation_error",
            "message": "پیام خطا"
        }
    """
    pass
```

## Error Handling

### استاندارد Response
```python
# Success Response
{
    "success": True,
    "data": {},
    "message": "عملیات موفق بود"
}

# Error Response
{
    "success": False,
    "error": "error_code",
    "message": "توضیح فارسی خطا",
    "details": {}  # اختیاری
}
```

### Error Codes
- `validation_error`: خطای اعتبارسنجی
- `not_found`: موردی یافت نشد
- `permission_denied`: عدم دسترسی
- `rate_limit_exceeded`: محدودیت نرخ
- `internal_error`: خطای داخلی

## لاگینگ

### Log Levels
```python
import logging

logger = logging.getLogger(__name__)

logger.debug('Detailed information for debugging')
logger.info('General information')
logger.warning('Warning message')
logger.error('Error message')
logger.critical('Critical error')
```

### Log Format
```python
# با context
logger.info(
    'User action performed',
    extra={
        'user_id': user.id,
        'action': 'login',
        'ip': request.META.get('REMOTE_ADDR')
    }
)

# برای خطاها
logger.error(
    f'Error in {function_name}: {str(e)}',
    exc_info=True  # برای stack trace
)
```

## تاریخ و زمان

### استفاده از تاریخ شمسی
```python
import jdatetime

# تبدیل به شمسی
jalali_date = jdatetime.date.fromgregorian(
    date=gregorian_date
)

# نمایش
formatted = jalali_date.strftime('%Y/%m/%d')  # 1402/10/15
```

### Timezone
```python
from django.utils import timezone

# همیشه از timezone-aware استفاده کنید
now = timezone.now()

# تنظیم timezone تهران
TIME_ZONE = 'Asia/Tehran'
USE_TZ = True
```