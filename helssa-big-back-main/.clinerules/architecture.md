# قوانین معماری پروژه هلسا

## معماری 4 هسته‌ای

### ساختار پوشه‌ها
```
app_name/
├── __init__.py
├── models.py
├── serializers.py
├── views.py
├── urls.py
├── admin.py
├── apps.py
├── cores/                    # هسته‌های اصلی
│   ├── __init__.py
│   ├── api_ingress.py       # هسته ورودی API
│   ├── text_processor.py    # هسته پردازش متن
│   ├── speech_processor.py  # هسته پردازش صوت
│   └── orchestrator.py      # هسته هماهنگی مرکزی
├── services/                 # سرویس‌های کمکی
│   ├── __init__.py
│   └── helpers.py
├── tests/                    # تست‌ها
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_views.py
│   └── test_services.py
├── migrations/              # migration های دیتابیس
└── management/              # دستورات مدیریت
    └── commands/
```

## هسته‌های اصلی

### 1. API Ingress Core
```python
from app_standards.four_cores import APIIngressCore
from rest_framework import serializers

class CustomAPIIngress(APIIngressCore):
    """هسته ورودی API برای [نام اپ]"""
    
    def validate_request(self, data: dict, serializer_class) -> Tuple[bool, dict]:
        """
        اعتبارسنجی درخواست
        
        Args:
            data: داده‌های ورودی
            serializer_class: کلاس serializer
            
        Returns:
            Tuple[bool, dict]: (معتبر است، داده‌های validated/errors)
        """
        serializer = serializer_class(data=data)
        if serializer.is_valid():
            return True, serializer.validated_data
        return False, serializer.errors
    
    def build_response(self, data: dict, status: str = 'success') -> dict:
        """ساخت پاسخ استاندارد"""
        if status == 'success':
            return {
                'success': True,
                'data': data,
                'timestamp': timezone.now().isoformat()
            }
        else:
            return {
                'success': False,
                'error': data.get('error', 'unknown_error'),
                'message': data.get('message', 'خطای ناشناخته'),
                'timestamp': timezone.now().isoformat()
            }
```

### 2. Text Processing Core
```python
from app_standards.four_cores import TextProcessingCore
from unified_ai.services import UnifiedAIService

class CustomTextProcessor(TextProcessingCore):
    """هسته پردازش متن برای [نام اپ]"""
    
    def __init__(self):
        super().__init__()
        self.ai_service = UnifiedAIService()
    
    def process_medical_text(self, text: str, context: dict = None) -> dict:
        """
        پردازش متن پزشکی
        
        Args:
            text: متن ورودی
            context: اطلاعات اضافی
            
        Returns:
            dict: نتیجه پردازش
        """
        # پیش‌پردازش
        cleaned_text = self._preprocess(text)
        
        # پردازش با AI
        result = self.ai_service.process_text(
            text=cleaned_text,
            task='medical_analysis',
            context=context or {}
        )
        
        # پس‌پردازش
        return self._postprocess(result)
    
    def _preprocess(self, text: str) -> str:
        """پیش‌پردازش متن"""
        # حذف کاراکترهای اضافی
        # نرمال‌سازی
        return text.strip()
    
    def _postprocess(self, result: dict) -> dict:
        """پس‌پردازش نتیجه"""
        # فرمت‌دهی خروجی
        return result
```

### 3. Speech Processing Core
```python
from app_standards.four_cores import SpeechProcessingCore
from stt.services import WhisperService

class CustomSpeechProcessor(SpeechProcessingCore):
    """هسته پردازش صوت برای [نام اپ]"""
    
    def __init__(self):
        super().__init__()
        self.stt_service = WhisperService()
    
    def transcribe_audio(self, audio_file, language: str = 'fa') -> dict:
        """
        تبدیل صوت به متن
        
        Args:
            audio_file: فایل صوتی
            language: زبان (پیش‌فرض فارسی)
            
        Returns:
            dict: متن و اطلاعات
        """
        # بررسی فرمت فایل
        if not self._validate_audio_format(audio_file):
            raise ValueError('فرمت فایل صوتی پشتیبانی نمی‌شود')
        
        # تبدیل به متن
        result = self.stt_service.transcribe(
            audio_file=audio_file,
            language=language
        )
        
        return {
            'text': result['text'],
            'segments': result.get('segments', []),
            'confidence': result.get('confidence', 0.0),
            'duration': result.get('duration', 0)
        }
    
    def _validate_audio_format(self, audio_file) -> bool:
        """بررسی فرمت فایل صوتی"""
        allowed_formats = ['.mp3', '.wav', '.ogg', '.m4a']
        # بررسی فرمت
        return True
```

