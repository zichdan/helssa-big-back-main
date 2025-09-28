# دستورالعمل‌های GitHub Copilot برای پروژه هلسا

## زبان و فرهنگ
- کامنت‌ها و مستندات به فارسی
- نام متغیرها و توابع به انگلیسی
- پیام‌های کاربری به فارسی
- استفاده از تقویم شمسی برای تاریخ‌ها

## معماری پروژه
پروژه هلسا بر اساس معماری 4 هسته‌ای طراحی شده:

1. **API Ingress Core**: مدیریت درخواست‌ها و پاسخ‌ها
2. **Text Processing Core**: پردازش متن با AI
3. **Speech Processing Core**: پردازش صوت (STT/TTS)
4. **Central Orchestration Core**: هماهنگی بین هسته‌ها

## قوانین کدنویسی

### Django Models
```python
class ModelName(BaseModel):
    """توضیح فارسی مدل"""
    
    field_name = models.CharField(
        max_length=100,
        verbose_name='نام فیلد'
    )
    
    class Meta:
        verbose_name = 'نام مدل'
        verbose_name_plural = 'نام‌های مدل'
```

### API Views
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def endpoint_name(request):
    """
    توضیح endpoint
    
    Returns:
        Response: با فرمت {'success': bool, 'data': dict}
    """
    try:
        # Validation با serializer
        # Process با service
        # Response با status code مناسب
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return Response({'error': 'خطای سرور'}, status=500)
```

### سرویس‌ها
```python
class ServiceName:
    """سرویس برای ..."""
    
    def process(self, data: dict) -> Tuple[bool, dict]:
        """
        Returns:
            Tuple[bool, dict]: (موفقیت، نتیجه/خطا)
        """
        pass
```

## نکات مهم

### احراز هویت
- همیشه از `UnifiedUser` استفاده کنید
- JWT برای API ها
- OTP برای ورود با کاوه‌نگار

### امنیت
- Validation ورودی‌ها الزامی
- Rate limiting برای همه endpoint ها
- استفاده از Django ORM (بدون raw SQL)

### دیتابیس
- استفاده از `select_related` و `prefetch_related`
- Index برای فیلدهای پرکاربرد
- Soft delete برای داده‌های حساس

### تست
- حداقل یک تست برای هر endpoint
- Mock کردن سرویس‌های خارجی
- تست‌های edge case

## الگوهای رایج

### ارسال OTP
```python
from auth_otp.services import OTPService

otp_service = OTPService()
success, result = otp_service.send_otp(
    phone_number='09123456789',
    purpose='login'
)
```

### بررسی دسترسی
```python
from unified_access.services import AccessService

has_access = AccessService.check_doctor_access(
    doctor=request.user,
    patient=patient
)
```

### پردازش با AI
```python
from unified_ai.services import UnifiedAIService

ai_service = UnifiedAIService()
result = ai_service.process_text(
    text=input_text,
    task='medical_summary'
)
```

## پیام‌های خطا
```python
ERRORS = {
    'validation': 'داده‌های ورودی نامعتبر است',
    'not_found': 'موردی یافت نشد',
    'permission': 'شما دسترسی ندارید',
    'rate_limit': 'تعداد درخواست‌ها بیش از حد مجاز',
    'server': 'خطای داخلی سرور'
}
```

## نام‌گذاری
- متغیرها: `snake_case`
- کلاس‌ها: `PascalCase`
- ثابت‌ها: `UPPER_SNAKE_CASE`
- URL ها: `kebab-case`