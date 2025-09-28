"""
سیگنال‌های اپلیکیشن پرداخت
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import logging

from .models import Payment, WalletTransaction
from .settings import PAYMENT_NOTIFICATIONS

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Payment)
def send_payment_notification(sender, instance, created, **kwargs):
    """
    ارسال اعلان پس از ایجاد یا بروزرسانی پرداخت
    """
    if not PAYMENT_NOTIFICATIONS.get('SEND_SMS', True):
        return
        
    try:
        # ارسال اعلان برای پرداخت‌های جدید
        if created and instance.status == 'pending':
            # TODO: ارسال SMS/Email/Push notification
            logger.info(f"Payment notification queued for {instance.payment_id}")
            
        # ارسال اعلان برای تغییر وضعیت
        elif not created and instance.tracker.has_changed('status'):
            old_status = instance.tracker.previous('status')
            new_status = instance.status
            
            # پرداخت موفق
            if new_status == 'success' and old_status != 'success':
                message = PAYMENT_NOTIFICATIONS['SMS_TEMPLATES']['payment_success'].format(
                    amount=instance.amount,
                    tracking_code=instance.tracking_code
                )
                # TODO: ارسال پیامک
                logger.info(f"Success notification for payment {instance.payment_id}")
                
            # پرداخت ناموفق
            elif new_status == 'failed' and old_status != 'failed':
                message = PAYMENT_NOTIFICATIONS['SMS_TEMPLATES']['payment_failed'].format(
                    amount=instance.amount
                )
                # TODO: ارسال پیامک
                logger.info(f"Failed notification for payment {instance.payment_id}")
                
            # بازپرداخت
            elif new_status in ['refunded', 'partially_refunded']:
                message = PAYMENT_NOTIFICATIONS['SMS_TEMPLATES']['refund_success'].format(
                    amount=instance.amount
                )
                # TODO: ارسال پیامک
                logger.info(f"Refund notification for payment {instance.payment_id}")
                
    except Exception as e:
        logger.error(f"Error sending payment notification: {str(e)}")


@receiver(pre_save, sender=Payment)
def validate_payment_status_change(sender, instance, **kwargs):
    """
    اعتبارسنجی تغییر وضعیت پرداخت
    """
    if instance.pk:  # فقط برای رکوردهای موجود
        try:
            old_payment = Payment.objects.get(pk=instance.pk)
            
            # جلوگیری از تغییر وضعیت‌های غیرمجاز
            invalid_transitions = {
                'success': ['pending', 'processing'],  # نمی‌توان از موفق به معلق برگشت
                'failed': ['success', 'refunded'],  # نمی‌توان از ناموفق به موفق رفت
                'refunded': ['pending', 'processing', 'failed'],  # نمی‌توان از بازپرداخت شده تغییر داد
            }
            
            if old_payment.status in invalid_transitions:
                if instance.status in invalid_transitions[old_payment.status]:
                    logger.warning(
                        f"Invalid status transition for payment {instance.payment_id}: "
                        f"{old_payment.status} -> {instance.status}"
                    )
                    # برگرداندن به وضعیت قبلی
                    instance.status = old_payment.status
                    
        except Payment.DoesNotExist:
            pass


@receiver(post_save, sender=WalletTransaction)
def update_wallet_last_transaction(sender, instance, created, **kwargs):
    """
    بروزرسانی زمان آخرین تراکنش کیف پول
    """
    if created:
        try:
            wallet = instance.wallet
            wallet.last_transaction_at = instance.created_at
            wallet.save(update_fields=['last_transaction_at'])
            
            logger.info(f"Updated last transaction time for wallet {wallet.id}")
            
        except Exception as e:
            logger.error(f"Error updating wallet last transaction: {str(e)}")


# نکته: برای استفاده از model-tracker باید در مدل Payment اضافه شود:
# from model_utils import FieldTracker
# tracker = FieldTracker()