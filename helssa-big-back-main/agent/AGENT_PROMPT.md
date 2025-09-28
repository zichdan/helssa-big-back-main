# 🤖 پرامپت اصلی برای ایجنت‌های توسعه اپلیکیشن هلسا

## دستورالعمل اجرایی ایجنت

شما یک ایجنت توسعه‌دهنده حرفه‌ای برای پلتفرم هلسا هستید. وظیفه شما ایجاد یک اپلیکیشن کامل بر اساس معماری چهار هسته‌ای و استانداردهای تعریف شده است.

### 📋 ورودی‌های مورد نیاز از کاربر

1. **نام اپلیکیشن**: (مثال: patient_chatbot)
2. **توضیح مختصر**: (مثال: چت‌بات پزشکی برای بیماران)

### 🎯 خروجی‌های مورد انتظار

1. **کد کامل اپلیکیشن** در مسیر `apps/{app_name}/`
2. **مستندات کامل** شامل README و API spec
3. **تست‌های نوشته شده** (بدون نیاز به اجرا)
4. **فایل‌های deployment** برای integration
5. **گزارش پیشرفت** با نمودار SVG

## 🔄 فرآیند اجرایی گام به گام

### گام 1: مطالعه و آماده‌سازی (10%)

```bash
1. مطالعه unified_agent/instructions/CORE_ARCHITECTURE.md
2. مطالعه unified_agent/instructions/SECURITY_POLICIES.md
3. بررسی unified_agent/app_standards/
4. ایجاد پوشه apps/{app_name}/
```

### گام 2: طراحی و برنامه‌ریزی (20%)

```bash
1. کپی unified_agent/templates/PLAN.md.template به apps/{app_name}/PLAN.md
2. تکمیل PLAN.md با:
   - تعریف دقیق scope
   - لیست API endpoints
   - طراحی مدل‌های داده
   - تعیین dependencies
   - نقشه راه پیاده‌سازی
```

### گام 3: ایجاد ساختار پایه (30%)

```bash
apps/{app_name}/
├── app_code/
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── permissions.py
│   ├── cores/
│   │   ├── __init__.py
│   │   ├── api_ingress.py
│   │   ├── text_processor.py
│   │   ├── speech_processor.py
│   │   └── orchestrator.py
│   ├── services/
│   ├── migrations/
│   └── tests/
├── deployment/
│   ├── settings_additions.py
│   ├── urls_additions.py
│   └── requirements_additions.txt
└── docs/
    ├── api_spec.yaml
    ├── user_manual.md
    └── admin_guide.md
```

### گام 4: پیاده‌سازی چهار هسته (50%)

#### 4.1 هسته API Ingress

```python
# app_code/cores/api_ingress.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from unified_auth.decorators import require_patient_access
import logging

logger = logging.getLogger(__name__)

class APIIngressCore:
    """هسته مدیریت ورودی API"""
    
    def validate_request(self, request_data, serializer_class):
        """اعتبارسنجی درخواست"""
        serializer = serializer_class(data=request_data)
        if not serializer.is_valid():
            return False, serializer.errors
        return True, serializer.validated_data
    
    def check_permissions(self, user, resource, action):
        """بررسی دسترسی‌ها"""
        # Implementation based on unified_access
        pass
    
    def log_request(self, request, response_status):
        """ثبت لاگ درخواست"""
        logger.info(f"API Request: {request.path} - Status: {response_status}")
```

#### 4.2 هسته Text Processing

```python
# app_code/cores/text_processor.py
from unified_ai.services import UnifiedAIService

class TextProcessorCore:
    """هسته پردازش متن"""
    
    def __init__(self):
        self.ai_service = UnifiedAIService()
    
    def process_medical_text(self, text, context):
        """پردازش متن پزشکی"""
        return self.ai_service.process_text(
            text=text,
            context=context,
            task='medical_analysis'
        )
```

#### 4.3 هسته Speech Processing (در صورت نیاز)

```python
# app_code/cores/speech_processor.py
from unified_ai.services import STTService

class SpeechProcessorCore:
    """هسته پردازش صوت"""
    
    def __init__(self):
        self.stt_service = STTService()
    
    def transcribe_audio(self, audio_file):
        """تبدیل صوت به متن"""
        return self.stt_service.transcribe(audio_file)
```

#### 4.4 هسته Orchestration

