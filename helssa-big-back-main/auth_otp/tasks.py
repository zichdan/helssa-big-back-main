"""
تسک‌های Celery برای auth_otp
Celery Tasks for auth_otp
"""

from celery import shared_task
from django.utils import timezone
import logging

from .services import OTPService, AuthService

logger = logging.getLogger(__name__)


@shared_task(name='auth_otp.tasks.cleanup_expired_otp')
def cleanup_expired_otp():
    """

    پاکسازی دوره‌ای OTP‌های منقضی‌شده و بازگشت گزارش اجرای تسک.
    
    این تابع به‌عنوان یک تسک پس‌زمینه اجرا می‌شود و تمام OTPهایی را که براساس منطق داخل سرویس OTPService منقضی شده‌اند حذف می‌کند. عملیات حذف توسط OTPService.cleanup_expired_otps() انجام می‌شود و تعداد رکوردهای حذف‌شده گزارش می‌شود. خطاها مستقیماً پرتاب نمی‌شوند؛ در صورت بروز استثنا، تابع آن را لاگ کرده و نتیجه‌ای با وضعیت خطا برمی‌گرداند.
    
    Returns:
        dict: یک دیکشنری حاوی نتیجه اجرا با ساختار زیر:
            - status (str): 'success' در صورت موفقیت یا 'error' در صورت خطا.
            - deleted_count (int): تعداد OTP‌های حذف‌شده (فقط در صورت موفقیت).
            - error (str): پیام خطا (فقط در صورت خطا).
            - timestamp (str): زمان اجرای تسک به فرمت ISO.

    """
    try:
        logger.info("Starting OTP cleanup task")
        
        deleted_count = OTPService.cleanup_expired_otps()
        
        logger.info(f"Successfully cleaned up {deleted_count} expired OTP requests")
        
        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in OTP cleanup task: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task(name='auth_otp.tasks.cleanup_expired_tokens')
def cleanup_expired_tokens():
    """

    تسک پس‌زمینه برای حذف توکن‌های منقضی از لیست سیاه.
    
    این تابع فراخوانی‌ای به AuthService.cleanup_expired_blacklist انجام می‌دهد تا ورودی‌های لیست سیاه (blacklist) که تاریخ انقضای آن‌ها گذشته است حذف شوند، و سپس یک نتیجه ساختاری بازمی‌گرداند. در اجرای موفق، دیکشنری‌ای با کلیدهای زیر برمی‌گردد:
    - status: 'success'
    - deleted_count: تعداد رکوردهای حذف‌شده
    - timestamp: زمان اجرای عملیات به صورت ISO
    
    در صورت بروز هرگونه استثنا، استثنا لاگ شده و به‌جای آن دیکشنری خطا بازگردانده می‌شود با کلیدهای:
    - status: 'error'
    - error: متن پیام خطا
    - timestamp: زمان وقوع خطا به صورت ISO
    
    تأثیر جانبی: تغییر در داده‌های persistent (حذف رکوردهای blacklist) از طریق AuthService.

    """
    try:
        logger.info("Starting token blacklist cleanup task")
        
        deleted_count = AuthService.cleanup_expired_blacklist()
        
        logger.info(f"Successfully cleaned up {deleted_count} expired blacklisted tokens")
        
        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in token cleanup task: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task(name='auth_otp.tasks.check_rate_limits')
