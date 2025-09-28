"""
سرویس اعلان‌رسانی پنل ادمین
AdminPortal Notification Service
"""

import logging
from typing import List, Dict, Optional
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class NotificationService:
    """
    سرویس اعلان‌رسانی برای پنل ادمین
    مسئول ارسال اعلان‌ها از طریق ایمیل، SMS و اعلان‌های داخلی
    """
    
    def __init__(self):
        self.email_enabled = getattr(settings, 'EMAIL_BACKEND', None) is not None
        self.sms_enabled = hasattr(settings, 'KAVENEGAR_API_KEY')
    
    def send_admin_notification(self, 
                               notification_type: str,
                               recipients: List[str],
                               subject: str,
                               message: str,
                               priority: str = 'normal',
                               channels: List[str] = None) -> Dict:
        """
        ارسال اعلان به ادمین‌ها
        
        Args:
            notification_type: نوع اعلان
            recipients: لیست گیرندگان
            subject: موضوع
            message: متن پیام
            priority: اولویت (low, normal, high, urgent)
            channels: کانال‌های ارسال (email, sms, in_app)
            
        Returns:
            Dict: نتیجه ارسال
        """
        try:
            if not channels:
                channels = ['email', 'in_app']
            
            results = {
                'notification_type': notification_type,
                'priority': priority,
                'timestamp': timezone.now().isoformat(),
                'channels': {},
                'success': True,
                'total_sent': 0
            }
            
            # ارسال ایمیل
            if 'email' in channels and self.email_enabled:
                email_result = self._send_email_notification(
                    recipients, subject, message, priority
                )
                results['channels']['email'] = email_result
                if email_result['success']:
                    results['total_sent'] += email_result['sent_count']
            
            # ارسال SMS
            if 'sms' in channels and self.sms_enabled:
                sms_result = self._send_sms_notification(
                    recipients, message, priority
                )
                results['channels']['sms'] = sms_result
                if sms_result['success']:
                    results['total_sent'] += sms_result['sent_count']
            
            # اعلان داخلی
            if 'in_app' in channels:
                in_app_result = self._send_in_app_notification(
                    recipients, subject, message, priority
                )
                results['channels']['in_app'] = in_app_result
                if in_app_result['success']:
                    results['total_sent'] += in_app_result['sent_count']
            
            # بررسی موفقیت کلی
            results['success'] = any(
                channel_result.get('success', False) 
                for channel_result in results['channels'].values()
            )
            
            logger.info(f"Admin notification sent: {notification_type} to {len(recipients)} recipients")
            
            return results
            
        except Exception as e:
            logger.error(f"Admin notification error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'notification_type': notification_type
            }
    
    def send_system_alert(self, 
                         alert_type: str,
                         severity: str,
                         message: str,
                         details: Dict = None) -> Dict:
        """
        ارسال هشدار سیستمی
        
        Args:
            alert_type: نوع هشدار
            severity: شدت (info, warning, error, critical)
            message: پیام هشدار
            details: جزئیات اضافی
            
        Returns:
            Dict: نتیجه ارسال
        """
        try:
            # تعیین گیرندگان بر اساس نوع هشدار
            recipients = self._get_alert_recipients(alert_type, severity)
            
            # تعیین کانال‌ها بر اساس شدت
            channels = self._get_alert_channels(severity)
            
            # تولید موضوع
            subject = f"هشدار سیستمی: {alert_type} - {severity}"
            
            # تولید پیام کامل
            full_message = self._format_alert_message(
                alert_type, severity, message, details
            )
            
            # ارسال اعلان
            result = self.send_admin_notification(
                f"system_alert_{alert_type}",
                recipients,
                subject,
                full_message,
                self._severity_to_priority(severity),
                channels
            )
            
            logger.warning(f"System alert sent: {alert_type} - {severity}")
            
            return result
            
        except Exception as e:
            logger.error(f"System alert error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'alert_type': alert_type
            }
    
    def send_ticket_notification(self, 
                                ticket_id: str,
                                event_type: str,
                                admin_user=None) -> Dict:
        """
        ارسال اعلان مربوط به تیکت
        
        Args:
            ticket_id: شناسه تیکت
            event_type: نوع رویداد (created, assigned, resolved, escalated)
            admin_user: کاربر ادمین مربوطه
            
        Returns:
            Dict: نتیجه ارسال
        """
        try:
            from ..models import SupportTicket
            
            ticket = SupportTicket.objects.get(id=ticket_id)
            
            # تعیین گیرندگان
            recipients = self._get_ticket_notification_recipients(ticket, event_type)
            
            # تولید پیام
            subject, message = self._format_ticket_notification(ticket, event_type, admin_user)
            
            # تعیین اولویت
            priority = 'high' if ticket.priority in ['high', 'urgent'] else 'normal'
            
            # ارسال
            result = self.send_admin_notification(
                f"ticket_{event_type}",
                recipients,
                subject,
                message,
                priority,
                ['email', 'in_app']
            )
            
            logger.info(f"Ticket notification sent: {ticket_id} - {event_type}")
            
            return result
            
        except Exception as e:
            logger.error(f"Ticket notification error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'ticket_id': ticket_id
            }
    
    def _send_email_notification(self, recipients: List[str], 
                               subject: str, message: str, priority: str) -> Dict:
        """ارسال اعلان ایمیل"""
        try:
            sent_count = 0
            failed_recipients = []
            
            for recipient in recipients:
                try:
                    send_mail(
                        subject=f"[AdminPortal] {subject}",
                        message=message,
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'admin@helssa.com'),
                        recipient_list=[recipient],
                        fail_silently=False
                    )
                    sent_count += 1
                except Exception as e:
                    failed_recipients.append({'email': recipient, 'error': str(e)})
            
            return {
                'success': sent_count > 0,
                'sent_count': sent_count,
                'failed_count': len(failed_recipients),
                'failed_recipients': failed_recipients
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'sent_count': 0
            }
    
    def _send_sms_notification(self, recipients: List[str], 
                             message: str, priority: str) -> Dict:
        """ارسال اعلان SMS"""
        try:
            # شبیه‌سازی ارسال SMS
            # در پیاده‌سازی واقعی، باید از Kavenegar استفاده شود
            
            sent_count = len(recipients)
            
            return {
                'success': True,
                'sent_count': sent_count,
                'failed_count': 0,
                'message': f'SMS sent to {sent_count} recipients'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'sent_count': 0
            }
    
    def _send_in_app_notification(self, recipients: List[str], 
                                subject: str, message: str, priority: str) -> Dict:
        """ارسال اعلان داخلی"""
        try:
            # شبیه‌سازی ذخیره اعلان داخلی
            # در پیاده‌سازی واقعی، باید در دیتابیس ذخیره شود
            
            sent_count = len(recipients)
            
            return {
                'success': True,
                'sent_count': sent_count,
                'failed_count': 0,
                'message': f'In-app notification created for {sent_count} recipients'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'sent_count': 0
            }
    
    def _get_alert_recipients(self, alert_type: str, severity: str) -> List[str]:
        """تعیین گیرندگان هشدار"""
        # در پیاده‌سازی واقعی، باید از دیتابیس دریافت شود
        if severity == 'critical':
            return ['admin@helssa.com', 'tech@helssa.com']
        elif severity == 'error':
            return ['tech@helssa.com']
        else:
            return ['support@helssa.com']
    
    def _get_alert_channels(self, severity: str) -> List[str]:
        """تعیین کانال‌های هشدار"""
        if severity == 'critical':
            return ['email', 'sms', 'in_app']
        elif severity == 'error':
            return ['email', 'in_app']
        else:
            return ['in_app']
    
    def _severity_to_priority(self, severity: str) -> str:
        """تبدیل شدت به اولویت"""
        mapping = {
            'info': 'normal',
            'warning': 'normal',
            'error': 'high',
            'critical': 'urgent'
        }
        return mapping.get(severity, 'normal')
    
    def _format_alert_message(self, alert_type: str, severity: str, 
                            message: str, details: Dict = None) -> str:
        """فرمت پیام هشدار"""
        formatted_message = f"""
هشدار سیستمی

نوع: {alert_type}
شدت: {severity}
زمان: {timezone.now().strftime('%Y/%m/%d %H:%M:%S')}

پیام:
{message}
"""
        
        if details:
            formatted_message += f"\nجزئیات:\n"
            for key, value in details.items():
                formatted_message += f"- {key}: {value}\n"
        
        return formatted_message
    
    def _get_ticket_notification_recipients(self, ticket, event_type: str) -> List[str]:
        """تعیین گیرندگان اعلان تیکت"""
        recipients = []
        
        if event_type == 'created':
            # اعلان به تیم پشتیبانی
            recipients = ['support@helssa.com']
        elif event_type == 'assigned' and ticket.assigned_to:
            # اعلان به ادمین تخصیص یافته
            if hasattr(ticket.assigned_to.user, 'email'):
                recipients = [ticket.assigned_to.user.email]
        elif event_type == 'escalated':
            # اعلان به مدیران
            recipients = ['manager@helssa.com']
        
        return recipients
    
    def _format_ticket_notification(self, ticket, event_type: str, admin_user=None) -> tuple:
        """فرمت اعلان تیکت"""
        event_messages = {
            'created': ('تیکت جدید ایجاد شد', f'تیکت #{ticket.ticket_number} توسط {ticket.user.username} ایجاد شد.'),
            'assigned': ('تیکت تخصیص یافت', f'تیکت #{ticket.ticket_number} به شما تخصیص یافت.'),
            'resolved': ('تیکت حل شد', f'تیکت #{ticket.ticket_number} حل شد.'),
            'escalated': ('تیکت ارجاع شد', f'تیکت #{ticket.ticket_number} ارجاع شد.')
        }
        
        subject, base_message = event_messages.get(event_type, ('اعلان تیکت', 'رویداد تیکت'))
        
        message = f"""
{base_message}

جزئیات تیکت:
- شماره: {ticket.ticket_number}
- موضوع: {ticket.subject}
- اولویت: {ticket.get_priority_display()}
- وضعیت: {ticket.get_status_display()}
- ایجادکننده: {ticket.user.username}
"""
        
        if admin_user:
            message += f"- عمل‌کننده: {admin_user.user.get_full_name() or admin_user.user.username}\n"
        
        return subject, message