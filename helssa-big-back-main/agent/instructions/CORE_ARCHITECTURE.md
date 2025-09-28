# معماری چهار هسته‌ای پلتفرم هلسا

## نمای کلی

این سند معماری استاندارد چهار هسته‌ای پلتفرم هلسا را تعریف می‌کند که تمامی اپلیکیشن‌ها باید بر اساس آن طراحی شوند.

## هسته‌های مرکزی

### 1. هسته‌ی ورودی API (API Ingress Core)

**مسئولیت‌ها:**

- مدیریت HTTP requests و responses
- اعتبارسنجی ورودی‌ها (validation)
- احراز هویت و authorization
- Rate limiting و throttling
- CORS و security headers
- API versioning
- Request/Response logging

**الگوی پیاده‌سازی:**

```bash
# views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def endpoint_name(request):
    """
    API endpoint with standard error handling
    """
    try:
        # Validation
        serializer = RequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid input', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process through other cores
        result = orchestration_core.process(serializer.validated_data, request.user)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

### 2. هسته‌ی پردازش متن (Text Processing Core)

**مسئولیت‌ها:**

- پردازش زبان طبیعی (NLP)
- تولید متن با AI
- خلاصه‌سازی گفتگوها
- ترجمه و تبدیل زبان
- استخراج entity ها از متن
- sentiment analysis

**الگوی پیاده‌سازی:**

```bash
# text_processor.py
from unified_ai.services import UnifiedAIService
import logging

class TextProcessor:
    def __init__(self):
        self.ai_service = UnifiedAIService()
        self.logger = logging.getLogger(__name__)
    
    def process_medical_text(self, text: str, context: dict) -> dict:
        """
        پردازش متن پزشکی با AI
        """
        try:
            # Call unified AI service
            result = self.ai_service.process_text(
                text=text,
                context=context,
                task='medical_analysis'
            )
            
            return {
                'processed_text': result.get('text'),
                'entities': result.get('entities', []),
                'summary': result.get('summary', ''),
                'confidence': result.get('confidence', 0.0)
            }
        except Exception as e:
            self.logger.error(f"Text processing error: {str(e)}")
            raise
```

### 3. هسته‌ی پردازش صوت (Speech Processing Core)

**مسئولیت‌ها:**

- تبدیل گفتار به متن (STT)
- تبدیل متن به گفتار (TTS)
- پردازش فایل‌های صوتی
- کیفیت‌سنجی صوت
- تقسیم‌بندی صوت (segmentation)
- کاهش نویز

**الگوی پیاده‌سازی:**

```python
# speech_processor.py
from stt.services.whisper_service import WhisperService
import logging

class SpeechProcessor:
    def __init__(self):
        self.whisper_service = WhisperService()
        self.logger = logging.getLogger(__name__)
    
    def process_audio_to_text(self, audio_file, language='fa') -> dict:
        """
        تبدیل صوت به متن
        """
        try:
            # Process with Whisper
            result = self.whisper_service.transcribe(
                audio_file=audio_file,
                language=language
            )
            
            return {
                'text': result.get('text', ''),
                'segments': result.get('segments', []),
                'confidence': result.get('confidence', 0.0),
                'language': result.get('language', language)
            }
        except Exception as e:
            self.logger.error(f"Speech processing error: {str(e)}")
            raise
```

### 4. هسته‌ی ارکستراسیون مرکزی (Central Orchestration Core)

**مسئولیت‌ها:**

- هماهنگی بین هسته‌ها
- مدیریت workflow ها
- اعمال business logic
- مدیریت تراکنش‌ها
- ثبت رویدادها (audit logging)
- مدیریت cache
- اجرای background tasks

**الگوی پیاده‌سازی:**

```python
# orchestrator.py
from django.db import transaction
import logging

