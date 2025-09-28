"""
هسته API Ingress برای مدیریت ورودی و خروجی API های STT
"""
import logging
from typing import Dict, Tuple, Optional
from django.core.files.base import ContentFile
from django.core.cache import cache
from rest_framework import status
import hashlib
import os

logger = logging.getLogger(__name__)


class APIIngressCore:
    """
    مدیریت ورودی و خروجی API های تبدیل گفتار به متن
    
    وظایف:
    - اعتبارسنجی درخواست‌ها
    - محدودیت نرخ درخواست (Rate Limiting)
    - تبدیل فرمت‌های ورودی/خروجی
    - مدیریت کش
    """
    
    def __init__(self):
        self.logger = logger
        self.rate_limit_window = 3600  # 1 ساعت
        self.rate_limit_max_requests = {
            'patient': 20,  # بیمار: 20 درخواست در ساعت
            'doctor': 50,   # دکتر: 50 درخواست در ساعت
        }
    
    def validate_request(self, request_data: dict, user) -> Tuple[bool, Optional[dict]]:
        """
        اعتبارسنجی درخواست ورودی
        
        Args:
            request_data: داده‌های درخواست
            user: کاربر درخواست دهنده
            
        Returns:
            Tuple[bool, Optional[dict]]: (معتبر بودن، پیام خطا)
        """
        try:
            # بررسی وجود فایل صوتی
            if 'audio_file' not in request_data:
                return False, {'error': 'فایل صوتی الزامی است'}
            
            # بررسی محدودیت نرخ
            if not self._check_rate_limit(user):
                return False, {
                    'error': 'تعداد درخواست‌های شما بیش از حد مجاز است',
                    'retry_after': self._get_rate_limit_reset_time(user)
                }
            
            # بررسی اندازه فایل
            audio_file = request_data.get('audio_file')
            if audio_file and audio_file.size > 52428800:  # 50MB
                return False, {'error': 'حجم فایل نباید بیشتر از 50 مگابایت باشد'}
            
            return True, None
            
        except Exception as e:
            self.logger.error(f"Error in validate_request: {str(e)}")
            return False, {'error': 'خطا در اعتبارسنجی درخواست'}
    
    def _check_rate_limit(self, user) -> bool:
        """بررسی محدودیت نرخ درخواست"""
        cache_key = f'stt_rate_limit_{user.id}'
        current_count = cache.get(cache_key, 0)
        
        limit = self.rate_limit_max_requests.get(
            user.user_type, 
            self.rate_limit_max_requests['patient']
        )
        
        if current_count >= limit:
            return False
        
        # افزایش شمارنده
        cache.set(cache_key, current_count + 1, self.rate_limit_window)
        return True
    
    def _get_rate_limit_reset_time(self, user) -> int:
        """زمان باقیمانده تا ریست شدن محدودیت"""
        cache_key = f'stt_rate_limit_{user.id}'
        ttl = cache.ttl(cache_key)
        return ttl if ttl else 0
    
    def prepare_response(self, task, include_quality_control: bool = False) -> dict:
        """
        آماده‌سازی پاسخ API
        
        Args:
            task: وظیفه STT
            include_quality_control: آیا اطلاعات کنترل کیفیت اضافه شود
            
        Returns:
            dict: پاسخ فرمت شده
        """
        response = {
            'task_id': str(task.task_id),
            'status': task.status,
            'created_at': task.created_at.isoformat(),
        }
        
        if task.status == 'completed':
            response.update({
                'transcription': task.transcription,
                'language': task.language,
                'confidence_score': task.confidence_score,
                'duration': task.duration,
                'processing_time': task.processing_time,
            })
            
            if include_quality_control and hasattr(task, 'quality_control'):
                qc = task.quality_control
                response['quality_control'] = {
                    'audio_quality_score': qc.audio_quality_score,
                    'background_noise_level': qc.background_noise_level,
                    'speech_clarity': qc.speech_clarity,
                    'medical_terms_detected': qc.medical_terms_detected,
                    'needs_human_review': qc.needs_human_review,
                }
                
                if qc.corrected_transcription:
                    response['corrected_transcription'] = qc.corrected_transcription
        
        elif task.status == 'failed':
            response['error_message'] = task.error_message
        
        elif task.status == 'processing':
            # تخمین پیشرفت بر اساس زمان
            if task.started_at:
                from django.utils import timezone
                elapsed = (timezone.now() - task.started_at).total_seconds()
                estimated_total = task.duration * 0.5 if task.duration else 30  # تخمین
                progress = min(int((elapsed / estimated_total) * 100), 95)
                response['progress'] = progress
        
        return response
    
    def get_cached_result(self, audio_hash: str, language: str, model: str) -> Optional[dict]:
        """
        بررسی وجود نتیجه در کش
        
        Args:
            audio_hash: هش فایل صوتی
            language: زبان
            model: مدل استفاده شده
            
        Returns:
            Optional[dict]: نتیجه کش شده یا None
        """
        cache_key = f'stt_result_{audio_hash}_{language}_{model}'
        return cache.get(cache_key)
    
    def cache_result(self, audio_hash: str, language: str, model: str, 
                    result: dict, timeout: int = 86400):
        """
        ذخیره نتیجه در کش
        
        Args:
            audio_hash: هش فایل صوتی
            language: زبان
            model: مدل استفاده شده
            result: نتیجه تبدیل
            timeout: مدت زمان نگهداری در کش (پیش‌فرض 24 ساعت)
        """
        cache_key = f'stt_result_{audio_hash}_{language}_{model}'
        cache.set(cache_key, result, timeout)
    
    def calculate_audio_hash(self, audio_file) -> str:
        """محاسبه هش فایل صوتی برای کش"""
        hasher = hashlib.sha256()
        
        # خواندن فایل به صورت chunk
        for chunk in audio_file.chunks(8192):
            hasher.update(chunk)
        
        # برگشت به ابتدای فایل
        audio_file.seek(0)
        
        return hasher.hexdigest()
    
    def validate_user_permissions(self, user, task=None) -> Tuple[bool, Optional[dict]]:
        """
        بررسی دسترسی کاربر
        
        Args:
            user: کاربر
            task: وظیفه STT (برای بررسی دسترسی به وظیفه خاص)
            
        Returns:
            Tuple[bool, Optional[dict]]: (دسترسی دارد، پیام خطا)
        """
        # اگر وظیفه‌ای داده شده، بررسی مالکیت
        if task:
            if task.user != user:
                # فقط ادمین‌ها می‌توانند وظایف دیگران را ببینند
                if not user.is_staff:
                    return False, {'error': 'شما دسترسی به این وظیفه ندارید'}
        
        # بررسی فعال بودن کاربر
        if not user.is_active:
            return False, {'error': 'حساب کاربری شما غیرفعال است'}
        
        return True, None
    
    def format_error_response(self, error_code: str, message: str, 
                            details: Optional[dict] = None) -> dict:
        """
        فرمت استاندارد برای پاسخ‌های خطا
        
        Args:
            error_code: کد خطا
            message: پیام خطا
            details: جزئیات اضافی
            
        Returns:
            dict: پاسخ خطای فرمت شده
        """
        response = {
            'success': False,
            'error': {
                'code': error_code,
                'message': message,
            }
        }
        
        if details:
            response['error']['details'] = details
        
        return response
    
    def log_api_call(self, user, endpoint: str, request_data: dict, 
                    response_status: int, response_time: float):
        """
        ثبت فراخوانی API برای آنالیز
        
        Args:
            user: کاربر
            endpoint: نام endpoint
            request_data: داده‌های درخواست
            response_status: کد وضعیت پاسخ
            response_time: زمان پاسخ (ثانیه)
        """
        self.logger.info(
            f"API Call - User: {user.id}, Endpoint: {endpoint}, "
            f"Status: {response_status}, Response Time: {response_time:.2f}s",
            extra={
                'user_id': user.id,
                'user_type': user.user_type,
                'endpoint': endpoint,
                'response_status': response_status,
                'response_time': response_time,
                'has_audio': 'audio_file' in request_data,
                'language': request_data.get('language', 'unknown'),
                'model': request_data.get('model', 'unknown'),
            }
        )