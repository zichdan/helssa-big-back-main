# 💻 نمونه کدهای کاربردی HELSSA

## 📋 فهرست مطالب

- [اتصال به MinIO](## 📦 اتصال به MinIO)
- [پیاده‌سازی درگاه پرداخت BitPay](## 💳 پیاده‌سازی درگاه پرداخت BitPay)
- [ارتباط با OpenAI](## 🤖 ارتباط با OpenAI)
- [OpenAI Agent](## 🤖 OpenAI Agent)
- [ارسال SMS با کاوه‌نگار](## 📱 ارسال SMS با کاوه‌نگار)
- [ارسال ایمیل](## 📧 ارسال ایمیل)
- [Integration با سرویس‌های خارجی](## 🔌 Integration با سرویس‌های خارجی)
- [پردازش و ارسال صدا](## 🎤 پردازش و ارسال صدا)
- [ضبط صدا](## 🎤 ضبط صدا)
- [مسائل فنی پردازش صدا](## 🔍 مسائل فنی پردازش صدا)
- [ایجاد گزارش SOAP](## 📄 ایجاد گزارش SOAP)

---

## 📦 اتصال به MinIO

### پیکربندی اولیه MinIO

```python
# core/storage/minio_client.py
from minio import Minio
from minio.error import S3Error
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class MinIOClient:
    """کلاینت MinIO برای مدیریت فایل‌ها"""
    
    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL
        )
        self._ensure_buckets()
    
    def _ensure_buckets(self):
        """اطمینان از وجود bucket های مورد نیاز"""
        buckets = ['audio', 'documents', 'images', 'backups']
        
        for bucket in buckets:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    logger.info(f"Bucket '{bucket}' created successfully")
            except S3Error as e:
                logger.error(f"Error creating bucket {bucket}: {str(e)}")
    
    def upload_file(self, bucket_name, object_name, file_path, metadata=None):
        """آپلود فایل به MinIO"""
        try:
            # آپلود فایل با metadata
            self.client.fput_object(
                bucket_name=bucket_name,
                object_name=object_name,
                file_path=file_path,
                metadata=metadata or {}
            )
            
            # دریافت URL
            url = self.client.presigned_get_object(
                bucket_name=bucket_name,
                object_name=object_name,
                expires=timedelta(days=7)
            )
            
            logger.info(f"File uploaded successfully: {object_name}")
            return url
            
        except S3Error as e:
            logger.error(f"Error uploading file: {str(e)}")
            raise
    
    def download_file(self, bucket_name, object_name, file_path):
        """دانلود فایل از MinIO"""
        try:
            self.client.fget_object(
                bucket_name=bucket_name,
                object_name=object_name,
                file_path=file_path
            )
            logger.info(f"File downloaded successfully: {object_name}")
            return file_path
            
        except S3Error as e:
            logger.error(f"Error downloading file: {str(e)}")
            raise

# مثال استفاده
minio_client = MinIOClient()

# آپلود فایل صوتی
audio_url = minio_client.upload_file(
    bucket_name='audio',
    object_name='recordings/session_123.mp3',
    file_path='/tmp/recording.mp3',
    metadata={
        'user_id': 'user_123',
        'session_id': 'session_123',
        'duration': '300'
    }
)
```

## 💳 پیاده‌سازی درگاه پرداخت BitPay

### BitPay Payment Gateway

```python
# telemedicine/payment/bitpay.py
import requests
import hashlib
import json
from django.conf import settings
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)

class BitPayGateway:
    """درگاه پرداخت BitPay.ir"""
    
    def __init__(self):
        self.api_key = settings.BITPAY_API_KEY
        self.base_url = "https://bitpay.ir/payment"
        self.gateway_url = "https://bitpay.ir/payment/gateway"
        
    def create_payment(self, amount, order_id, callback_url, description=""):
        """ایجاد پرداخت جدید"""
        
        data = {
            'api': self.api_key,
            'amount': int(amount),
            'redirect': callback_url,
            'factorId': order_id,
            'name': description
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/gateway-send",
                data=data,
                timeout=10
            )
            
            result = response.json()
            
            if result.get('status') == 1:
                # ایجاد موفق
                trans_id = result.get('trans_id')
                payment_url = f"{self.gateway_url}/{trans_id}"
                
                logger.info(f"Payment created: {trans_id}")
                
                return {
                    'success': True,
                    'trans_id': trans_id,
                    'payment_url': payment_url
                }
            else:
                # خطا
                error_code = result.get('errorCode')
                error_message = self._get_error_message(error_code)
                
                logger.error(f"Payment creation failed: {error_message}")
                
                return {
                    'success': False,
                    'error': error_message
                }
                
        except Exception as e:
            logger.error(f"BitPay API error: {str(e)}")
            return {
                'success': False,
                'error': 'خطا در ارتباط با درگاه پرداخت'
            }
    
    def verify_payment(self, trans_id, id_get):
        """تایید پرداخت"""
        
        data = {
            'api': self.api_key,
            'trans_id': trans_id,
            'id_get': id_get
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/gateway-result-second",
                data=data,
                timeout=10
            )
            
            result = response.json()
            
            if result.get('status') == 1:
                # پرداخت موفق
                return {
                    'success': True,
                    'amount': result.get('amount'),
                    'factor_id': result.get('factorId'),
                    'card_number': result.get('cardNumber'),
                    'date': result.get('date')
                }
            else:
                # پرداخت ناموفق
                return {
                    'success': False,
                    'error': self._get_error_message(result.get('errorCode'))
                }
                
        except Exception as e:
            logger.error(f"BitPay verification error: {str(e)}")
            return {
                'success': False,
                'error': 'خطا در تایید پرداخت'
            }
    
    def _get_error_message(self, error_code):
        """دریافت پیام خطا بر اساس کد"""
        
        error_messages = {
            '-1': 'api ارسالی با نوع api تعریف شده در bitpay سازگار نیست',
            '-2': 'مقدار amount داده عددی نمی باشد',
            '-3': 'مقدار redirect رشته null است',
            '-4': 'درگاه پرداختی با api ارسالی یافت نشد',
            '-5': 'خطا در اتصال به درگاه پرداخت'
        }
        
        return error_messages.get(str(error_code), 'خطای نامشخص')

# استفاده در View
# telemedicine/views.py
from django.views import View
from django.shortcuts import redirect
from django.http import JsonResponse

class CreatePaymentView(View):
    """ایجاد پرداخت جدید"""
    
    def post(self, request):
        amount = request.POST.get('amount')
        order_id = request.POST.get('order_id')
        
        # ایجاد callback URL
        callback_url = request.build_absolute_uri(
            reverse('payment:verify')
        )
        
        # ایجاد پرداخت
        gateway = BitPayGateway()
        result = gateway.create_payment(
            amount=amount,
            order_id=order_id,
            callback_url=callback_url,
            description=f"پرداخت سفارش {order_id}"
        )
        
        if result['success']:
            # ذخیره اطلاعات تراکنش
            Payment.objects.create(
                order_id=order_id,
                trans_id=result['trans_id'],
                amount=amount,
                status='pending'
            )
            
            # ریدایرکت به درگاه
            return redirect(result['payment_url'])
        else:
            return JsonResponse({
                'error': result['error']
            }, status=400)

class VerifyPaymentView(View):
    """تایید پرداخت"""
    
    def get(self, request):
        trans_id = request.GET.get('trans_id')
        id_get = request.GET.get('id_get')
        
        # بازیابی اطلاعات پرداخت
        try:
            payment = Payment.objects.get(trans_id=trans_id)
        except Payment.DoesNotExist:
            return JsonResponse({
                'error': 'تراکنش یافت نشد'
            }, status=404)
        
        # تایید پرداخت
        gateway = BitPayGateway()
        result = gateway.verify_payment(trans_id, id_get)
        
        if result['success']:
            # به‌روزرسانی وضعیت
            payment.status = 'completed'
            payment.card_number = result['card_number']
            payment.paid_at = result['date']
            payment.save()
            
            # اجرای عملیات پس از پرداخت موفق
            self._handle_successful_payment(payment)
            
            return redirect('payment:success')
        else:
            payment.status = 'failed'
            payment.save()
            
            return redirect(f"payment:failed?error={result['error']}")
```

## 🤖 ارتباط با OpenAI

### OpenAI Service Implementation

```python
# unified_ai/services/openai_service.py
import openai
from django.conf import settings
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class OpenAIService:
    """سرویس ارتباط با OpenAI"""
    
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        if hasattr(settings, 'OPENAI_BASE_URL'):
            openai.api_base = settings.OPENAI_BASE_URL
            
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_prompt: Optional[str] = None
    ) -> Dict:
        """ایجاد پاسخ چت"""
        
        try:
            # افزودن system prompt
            if system_prompt:
                messages = [
                    {"role": "system", "content": system_prompt}
                ] + messages
            
            # درخواست به OpenAI
            response = await openai.ChatCompletion.acreate(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                presence_penalty=0.6,
                frequency_penalty=0.3
            )
            
            # استخراج پاسخ
            content = response.choices[0].message.content
            usage = response.usage
            
            logger.info(f"OpenAI request successful. Tokens: {usage.total_tokens}")
            
            return {
                'success': True,
                'content': content,
                'usage': {
                    'prompt_tokens': usage.prompt_tokens,
                    'completion_tokens': usage.completion_tokens,
                    'total_tokens': usage.total_tokens
                },
                'model': model
            }
            
        except openai.error.RateLimitError:
            logger.error("OpenAI rate limit exceeded")
            return {
                'success': False,
                'error': 'محدودیت تعداد درخواست. لطفا کمی صبر کنید.'
            }
            
        except Exception as e:
            logger.error(f"OpenAI error: {str(e)}")
            return {
                'success': False,
                'error': 'خطا در ارتباط با سرویس AI'
            }
    
    async def analyze_medical_text(self, text: str) -> Dict:
        """تحلیل متن پزشکی"""
        
        system_prompt = """شما یک دستیار پزشکی هستید. 
        متن پزشکی را تحلیل کرده و اطلاعات مهم را استخراج کنید.
        پاسخ را به صورت JSON با فیلدهای زیر ارائه دهید:
        - symptoms: لیست علائم
        - medications: لیست داروها
        - diagnoses: تشخیص‌های احتمالی
        - recommendations: توصیه‌ها
        """
        
        messages = [
            {"role": "user", "content": text}
        ]
        
        response = await self.chat_completion(
            messages=messages,
            system_prompt=system_prompt,
            temperature=0.3,  # دقت بیشتر
            model="gpt-4"
        )
        
        if response['success']:
            try:
                import json
                analysis = json.loads(response['content'])
                return {
                    'success': True,
                    'analysis': analysis
                }
            except:
                return {
                    'success': False,
                    'error': 'خطا در پردازش پاسخ'
                }
        
        return response
```

## 🤖 OpenAI Agent

### Autonomous Medical Assistant Agent

```python
# unified_ai/agents/medical_agent.py
from typing import List, Dict, Optional
import json
from datetime import datetime

class MedicalAssistantAgent:
    """عامل هوشمند دستیار پزشکی"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.tools = {
            'search_symptoms': self._search_symptoms,
            'check_drug_interactions': self._check_drug_interactions,
            'suggest_tests': self._suggest_tests,
            'create_soap_report': self._create_soap_report
        }
        self.conversation_history = []
        
    async def process_request(
        self,
        user_input: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """پردازش درخواست کاربر"""
        
        # تحلیل intent
        intent = await self._analyze_intent(user_input)
        
        # انتخاب ابزار مناسب
        if intent['tool_needed']:
            tool_name = intent['tool']
            if tool_name in self.tools:
                tool_result = await self.tools[tool_name](
                    user_input,
                    context
                )
                
                # ترکیب نتیجه با پاسخ
                response = await self._generate_response(
                    user_input,
                    tool_result,
                    context
                )
            else:
                response = await self._generate_response(
                    user_input,
                    None,
                    context
                )
        else:
            response = await self._generate_response(
                user_input,
                None,
                context
            )
        
        # ذخیره در history
        self.conversation_history.append({
            'timestamp': datetime.now(),
            'user_input': user_input,
            'response': response,
            'context': context
        })
        
        return response
    
    async def _analyze_intent(self, user_input: str) -> Dict:
        """تحلیل قصد کاربر"""
        
        prompt = f"""تحلیل کنید که آیا متن زیر نیاز به استفاده از ابزار خاصی دارد:
        
        متن: {user_input}
        
        ابزارهای موجود:
        - search_symptoms: جستجوی علائم و بیماری‌ها
        - check_drug_interactions: بررسی تداخل دارویی
        - suggest_tests: پیشنهاد آزمایشات
        - create_soap_report: ایجاد گزارش SOAP
        
        پاسخ را به صورت JSON:
        {{
            "tool_needed": true/false,
            "tool": "نام ابزار" یا null,
            "confidence": 0.0-1.0
        }}
        """
        
        response = await self.openai_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            model="gpt-4"
        )
        
        if response['success']:
            try:
                return json.loads(response['content'])
            except:
                return {'tool_needed': False, 'tool': None}
        
        return {'tool_needed': False, 'tool': None}
    
    async def _search_symptoms(
        self,
        query: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """جستجوی علائم در پایگاه داده"""
        
        # شبیه‌سازی جستجو در دیتابیس
        # در عمل از Elasticsearch یا دیتابیس واقعی استفاده کنید
        
        symptoms_db = {
            'سردرد': {
                'causes': ['میگرن', 'تنش', 'سینوزیت', 'فشار خون'],
                'tests': ['CBC', 'CT Scan', 'فشار خون'],
                'treatments': ['استامینوفن', 'ایبوپروفن', 'استراحت']
            },
            'تب': {
                'causes': ['عفونت', 'آنفولانزا', 'کرونا'],
                'tests': ['CBC', 'CRP', 'تست کرونا'],
                'treatments': ['استامینوفن', 'مایعات', 'استراحت']
            }
        }
        
        results = []
        for symptom, data in symptoms_db.items():
            if symptom in query:
                results.append({
                    'symptom': symptom,
                    'data': data
                })
        
        return {
            'found': len(results) > 0,
            'results': results
        }
    
    async def _generate_response(
        self,
        user_input: str,
        tool_result: Optional[Dict],
        context: Optional[Dict]
    ) -> Dict:
        """تولید پاسخ نهایی"""
        
        system_prompt = """شما یک دستیار پزشکی هستید.
        با دقت و احتیاط پاسخ دهید.
        همیشه توصیه کنید که برای تشخیص دقیق به پزشک مراجعه شود.
        از اطلاعات ابزارها (در صورت وجود) استفاده کنید.
        """
        
        # ساخت پیام با نتایج ابزار
        message_content = f"سوال کاربر: {user_input}"
        
        if tool_result:
            message_content += f"\n\nنتایج جستجو: {json.dumps(tool_result, ensure_ascii=False)}"
        
        if context:
            message_content += f"\n\nاطلاعات بیمار: {json.dumps(context, ensure_ascii=False)}"
        
        response = await self.openai_service.chat_completion(
            messages=[{"role": "user", "content": message_content}],
            system_prompt=system_prompt,
            temperature=0.7
        )
        
        return response

# مثال استفاده
agent = MedicalAssistantAgent()

# پردازش درخواست
result = await agent.process_request(
    user_input="سردرد شدید دارم و تب کردم",
    context={
        'patient_age': 35,
        'gender': 'male',
        'medical_history': ['میگرن']
    }
)

print(result)
```

## 📱 ارسال SMS با کاوه‌نگار

### Kavenegar SMS Service

```python
# core/sms/kavenegar_service.py
from kavenegar import *
from django.conf import settings
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class KavenegarService:
    """سرویس ارسال SMS با کاوه‌نگار"""
    
    def __init__(self):
        self.api_key = settings.KAVENEGAR_API_KEY
        self.sender = settings.KAVENEGAR_SENDER
        self.client = KavenegarAPI(self.api_key)
        
    def send_otp(self, receptor: str, token: str) -> bool:
        """ارسال کد تایید"""
        
        try:
            # استفاده از template تایید شده
            params = {
                'receptor': receptor,
                'token': token,
                'template': 'verify'  # نام template در پنل کاوه‌نگار
            }
            
            response = self.client.verify_lookup(params)
            
            logger.info(f"OTP sent successfully to {receptor}")
            return True
            
        except APIException as e:
            logger.error(f"Kavenegar API error: {e}")
            return False
            
        except HTTPException as e:
            logger.error(f"Kavenegar HTTP error: {e}")
            return False
            
    def send_sms(
        self,
        receptor: str,
        message: str,
        sender: Optional[str] = None
    ) -> bool:
        """ارسال پیامک عادی"""
        
        try:
            params = {
                'sender': sender or self.sender,
                'receptor': receptor,
                'message': message
            }
            
            response = self.client.sms_send(params)
            
            logger.info(f"SMS sent successfully to {receptor}")
            return True
            
        except Exception as e:
            logger.error(f"SMS send error: {e}")
            return False
    
    def send_bulk_sms(
        self,
        receptors: List[str],
        message: str
    ) -> Dict:
        """ارسال پیامک گروهی"""
        
        success_count = 0
        failed_numbers = []
        
        # تقسیم به دسته‌های 200 تایی (محدودیت API)
        batch_size = 200
        
        for i in range(0, len(receptors), batch_size):
            batch = receptors[i:i + batch_size]
            
            try:
                params = {
                    'sender': self.sender,
                    'receptor': batch,
                    'message': message
                }
                
                response = self.client.sms_sendarray(params)
                success_count += len(batch)
                
            except Exception as e:
                logger.error(f"Bulk SMS error: {e}")
                failed_numbers.extend(batch)
        
        return {
            'total': len(receptors),
            'success': success_count,
            'failed': len(failed_numbers),
            'failed_numbers': failed_numbers
        }

# استفاده در سیگنال
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def send_welcome_sms(sender, instance, created, **kwargs):
    """ارسال پیامک خوش‌آمدگویی"""
    
    if created and instance.phone_number:
        sms_service = KavenegarService()
        
        message = f"""سلام {instance.first_name} عزیز
به پلتفرم پزشکی هلسا خوش آمدید.
برای دریافت خدمات به پنل کاربری مراجعه کنید.
helssa.ir"""
        
        sms_service.send_sms(
            receptor=instance.phone_number,
            message=message
        )
```

## 📧 ارسال ایمیل

### Email Service from telemedicine/signals.py

```python
# telemedicine/signals.py
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """سرویس ارسال ایمیل"""
    
    @staticmethod
    def send_appointment_confirmation(appointment):
        """ارسال ایمیل تایید قرار ملاقات"""
        
        subject = f'تایید قرار ملاقات - {appointment.doctor.get_full_name()}'
        
        # رندر کردن template
        html_content = render_to_string(
            'emails/appointment_confirmation.html',
            {
                'appointment': appointment,
                'patient': appointment.patient,
                'doctor': appointment.doctor,
                'meeting_link': appointment.get_meeting_link()
            }
        )
        
        text_content = render_to_string(
            'emails/appointment_confirmation.txt',
            {
                'appointment': appointment,
                'patient': appointment.patient,
                'doctor': appointment.doctor
            }
        )
        
        # ایجاد ایمیل
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[appointment.patient.email],
            reply_to=[appointment.doctor.email]
        )
        
        # افزودن نسخه HTML
        email.attach_alternative(html_content, "text/html")
        
        # افزودن تقویم (iCal)
        ical_content = appointment.generate_ical()
        email.attach(
            'appointment.ics',
            ical_content,
            'text/calendar'
        )
        
        try:
            email.send()
            logger.info(f"Appointment email sent to {appointment.patient.email}")
            return True
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return False
    
    @staticmethod
    def send_prescription_email(prescription):
        """ارسال نسخه دارویی"""
        
        subject = f'نسخه دارویی - دکتر {prescription.doctor.get_full_name()}'
        
        context = {
            'prescription': prescription,
            'patient': prescription.patient,
            'doctor': prescription.doctor,
            'medications': prescription.medications.all(),
            'qr_code_url': prescription.get_qr_code_url()
        }
        
        html_content = render_to_string(
            'emails/prescription.html',
            context
        )
        
        email = EmailMultiAlternatives(
            subject=subject,
            body='نسخه دارویی شما',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[prescription.patient.email]
        )
        
        email.attach_alternative(html_content, "text/html")
        
        # افزودن PDF نسخه
        if prescription.pdf_file:
            email.attach_file(prescription.pdf_file.path)
        
        try:
            email.send()
            return True
        except Exception as e:
            logger.error(f"Prescription email error: {e}")
            return False

# سیگنال‌ها
@receiver(post_save, sender=Appointment)
def appointment_created(sender, instance, created, **kwargs):
    """ارسال ایمیل پس از ایجاد قرار ملاقات"""
    
    if created:
        # ارسال ایمیل به بیمار
        EmailService.send_appointment_confirmation(instance)
        
        # ارسال SMS
        sms_service = KavenegarService()
        sms_service.send_sms(
            receptor=instance.patient.phone_number,
            message=f"قرار ملاقات شما با {instance.doctor.get_full_name()} "
                   f"در تاریخ {instance.scheduled_at.strftime('%Y/%m/%d')} "
                   f"ساعت {instance.scheduled_at.strftime('%H:%M')} ثبت شد."
        )

@receiver(post_save, sender=Prescription)
def prescription_created(sender, instance, created, **kwargs):
    """ارسال نسخه پس از ایجاد"""
    
    if created and instance.is_finalized:
        EmailService.send_prescription_email(instance)
```

## 🔌 Integration با سرویس‌های خارجی

### External API Integration

```python
# integrations/external_api.py
import httpx
import asyncio
from typing import Dict, Optional
from django.conf import settings
import jwt
from datetime import datetime, timedelta

class ExternalAPIClient:
    """کلاینت برای ارتباط با API های خارجی"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'HELSSA/1.0',
                'Accept': 'application/json'
            }
        )
    
    async def authenticate(self) -> str:
        """دریافت توکن احراز هویت"""
        
        response = await self.client.post(
            f"{self.base_url}/auth/token",
            json={
                'api_key': self.api_key,
                'grant_type': 'client_credentials'
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return data['access_token']
        else:
            raise Exception(f"Authentication failed: {response.text}")
    
    async def get_lab_results(self, patient_id: str) -> Dict:
        """دریافت نتایج آزمایشگاه از سیستم خارجی"""
        
        token = await self.authenticate()
        
        response = await self.client.get(
            f"{self.base_url}/lab/results/{patient_id}",
            headers={
                'Authorization': f'Bearer {token}'
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {'error': 'Failed to fetch lab results'}
    
    async def send_referral(self, referral_data: Dict) -> Dict:
        """ارسال ارجاع به مرکز تخصصی"""
        
        token = await self.authenticate()
        
        # امضای دیجیتال داده‌ها
        signed_data = self._sign_data(referral_data)
        
        response = await self.client.post(
            f"{self.base_url}/referrals",
            json=signed_data,
            headers={
                'Authorization': f'Bearer {token}',
                'X-Signature': signed_data['signature']
            }
        )
        
        return response.json()
    
    def _sign_data(self, data: Dict) -> Dict:
        """امضای دیجیتال داده‌ها"""
        
        payload = {
            'data': data,
            'timestamp': datetime.utcnow().isoformat(),
            'exp': datetime.utcnow() + timedelta(minutes=5)
        }
        
        signature = jwt.encode(
            payload,
            settings.JWT_PRIVATE_KEY,
            algorithm='RS256'
        )
        
        data['signature'] = signature
        return data
    
    async def close(self):
        """بستن کانکشن"""
        await self.client.aclose()

# Webhook handler
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import hmac

@csrf_exempt
async def webhook_handler(request):
    """دریافت webhook از سرویس خارجی"""
    
    # تایید امضا
    signature = request.headers.get('X-Webhook-Signature')
    
    if not verify_webhook_signature(request.body, signature):
        return JsonResponse({'error': 'Invalid signature'}, status=401)
    
    # پردازش داده
    data = json.loads(request.body)
    event_type = data.get('event')
    
    if event_type == 'lab_results_ready':
        # نتایج آزمایش آماده است
        await process_lab_results(data['payload'])
        
    elif event_type == 'referral_accepted':
        # ارجاع پذیرفته شده
        await update_referral_status(data['payload'])
    
    return JsonResponse({'status': 'processed'})

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """تایید امضای webhook"""
    
    expected_signature = hmac.new(
        settings.WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)
```

## 🎤 پردازش و ارسال صدا

### Audio Processing Service

```python
# audio/services/audio_processor.py
import wave
import numpy as np
from pydub import AudioSegment
import io
import asyncio
from typing import Tuple, Optional

class AudioProcessor:
    """سرویس پردازش فایل‌های صوتی"""
    
    def __init__(self):
        self.supported_formats = ['wav', 'mp3', 'ogg', 'webm', 'm4a']
        self.target_sample_rate = 16000  # برای STT
        
    async def process_audio_file(
        self,
        file_path: str,
        output_format: str = 'wav'
    ) -> Tuple[bytes, Dict]:
        """پردازش فایل صوتی"""
        
        # بارگذاری فایل
        audio = AudioSegment.from_file(file_path)
        
        # تبدیل به مونو
        audio = audio.set_channels(1)
        
        # تنظیم sample rate
        audio = audio.set_frame_rate(self.target_sample_rate)
        
        # نرمال‌سازی صدا
        audio = self._normalize_audio(audio)
        
        # کاهش نویز
        audio = await self._reduce_noise(audio)
        
        # تبدیل به فرمت خروجی
        output_buffer = io.BytesIO()
        audio.export(
            output_buffer,
            format=output_format,
            parameters=["-q:a", "0"]  # بالاترین کیفیت
        )
        
        # استخراج metadata
        metadata = {
            'duration': len(audio) / 1000.0,  # به ثانیه
            'sample_rate': audio.frame_rate,
            'channels': audio.channels,
            'format': output_format,
            'size': output_buffer.tell()
        }
        
        output_buffer.seek(0)
        return output_buffer.read(), metadata
    
    def _normalize_audio(self, audio: AudioSegment) -> AudioSegment:
        """نرمال‌سازی سطح صدا"""
        
        # محاسبه RMS فعلی
        current_rms = audio.rms
        
        # هدف RMS (برای -20 dB)
        target_rms = 10 ** (-20 / 20) * audio.max_possible_amplitude
        
        # محاسبه gain مورد نیاز
        gain = target_rms / current_rms
        
        # اعمال gain با محدودیت
        return audio.apply_gain(
            min(gain, 10)  # حداکثر 10x افزایش
        )
    
    async def _reduce_noise(self, audio: AudioSegment) -> AudioSegment:
        """کاهش نویز با استفاده از spectral subtraction"""
        
        # تبدیل به numpy array
        samples = np.array(audio.get_array_of_samples())
        
        # تخمین نویز از 0.5 ثانیه اول
        noise_sample = samples[:int(0.5 * audio.frame_rate)]
        noise_fft = np.fft.rfft(noise_sample)
        noise_power = np.abs(noise_fft) ** 2
        
        # اعمال spectral subtraction
        window_size = 2048
        hop_size = window_size // 2
        
        processed_samples = []
        
        for i in range(0, len(samples) - window_size, hop_size):
            window = samples[i:i + window_size]
            
            # FFT
            window_fft = np.fft.rfft(window)
            window_power = np.abs(window_fft) ** 2
            
            # کاهش نویز
            clean_power = window_power - noise_power[:len(window_power)]
            clean_power = np.maximum(clean_power, 0)
            
            # بازسازی سیگنال
            clean_fft = np.sqrt(clean_power) * np.exp(1j * np.angle(window_fft))
            clean_window = np.fft.irfft(clean_fft)
            
            processed_samples.extend(clean_window[:hop_size])
        
        # تبدیل به AudioSegment
        processed_audio = AudioSegment(
            processed_samples.tobytes(),
            frame_rate=audio.frame_rate,
            sample_width=audio.sample_width,
            channels=1
        )
        
        return processed_audio

# استفاده برای ارسال به STT
class AudioUploader:
    """آپلود و ارسال فایل صوتی برای پردازش"""
    
    def __init__(self):
        self.processor = AudioProcessor()
        self.storage = MinIOClient()
        
    async def upload_for_transcription(
        self,
        audio_file,
        session_id: str
    ) -> Dict:
        """آپلود فایل برای رونویسی"""
        
        # پردازش فایل
        processed_audio, metadata = await self.processor.process_audio_file(
            audio_file.temporary_file_path()
        )
        
        # آپلود به MinIO
        object_name = f"audio/sessions/{session_id}/audio.wav"
        
        url = self.storage.upload_file(
            bucket_name='audio',
            object_name=object_name,
            file_path=io.BytesIO(processed_audio),
            metadata={
                'session_id': session_id,
                'original_name': audio_file.name,
                **metadata
            }
        )
        
        # ارسال به صف STT
        stt_task.delay(
            audio_url=url,
            session_id=session_id,
            metadata=metadata
        )
        
        return {
            'session_id': session_id,
            'audio_url': url,
            'metadata': metadata,
            'status': 'processing'
        }
```

## 🎙️ ضبط صدا

### Audio Recording Implementation

```python
# static/js/audio_recorder.js
class AudioRecorder {
    constructor(options = {}) {
        this.options = {
            mimeType: 'audio/webm',
            audioBitsPerSecond: 128000,
            ...options
        };
        
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.stream = null;
        this.startTime = null;
        this.pausedDuration = 0;
        this.isPaused = false;
    }
    
    async initialize() {
        try {
            // درخواست دسترسی به میکروفون
            this.stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 44100
                }
            });
            
            // تنظیم MediaRecorder
            this.mediaRecorder = new MediaRecorder(this.stream, this.options);
            
            // Event handlers
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                this.onRecordingComplete();
            };
            
            // تحلیل real-time صدا
            this.setupAudioAnalyzer();
            
            return true;
            
        } catch (error) {
            console.error('Error initializing recorder:', error);
            throw new Error('دسترسی به میکروفون امکان‌پذیر نیست');
        }
    }
    
    setupAudioAnalyzer() {
        const audioContext = new AudioContext();
        const source = audioContext.createMediaStreamSource(this.stream);
        const analyzer = audioContext.createAnalyser();
        
        analyzer.fftSize = 256;
        source.connect(analyzer);
        
        const bufferLength = analyzer.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        
        // نمایش سطح صدا
        const checkAudioLevel = () => {
            analyzer.getByteFrequencyData(dataArray);
            
            const average = dataArray.reduce((a, b) => a + b) / bufferLength;
            const level = average / 255; // نرمال‌سازی به 0-1
            
            // ارسال event برای نمایش در UI
            this.onAudioLevel(level);
            
            if (this.mediaRecorder?.state === 'recording') {
                requestAnimationFrame(checkAudioLevel);
            }
        };
        
        this.checkAudioLevel = checkAudioLevel;
    }
    
    start() {
        if (this.mediaRecorder?.state === 'inactive') {
            this.audioChunks = [];
            this.startTime = Date.now();
            this.mediaRecorder.start(1000); // ذخیره هر 1 ثانیه
            this.checkAudioLevel();
            this.onStateChange('recording');
        }
    }
    
    pause() {
        if (this.mediaRecorder?.state === 'recording') {
            this.mediaRecorder.pause();
            this.pauseStartTime = Date.now();
            this.isPaused = true;
            this.onStateChange('paused');
        }
    }
    
    resume() {
        if (this.mediaRecorder?.state === 'paused') {
            this.mediaRecorder.resume();
            this.pausedDuration += Date.now() - this.pauseStartTime;
            this.isPaused = false;
            this.checkAudioLevel();
            this.onStateChange('recording');
        }
    }
    
    stop() {
        if (this.mediaRecorder && 
            (this.mediaRecorder.state === 'recording' || 
             this.mediaRecorder.state === 'paused')) {
            this.mediaRecorder.stop();
            this.stream.getTracks().forEach(track => track.stop());
            this.onStateChange('stopped');
        }
    }
    
    async onRecordingComplete() {
        const audioBlob = new Blob(this.audioChunks, {
            type: this.options.mimeType
        });
        
        const duration = (Date.now() - this.startTime - this.pausedDuration) / 1000;
        
        // تبدیل به WAV برای سازگاری بهتر
        const wavBlob = await this.convertToWav(audioBlob);
        
        // آپلود به سرور
        await this.uploadAudio(wavBlob, duration);
    }
    
    async convertToWav(blob) {
        // استفاده از Web Audio API برای تبدیل
        const audioContext = new AudioContext();
        const arrayBuffer = await blob.arrayBuffer();
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        
        // ایجاد WAV
        const wavBuffer = this.audioBufferToWav(audioBuffer);
        return new Blob([wavBuffer], { type: 'audio/wav' });
    }
    
    audioBufferToWav(buffer) {
        const numOfChan = buffer.numberOfChannels;
        const length = buffer.length * numOfChan * 2 + 44;
        const out = new ArrayBuffer(length);
        const view = new DataView(out);
        const channels = [];
        let sample;
        let offset = 0;
        let pos = 0;
        
        // WAV header
        setUint32(0x46464952); // "RIFF"
        setUint32(length - 8); // file length - 8
        setUint32(0x45564157); // "WAVE"
        
        setUint32(0x20746d66); // "fmt " chunk
        setUint32(16); // length = 16
        setUint16(1); // PCM
        setUint16(numOfChan);
        setUint32(buffer.sampleRate);
        setUint32(buffer.sampleRate * 2 * numOfChan); // avg. bytes/sec
        setUint16(numOfChan * 2); // block-align
        setUint16(16); // 16-bit
        
        setUint32(0x61746164); // "data" chunk
        setUint32(length - pos - 4); // chunk length
        
        // Write interleaved data
        for (let i = 0; i < buffer.numberOfChannels; i++) {
            channels.push(buffer.getChannelData(i));
        }
        
        while (pos < length) {
            for (let i = 0; i < numOfChan; i++) {
                sample = Math.max(-1, Math.min(1, channels[i][offset]));
                sample = (sample * 0x7FFF) | 0;
                view.setInt16(pos, sample, true);
                pos += 2;
            }
            offset++;
        }
        
        return out;
        
        function setUint16(data) {
            view.setUint16(pos, data, true);
            pos += 2;
        }
        
        function setUint32(data) {
            view.setUint32(pos, data, true);
            pos += 4;
        }
    }
    
    async uploadAudio(blob, duration) {
        const formData = new FormData();
        formData.append('audio', blob, 'recording.wav');
        formData.append('duration', duration);
        formData.append('session_id', this.options.sessionId);
        
        try {
            const response = await fetch('/api/v1/audio/upload/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.options.token}`
                },
                body: formData
            });
            
            const result = await response.json();
            this.onUploadComplete(result);
            
        } catch (error) {
            this.onUploadError(error);
        }
    }
    
    // Callbacks
    onStateChange(state) {
        console.log('Recorder state:', state);
    }
    
    onAudioLevel(level) {
        // Override in implementation
    }
    
    onUploadComplete(result) {
        console.log('Upload complete:', result);
    }
    
    onUploadError(error) {
        console.error('Upload error:', error);
    }
}

// استفاده در React Component
const RecordingComponent = () => {
    const [recorder, setRecorder] = useState(null);
    const [isRecording, setIsRecording] = useState(false);
    const [audioLevel, setAudioLevel] = useState(0);
    
    useEffect(() => {
        const audioRecorder = new AudioRecorder({
            sessionId: 'session_123',
            token: localStorage.getItem('access_token')
        });
        
        audioRecorder.onAudioLevel = (level) => {
            setAudioLevel(level);
        };
        
        audioRecorder.onStateChange = (state) => {
            setIsRecording(state === 'recording');
        };
        
        audioRecorder.onUploadComplete = (result) => {
            // نمایش نتیجه رونویسی
            console.log('Transcription:', result);
        };
        
        audioRecorder.initialize().then(() => {
            setRecorder(audioRecorder);
        });
        
        return () => {
            audioRecorder.stop();
        };
    }, []);
    
    return (
        <div className="recorder-container">
            <div className="audio-level">
                <div 
                    className="level-bar"
                    style={{ width: `${audioLevel * 100}%` }}
                />
            </div>
            
            <button
                onClick={() => {
                    if (isRecording) {
                        recorder.stop();
                    } else {
                        recorder.start();
                    }
                }}
                className={isRecording ? 'recording' : ''}
            >
                {isRecording ? 'توقف ضبط' : 'شروع ضبط'}
            </button>
            
            {isRecording && (
                <button onClick={() => recorder.pause()}>
                    مکث
                </button>
            )}
        </div>
    );
};
```

## 🔧 مسائل فنی پردازش صدا

### Technical Audio Processing Issues

```python
# audio/technical/audio_issues.py

class AudioTechnicalHandler:
    """مدیریت مسائل فنی پردازش صوت"""
    
    def __init__(self):
        self.sample_rate_target = 16000
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        
    async def handle_audio_issues(self, audio_file) -> Dict:
        """بررسی و رفع مشکلات فنی فایل صوتی"""
        
        issues = []
        solutions = []
        
        # بررسی فرمت
        format_issue = self._check_format(audio_file)
        if format_issue:
            issues.append(format_issue)
            solutions.append(await self._fix_format(audio_file))
        
        # بررسی sample rate
        sr_issue = self._check_sample_rate(audio_file)
        if sr_issue:
            issues.append(sr_issue)
            solutions.append(await self._fix_sample_rate(audio_file))
        
        # بررسی کیفیت
        quality_issue = self._check_quality(audio_file)
        if quality_issue:
            issues.append(quality_issue)
            solutions.append(await self._enhance_quality(audio_file))
        
        # بررسی حجم
        size_issue = self._check_file_size(audio_file)
        if size_issue:
            issues.append(size_issue)
            solutions.append(await self._compress_audio(audio_file))
        
        return {
            'issues_found': len(issues),
            'issues': issues,
            'solutions_applied': solutions,
            'processed_file': audio_file
        }
    
    def _check_format(self, audio_file) -> Optional[str]:
        """بررسی فرمت فایل"""
        
        # استفاده از ffprobe برای تشخیص دقیق
        import subprocess
        
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=format_name',
                '-of', 'json', audio_file.path
            ], capture_output=True, text=True)
            
            data = json.loads(result.stdout)
            format_name = data['format']['format_name']
            
            # فرمت‌های مشکل‌دار برای STT
            problematic_formats = ['amr', 'wma', 'aac']
            
            if format_name in problematic_formats:
                return f"فرمت {format_name} برای پردازش STT مناسب نیست"
                
        except Exception as e:
            return f"خطا در تشخیص فرمت: {str(e)}"
            
        return None
    
    async def _fix_format(self, audio_file) -> str:
        """تبدیل به فرمت مناسب"""
        
        output_path = audio_file.path.replace(
            audio_file.ext,
            '.wav'
        )
        
        # تبدیل با ffmpeg
        cmd = [
            'ffmpeg', '-i', audio_file.path,
            '-acodec', 'pcm_s16le',
            '-ar', str(self.sample_rate_target),
            '-ac', '1',  # مونو
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        await process.communicate()
        
        return "تبدیل به فرمت WAV انجام شد"
    
    def _check_quality(self, audio_file) -> Optional[str]:
        """بررسی کیفیت صوت"""
        
        audio = AudioSegment.from_file(audio_file.path)
        
        # بررسی SNR (Signal-to-Noise Ratio)
        signal_power = audio.rms
        
        # تخمین نویز از بخش ساکت
        silent_parts = detect_silence(
            audio,
            min_silence_len=500,
            silence_thresh=-40
        )
        
        if silent_parts:
            noise_segment = audio[silent_parts[0][0]:silent_parts[0][1]]
            noise_power = noise_segment.rms
            
            snr = 20 * np.log10(signal_power / (noise_power + 1e-10))
            
            if snr < 10:  # SNR کمتر از 10 دسی‌بل
                return f"کیفیت صوت پایین است (SNR: {snr:.1f} dB)"
                
        # بررسی clipping
        samples = np.array(audio.get_array_of_samples())
        max_sample = np.max(np.abs(samples))
        
        if max_sample > 0.95 * audio.max_possible_amplitude:
            return "صدا دارای برش (clipping) است"
            
        return None
    
    async def _enhance_quality(self, audio_file) -> str:
        """بهبود کیفیت صوت"""
        
        # استفاده از کتابخانه noisereduce
        import noisereduce as nr
        
        # بارگذاری صوت
        audio = AudioSegment.from_file(audio_file.path)
        samples = np.array(audio.get_array_of_samples())
        
        # کاهش نویز
        reduced_noise = nr.reduce_noise(
            y=samples,
            sr=audio.frame_rate,
            stationary=True,
            prop_decrease=1.0
        )
        
        # نرمال‌سازی
        normalized = reduced_noise / np.max(np.abs(reduced_noise))
        normalized = (normalized * 0.8 * audio.max_possible_amplitude).astype(np.int16)
        
        # ذخیره
        enhanced_audio = AudioSegment(
            normalized.tobytes(),
            frame_rate=audio.frame_rate,
            sample_width=audio.sample_width,
            channels=audio.channels
        )
        
        enhanced_path = audio_file.path.replace('.', '_enhanced.')
        enhanced_audio.export(enhanced_path, format='wav')
        
        return "کیفیت صوت بهبود یافت"

# مسائل رایج و راه‌حل‌ها
COMMON_AUDIO_ISSUES = {
    'low_volume': {
        'description': 'صدای ضعیف',
        'detection': lambda audio: audio.rms < 100,
        'solution': 'تقویت صدا با normalize',
        'code': '''
audio = audio.normalize()  # یا
audio = audio + 10  # افزایش 10dB
        '''
    },
    
    'background_noise': {
        'description': 'نویز پس‌زمینه',
        'detection': 'SNR < 15dB',
        'solution': 'استفاده از noisereduce',
        'code': '''
import noisereduce as nr
reduced = nr.reduce_noise(audio_data, sr=sample_rate)
        '''
    },
    
    'echo': {
        'description': 'اکو در صدا',
        'detection': 'Cross-correlation analysis',
        'solution': 'Echo cancellation',
        'code': '''
# استفاده از speexdsp
from speexdsp import EchoCanceller
ec = EchoCanceller.create(frame_size, filter_length)
        '''
    },
    
    'wrong_sample_rate': {
        'description': 'نرخ نمونه‌برداری نامناسب',
        'detection': 'sample_rate != 16000',
        'solution': 'Resample به 16kHz',
        'code': '''
audio = audio.set_frame_rate(16000)
        '''
    },
    
    'stereo_to_mono': {
        'description': 'تبدیل استریو به مونو',
        'detection': 'channels > 1',
        'solution': 'میانگین کانال‌ها',
        'code': '''
audio = audio.set_channels(1)
        '''
    }
}
```

## 📝 ایجاد گزارش SOAP

### SOAP Report Generation

```python
# outputs/soap_generator.py
from typing import Dict, List, Optional
import json
from datetime import datetime

class SOAPReportGenerator:
    """تولیدکننده گزارش SOAP از رونویسی"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.template_engine = TemplateEngine()
        
    async def generate_soap_from_transcript(
        self,
        transcript: str,
        patient_info: Dict,
        doctor_info: Dict,
        encounter_id: str
    ) -> Dict:
        """تولید گزارش SOAP از رونویسی ملاقات"""
        
        # آماده‌سازی context
        context = self._prepare_context(
            transcript,
            patient_info,
            doctor_info
        )
        
        # تولید بخش‌های SOAP
        soap_sections = await asyncio.gather(
            self._generate_subjective(context),
            self._generate_objective(context),
            self._generate_assessment(context),
            self._generate_plan(context)
        )
        
        # ترکیب بخش‌ها
        soap_report = {
            'encounter_id': encounter_id,
            'generated_at': datetime.now().isoformat(),
            'subjective': soap_sections[0],
            'objective': soap_sections[1],
            'assessment': soap_sections[2],
            'plan': soap_sections[3],
            'metadata': {
                'generator_version': '2.0',
                'confidence_score': self._calculate_confidence(soap_sections),
                'word_count': len(transcript.split())
            }
        }
        
        # ذخیره در دیتابیس
        await self._save_soap_report(soap_report)
        
        # تولید فرمت‌های مختلف
        formats = await self._generate_formats(soap_report)
        
        return {
            'soap_report': soap_report,
            'formats': formats
        }
    
    async def _generate_subjective(self, context: Dict) -> Dict:
        """تولید بخش Subjective"""
        
        prompt = f"""
        بر اساس رونویسی زیر، بخش Subjective گزارش SOAP را تولید کنید.
        
        اطلاعات بیمار:
        {json.dumps(context['patient_info'], ensure_ascii=False)}
        
        رونویسی:
        {context['transcript']}
        
        بخش Subjective باید شامل:
        1. Chief Complaint (CC)
        2. History of Present Illness (HPI) با جزئیات OLDCARTS
        3. Review of Systems (ROS)
        4. Past Medical History (PMH)
        5. Medications
        6. Allergies
        7. Social History (در صورت ذکر)
        8. Family History (در صورت ذکر)
        
        پاسخ را به صورت JSON ساختاریافته ارائه دهید.
        """
        
        response = await self.openai_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            model="gpt-4"
        )
        
        if response['success']:
            return json.loads(response['content'])
        else:
            raise Exception("Failed to generate subjective section")
    
    async def _generate_formats(self, soap_report: Dict) -> Dict:
        """تولید فرمت‌های مختلف گزارش"""
        
        # HTML format
        html_content = await self.template_engine.render(
            'soap_report.html',
            context=soap_report
        )
        
        # PDF format
        pdf_generator = PDFGenerator()
        pdf_path = await pdf_generator.generate_from_html(
            html_content,
            f"soap_{soap_report['encounter_id']}.pdf"
        )
        
        # Markdown format
        md_content = self._generate_markdown(soap_report)
        
        # Word format
        docx_generator = DocxGenerator()
        docx_path = await docx_generator.generate_soap(
            soap_report,
            f"soap_{soap_report['encounter_id']}.docx"
        )
        
        return {
            'html': html_content,
            'pdf': pdf_path,
            'markdown': md_content,
            'docx': docx_path
        }
    
    def _generate_markdown(self, soap_report: Dict) -> str:
        """تولید فرمت Markdown"""
        
        md = f"""# گزارش SOAP
        
تاریخ: {soap_report['generated_at']}
شماره ملاقات: {soap_report['encounter_id']}

## Subjective (شرح حال)

**شکایت اصلی:** {soap_report['subjective']['chief_complaint']}

**تاریخچه بیماری فعلی:**
{soap_report['subjective']['hpi']['narrative']}

- **شروع:** {soap_report['subjective']['hpi'].get('onset', 'نامشخص')}
- **محل:** {soap_report['subjective']['hpi'].get('location', 'نامشخص')}
- **مدت:** {soap_report['subjective']['hpi'].get('duration', 'نامشخص')}
- **شدت:** {soap_report['subjective']['hpi'].get('severity', 'نامشخص')}/10

**سابقه پزشکی:**
{chr(10).join('- ' + pmh for pmh in soap_report['subjective'].get('pmh', []))}

**داروهای مصرفی:**
{chr(10).join('- ' + med for med in soap_report['subjective'].get('medications', []))}

**آلرژی‌ها:**
{chr(10).join('- ' + allergy for allergy in soap_report['subjective'].get('allergies', []))}

## Objective (معاینه)

**علائم حیاتی:**
- فشار خون: {soap_report['objective']['vital_signs'].get('bp', 'ثبت نشده')}
- ضربان قلب: {soap_report['objective']['vital_signs'].get('hr', 'ثبت نشده')}
- تنفس: {soap_report['objective']['vital_signs'].get('rr', 'ثبت نشده')}
- دما: {soap_report['objective']['vital_signs'].get('temp', 'ثبت نشده')}

**معاینه فیزیکی:**
{soap_report['objective'].get('physical_exam', 'انجام نشده')}

## Assessment (ارزیابی)

**تشخیص‌ها:**
{chr(10).join(f"{i+1}. {dx['description']} (ICD-10: {dx.get('icd_code', 'N/A')})" 
              for i, dx in enumerate(soap_report['assessment'].get('diagnoses', [])))}

## Plan (برنامه درمان)

**داروها:**
{chr(10).join(f"- {med['name']} {med['dosage']} - {med['frequency']} برای {med['duration']}" 
              for med in soap_report['plan'].get('medications', []))}

**آزمایشات:**
{chr(10).join('- ' + test for test in soap_report['plan'].get('lab_orders', []))}

**پیگیری:** {soap_report['plan'].get('follow_up', 'تعیین نشده')}

---
*این گزارش به صورت خودکار تولید شده است*
"""
        return md

# استفاده در API
from rest_framework.views import APIView
from rest_framework.response import Response

class GenerateSOAPView(APIView):
    """API برای تولید گزارش SOAP"""
    
    permission_classes = [IsAuthenticated, IsDoctor]
    
    def post(self, request):
        encounter_id = request.data.get('encounter_id')
        
        # بازیابی اطلاعات
        encounter = Encounter.objects.get(id=encounter_id)
        transcript = encounter.transcripts.first()
        
        if not transcript:
            return Response({
                'error': 'رونویسی یافت نشد'
            }, status=404)
        
        # تولید SOAP
        generator = SOAPReportGenerator()
        
        try:
            result = asyncio.run(
                generator.generate_soap_from_transcript(
                    transcript=transcript.text,
                    patient_info={
                        'name': encounter.patient.get_full_name(),
                        'age': encounter.patient.age,
                        'gender': encounter.patient.gender,
                        'medical_record_number': encounter.patient.mrn
                    },
                    doctor_info={
                        'name': request.user.get_full_name(),
                        'specialty': request.user.specialty,
                        'medical_license': request.user.medical_license_number
                    },
                    encounter_id=str(encounter_id)
                )
            )
            
            return Response({
                'success': True,
                'soap_report': result['soap_report'],
                'download_links': {
                    'pdf': f"/api/v1/soap/{encounter_id}/download/pdf/",
                    'docx': f"/api/v1/soap/{encounter_id}/download/docx/",
                    'html': f"/api/v1/soap/{encounter_id}/download/html/"
                }
            })
            
        except Exception as e:
            logger.error(f"SOAP generation error: {str(e)}")
            return Response({
                'error': 'خطا در تولید گزارش'
            }, status=500)
```

---

[ELEMENT: div align="center"]

✨ **این نمونه کدها آماده استفاده در پروژه HELSSA هستند**

برای سوالات فنی به مستندات API مراجعه کنید

[→ قبلی: راهنمای شروع سریع](17-quick-start.md) | [پایان مستندات]

</div>
