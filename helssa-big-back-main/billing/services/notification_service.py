"""
سرویس اعلان‌های سیستم مالی
Financial System Notification Service
"""

from typing import Dict, Any
from django.contrib.auth import get_user_model
from .base_service import BaseService

User = get_user_model()


class NotificationService(BaseService):
    """سرویس ارسال اعلان‌های مالی"""
    
    def __init__(self):
        super().__init__()
        
    def send_subscription_welcome(self, user: User, plan, subscription):
        """ارسال پیام خوش‌آمدگویی اشتراک"""
        try:
            message = f"خوش آمدید! اشتراک {plan.name} شما فعال شد."
            self._send_notification(user, "اشتراک فعال شد", message)
        except Exception as e:
            self.logger.error(f"خطا در ارسال پیام خوش‌آمد: {str(e)}")
    
    def send_subscription_cancellation(self, subscription, immediate: bool):
        """ارسال پیام لغو اشتراک"""
        try:
            if immediate:
                message = "اشتراک شما لغو شد."
            else:
                message = f"اشتراک شما در تاریخ {subscription.end_date} لغو خواهد شد."
            
            self._send_notification(subscription.user, "لغو اشتراک", message)
        except Exception as e:
            self.logger.error(f"خطا در ارسال پیام لغو: {str(e)}")
    
    def send_payment_failure_notification(self, subscription, error_message: str):
        """ارسال اعلان شکست پرداخت"""
        try:
            message = f"پرداخت اشتراک شما ناموفق بود. لطفاً اقدام کنید."
            self._send_notification(subscription.user, "شکست پرداخت", message)
        except Exception as e:
            self.logger.error(f"خطا در ارسال اعلان شکست: {str(e)}")
    
    def _send_notification(self, user: User, title: str, message: str):
        """ارسال اعلان به کاربر"""
        # پیاده‌سازی ارسال اعلان (SMS، ایمیل، Push Notification)
        self.logger.info(f"Notification sent to {user.phone_number}: {title}")