### 4. Central Orchestration Core
```python
from app_standards.four_cores import CentralOrchestrator
from django.db import transaction

class CustomOrchestrator(CentralOrchestrator):
    """هسته هماهنگی مرکزی برای [نام اپ]"""
    
    def __init__(self):
        super().__init__()
        self.api_ingress = CustomAPIIngress()
        self.text_processor = CustomTextProcessor()
        self.speech_processor = CustomSpeechProcessor()
    
    @transaction.atomic
    def execute_workflow(self, workflow_type: str, data: dict, user) -> dict:
        """
        اجرای workflow
        
        Args:
            workflow_type: نوع workflow
            data: داده‌های ورودی
            user: کاربر
            
        Returns:
            dict: نتیجه workflow
        """
        self.logger.info(f"Starting workflow: {workflow_type}")
        
        try:
            # انتخاب workflow
            if workflow_type == 'process_audio_consultation':
                return self._process_audio_consultation(data, user)
            elif workflow_type == 'analyze_text':
                return self._analyze_text(data, user)
            else:
                raise ValueError(f'Unknown workflow: {workflow_type}')
                
        except Exception as e:
            self.logger.error(f"Workflow error: {str(e)}")
            raise
    
    def _process_audio_consultation(self, data: dict, user) -> dict:
        """پردازش مشاوره صوتی"""
        # 1. تبدیل صوت به متن
        audio_file = data['audio_file']
        transcription = self.speech_processor.transcribe_audio(audio_file)
        
        # 2. پردازش متن
        analysis = self.text_processor.process_medical_text(
            text=transcription['text'],
            context={'user_id': user.id}
        )
        
        # 3. ذخیره در دیتابیس
        from .models import Consultation
        consultation = Consultation.objects.create(
            user=user,
            transcript=transcription['text'],
            analysis=analysis,
            audio_file=audio_file
        )
        
        # 4. برگرداندن نتیجه
        return {
            'consultation_id': str(consultation.id),
            'transcript': transcription['text'],
            'analysis': analysis
        }
```

## الگوی استفاده در Views

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_consultation(request):
    """پردازش مشاوره"""
    
    # استفاده از orchestrator
    orchestrator = CustomOrchestrator()
    
    try:
        result = orchestrator.execute_workflow(
            workflow_type='process_audio_consultation',
            data=request.data,
            user=request.user
        )
        
        return Response({
            'success': True,
            'data': result
        }, status=200)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': 'processing_failed',
            'message': str(e)
        }, status=500)
```

## سرویس‌های یکپارچه

### استفاده از Unified Services
```python
# احراز هویت
from unified_auth.models import UnifiedUser
from unified_auth.services import UnifiedAuthService

# دسترسی
from unified_access.services import AccessService

# AI
from unified_ai.services import UnifiedAIService

# پرداخت
from unified_billing.services import BillingService

# مثال استفاده
class MyService:
    def __init__(self):
        self.auth_service = UnifiedAuthService()
        self.ai_service = UnifiedAIService()
        self.billing_service = BillingService()
    
    def process(self, user, data):
        # بررسی اعتبار اشتراک
        if not self.billing_service.check_subscription(user):
            raise PermissionError('اشتراک شما منقضی شده')
        
        # پردازش با AI
        result = self.ai_service.process(data)
        
        # ثبت مصرف
        self.billing_service.record_usage(
            user=user,
            service='ai_processing',
            units=1
        )
        
        return result
```

## نکات مهم

### 1. جدایی نگرانی‌ها
- هر هسته فقط مسئولیت خاص خود را دارد
- ارتباط بین هسته‌ها فقط از طریق orchestrator
- هیچ هسته‌ای نباید مستقیماً هسته دیگر را صدا بزند

### 2. مدیریت خطا
- هر هسته باید خطاهای خود را handle کند
- Orchestrator خطاهای کلی را مدیریت می‌کند
- همیشه لاگ مناسب داشته باشید

### 3. تست‌پذیری
- هر هسته باید مستقل قابل تست باشد
- از dependency injection استفاده کنید
- Mock کردن dependencies در تست‌ها