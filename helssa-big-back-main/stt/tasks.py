"""
وظایف Celery برای پردازش async
"""
from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

from .models import STTTask, STTUsageStats
from .cores import CentralOrchestrator

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3)
def process_stt_task(self, task_id: int, context_type: str = 'general'):
    """
    پردازش وظیفه تبدیل گفتار به متن
    
    Args:
        task_id: شناسه وظیفه
        context_type: نوع محتوا
    """
    try:
        logger.info(f"Starting processing task {task_id}")
        
        orchestrator = CentralOrchestrator()
        orchestrator.process_task(task_id, context_type)
        
        logger.info(f"Task {task_id} processed successfully")
        
    except Exception as e:
        logger.error(f"Error processing task {task_id}: {str(e)}")
        
        # Retry logic
        try:
            task = STTTask.objects.get(id=task_id)
            retry_count = task.metadata.get('retry_count', 0)
            
            if retry_count < self.max_retries:
                # به‌روزرسانی تعداد تلاش
                task.metadata['retry_count'] = retry_count + 1
                task.save()
                
                # تلاش مجدد با تأخیر
                raise self.retry(countdown=60 * (retry_count + 1))
            else:
                # شکست نهایی
                task.status = 'failed'
                task.error_message = f'خطا پس از {self.max_retries} تلاش: {str(e)}'
                task.completed_at = timezone.now()
                task.save()
                
        except STTTask.DoesNotExist:
            logger.error(f"Task {task_id} not found")


@shared_task
def cleanup_old_tasks(days: int = 30):
    """
    پاکسازی وظایف قدیمی
    
    Args:
        days: تعداد روزهای نگهداری
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # شمارش وظایف قدیمی
        old_tasks = STTTask.objects.filter(
            created_at__lt=cutoff_date,
            status__in=['completed', 'failed', 'cancelled']
        )
        
        count = old_tasks.count()
        
        if count > 0:
            logger.info(f"Deleting {count} old STT tasks")
            
            # حذف فایل‌های صوتی
            for task in old_tasks:
                if task.audio_file:
                    try:
                        task.audio_file.delete()
                    except Exception as e:
                        logger.error(f"Error deleting audio file: {e}")
            
            # حذف رکوردها
            old_tasks.delete()
            
            logger.info(f"Cleanup completed. Deleted {count} tasks")
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_tasks: {str(e)}")


@shared_task
def update_daily_statistics():
    """
    به‌روزرسانی آمار روزانه
    """
    try:
        from django.db.models import Count, Avg, Sum, Q
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        today = timezone.now().date()
        
        # دریافت کاربران فعال امروز
        active_users = STTTask.objects.filter(
            created_at__date=today
        ).values_list('user', flat=True).distinct()
        
        for user_id in active_users:
            try:
                user = User.objects.get(id=user_id)
                
                # محاسبه آمار روز
                tasks_today = STTTask.objects.filter(
                    user=user,
                    created_at__date=today
                )
                
                stats = tasks_today.aggregate(
                    total=Count('id'),
                    successful=Count('id', filter=Q(status='completed')),
                    failed=Count('id', filter=Q(status='failed')),
                    total_duration=Sum('duration'),
                    total_processing=Sum('processing_time'),
                    avg_confidence=Avg('confidence_score')
                )
                
                # ذخیره یا به‌روزرسانی آمار
                STTUsageStats.objects.update_or_create(
                    user=user,
                    date=today,
                    defaults={
                        'total_requests': stats['total'] or 0,
                        'successful_requests': stats['successful'] or 0,
                        'failed_requests': stats['failed'] or 0,
                        'total_audio_duration': stats['total_duration'] or 0,
                        'total_processing_time': stats['total_processing'] or 0,
                        'average_confidence_score': stats['avg_confidence'],
                    }
                )
                
            except User.DoesNotExist:
                logger.error(f"User {user_id} not found")
                continue
            except Exception as e:
                logger.error(f"Error updating stats for user {user_id}: {e}")
                continue
        
        logger.info(f"Daily statistics updated for {len(active_users)} users")
        
    except Exception as e:
        logger.error(f"Error in update_daily_statistics: {str(e)}")


@shared_task
def check_pending_reviews():
    """
    بررسی و اطلاع‌رسانی وظایف نیازمند بررسی
    """
    try:
        from .models import STTQualityControl
        
        # وظایف نیازمند بررسی
        pending_count = STTQualityControl.objects.filter(
            needs_human_review=True,
            reviewed_by__isnull=True
        ).count()
        
        if pending_count > 0:
            logger.info(f"{pending_count} tasks need human review")
            
            # TODO: ارسال نوتیفیکیشن به ادمین‌ها
            # notification_service.send_admin_notification(
            #     f"{pending_count} وظیفه STT نیاز به بررسی دارد"
            # )
            
            # ذخیره در کش برای نمایش در داشبورد
            cache.set('stt_pending_reviews_count', pending_count, timeout=3600)
        
    except Exception as e:
        logger.error(f"Error in check_pending_reviews: {str(e)}")


@shared_task
def warm_up_models():
    """
    بارگذاری مدل‌های Whisper برای آماده‌سازی
    """
    try:
        from .cores.speech_processor import SpeechProcessorCore
        from .settings import WHISPER_SETTINGS
        
        processor = SpeechProcessorCore()
        
        # بارگذاری مدل پیش‌فرض
        default_model = WHISPER_SETTINGS['DEFAULT_MODEL']
        logger.info(f"Warming up default model: {default_model}")
        
        processor.load_model(default_model)
        
        logger.info("Model warm-up completed")
        
    except Exception as e:
        logger.error(f"Error in warm_up_models: {str(e)}")


@shared_task
def analyze_audio_quality_trends():
    """
    تحلیل روند کیفیت صوت‌ها
    """
    try:
        from django.db.models import Avg
        from .models import STTQualityControl
        
        # میانگین کیفیت در 7 روز گذشته
        week_ago = timezone.now() - timedelta(days=7)
        
        quality_stats = STTQualityControl.objects.filter(
            created_at__gte=week_ago
        ).aggregate(
            avg_audio_quality=Avg('audio_quality_score'),
            total_count=Count('id'),
            needs_review_count=Count('id', filter=Q(needs_human_review=True))
        )
        
        if quality_stats['total_count'] > 0:
            review_rate = (
                quality_stats['needs_review_count'] / 
                quality_stats['total_count'] * 100
            )
            
            logger.info(
                f"Weekly quality stats - "
                f"Avg quality: {quality_stats['avg_audio_quality']:.2f}, "
                f"Review rate: {review_rate:.1f}%"
            )
            
            # هشدار اگر کیفیت پایین است
            if quality_stats['avg_audio_quality'] < 0.5:
                logger.warning(
                    f"Low audio quality detected. "
                    f"Average: {quality_stats['avg_audio_quality']:.2f}"
                )
                
                # TODO: ارسال هشدار
                # alert_service.send_quality_alert(quality_stats)
        
    except Exception as e:
        logger.error(f"Error in analyze_audio_quality_trends: {str(e)}")