def check_rate_limits():
    """

    بررسی و بروزرسانی پنجره‌های محدودیت نرخ (rate limits) برای OTP.
    
    این تسک تمام رکوردهای OTPRateLimit را بارگذاری می‌کند، برای هر رکورد متد
    `check_and_update_windows()` را فراخوانی می‌کند و در صورت نیاز شمارنده‌های
    دقیقه‌ای یا ساعتی را ریست می‌کند یا وضعیت مسدودسازی را به‌روزرسانی می‌کند.
    هر رکورد پس از بروزرسانی ذخیره می‌شود؛ بنابراین این تابع تغییراتی در پایگاه‌داده ایجاد می‌کند.
    
    بازگشتی:
        dict: در حالت موفقیت ساختاری شامل کل تعداد بررسی‌شده (`total_checked`)،
        تعداد رکوردهایی که پنجره‌هایشان ریست یا آپدیت شده‌اند (`updated_count`)،
        تعداد رکوردهایی که از حالت مسدود خارج شده‌اند (`unblocked_count`)،
        وضعیت عملیات (`status` == 'success') و یک `timestamp` به صورت ISO.
        در صورت بروز خطا یک دیکشنری شامل `status` == 'error'، پیام خطا در `error`
        و `timestamp` بازگردانده می‌شود.
    
    توجه:
        - این تابع صراحتاً استثناها را پرتاب نمی‌کند؛ خطاها گرفته و به صورت دیکشنری بازگردانده می‌شوند.
        - تابع وابسته به مدل `OTPRateLimit` است و از آن در زمان اجرا وارد می‌شود.

    """
    try:
        from .models import OTPRateLimit
        
        logger.info("Starting rate limit check task")
        
        # دریافت تمام rate limit ها
        rate_limits = OTPRateLimit.objects.all()
        
        updated_count = 0
        unblocked_count = 0
        
        for rate_limit in rate_limits:
            # بررسی و بروزرسانی پنجره‌های زمانی
            rate_limit.check_and_update_windows()
            
            # شمارش موارد بروزرسانی شده
            if rate_limit.minute_count == 0 or rate_limit.hour_count == 0:
                updated_count += 1
            
            # شمارش موارد رفع مسدودیت
            if not rate_limit.is_blocked and rate_limit.blocked_until:
                unblocked_count += 1
            
            rate_limit.save()
        
        logger.info(
            f"Rate limit check completed: "
            f"{updated_count} updated, {unblocked_count} unblocked"
        )
        
        return {
            'status': 'success',
            'total_checked': rate_limits.count(),
            'updated_count': updated_count,
            'unblocked_count': unblocked_count,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in rate limit check task: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task(name='auth_otp.tasks.send_otp_async')
def send_otp_async(phone_number, purpose='login', sent_via='sms'):
    """

    ارسال یک OTP در پس‌زمینه و بازگرداندن وضعیت اجرا.
    
    این تابع با استفاده از سرویس OTPService یک کد یک‌بار مصرف (OTP) برای شماره تلفن مشخص ارسال می‌کند و برای اجرا در تسک‌های پس‌زمینه مناسب است. تابع وضعیت ارسال را ثبت کرده و یک دیکشنری نتیجه شامل وضعیت، خروجی سرویس و زمان اجرای عملیات را بازمی‌گرداند. در صورت بروز استثناء، استثناء گرفته شده و یک پاسخ با وضعیت 'error' و پیام خطا بازگردانده می‌شود.
    
    پارامترها:
        phone_number (str): شماره تلفنی که باید OTP برای آن ارسال شود (فرمت مورد انتظار وابسته به پیاده‌سازی سرویس).
        purpose (str, اختیاری): هدف OTP (مثلاً 'login', 'verification'). مقدار پیش‌فرض 'login' است و برای تعیین منطق اختصاصی در سرویس استفاده می‌شود.
        sent_via (str, اختیاری): کانال ارسال؛ معمولاً 'sms' یا 'call'. مقدار پیش‌فرض 'sms' است.
    
    مقدار بازگشتی:
        dict: دیکشنری با کلیدهای زیر:
            - status (str): یکی از 'success' (ارسال موفق)، 'failed' (ارسال ناموفق اما بدون استثناء)، یا 'error' (خطای اجرایی).
            - result (any): خروجی بازگشتی از OTPService.send_otp در حالت‌های 'success' یا 'failed' (ممکن است شامل شناسه ارسال، پیام خطا یا جزئیات دیگر باشد).
            - error (str, فقط در صورت 'error'): رشته پیام خطا هنگام بروز استثناء.
            - timestamp (str): زمان ایجاد پاسخ به فرمت ISO (به صورت timezone-aware).
    
    توجه:
        - تابع خود استثناء‌ها را مدیریت می‌کند و آنها را به صورت یک پاسخ خطاداده (status='error') تبدیل می‌کند، بنابراین فراخواننده نیازی به مدیریت استثناء برای مقاصد رایج ندارد.
        - جزئیات دقیق رفتار و فرمت خروجی در result وابسته به پیاده‌سازی OTPService.send_otp است.

    """
    try:
        from .services import OTPService
        
        logger.info(f"Sending OTP asynchronously to {phone_number}")
        
        otp_service = OTPService()
        success, result = otp_service.send_otp(
            phone_number=phone_number,
            purpose=purpose,
            sent_via=sent_via
        )
        
        if success:
            logger.info(f"OTP sent successfully to {phone_number}")
        else:
            logger.error(f"Failed to send OTP to {phone_number}: {result}")
        
        return {
            'status': 'success' if success else 'failed',
            'result': result,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in async OTP send: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task(name='auth_otp.tasks.generate_otp_report')
def generate_otp_report(start_date=None, end_date=None):
    """

    تولید گزارش استفاده از سیستم OTP برای یک بازهٔ زمانی مشخص.
    
    توضیحات:
    این تابع آمارهای کلیدی مربوط به درخواست‌ها و تأییدیه‌های OTP را در بازهٔ زمانی داده‌شده محاسبه کرده و گزارشی شامل دورهٔ گزارش، آمار درخواست‌ها، آمار تأییدیه‌ها، تفکیک بر اساس purpose، نرخ موفقیت (درصد درخواست‌های استفاده‌شده) و زمان تولید گزارش بازمی‌گرداند. در صورت بروز خطا، به‌جای پرتاب استثناء یک دیکت با کلیدهای `status='error'`، `error` و `timestamp` بازگردانده می‌شود.
    
    پارامترها:
        start_date (datetime | None): شروع بازهٔ گزارش. اگر ارائه نشود، برابر با end_date منهای ۷ روز قرار می‌گیرد.
        end_date (datetime | None): پایان بازهٔ گزارش. اگر ارائه نشود، زمان جاری در نظر گرفته می‌شود.
    
    مقدار بازگشتی:
        dict: در حالت موفقیت یک دیکت حاوی کلیدهای زیر برمی‌گردد:
            - period: {'start': ISO-8601 شروع، 'end': ISO-8601 پایان}
            - otp_stats: دیکشنری شامل شمارش‌ها (total_requests, used_requests, sms_requests, call_requests)
            - verification_stats: دیکشنری شامل شمارش‌های تأییدیه (total_verifications, active_sessions)
            - purpose_breakdown: لیستی از دیکشنری‌ها با کلیدهای 'purpose' و 'count'
            - success_rate: درصد درخواست‌های استفاده‌شده نسبت به کل درخواست‌ها (عدد بین 0 تا 100)
            - generated_at: زمان تولید گزارش به صورت رشتهٔ ISO-8601
        در صورت خطا، دیکشنری با کلیدهای:
            - status: 'error'
            - error: پیام خطا
            - timestamp: زمان وقوع خطا (ISO-8601)
    
    وضاحت‌های اضافی:
        - بازه‌ها شامل مرزهای شروع و پایان هستند (>= start_date و <= end_date).
        - تابع استثناءها را درون خود مدیریت می‌کند و به‌جای پرتاب، ساختار خطا را بازمی‌گرداند.

    """
    try:
        from .models import OTPRequest, OTPVerification
        from django.db.models import Count, Q
        from datetime import timedelta
        
        logger.info("Generating OTP usage report")
        
        # تعیین بازه زمانی
        if not end_date:
            end_date = timezone.now()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        # آمار درخواست‌های OTP
        otp_stats = OTPRequest.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).aggregate(
            total_requests=Count('id'),
            used_requests=Count('id', filter=Q(is_used=True)),
            sms_requests=Count('id', filter=Q(sent_via='sms')),
            call_requests=Count('id', filter=Q(sent_via='call')),
        )
        
        # آمار تأییدیه‌ها
        verification_stats = OTPVerification.objects.filter(
            verified_at__gte=start_date,
            verified_at__lte=end_date
        ).aggregate(
            total_verifications=Count('id'),
            active_sessions=Count('id', filter=Q(is_active=True)),
        )
        
        # آمار بر اساس purpose
        purpose_stats = OTPRequest.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).values('purpose').annotate(count=Count('id'))
        
        report = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'otp_stats': otp_stats,
            'verification_stats': verification_stats,
            'purpose_breakdown': list(purpose_stats),
            'success_rate': (
                (otp_stats['used_requests'] / otp_stats['total_requests'] * 100)
                if otp_stats['total_requests'] > 0 else 0
            ),
            'generated_at': timezone.now().isoformat()
        }
        
        logger.info(f"OTP report generated successfully: {report}")
        
        return report
        
    except Exception as e:
        logger.error(f"Error generating OTP report: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }