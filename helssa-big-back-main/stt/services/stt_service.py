"""
سرویس اصلی تبدیل گفتار به متن
"""
import logging
from typing import Dict, Tuple, Optional, List
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from ..models import STTTask, STTQualityControl, STTUsageStats
from ..cores import CentralOrchestrator

logger = logging.getLogger(__name__)


class STTService:
    """
    سرویس مدیریت تبدیل گفتار به متن
    
    این سرویس رابط اصلی برای استفاده از قابلیت‌های STT است
    """
    
    def __init__(self):
        self.logger = logger
        self.orchestrator = CentralOrchestrator()
    
    def create_transcription_task(self, user, audio_file, 
                                language: str = 'fa',
                                model_size: str = 'base',
                                context_type: str = 'general',
                                metadata: Optional[dict] = None) -> Tuple[bool, dict]:
        """
        ایجاد وظیفه تبدیل گفتار به متن
        
        Args:
            user: کاربر
            audio_file: فایل صوتی
            language: زبان گفتار
            model_size: اندازه مدل
            context_type: نوع محتوا
            metadata: اطلاعات اضافی
            
        Returns:
            Tuple[bool, dict]: (موفقیت، نتیجه/خطا)
        """
        try:
            # اعتبارسنجی درخواست
            request_data = {
                'audio_file': audio_file,
                'language': language,
                'model': model_size,
                'context_type': context_type,
            }
            
            is_valid, error = self.orchestrator.api_core.validate_request(
                request_data, user
            )
            
            if not is_valid:
                return False, error
            
            # پردازش درخواست
            return self.orchestrator.process_stt_request(
                user, audio_file, language, model_size, context_type, metadata
            )
            
        except Exception as e:
            self.logger.error(f"Error creating transcription task: {str(e)}")
            return False, {
                'error': 'service_error',
                'message': 'خطا در ایجاد وظیفه تبدیل'
            }
    
    def get_task_status(self, task_id: str, user) -> Tuple[bool, dict]:
        """
        دریافت وضعیت وظیفه
        
        Args:
            task_id: شناسه وظیفه
            user: کاربر
            
        Returns:
            Tuple[bool, dict]: (موفقیت، وضعیت/خطا)
        """
        return self.orchestrator.get_task_status(task_id, user)
    
    def cancel_task(self, task_id: str, user) -> Tuple[bool, dict]:
        """
        لغو وظیفه
        
        Args:
            task_id: شناسه وظیفه
            user: کاربر
            
        Returns:
            Tuple[bool, dict]: (موفقیت، نتیجه/خطا)
        """
        return self.orchestrator.cancel_task(task_id, user)
    
    def get_user_tasks(self, user, status: Optional[str] = None,
                      limit: int = 10, offset: int = 0) -> Tuple[bool, dict]:
        """
        دریافت لیست وظایف کاربر
        
        Args:
            user: کاربر
            status: فیلتر وضعیت
            limit: تعداد نتایج
            offset: شروع از
            
        Returns:
            Tuple[bool, dict]: (موفقیت، لیست/خطا)
        """
        try:
            # ساخت query
            query = Q(user=user)
            if status:
                query &= Q(status=status)
            
            # دریافت وظایف
            tasks = STTTask.objects.filter(query).order_by('-created_at')
            total_count = tasks.count()
            
            # اعمال pagination
            tasks = tasks[offset:offset + limit]
            
            # آماده‌سازی نتایج
            results = []
            for task in tasks:
                response = self.orchestrator.api_core.prepare_response(task)
                results.append(response)
            
            return True, {
                'total': total_count,
                'count': len(results),
                'results': results,
                'offset': offset,
                'limit': limit
            }
            
        except Exception as e:
            self.logger.error(f"Error getting user tasks: {str(e)}")
            return False, {
                'error': 'service_error',
                'message': 'خطا در دریافت لیست وظایف'
            }
    
    def get_user_statistics(self, user, days: int = 30) -> Tuple[bool, dict]:
        """
        دریافت آمار استفاده کاربر
        
        Args:
            user: کاربر
            days: تعداد روزهای گذشته
            
        Returns:
            Tuple[bool, dict]: (موفقیت، آمار/خطا)
        """
        try:
            # محاسبه بازه زمانی
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days)
            
            # دریافت آمار
            stats = STTUsageStats.objects.filter(
                user=user,
                date__range=[start_date, end_date]
            ).order_by('date')
            
            # محاسبه مجموع
            total_stats = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'total_audio_duration': 0,
                'total_processing_time': 0,
                'average_confidence_score': 0,
                'success_rate': 0,
            }
            
            daily_stats = []
            confidence_scores = []
            
            for stat in stats:
                # آمار روزانه
                daily_stats.append({
                    'date': stat.date.isoformat(),
                    'requests': stat.total_requests,
                    'success_rate': (
                        stat.successful_requests / stat.total_requests * 100
                        if stat.total_requests > 0 else 0
                    ),
                    'audio_duration': stat.total_audio_duration,
                })
                
                # جمع‌آوری برای مجموع
                total_stats['total_requests'] += stat.total_requests
                total_stats['successful_requests'] += stat.successful_requests
                total_stats['failed_requests'] += stat.failed_requests
                total_stats['total_audio_duration'] += stat.total_audio_duration
                total_stats['total_processing_time'] += stat.total_processing_time
                
                if stat.average_confidence_score:
                    confidence_scores.append(stat.average_confidence_score)
            
            # محاسبه میانگین‌ها
            if total_stats['total_requests'] > 0:
                total_stats['success_rate'] = (
                    total_stats['successful_requests'] / 
                    total_stats['total_requests'] * 100
                )
            
            if confidence_scores:
                total_stats['average_confidence_score'] = (
                    sum(confidence_scores) / len(confidence_scores)
                )
            
            # آمار کیفیت
            quality_stats = self._get_quality_statistics(user, start_date, end_date)
            
            return True, {
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'days': days
                },
                'summary': total_stats,
                'daily': daily_stats,
                'quality': quality_stats,
            }
            
        except Exception as e:
            self.logger.error(f"Error getting user statistics: {str(e)}")
            return False, {
                'error': 'service_error',
                'message': 'خطا در دریافت آمار'
            }
    
    def _get_quality_statistics(self, user, start_date, end_date) -> dict:
        """محاسبه آمار کیفیت"""
        try:
            # دریافت وظایف در بازه زمانی
            tasks = STTTask.objects.filter(
                user=user,
                created_at__date__range=[start_date, end_date],
                status='completed'
            ).prefetch_related('quality_control')
            
            # آمار کیفیت
            total_tasks = tasks.count()
            needs_review_count = 0
            noise_levels = {'low': 0, 'medium': 0, 'high': 0}
            clarity_levels = {'clear': 0, 'moderate': 0, 'unclear': 0}
            
            for task in tasks:
                if hasattr(task, 'quality_control'):
                    qc = task.quality_control
                    
                    if qc.needs_human_review:
                        needs_review_count += 1
                    
                    noise_levels[qc.background_noise_level] = (
                        noise_levels.get(qc.background_noise_level, 0) + 1
                    )
                    
                    clarity_levels[qc.speech_clarity] = (
                        clarity_levels.get(qc.speech_clarity, 0) + 1
                    )
            
            return {
                'total_reviewed': total_tasks,
                'needs_human_review': needs_review_count,
                'review_rate': (
                    needs_review_count / total_tasks * 100
                    if total_tasks > 0 else 0
                ),
                'noise_distribution': noise_levels,
                'clarity_distribution': clarity_levels,
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating quality statistics: {str(e)}")
            return {}
    
    def review_transcription(self, task_id: str, reviewer,
                           corrected_text: str,
                           review_notes: Optional[str] = None) -> Tuple[bool, dict]:
        """
        بررسی و اصلاح نتیجه تبدیل
        
        Args:
            task_id: شناسه وظیفه
            reviewer: کاربر بررسی کننده
            corrected_text: متن اصلاح شده
            review_notes: یادداشت‌های بررسی
            
        Returns:
            Tuple[bool, dict]: (موفقیت، نتیجه/خطا)
        """
        try:
            # دریافت وظیفه
            task = STTTask.objects.get(task_id=task_id)
            
            # بررسی دسترسی (فقط staff)
            if not reviewer.is_staff:
                return False, {
                    'error': 'permission_denied',
                    'message': 'شما دسترسی به بررسی ندارید'
                }
            
            # دریافت کنترل کیفیت
            if not hasattr(task, 'quality_control'):
                return False, {
                    'error': 'no_quality_control',
                    'message': 'کنترل کیفیت برای این وظیفه وجود ندارد'
                }
            
            qc = task.quality_control
            
            # به‌روزرسانی
            qc.corrected_transcription = corrected_text
            qc.reviewed_by = reviewer
            qc.reviewed_at = timezone.now()
            qc.needs_human_review = False
            
            if review_notes:
                qc.review_reason = f"بررسی شده: {review_notes}"
            
            qc.save()
            
            # به‌روزرسانی متن اصلی
            task.transcription = corrected_text
            task.save()
            
            self.logger.info(
                f"Task {task_id} reviewed by {reviewer.id}. "
                f"Original: {len(task.transcription)} chars, "
                f"Corrected: {len(corrected_text)} chars"
            )
            
            return True, {
                'message': 'بررسی با موفقیت انجام شد',
                'task_id': str(task.task_id)
            }
            
        except STTTask.DoesNotExist:
            return False, {
                'error': 'not_found',
                'message': 'وظیفه مورد نظر یافت نشد'
            }
        except Exception as e:
            self.logger.error(f"Error reviewing transcription: {str(e)}")
            return False, {
                'error': 'service_error',
                'message': 'خطا در بررسی'
            }
    
    def get_pending_reviews(self, limit: int = 10, offset: int = 0) -> Tuple[bool, dict]:
        """
        دریافت لیست وظایف نیازمند بررسی
        
        Args:
            limit: تعداد نتایج
            offset: شروع از
            
        Returns:
            Tuple[bool, dict]: (موفقیت، لیست/خطا)
        """
        try:
            # دریافت وظایف نیازمند بررسی
            quality_controls = STTQualityControl.objects.filter(
                needs_human_review=True,
                reviewed_by__isnull=True
            ).select_related('task', 'task__user').order_by('-created_at')
            
            total_count = quality_controls.count()
            
            # اعمال pagination
            quality_controls = quality_controls[offset:offset + limit]
            
            # آماده‌سازی نتایج
            results = []
            for qc in quality_controls:
                task = qc.task
                results.append({
                    'task_id': str(task.task_id),
                    'user': {
                        'id': task.user.id,
                        'name': task.user.get_full_name() if hasattr(task.user, 'get_full_name') else str(task.user),
                        'type': task.user_type,
                    },
                    'transcription': task.transcription,
                    'confidence_score': task.confidence_score,
                    'review_reason': qc.review_reason,
                    'audio_quality': {
                        'score': qc.audio_quality_score,
                        'noise_level': qc.background_noise_level,
                        'clarity': qc.speech_clarity,
                    },
                    'created_at': task.created_at.isoformat(),
                })
            
            return True, {
                'total': total_count,
                'count': len(results),
                'results': results,
                'offset': offset,
                'limit': limit
            }
            
        except Exception as e:
            self.logger.error(f"Error getting pending reviews: {str(e)}")
            return False, {
                'error': 'service_error',
                'message': 'خطا در دریافت لیست بررسی'
            }