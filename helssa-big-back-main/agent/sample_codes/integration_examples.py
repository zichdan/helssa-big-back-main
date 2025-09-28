"""
نمونه کدهای Integration برای ایجنت‌ها
Sample Integration Code Examples for Agents
"""

from typing import Dict, Any, Optional, List
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from rest_framework.exceptions import APIException
import requests
import logging
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


# ====================================
# نمونه 1: Unified Auth Integration
# ====================================

class UnifiedAuthIntegration:
    """
    یکپارچه‌سازی با سیستم احراز هویت یکپارچه
    """
    
    def __init__(self):
        self.auth_service_url = getattr(settings, 'UNIFIED_AUTH_URL', '')
        self.api_key = getattr(settings, 'UNIFIED_AUTH_API_KEY', '')
    
    def verify_user_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        تأیید توکن کاربر
        
        Args:
            token: JWT token
            
        Returns:
            اطلاعات کاربر یا None
        """
        try:
            # بررسی کش
            cache_key = f"auth_token:{hashlib.md5(token.encode()).hexdigest()}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data
            
            # درخواست به سرویس
            headers = {
                'Authorization': f'Bearer {token}',
                'X-API-Key': self.api_key
            }
            
            response = requests.post(
                f"{self.auth_service_url}/verify",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                user_data = response.json()
                # ذخیره در کش برای 5 دقیقه
                cache.set(cache_key, user_data, 300)
                return user_data
            
            return None
            
        except Exception as e:
            logger.error(f"Auth verification error: {str(e)}")
            return None
    
    def send_otp(self, phone_number: str) -> bool:
        """
        ارسال کد OTP
        
        Args:
            phone_number: شماره موبایل
            
        Returns:
            موفقیت عملیات
        """
        try:
            from unified_auth.services import OTPService
            
            otp_service = OTPService()
            return otp_service.send_otp(phone_number)
            
        except Exception as e:
            logger.error(f"OTP sending error: {str(e)}")
            return False
    
    def check_user_permissions(self, user_id: str, resource: str, 
                             action: str) -> bool:
        """
        بررسی دسترسی کاربر
        
        Args:
            user_id: شناسه کاربر
            resource: نام منبع
            action: نوع عملیات
            
        Returns:
            دسترسی مجاز یا خیر
        """
        try:
            from unified_access.services import AccessControlService
            
            access_service = AccessControlService()
            return access_service.check_permission(
                user_id=user_id,
                resource=resource,
                action=action
            )
            
        except Exception as e:
            logger.error(f"Permission check error: {str(e)}")
            # در صورت خطا، دسترسی را محدود می‌کنیم
            return False


# ====================================
# نمونه 2: Unified AI Integration
# ====================================

class UnifiedAIIntegration:
    """
    یکپارچه‌سازی با سیستم AI یکپارچه
    """
    
    def __init__(self):
        from unified_ai.services import UnifiedAIService
        self.ai_service = UnifiedAIService()
        self.max_retries = 3
        self.retry_delay = 1  # seconds
    
    def process_medical_query(self, query: str, patient_context: Dict[str, Any],
                            conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        پردازش سوال پزشکی با AI
        
        Args:
            query: سوال کاربر
            patient_context: اطلاعات بیمار
            conversation_history: تاریخچه مکالمه
            
        Returns:
            پاسخ AI
        """
        try:
            # آماده‌سازی context
            context = {
                'patient_age': patient_context.get('age'),
                'patient_gender': patient_context.get('gender'),
                'medical_history': patient_context.get('medical_history', []),
                'current_medications': patient_context.get('medications', []),
                'conversation_history': conversation_history or []
            }
            
            # تلاش با retry
            for attempt in range(self.max_retries):
                try:
                    response = self.ai_service.process_medical_query(
                        query=query,
                        context=context,
                        model='medical-gpt-4'
                    )
                    
                    # ثبت استفاده
                    self._log_ai_usage(query, response)
                    
                    return {
                        'success': True,
                        'response': response.get('text'),
                        'suggestions': response.get('suggestions', []),
                        'confidence': response.get('confidence', 0.0),
                        'warnings': response.get('warnings', [])
                    }
                    
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        import time
                        time.sleep(self.retry_delay * (attempt + 1))
                    else:
                        raise
            
        except Exception as e:
            logger.error(f"AI processing error: {str(e)}")
            return {
                'success': False,
                'error': 'خطا در پردازش درخواست',
                'fallback_response': 'متاسفانه در حال حاضر امکان پاسخگویی وجود ندارد. لطفا با پزشک خود مشورت کنید.'
            }
    
    def transcribe_medical_audio(self, audio_file_path: str,
                               language: str = 'fa') -> Dict[str, Any]:
        """
        تبدیل صوت پزشکی به متن
        
        Args:
            audio_file_path: مسیر فایل صوتی
            language: زبان صوت
            
        Returns:
            نتیجه رونویسی
        """
        try:
            result = self.ai_service.transcribe_audio(
                file_path=audio_file_path,
                language=language,
                medical_mode=True
            )
            
            return {
                'success': True,
                'text': result.get('text'),
                'segments': result.get('segments', []),
                'confidence': result.get('confidence', 0.0),
                'duration': result.get('duration')
            }
            
        except Exception as e:
            logger.error(f"Audio transcription error: {str(e)}")
            return {
                'success': False,
                'error': 'خطا در پردازش فایل صوتی'
            }
    
    def _log_ai_usage(self, query: str, response: Dict[str, Any]):
        """ثبت استفاده از AI"""
        try:
            from unified_ai.models import AIUsageLog
            
            AIUsageLog.objects.create(
                service_type='medical_query',
                input_text=query[:500],  # محدود کردن طول
                output_text=response.get('text', '')[:500],
                tokens_used=response.get('tokens_used', 0),
                model_name=response.get('model', 'unknown'),
                response_time=response.get('processing_time', 0)
            )
            
        except Exception as e:
            logger.warning(f"Failed to log AI usage: {str(e)}")