```python
# app_code/cores/orchestrator.py
class CentralOrchestrator:
    """هماهنگ‌کننده مرکزی"""
    
    def __init__(self):
        self.api_core = APIIngressCore()
        self.text_core = TextProcessorCore()
        self.speech_core = SpeechProcessorCore()
    
    def execute_workflow(self, workflow_name, data, user):
        """اجرای فرآیند کاری"""
        # Implementation based on workflow
        pass
```

### گام 5: پیاده‌سازی Models (60%)

```python
# app_code/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class BaseModel(models.Model):
    """مدل پایه برای همه مدل‌ها"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='%(class)s_created'
    )
    
    class Meta:
        abstract = True
        ordering = ['-created_at']

# مدل‌های اختصاصی اپ
```

### گام 6: پیاده‌سازی Views و APIs (70%)

```python
# app_code/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .cores.orchestrator import CentralOrchestrator
from .serializers import RequestSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def main_endpoint(request):
    """نقطه ورود اصلی API"""
    try:
        orchestrator = CentralOrchestrator()
        
        # Validation
        is_valid, data = orchestrator.api_core.validate_request(
            request.data, 
            RequestSerializer
        )
        if not is_valid:
            return Response(
                {'error': 'Invalid input', 'details': data},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process
        result = orchestrator.execute_workflow(
            'main_workflow',
            data,
            request.user
        )
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

### گام 7: نوشتن تست‌ها (80%)

```python
# app_code/tests/test_integration.py
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

class AppIntegrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_main_workflow(self):
        """تست فرآیند اصلی"""
        response = self.client.post('/api/{app_name}/main/', {
            'data': 'test'
        })
        self.assertEqual(response.status_code, 200)
```

### گام 8: ایجاد Deployment Files (90%)

```python
# deployment/settings_additions.py
INSTALLED_APPS += [
    '{app_name}.apps.{AppName}Config',
]

# Rate limiting
RATE_LIMIT_{APP_NAME} = {
    'api_calls': '100/minute',
    'ai_requests': '20/minute',
}

# Logging
LOGGING['loggers']['{app_name}'] = {
    'handlers': ['file', 'console'],
    'level': 'INFO',
    'propagate': False,
}
```

### گام 9: مستندسازی (95%)

```yaml
# docs/api_spec.yaml
openapi: 3.0.0
info:
  title: {App Name} API
  version: 1.0.0
  description: API documentation for {app_name}

paths:
  /api/{app_name}/main/:
    post:
      summary: Main endpoint
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        200:
          description: Success
```

### گام 10: تکمیل و بررسی نهایی (100%)

```json
// CHECKLIST.json
{
  "architecture": {
    "four_cores_implemented": true,
    "unified_auth_integrated": true,
    "security_policies_followed": true
  },
  "code_quality": {
    "tests_written": true,
    "documentation_complete": true,
    "error_handling": true
  },
  "deployment": {
    "settings_updated": true,
    "urls_configured": true,
    "requirements_listed": true
  }
}
```

## ⚠️ نکات بسیار مهم

### ✅ الزامات مطلق

1. **هرگز** مدل User جدید نسازید - فقط UnifiedUser
2. **حتماً** معماری چهار هسته‌ای را رعایت کنید
3. **همیشه** از unified services استفاده کنید
4. **بدون استثناء** سیاست‌های امنیتی را اجرا کنید
5. **دقیقاً** طبق الگوهای تعریف شده کد بزنید

### 🚫 ممنوعیت‌های مطلق

1. ایجاد user model جدید
2. استفاده از Raw SQL
3. Hard-coded values
4. تغییر معماری چهار هسته‌ای
5. نادیده گرفتن security policies

### 📊 معیارهای پذیرش

1. تست‌ها نوشته شده (اجرا نمی‌شود)
2. مستندات کامل
3. رعایت تمام استانداردها
4. یکپارچگی با unified services
5. گزارش پیشرفت 100%

## 🎁 خروجی نهایی

پس از اتمام، اپلیکیشن شما باید:

1. **کاملاً عملیاتی** و آماده deployment باشد
2. **یکپارچه** با تمام سرویس‌های unified باشد
3. **مستند** با API spec و راهنماها باشد
4. **تست شده** با coverage مناسب باشد
5. **استاندارد** طبق معماری تعریف شده باشد

---

**یادآوری**: این پرامپت را دقیقاً و بدون تغییر دنبال کنید. هیچ تصمیم سلیقه‌ای مجاز نیست.
