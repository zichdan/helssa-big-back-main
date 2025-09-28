"""
هسته Orchestrator برای هماهنگی بین هسته‌های دیگر در STT
"""
import logging
from typing import Dict, Any, Optional, Tuple
from django.utils import timezone
from django.db import transaction
from celery import shared_task
import json

from ..models import STTTask, STTQualityControl, STTUsageStats
from .api_ingress import APIIngressCore
from .text_processor import TextProcessorCore
from .speech_processor import SpeechProcessorCore

logger = logging.getLogger(__name__)


class CentralOrchestrator:
    """
    هماهنگی مرکزی بین هسته‌های مختلف STT
    
    وظایف:
    - مدیریت جریان کار تبدیل گفتار به متن
    - هماهنگی بین هسته‌ها
    - مدیریت وضعیت وظایف
    - کنترل کیفیت
    """
    
    def __init__(self):
        self.logger = logger
        self.api_core = APIIngressCore()
        self.text_core = TextProcessorCore()
        self.speech_core = SpeechProcessorCore()
    
    def process_stt_request(self, user, audio_file, language: str = 'fa',
                          model_size: str = 'base', 
                          context_type: str = 'general',
                          metadata: Optional[dict] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        پردازش درخواست تبدیل گفتار به متن
        
        Args:
            user: کاربر درخواست دهنده
            audio_file: فایل صوتی
            language: زبان گفتار
            model_size: اندازه مدل Whisper
            context_type: نوع محتوا
            metadata: اطلاعات اضافی
            
        Returns:
            Tuple[bool, Dict]: (موفقیت، نتیجه/خطا)
        """
        try:
            # ایجاد وظیفه
            task = self._create_task(
                user, audio_file, language, model_size, metadata
            )
            
            # بررسی کش
            audio_hash = self.api_core.calculate_audio_hash(audio_file)
            cached_result = self.api_core.get_cached_result(
                audio_hash, language, model_size
            )
            
            if cached_result:
                self.logger.info(f"Using cached result for task {task.task_id}")
                self._update_task_with_result(task, cached_result)
                return True, self.api_core.prepare_response(task, include_quality_control=True)
            
            # شروع پردازش async
            process_stt_task.delay(task.id, context_type)
            
            # پاسخ اولیه
            return True, {
                'task_id': str(task.task_id),
                'status': 'processing',
                'message': 'درخواست شما در حال پردازش است',
                'estimated_time': self.speech_core.estimate_processing_time(
                    task.duration or 30, model_size
                )
            }
            
        except Exception as e:
            self.logger.error(f"Error in process_stt_request: {str(e)}")
            return False, {
                'error': 'process_failed',
                'message': 'خطا در پردازش درخواست',
                'details': str(e)
            }
    
    def _create_task(self, user, audio_file, language: str,
                    model_size: str, metadata: Optional[dict]) -> STTTask:
        """ایجاد وظیفه جدید"""
        task = STTTask.objects.create(
            user=user,
            user_type=user.user_type,
            audio_file=audio_file,
            file_size=audio_file.size,
            language=language,
            model_used=model_size,
            metadata=metadata or {},
            status='pending'
        )
        
        self.logger.info(f"Created STT task {task.task_id} for user {user.id}")
        return task
    
    def process_task(self, task_id: int, context_type: str = 'general'):
        """
        پردازش وظیفه STT
        
        Args:
            task_id: شناسه وظیفه
            context_type: نوع محتوا
        """
        try:
            task = STTTask.objects.get(id=task_id)
            
            # به‌روزرسانی وضعیت
            task.status = 'processing'
            task.started_at = timezone.now()
            task.save()
            
            # پردازش صوت
            self.logger.info(f"Processing audio for task {task.task_id}")
            audio_result = self.speech_core.process_audio_file(
                task.audio_file.path,
                task.language,
                task.model_used
            )
            
            # ذخیره نتیجه اولیه
            task.transcription = audio_result['transcription']
            task.confidence_score = audio_result['confidence_score']
            task.duration = audio_result['duration']
            task.save()
            
            # پردازش متن
            self.logger.info(f"Processing text for task {task.task_id}")
            text_result = self.text_core.process_transcription(
                audio_result['transcription'],
                context_type
            )
            
            # کنترل کیفیت
            quality_control = self._perform_quality_control(
                task, audio_result, text_result
            )
            
            # به‌روزرسانی نهایی
            with transaction.atomic():
                # به‌روزرسانی متن نهایی
                if quality_control.corrected_transcription:
                    task.transcription = quality_control.corrected_transcription
                
                task.status = 'completed'
                task.completed_at = timezone.now()
                task.save()
                
                # ذخیره در کش
                audio_hash = self.api_core.calculate_audio_hash(task.audio_file)
                cache_data = {
                    'transcription': task.transcription,
                    'confidence_score': task.confidence_score,
                    'duration': task.duration,
                    'quality_control': {
                        'audio_quality_score': quality_control.audio_quality_score,
                        'needs_human_review': quality_control.needs_human_review,
                    }
                }
                self.api_core.cache_result(
                    audio_hash, task.language, task.model_used, cache_data
                )
                
                # به‌روزرسانی آمار
                self._update_usage_stats(task)
            
            self.logger.info(f"Task {task.task_id} completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error processing task {task_id}: {str(e)}")
            self._handle_task_failure(task_id, str(e))
    
    def _perform_quality_control(self, task: STTTask, 
                               audio_result: dict,
                               text_result: dict) -> STTQualityControl:
        """انجام کنترل کیفیت"""
        try:
            # محاسبه معیارهای کیفیت
            audio_quality = audio_result.get('audio_quality', {})
            
            # تعیین نیاز به بررسی انسانی
            needs_review = self._check_needs_human_review(
                task, audio_result, text_result
            )
            
            # ایجاد رکورد کنترل کیفیت
            quality_control = STTQualityControl.objects.create(
                task=task,
                audio_quality_score=audio_quality.get('quality_score', 0.5),
                background_noise_level=audio_quality.get('noise_level', 'medium'),
                speech_clarity=self._determine_speech_clarity(audio_result),
                medical_terms_detected=text_result.get('medical_entities', []),
                suggested_corrections=text_result.get('corrections_made', []),
                corrected_transcription=text_result.get('processed_text', ''),
                needs_human_review=needs_review['needs_review'],
                review_reason=needs_review['reason']
            )
            
            self.logger.info(
                f"Quality control completed for task {task.task_id}. "
                f"Needs review: {needs_review['needs_review']}"
            )
            
            return quality_control
            
        except Exception as e:
            self.logger.error(f"Error in quality control: {str(e)}")
            # ایجاد رکورد پیش‌فرض
            return STTQualityControl.objects.create(
                task=task,
                audio_quality_score=0.5,
                background_noise_level='unknown',
                speech_clarity='moderate',
                needs_human_review=True,
                review_reason=f'خطا در کنترل کیفیت: {str(e)}'
            )
    
    def _check_needs_human_review(self, task: STTTask,
                                audio_result: dict,
                                text_result: dict) -> Dict[str, Any]:
        """بررسی نیاز به بازبینی انسانی"""
        reasons = []
        
        # کیفیت صوت پایین
        if audio_result.get('audio_quality', {}).get('quality_score', 1) < 0.3:
            reasons.append('کیفیت صوت پایین')
        
        # اطمینان پایین
        if task.confidence_score and task.confidence_score < 0.5:
            reasons.append('امتیاز اطمینان پایین')
        
        # متن کوتاه مشکوک
        if len(task.transcription) < 10:
            reasons.append('متن بسیار کوتاه')
        
        # کلمات با اطمینان پایین
        low_confidence_count = len(audio_result.get('low_confidence_words', []))
        if low_confidence_count > 5:
            reasons.append(f'{low_confidence_count} کلمه با اطمینان پایین')
        
        # درخواست‌های دکتر برای نسخه
        if task.user_type == 'doctor' and task.metadata.get('context_type') == 'prescription':
            reasons.append('نسخه پزشکی - نیاز به دقت بیشتر')
        
        return {
            'needs_review': len(reasons) > 0,
            'reason': ' | '.join(reasons) if reasons else ''
        }
    
    def _determine_speech_clarity(self, audio_result: dict) -> str:
        """تعیین وضوح گفتار"""
        confidence = audio_result.get('confidence_score', 0.5)
        
        if confidence > 0.8:
            return 'clear'
        elif confidence > 0.5:
            return 'moderate'
        else:
            return 'unclear'
    
    def _update_task_with_result(self, task: STTTask, cached_result: dict):
        """به‌روزرسانی وظیفه با نتیجه کش شده"""
        task.transcription = cached_result['transcription']
        task.confidence_score = cached_result['confidence_score']
        task.duration = cached_result['duration']
        task.status = 'completed'
        task.started_at = timezone.now()
        task.completed_at = timezone.now()
        task.save()
        
        # ایجاد کنترل کیفیت از کش
        if 'quality_control' in cached_result:
            qc_data = cached_result['quality_control']
            STTQualityControl.objects.create(
                task=task,
                audio_quality_score=qc_data.get('audio_quality_score', 0.5),
                background_noise_level='unknown',
                speech_clarity='moderate',
                corrected_transcription=task.transcription,
                needs_human_review=qc_data.get('needs_human_review', False),
                review_reason='نتیجه از کش'
            )
    
    def _handle_task_failure(self, task_id: int, error_message: str):
        """مدیریت خطا در پردازش وظیفه"""
        try:
            task = STTTask.objects.get(id=task_id)
            task.status = 'failed'
            task.error_message = error_message
            task.completed_at = timezone.now()
            task.save()
            
            # به‌روزرسانی آمار
            self._update_usage_stats(task, success=False)
            
        except Exception as e:
            self.logger.error(f"Error handling task failure: {str(e)}")
    
    def _update_usage_stats(self, task: STTTask, success: bool = True):
        """به‌روزرسانی آمار استفاده"""
        try:
            from django.db.models import F
            
            stats, created = STTUsageStats.objects.get_or_create(
                user=task.user,
                date=task.created_at.date(),
                defaults={
                    'total_requests': 0,
                    'successful_requests': 0,
                    'failed_requests': 0,
                    'total_audio_duration': 0,
                    'total_processing_time': 0,
                }
            )
            
            # به‌روزرسانی آمار
            stats.total_requests = F('total_requests') + 1
            
            if success:
                stats.successful_requests = F('successful_requests') + 1
                if task.duration:
                    stats.total_audio_duration = F('total_audio_duration') + task.duration
                if task.processing_time:
                    stats.total_processing_time = F('total_processing_time') + task.processing_time
            else:
                stats.failed_requests = F('failed_requests') + 1
            
            stats.save()
            
        except Exception as e:
            self.logger.error(f"Error updating usage stats: {str(e)}")
    
    def get_task_status(self, task_id: str, user) -> Tuple[bool, Dict[str, Any]]:
        """
        دریافت وضعیت وظیفه
        
        Args:
            task_id: شناسه وظیفه
            user: کاربر درخواست کننده
            
        Returns:
            Tuple[bool, Dict]: (موفقیت، وضعیت/خطا)
        """
        try:
            task = STTTask.objects.get(task_id=task_id)
            
            # بررسی دسترسی
            has_access, error = self.api_core.validate_user_permissions(user, task)
            if not has_access:
                return False, error
            
            # آماده‌سازی پاسخ
            include_qc = task.status == 'completed'
            response = self.api_core.prepare_response(task, include_qc)
            
            return True, response
            
        except STTTask.DoesNotExist:
            return False, {
                'error': 'not_found',
                'message': 'وظیفه مورد نظر یافت نشد'
            }
        except Exception as e:
            self.logger.error(f"Error getting task status: {str(e)}")
            return False, {
                'error': 'internal_error',
                'message': 'خطا در دریافت وضعیت'
            }
    
    def cancel_task(self, task_id: str, user) -> Tuple[bool, Dict[str, Any]]:
        """
        لغو وظیفه در حال پردازش
        
        Args:
            task_id: شناسه وظیفه
            user: کاربر درخواست کننده
            
        Returns:
            Tuple[bool, Dict]: (موفقیت، نتیجه/خطا)
        """
        try:
            task = STTTask.objects.get(task_id=task_id)
            
            # بررسی دسترسی
            has_access, error = self.api_core.validate_user_permissions(user, task)
            if not has_access:
                return False, error
            
            # بررسی امکان لغو
            if not task.can_cancel():
                return False, {
                    'error': 'invalid_status',
                    'message': 'این وظیفه قابل لغو نیست'
                }
            
            # لغو وظیفه
            task.status = 'cancelled'
            task.completed_at = timezone.now()
            task.save()
            
            self.logger.info(f"Task {task.task_id} cancelled by user {user.id}")
            
            return True, {
                'message': 'وظیفه با موفقیت لغو شد',
                'task_id': str(task.task_id)
            }
            
        except STTTask.DoesNotExist:
            return False, {
                'error': 'not_found',
                'message': 'وظیفه مورد نظر یافت نشد'
            }
        except Exception as e:
            self.logger.error(f"Error cancelling task: {str(e)}")
            return False, {
                'error': 'internal_error',
                'message': 'خطا در لغو وظیفه'
            }


@shared_task
def process_stt_task(task_id: int, context_type: str = 'general'):
    """
    Celery task برای پردازش async
    
    Args:
        task_id: شناسه وظیفه
        context_type: نوع محتوا
    """
    orchestrator = CentralOrchestrator()
    orchestrator.process_task(task_id, context_type)