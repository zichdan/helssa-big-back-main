"""
سیگنال‌های اپلیکیشن Checklist
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
import logging

from .models import ChecklistEval, ChecklistAlert

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ChecklistEval)
def create_alert_for_critical_items(sender, instance, created, **kwargs):
    """
    ایجاد هشدار برای آیتم‌های بحرانی که پوشش داده نشده‌اند
    """
    if created and instance.catalog_item.priority == 'critical':
        if instance.status in ['missing', 'unclear']:
            ChecklistAlert.objects.create(
                encounter=instance.encounter,
                evaluation=instance,
                alert_type='missing_critical',
                message=f"آیتم بحرانی '{instance.catalog_item.title}' پوشش داده نشده است. لطفاً بررسی کنید.",
                created_by=instance.created_by
            )
            logger.info(f"Critical alert created for evaluation {instance.id}")


@receiver(pre_save, sender=ChecklistEval)
def update_acknowledgment_time(sender, instance, **kwargs):
    """
    به‌روزرسانی زمان تایید هنگام تغییر وضعیت
    """
    if instance.pk:  # فقط برای آبجکت‌های موجود
        try:
            old_instance = ChecklistEval.objects.get(pk=instance.pk)
            
            # اگر وضعیت تایید تغییر کرد
            if old_instance.is_acknowledged != instance.is_acknowledged:
                if instance.is_acknowledged:
                    instance.acknowledged_at = timezone.now()
                else:
                    instance.acknowledged_at = None
                    
        except ChecklistEval.DoesNotExist:
            pass


@receiver(post_save, sender=ChecklistEval)
def check_low_confidence_scores(sender, instance, created, **kwargs):
    """
    بررسی امتیازهای اطمینان پایین و ایجاد هشدار
    """
    if instance.confidence_score < 0.5 and instance.status != 'not_applicable':
        # بررسی وجود هشدار مشابه
        existing_alert = ChecklistAlert.objects.filter(
            encounter=instance.encounter,
            evaluation=instance,
            alert_type='low_confidence',
            is_dismissed=False
        ).exists()
        
        if not existing_alert:
            ChecklistAlert.objects.create(
                encounter=instance.encounter,
                evaluation=instance,
                alert_type='low_confidence',
                message=f"اطمینان پایین برای آیتم '{instance.catalog_item.title}' (امتیاز: {instance.confidence_score:.2f}). بررسی دستی توصیه می‌شود.",
                created_by=instance.created_by
            )


@receiver(post_save, sender=ChecklistEval)
def detect_red_flags(sender, instance, created, **kwargs):
    """
    تشخیص علائم خطر و ایجاد هشدار
    """
    if instance.catalog_item.category == 'red_flags' and instance.status == 'covered':
        # ایجاد هشدار علامت خطر
        ChecklistAlert.objects.create(
            encounter=instance.encounter,
            evaluation=instance,
            alert_type='red_flag',
            message=f"⚠️ علامت خطر شناسایی شد: {instance.catalog_item.title}. اقدام فوری مورد نیاز است.",
            created_by=instance.created_by
        )
        
        logger.warning(f"Red flag detected in encounter {instance.encounter.id}: {instance.catalog_item.title}")


@receiver(post_save, sender=ChecklistAlert)
def log_alert_creation(sender, instance, created, **kwargs):
    """
    ثبت لاگ برای هشدارهای ایجاد شده
    """
    if created:
        logger.info(
            f"Alert created: {instance.get_alert_type_display()} "
            f"for encounter {instance.encounter.id}"
        )


@receiver(pre_save, sender=ChecklistAlert)
def update_dismissal_info(sender, instance, **kwargs):
    """
    به‌روزرسانی اطلاعات رد کردن هشدار
    """
    if instance.pk:  # فقط برای آبجکت‌های موجود
        try:
            old_instance = ChecklistAlert.objects.get(pk=instance.pk)
            
            # اگر وضعیت رد شدن تغییر کرد
            if old_instance.is_dismissed != instance.is_dismissed:
                if instance.is_dismissed and not instance.dismissed_at:
                    instance.dismissed_at = timezone.now()
                    
                    # اگر کاربر رد کننده مشخص نشده، از context استفاده کن
                    if not instance.dismissed_by:
                        # این باید در view تنظیم شود
                        pass
                        
        except ChecklistAlert.DoesNotExist:
            pass