class CentralOrchestrator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @transaction.atomic
    def execute_workflow(self, workflow_type: str, data: dict, user) -> dict:
        """
        اجرای workflow مرکزی
        """
        try:
            # Log start
            self.logger.info(f"Starting workflow: {workflow_type} for user: {user.id}")
            
            # Apply business logic
            if workflow_type == 'medical_consultation':
                return self._handle_medical_consultation(data, user)
            elif workflow_type == 'prescription_generation':
                return self._handle_prescription(data, user)
            
            raise ValueError(f"Unknown workflow type: {workflow_type}")
            
        except Exception as e:
            self.logger.error(f"Orchestration error: {str(e)}")
            raise
    
    def _handle_medical_consultation(self, data: dict, user) -> dict:
        """
        پردازش مشاوره پزشکی
        """
        # Validate user permissions
        if not user.can_access_medical_features():
            raise PermissionError("Access denied")
        
        # Process through cores
        text_result = text_processor.process_medical_text(data['message'])
        
        # Apply billing rules
        billing_service.charge_for_consultation(user)
        
        # Store results
        consultation = Consultation.objects.create(
            user=user,
            input_text=data['message'],
            processed_result=text_result
        )
        
        return {
            'consultation_id': consultation.id,
            'response': text_result['processed_text']
        }
```

## اصول طراحی

### 1. جدایی نگرانی‌ها (Separation of Concerns)

- هر هسته فقط مسئولیت‌های خاص خود را دارد
- هیچ هسته‌ای نباید مستقیماً به هسته‌ی دیگر وابسته باشد
- تمام ارتباطات از طریق هسته‌ی ارکستراسیون انجام می‌شود

### 2. قابلیت تست‌پذیری

- هر هسته باید بتواند مستقل تست شود
- Mock objects برای تست‌های واحد
- Integration tests برای تست ارتباط بین هسته‌ها

### 3. مقیاس‌پذیری

- هر هسته باید قابلیت scale کردن مستقل داشته باشد
- استفاده از async/await برای عملیات I/O
- Cache strategy برای بهبود performance

### 4. مانیتورینگ و لاگ‌گذاری

- تمام عملیات در هسته‌ها لاگ می‌شوند
- Metrics برای monitoring performance
- Error tracking و alerting

## الگوهای امنیتی

### 1. احراز هویت یکپارچه

```python
# تمام endpoints باید از unified auth استفاده کنند
from unified_auth.decorators import unified_auth_required

@unified_auth_required(user_types=['patient', 'doctor'])
def secure_endpoint(request):
    # دسترسی به request.user تضمین شده
    pass
```

### 2. مدیریت دسترسی

```python
# بررسی سطح دسترسی
if request.user.user_type == 'patient':
    # منطق بیمار
elif request.user.user_type == 'doctor':
    # منطق پزشک
```

### 3. OTP و Kavenegar

```python
# استفاده از سرویس OTP یکپارچه
from unified_auth.services import UnifiedOTPService

otp_service = UnifiedOTPService()
result = otp_service.send_otp(phone_number, purpose='login')
```

## ادغام با سیستم‌های موجود

### 1. Unified Auth

- همه اپ‌ها باید از `unified_auth.UnifiedUser` استفاده کنند
- JWT authentication برای API ها
- OTP verification برای عملیات حساس

### 2. Unified Billing

- بررسی محدودیت‌های اشتراک قبل از پردازش
- ثبت استفاده از منابع
- مدیریت کیف پول

### 3. Unified Access

- دسترسی موقت پزشک به اطلاعات بیمار
- کدهای دسترسی 6 رقمی
- Session management و audit logging

## نمونه پیاده‌سازی کامل

```python
# app_name/cores/
├── __init__.py
├── api_ingress.py          # API endpoints و validation
├── text_processor.py       # پردازش متن و AI
├── speech_processor.py     # پردازش صوت (در صورت نیاز)
└── orchestrator.py         # Business logic و workflow

# app_name/
├── models.py               # Django models
├── serializers.py          # DRF serializers
├── views.py                # API views (فقط delegation به cores)
├── urls.py                 # URL routing
├── permissions.py          # Custom permissions
└── cores/                  # چهار هسته
```

این معماری تضمین می‌کند که تمام اپلیکیشن‌ها با استانداردهای یکسان و قابلیت نگهداری بالا ساخته شوند.