# ====================================
# نمونه 3: Unified Billing Integration
# ====================================

class UnifiedBillingIntegration:
    """
    یکپارچه‌سازی با سیستم مالی یکپارچه
    """
    
    def __init__(self):
        from unified_billing.services import UnifiedBillingService
        self.billing_service = UnifiedBillingService()
    
    def create_payment_request(self, user_id: str, amount: Decimal,
                             description: str, metadata: Dict = None) -> Dict[str, Any]:
        """
        ایجاد درخواست پرداخت
        
        Args:
            user_id: شناسه کاربر
            amount: مبلغ (ریال)
            description: توضیحات
            metadata: اطلاعات اضافی
            
        Returns:
            اطلاعات پرداخت
        """
        try:
            with transaction.atomic():
                # ایجاد درخواست پرداخت
                payment = self.billing_service.create_payment(
                    user_id=user_id,
                    amount=amount,
                    description=description,
                    payment_type='online',
                    metadata=metadata or {}
                )
                
                # دریافت لینک پرداخت
                payment_url = self.billing_service.get_payment_url(
                    payment_id=payment.id,
                    callback_url=settings.PAYMENT_CALLBACK_URL
                )
                
                return {
                    'success': True,
                    'payment_id': str(payment.id),
                    'payment_url': payment_url,
                    'amount': str(amount),
                    'reference_number': payment.reference_number
                }
                
        except Exception as e:
            logger.error(f"Payment creation error: {str(e)}")
            return {
                'success': False,
                'error': 'خطا در ایجاد درخواست پرداخت'
            }
    
    def verify_payment(self, payment_id: str, 
                      gateway_reference: str) -> Dict[str, Any]:
        """
        تأیید پرداخت
        
        Args:
            payment_id: شناسه پرداخت
            gateway_reference: شناسه مرجع درگاه
            
        Returns:
            نتیجه تأیید
        """
        try:
            result = self.billing_service.verify_payment(
                payment_id=payment_id,
                gateway_reference=gateway_reference
            )
            
            if result.is_valid:
                # به‌روزرسانی وضعیت‌های مرتبط
                self._update_related_status(payment_id, 'paid')
                
                return {
                    'success': True,
                    'verified': True,
                    'amount': str(result.amount),
                    'transaction_id': result.transaction_id
                }
            else:
                return {
                    'success': True,
                    'verified': False,
                    'error': result.error_message
                }
                
        except Exception as e:
            logger.error(f"Payment verification error: {str(e)}")
            return {
                'success': False,
                'error': 'خطا در تأیید پرداخت'
            }
    
    def check_wallet_balance(self, user_id: str) -> Decimal:
        """
        بررسی موجودی کیف پول
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            موجودی کیف پول
        """
        try:
            balance = self.billing_service.get_wallet_balance(user_id)
            return balance
            
        except Exception as e:
            logger.error(f"Wallet balance check error: {str(e)}")
            return Decimal('0')
    
    def _update_related_status(self, payment_id: str, status: str):
        """به‌روزرسانی وضعیت‌های مرتبط با پرداخت"""
        # این متد باید بر اساس نیاز هر اپ پیاده‌سازی شود
        pass


# ====================================
# نمونه 4: SMS Integration (Kavenegar)
# ====================================

class KavenegarIntegration:
    """
    یکپارچه‌سازی با سرویس پیامک کاوه‌نگار
    """
    
    def __init__(self):
        self.api_key = settings.KAVENEGAR_API_KEY
        self.base_url = "https://api.kavenegar.com/v1"
        self.sender = settings.KAVENEGAR_SENDER
    
    def send_otp_sms(self, receptor: str, token: str) -> bool:
        """
        ارسال پیامک OTP
        
        Args:
            receptor: شماره گیرنده
            token: کد OTP
            
        Returns:
            موفقیت ارسال
        """
        try:
            url = f"{self.base_url}/{self.api_key}/verify/lookup.json"
            
            data = {
                'receptor': receptor,
                'token': token,
                'template': settings.KAVENEGAR_OTP_TEMPLATE
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('return', {}).get('status') == 200:
                    logger.info(f"OTP sent successfully to {receptor}")
                    return True
            
            logger.error(f"SMS sending failed: {response.text}")
            return False
            
        except Exception as e:
            logger.error(f"SMS sending error: {str(e)}")
            return False
    
    def send_appointment_reminder(self, receptor: str, 
                                doctor_name: str,
                                appointment_time: str) -> bool:
        """
        ارسال یادآوری قرار ملاقات
        
        Args:
            receptor: شماره گیرنده
            doctor_name: نام پزشک
            appointment_time: زمان قرار
            
        Returns:
            موفقیت ارسال
        """
        try:
            url = f"{self.base_url}/{self.api_key}/verify/lookup.json"
            
            data = {
                'receptor': receptor,
                'token': doctor_name,
                'token2': appointment_time,
                'template': settings.KAVENEGAR_APPOINTMENT_TEMPLATE
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Appointment reminder error: {str(e)}")
            return False


# ====================================
# نمونه 5: File Storage Integration
# ====================================

class StorageIntegration:
    """
    یکپارچه‌سازی با سیستم ذخیره‌سازی فایل
    """
    
    def __init__(self):
        from django.core.files.storage import default_storage
        self.storage = default_storage
        self.allowed_extensions = [
            'jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx'
        ]
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    def save_medical_file(self, file, user_id: str, 
                         file_type: str) -> Dict[str, Any]:
        """
        ذخیره فایل پزشکی
        
        Args:
            file: فایل آپلود شده
            user_id: شناسه کاربر
            file_type: نوع فایل
            
        Returns:
            اطلاعات فایل ذخیره شده
        """
        try:
            # بررسی‌های امنیتی
            if not self._validate_file(file):
                return {
                    'success': False,
                    'error': 'فایل معتبر نیست'
                }
            
            # تولید نام یکتا
            file_extension = file.name.split('.')[-1].lower()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_hash = hashlib.md5(file.read()).hexdigest()[:8]
            file.seek(0)  # Reset file pointer
            
            file_name = f"medical/{user_id}/{file_type}/{timestamp}_{file_hash}.{file_extension}"
            
            # ذخیره فایل
            saved_path = self.storage.save(file_name, file)
            
            # دریافت URL
            file_url = self.storage.url(saved_path)
            
            return {
                'success': True,
                'file_path': saved_path,
                'file_url': file_url,
                'file_size': file.size,
                'file_name': file.name
            }
            
        except Exception as e:
            logger.error(f"File storage error: {str(e)}")
            return {
                'success': False,
                'error': 'خطا در ذخیره فایل'
            }
    
    def _validate_file(self, file) -> bool:
        """اعتبارسنجی فایل"""
        # بررسی حجم
        if file.size > self.max_file_size:
            return False
        
        # بررسی پسوند
        extension = file.name.split('.')[-1].lower()
        if extension not in self.allowed_extensions:
            return False
        
        # بررسی محتوا (برای تصاویر)
        if extension in ['jpg', 'jpeg', 'png']:
            try:
                from PIL import Image
                image = Image.open(file)
                image.verify()
                file.seek(0)
            except:
                return False
        
        return True
    
    def delete_file(self, file_path: str) -> bool:
        """حذف فایل"""
        try:
            if self.storage.exists(file_path):
                self.storage.delete(file_path)
                return True
            return False
            
        except Exception as e:
            logger.error(f"File deletion error: {str(e)}")
            return False


# ====================================
# نمونه 6: Cache Integration
# ====================================

class CacheIntegration:
    """
    یکپارچه‌سازی با سیستم کش
    """
    
    def __init__(self):
        self.cache = cache
        self.default_timeout = 300  # 5 minutes
    
    def get_or_set_user_data(self, user_id: str, 
                           data_fetcher: callable) -> Dict[str, Any]:
        """
        دریافت یا تنظیم داده‌های کاربر در کش
        
        Args:
            user_id: شناسه کاربر
            data_fetcher: تابع برای دریافت داده‌ها
            
        Returns:
            داده‌های کاربر
        """
        cache_key = f"user_data:{user_id}"
        
        # بررسی کش
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # دریافت داده‌ها
        data = data_fetcher(user_id)
        
        # ذخیره در کش
        self.cache.set(cache_key, data, self.default_timeout)
        
        return data
    
    def invalidate_user_cache(self, user_id: str):
        """پاک کردن کش کاربر"""
        patterns = [
            f"user_data:{user_id}",
            f"user_permissions:{user_id}",
            f"user_profile:{user_id}"
        ]
        
        for pattern in patterns:
            self.cache.delete(pattern)
    
    def rate_limit_check(self, identifier: str, 
                        action: str,
                        limit: int,
                        window: int) -> bool:
        """
        بررسی rate limit
        
        Args:
            identifier: شناسه (user_id یا IP)
            action: نوع عملیات
            limit: حد مجاز
            window: بازه زمانی (ثانیه)
            
        Returns:
            آیا مجاز است؟
        """
        cache_key = f"rate_limit:{identifier}:{action}"
        
        current_count = self.cache.get(cache_key, 0)
        
        if current_count >= limit:
            return False
        
        # افزایش شمارنده
        try:
            self.cache.incr(cache_key)
        except ValueError:
            # کلید وجود ندارد
            self.cache.set(cache_key, 1, window)
        
        return True


# ====================================
# نمونه 7: Webhook Integration
# ====================================

class WebhookIntegration:
    """
    مدیریت Webhook ها
    """
    
    def __init__(self):
        self.webhook_secret = settings.WEBHOOK_SECRET
    
    def verify_webhook_signature(self, payload: bytes, 
                                signature: str) -> bool:
        """
        تأیید امضای webhook
        
        Args:
            payload: محتوای درخواست
            signature: امضای ارسالی
            
        Returns:
            معتبر بودن امضا
        """
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def process_payment_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        پردازش webhook پرداخت
        
        Args:
            data: داده‌های webhook
            
        Returns:
            نتیجه پردازش
        """
        try:
            payment_id = data.get('payment_id')
            status = data.get('status')
            gateway_ref = data.get('gateway_reference')
            
            if not all([payment_id, status, gateway_ref]):
                return {
                    'success': False,
                    'error': 'Missing required fields'
                }
            
            # پردازش بر اساس وضعیت
            if status == 'success':
                # تأیید پرداخت
                billing = UnifiedBillingIntegration()
                result = billing.verify_payment(payment_id, gateway_ref)
                
                if result['success'] and result['verified']:
                    # اقدامات پس از پرداخت موفق
                    self._handle_successful_payment(payment_id)
                    
            elif status == 'failed':
                # مدیریت پرداخت ناموفق
                self._handle_failed_payment(payment_id)
            
            return {
                'success': True,
                'processed': True
            }
            
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _handle_successful_payment(self, payment_id: str):
        """مدیریت پرداخت موفق"""
        # پیاده‌سازی بر اساس نیاز
        pass
    
    def _handle_failed_payment(self, payment_id: str):
        """مدیریت پرداخت ناموفق"""
        # پیاده‌سازی بر اساس نیاز
        pass


# ====================================
# نمونه 8: Complete Integration Example
# ====================================

class AppointmentBookingIntegration:
    """
    مثال کامل یکپارچه‌سازی برای رزرو قرار
    """
    
    def __init__(self):
        self.auth = UnifiedAuthIntegration()
        self.billing = UnifiedBillingIntegration()
        self.sms = KavenegarIntegration()
        self.cache = CacheIntegration()
    
    def book_appointment(self, patient_id: str, doctor_id: str,
                        appointment_datetime: datetime,
                        visit_type: str = 'in_person') -> Dict[str, Any]:
        """
        رزرو قرار ملاقات با یکپارچه‌سازی کامل
        
        Args:
            patient_id: شناسه بیمار
            doctor_id: شناسه پزشک
            appointment_datetime: زمان قرار
            visit_type: نوع ویزیت
            
        Returns:
            نتیجه رزرو
        """
        try:
            with transaction.atomic():
                # 1. بررسی دسترسی
                if not self.auth.check_user_permissions(
                    patient_id, 'appointment', 'create'
                ):
                    return {
                        'success': False,
                        'error': 'عدم دسترسی'
                    }
                
                # 2. بررسی rate limit
                if not self.cache.rate_limit_check(
                    patient_id, 'appointment_booking', 5, 3600
                ):
                    return {
                        'success': False,
                        'error': 'تعداد درخواست‌ها بیش از حد مجاز'
                    }
                
                # 3. بررسی موجود بودن زمان
                from appointment_scheduler.models import Appointment
                
                existing = Appointment.objects.filter(
                    doctor_id=doctor_id,
                    appointment_datetime=appointment_datetime,
                    status__in=['scheduled', 'confirmed']
                ).exists()
                
                if existing:
                    return {
                        'success': False,
                        'error': 'این زمان قبلاً رزرو شده است'
                    }
                
                # 4. محاسبه هزینه
                from doctor_apps.models import DoctorProfile
                doctor_profile = DoctorProfile.objects.get(doctor_id=doctor_id)
                
                fee = doctor_profile.consultation_fee
                if visit_type == 'online':
                    fee = fee * Decimal('0.8')  # 20% تخفیف برای آنلاین
                
                # 5. ایجاد قرار
                appointment = Appointment.objects.create(
                    patient_id=patient_id,
                    doctor_id=doctor_id,
                    appointment_datetime=appointment_datetime,
                    visit_type=visit_type,
                    fee=fee,
                    status='scheduled'
                )
                
                # 6. ایجاد درخواست پرداخت
                payment_result = self.billing.create_payment_request(
                    user_id=patient_id,
                    amount=fee,
                    description=f'پرداخت ویزیت {doctor_profile.user.get_full_name()}',
                    metadata={
                        'appointment_id': str(appointment.id),
                        'doctor_id': doctor_id
                    }
                )
                
                if not payment_result['success']:
                    raise Exception('خطا در ایجاد درخواست پرداخت')
                
                # 7. ارسال پیامک تأیید
                patient = User.objects.get(id=patient_id)
                doctor = User.objects.get(id=doctor_id)
                
                self.sms.send_appointment_reminder(
                    receptor=patient.phone_number,
                    doctor_name=doctor.get_full_name(),
                    appointment_time=appointment_datetime.strftime('%Y/%m/%d ساعت %H:%M')
                )
                
                # 8. پاک کردن کش‌های مرتبط
                self.cache.invalidate_user_cache(patient_id)
                self.cache.invalidate_user_cache(doctor_id)
                
                return {
                    'success': True,
                    'appointment_id': str(appointment.id),
                    'payment_url': payment_result['payment_url'],
                    'amount': str(fee),
                    'appointment_time': appointment_datetime.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Appointment booking error: {str(e)}")
            return {
                'success': False,
                'error': 'خطا در رزرو قرار'
            }