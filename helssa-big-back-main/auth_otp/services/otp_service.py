"""
سرویس مدیریت OTP با قابلیت Rate Limiting
OTP Management Service with Rate Limiting
"""

from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from datetime import timedelta
from typing import Tuple, Optional
import logging

from ..models import OTPRequest, OTPRateLimit
from .kavenegar_service import KavenegarService

logger = logging.getLogger(__name__)


class OTPService:
    """
    سرویس مدیریت کامل OTP
    """
    
    def __init__(self):
        """

        یک نمونه‌ی سرویس OTP را مقداردهی اولیه می‌کند.
        
        این سازنده یک نمونه از KavenegarService را در صفت `self.kavenegar` ایجاد می‌کند که برای ارسال و قالب‌بندی پیام‌های OTP (از جمله SMS و تماس صوتی) توسط متدهای دیگر کلاس استفاده می‌شود.

        """
        self.kavenegar = KavenegarService()
    
    def send_otp(
        self,
        phone_number: str,
        purpose: str = 'login',
        sent_via: str = 'sms',
        ip_address: str = None,
        user_agent: str = None
    ) -> Tuple[bool, dict]:
        """

        ارسال یک کد یک‌بارمصرف (OTP) به شماره موبایل با اعمال محدودیت‌های نرخ و مدیریت چرخه‌ی OTP.
        
        این متد شماره را فرمت می‌کند، محدودیت‌های نرخ ارسال را بررسی می‌نماید، OTPهای قبلی برای همان شماره و هدف را باطل می‌کند، یک رکورد OTPRequest جدید می‌سازد و تلاش می‌کند کد را از طریق SMS یا تماس صوتی ارسال کند. در صورت موفقیت، شناسه پیام سرویس ارسال (kavenegar_message_id) در رکورد ذخیره و شمارنده‌های نرخ به‌روزرسانی می‌شوند و شناسهٔ درخواست OTP برای ۳ دقیقه در کش قرار می‌گیرد. در صورت شکست ارسال، خطای ارسال در متادیتا ثبت شده و شمارش تلاش‌های ناموفق افزایش می‌یابد. در صورت بروز استثنا، متد خطای داخلی را برگشت می‌دهد.
        
        Parameters:
            phone_number (str): شماره موبایل مقصد (قالب‌بندی توسط KavenegarService انجام می‌شود).
            purpose (str): هدف کاربردی OTP (مثلاً 'login'). به صورت پیش‌فرض 'login' است.
            sent_via (str): روش ارسال؛ مقدارهای پذیرفته‌شده: 'sms' یا 'call'.
            ip_address (str | None): آدرس IP درخواست‌دهنده (اختیاری).
            user_agent (str | None): رشته User-Agent درخواست‌دهنده (اختیاری).
        
        Returns:
            Tuple[bool, dict]: تاپل شامل نتیجهٔ عملیات و داده یا اطلاعات خطا.
                - موفقیت (True): {'otp_id', 'expires_at', 'expires_in', 'message'}
                - شکست در اثر محدودیت نرخ: {'error': 'rate_limit_exceeded', 'message', 'rate_limit_info'}
                - شکست ارسال: {'error': 'send_failed', 'message'}
                - روش ارسال نامعتبر: {'error': 'invalid_sent_via', 'message'}
                - خطای داخلی: {'error': 'internal_error', 'message'}

        """
        try:
            # فرمت کردن شماره
            phone_number = KavenegarService.format_phone_number(phone_number)
            
            # بررسی rate limit
            can_send, message = self._check_rate_limit(phone_number)
            if not can_send:
                return False, {
                    'error': 'rate_limit_exceeded',
                    'message': message,
                    'rate_limit_info': self._get_rate_limit_info(phone_number)
                }
            
            # باطل کردن OTP های قبلی
            self._invalidate_previous_otps(phone_number, purpose)
            
            # ایجاد OTP جدید
            otp_request = OTPRequest.objects.create(
                phone_number=phone_number,
                purpose=purpose,
                sent_via=sent_via,
                ip_address=ip_address,
                user_agent=user_agent or ''
            )
            
            # ارسال OTP
            if sent_via == 'sms':
                result = self.kavenegar.send_otp(
                    phone_number,
                    otp_request.otp_code
                )
            elif sent_via == 'call':
                result = self.kavenegar.send_voice_otp(
                    phone_number,
                    otp_request.otp_code
                )
            else:
                return False, {
                    'error': 'invalid_sent_via',
                    'message': 'روش ارسال نامعتبر است'
                }
            
            if result['success']:
                # ذخیره message_id
                otp_request.kavenegar_message_id = result['message_id']
                otp_request.save()
                
                # بروزرسانی rate limit
                self._update_rate_limit(phone_number)
                
                # کش کردن برای دسترسی سریع
                cache_key = f"otp_{phone_number}_{purpose}"
                cache.set(cache_key, otp_request.id, timeout=180)  # 3 دقیقه
                
                logger.info(
                    f"OTP sent successfully: {phone_number}, "
                    f"purpose: {purpose}, id: {otp_request.id}"
                )
                
                return True, {
                    'otp_id': str(otp_request.id),
                    'expires_at': otp_request.expires_at.isoformat(),
                    'expires_in': 180,  # ثانیه
                    'message': 'کد تأیید با موفقیت ارسال شد'
                }
            else:
                # خطا در ارسال
                otp_request.metadata['send_error'] = result.get('error_detail', '')
                otp_request.save()
                
                # افزایش تلاش ناموفق
                self._add_failed_attempt(phone_number)
                
                return False, {
                    'error': 'send_failed',
                    'message': result.get('error', 'خطا در ارسال کد تأیید')
                }
                
        except Exception as e:
            logger.error(f"Error in send_otp: {e}")
            return False, {
                'error': 'internal_error',
                'message': 'خطای سیستمی در ارسال کد تأیید'
            }
    
    def verify_otp(
        self,
        phone_number: str,
        otp_code: str,
        purpose: str = 'login'
    ) -> Tuple[bool, dict]:
        """

        بررسی و اعتبارسنجی یک کد OTP برای شماره موبایل مشخص و علامت‌گذاری آن به‌عنوان استفاده‌شده در صورت موفقیت.
        
        این تابع شماره را نرمال‌سازی می‌کند، ابتدا تلاش می‌کند درخواست OTP مرتبط را از کش بازیابی کند و در صورت عدم وجود از دیتابیس جدیدترین OTP غیر‌استفاده‌شده برای همان شماره و هدف را می‌یابد. سپس وضعیت قابل‌تأیید بودن OTP را بررسی می‌کند (منقضی/قبلاً استفاده‌شده/تعداد تلاش‌ها) و در صورت مطابقت کد:
        - در یک تراکنش اتمیک آن رکورد را به‌عنوان استفاده‌شده علامت‌گذاری می‌کند،
        - ورودی کش مربوطه را حذف می‌کند،
        - شمارندهٔ تلاش‌های ناموفق در محدودیت نرخ را بازنشانی می‌کند.
        
        پارامترها:
            phone_number (str): شماره موبایل هدف (ورودی قبل از نرمال‌سازی).
            otp_code (str): کدی که کاربر وارد کرده تا با OTP ذخیره‌شده مقایسه شود.
            purpose (str, optional): هدف OTP (مثلاً 'login'). به‌عنوان پیش‌فرض 'login' است.
        
        مقادیر بازگشتی:
            Tuple[bool, dict]: 
                - موفقیت (bool): True در صورت تأیید موفق، False در غیر این صورت.
                - dict: در حالت موفق شامل کلید 'otp_request' (رکورد OTP) و پیام موفقیت. در حالت ناموفق شامل کلید 'error' با یکی از مقادیر:
                    - 'otp_not_found' : وقتی هیچ OTP مربوطه یافت نشود.
                    - 'otp_expired' : وقتی OTP منقضی شده است.
                    - 'otp_already_used' : وقتی OTP قبلاً استفاده شده است.
                    - 'max_attempts_exceeded' : وقتی تعداد مجاز تلاش‌ها به پایان رسیده است.
                    - 'cannot_verify' : وقتی به دلایل دیگر نمی‌توان OTP را تأیید کرد.
                    - 'invalid_otp' : وقتی کد وارد‌شده نادرست است (شامل 'remaining_attempts').
                    - 'internal_error' : خطای سیستمی در هنگام اجرای عملیات.
        
        تأثیرات جانبی:
            - در صورت موفقیت، رکورد OTP به‌عنوان استفاده‌شده علامت‌گذاری شده و ورودی کش حذف می‌شود.
            - در صورت خطای بررسی یا تلاش ناموفق، شمارندهٔ تلاش‌های OTP افزایش می‌یابد.
            - در صورت تطابق موفق، شمارندهٔ تلاش‌های ناموفق مرتبط با محدودیت نرخ بازنشانی می‌شود.

        """
        try:
            # فرمت کردن شماره
            phone_number = KavenegarService.format_phone_number(phone_number)
            
            # جستجو در کش
            cache_key = f"otp_{phone_number}_{purpose}"
            otp_id = cache.get(cache_key)
            
            if otp_id:
                # پیدا کردن از کش
                otp_request = OTPRequest.objects.filter(
                    id=otp_id,
                    phone_number=phone_number,
                    purpose=purpose
                ).first()
            else:
                # جستجو در دیتابیس
                otp_request = OTPRequest.objects.filter(
                    phone_number=phone_number,
                    purpose=purpose,
                    is_used=False
                ).order_by('-created_at').first()
            
            if not otp_request:
                return False, {
                    'error': 'otp_not_found',
                    'message': 'کد تأیید یافت نشد یا منقضی شده است'
                }
            
            # بررسی امکان تأیید
            if not otp_request.can_verify:
                if otp_request.is_expired:
                    return False, {
                        'error': 'otp_expired',
                        'message': 'کد تأیید منقضی شده است'
                    }
                elif otp_request.is_used:
                    return False, {
                        'error': 'otp_already_used',
                        'message': 'این کد قبلاً استفاده شده است'
                    }
                elif otp_request.attempts >= 3:
                    return False, {
                        'error': 'max_attempts_exceeded',
                        'message': 'تعداد تلاش‌های مجاز به پایان رسیده است'
                    }
                else:
                    return False, {
                        'error': 'cannot_verify',
                        'message': 'امکان تأیید این کد وجود ندارد'
                    }
            
            # بررسی کد
            if otp_request.otp_code != otp_code:
                # افزایش تعداد تلاش
                otp_request.increment_attempts()
                
                remaining = 3 - otp_request.attempts
                if remaining > 0:
                    return False, {
                        'error': 'invalid_otp',
                        'message': f'کد تأیید اشتباه است. {remaining} تلاش باقی‌مانده',
                        'remaining_attempts': remaining
                    }
                else:
                    return False, {
                        'error': 'invalid_otp',
                        'message': 'کد تأیید اشتباه است و تلاش‌های مجاز تمام شد',
                        'remaining_attempts': 0
                    }
            
            # کد صحیح است
            with transaction.atomic():
                # علامت‌گذاری به عنوان استفاده شده
                otp_request.mark_as_used()
                
                # حذف از کش
                cache.delete(cache_key)
                
                # ریست rate limit برای تلاش‌های ناموفق
                self._reset_failed_attempts(phone_number)
                
                logger.info(
                    f"OTP verified successfully: {phone_number}, "
                    f"purpose: {purpose}"
                )
                
                return True, {
                    'otp_request': otp_request,
                    'message': 'کد تأیید با موفقیت تأیید شد'
                }
                
        except Exception as e:
            logger.error(f"Error in verify_otp: {e}")
            return False, {
                'error': 'internal_error',
                'message': 'خطای سیستمی در تأیید کد'
            }
    
    def resend_otp(
        self,
        phone_number: str,
        purpose: str = 'login',
        sent_via: str = 'sms',
        ip_address: str = None,
        user_agent: str = None
    ) -> Tuple[bool, dict]:
        """

        ارسال مجدد کد یک‌بارمصرف (OTP) — نمایشی که همان رفتار send_otp را اجرا می‌کند.
        
        این متد به سادگی فراخوانی send_otp با پارامترهای داده‌شده را انجام می‌دهد و برای مواقعی که نیاز به درخواست مجدد OTP است استفاده می‌شود. قبل از ایجاد OTP جدید، قبلی‌ها (برای همان شماره و هدف) باطل می‌شوند (رفتار از send_otp گرفته می‌شود).
        
        Parameters:
            phone_number (str): شماره تلفن مقصد (باید در فرمت قابل قبول سرویس ارسال باشد).
            purpose (str): هدف کد OTP (پیش‌فرض 'login'). برای تمایز OTPها بر حسب منظور استفاده می‌شود.
            sent_via (str): روش ارسال ('sms' یا 'call')، پیش‌فرض 'sms'.
            ip_address (str|None): آدرس آی‌پی درخواست‌دهنده در صورت موجود بودن.
            user_agent (str|None): رشته User-Agent در صورت موجود بودن.
        
        Returns:
            Tuple[bool, dict]: اگر موفق باشد (True, payload) بازمی‌گرداند که payload شامل کلیدهای مثلاً `otp_id`, `expires_at`, `expires_in`, `message` است. در صورت خطا (False, error_payload) مقدار بازگردانده شده شامل شناسه خطا و جزئیات (مانند اطلاعات محدودیت نرخ `rate_limit_info` یا پیام‌های مرتبط) خواهد بود.

        """
        # همان send_otp با باطل کردن قبلی‌ها
        return self.send_otp(
            phone_number,
            purpose,
            sent_via,
            ip_address,
            user_agent
        )
    
    def _check_rate_limit(self, phone_number: str) -> Tuple[bool, str]:
        """

        بررسی و بازیابی محدودیت نرخ ارسال OTP برای یک شماره تلفن.
        
        این متد یک رکورد OTPRateLimit برای phone_number را می‌گیرد یا در صورت عدم وجود ایجاد می‌کند و سپس وضعیت اجازه ارسال OTP را از متد `can_send_otp()` آن بازمی‌گرداند.
        
        Returns:
            Tuple[bool, str]: زوجی شامل
                - bool: نشان‌دهندهٔ امکان ارسال (True اگر مجاز به ارسال باشد).
                - str: رشتهٔ کوتاهی که دلیل عدم اجازه یا کد وضعیت را منتقل می‌کند (در صورت مجاز بودن معمولاً خالی یا مقدار مشابه).

        """
        rate_limit, created = OTPRateLimit.objects.get_or_create(
            phone_number=phone_number
        )
        
        return rate_limit.can_send_otp()
    
    def _update_rate_limit(self, phone_number: str):
        """

        شمارنده‌های محدودیت ارسال (rate limit) برای شماره تلفن داده‌شده را افزایش می‌کند.
        
        اگر رکورد OTPRateLimit مربوط به phone_number وجود نداشته باشد، آن را ایجاد می‌کند و سپس نگهداریِ پنجره‌های محدودیت (مانند شمارش‌های دقیقه‌ای/ساعتی/روزانه) را با فراخوانی `increment_counters` به‌روزرسانی می‌کند. این متد مقدار قابل ارسال بعدی را تغییر می‌دهد و برای اعمال سیاست‌های بلوکه‌سازی یا محاسبه باقیمانده‌ها استفاده می‌شود.
        
        پارامترها:
            phone_number (str): شماره تلفن هدف؛ انتظار می‌رود به فرمت نرمال‌شده (مثلاً با استفاده از سرویس فرمت‌کننده) باشد.

        """
        rate_limit, _ = OTPRateLimit.objects.get_or_create(
            phone_number=phone_number
        )
        rate_limit.increment_counters()
    
    def _add_failed_attempt(self, phone_number: str):
        """

        تعداد تلاش‌های ناموفق ورود با کد OTP برای یک شماره تلفن مشخص را افزایش می‌دهد.
        
        این متد یک رکورد OTPRateLimit برای شماره تلفن موردنظر را بازیابی یا در صورت نبود ایجاد می‌کند و سپس شمارش تلاش‌های ناموفق را از طریق متد rate_limit.add_failed_attempt() افزایش می‌دهد. از مقدار phone_number به‌عنوان رشته شماره تلفن (ترجیحاً در فرمت نرمال‌شده/بین‌المللی) استفاده می‌شود. متد مقداری بازنمی‌گرداند و خطاهای داده‌شده از لایه مدل به فراخواننده منتقل می‌شوند.

        """
        rate_limit, _ = OTPRateLimit.objects.get_or_create(
            phone_number=phone_number
        )
        rate_limit.add_failed_attempt()
    
    def _reset_failed_attempts(self, phone_number: str):
        """

        ریست شمارندهٔ تلاش‌های ناموفق ارسال/تأیید OTP برای یک شماره تلفن.
        
        پارامترها:
            phone_number (str): شماره تلفن (باید به فرم نرمال‌شده‌ای که در مدل‌ها ذخیره می‌شود)؛ اگر رکورد نرخ‌محدودسازی برای این شماره وجود نداشته باشد، تابع بدون خطا هیچ کاری انجام نمی‌دهد.
        
        توضیحات:
            این تابع فیلد `failed_attempts` را در شیٔ `OTPRateLimit` مربوط به شمارهٔ داده‌شده به صفر بازمی‌گرداند و تغییر را ذخیره می‌کند. هیچ مقداری برنمی‌گرداند و در صورت عدم وجود رکورد مرتبط، به‌صورت ساکت عبور می‌کند (بدون ایجاد خطا).

        """
        try:
            rate_limit = OTPRateLimit.objects.get(phone_number=phone_number)
            rate_limit.failed_attempts = 0
            rate_limit.save()
        except OTPRateLimit.DoesNotExist:
            pass
    
    def _invalidate_previous_otps(self, phone_number: str, purpose: str):
        """

        تمام OTPهای صادر شده قبلی برای یک شماره و هدف مشخص را به‌صورت دائمی باطل (نشانه‌گذاری شده به‌عنوان استفاده‌شده) می‌کند.
        
        این متد تمامی ردیف‌های OTPRequest که همان phone_number و purpose را دارند و هنوز is_used=False هستند را در پایگاه‌داده به‌روزرسانی می‌کند (is_used=True) تا از امکان استفادهٔ مجدد آن‌ها جلوگیری شود. عملیات فقط یک بروزرسانی در دیتابیس انجام می‌دهد و رکوردها را حذف نمی‌کند؛ فراخوانی مکرر ایمن و ایندمپوتنت است.

        """
        OTPRequest.objects.filter(
            phone_number=phone_number,
            purpose=purpose,
            is_used=False
        ).update(is_used=True)
    
    def _get_rate_limit_info(self, phone_number: str) -> dict:
        """

        اطلاعات وضعیت محدودیت نرخ (rate limit) مربوط به شماره‌ی تلفن را برمی‌گرداند.
        
        این متد موجودیت OTPRateLimit مرتبط با phone_number را بارگذاری کرده، پنجره‌های زمانی را به‌روزرسانی می‌کند و یک دیکشنری شامل باقی‌ماندهٔ ارسال‌ها در بازه‌های دقیقه‌ای، ساعتی و روزانه و همچنین وضعیت مسدودی را بازمی‌گرداند. اگر رکورد محدودیت وجود نداشته باشد، مقادیر پیش‌فرض بازگردانده می‌شوند.
        
        Parameters:
            phone_number (str): شماره تلفن هدف (ترجیحاً در فرمت نرمال‌شده/E.164).
        
        Returns:
            dict: دیکشنری با کلیدهای زیر:
                - minute_remaining (int): تعداد ارسال‌های قابل انجام باقی‌مانده در بازهٔ فعلی دقیقه.
                - hour_remaining (int): تعداد ارسال‌های قابل انجام باقی‌مانده در بازهٔ فعلی ساعت.
                - daily_remaining (int): تعداد ارسال‌های قابل انجام باقی‌مانده در بازهٔ روزانه.
                - is_blocked (bool): نشان‌دهندهٔ این‌که آیا شماره در حالت مسدودی است یا خیر.
                - blocked_until (str|None): زمان پایان مسدودی به صورت ISO8601 یا None در صورت عدم مسدودی.

        """
        try:
            rate_limit = OTPRateLimit.objects.get(phone_number=phone_number)
            rate_limit.check_and_update_windows()
            
            return {
                'minute_remaining': max(0, 1 - rate_limit.minute_count),
                'hour_remaining': max(0, 5 - rate_limit.hour_count),
                'daily_remaining': max(0, 10 - rate_limit.daily_count),
                'is_blocked': rate_limit.is_blocked,
                'blocked_until': rate_limit.blocked_until.isoformat() if rate_limit.blocked_until else None
            }
        except OTPRateLimit.DoesNotExist:
            return {
                'minute_remaining': 1,
                'hour_remaining': 5,
                'daily_remaining': 10,
                'is_blocked': False,
                'blocked_until': None
            }
    
    @staticmethod
    def cleanup_expired_otps():
        """

        حذف همهٔ رکوردهای OTPRequest که بیش از ۲۴ ساعت از ایجادشان گذشته است.
        
        این تابع رکوردهای مدل OTPRequest را که فیلد created_at آن‌ها کمتر از زمان فعلی منهای ۲۴ ساعت باشد حذف می‌کند، تعداد رکوردهای حذف‌شده را برمی‌گرداند و در صورت حذف شدن هر رکورد، یک پیام لاگ اطلاع‌رسانی ثبت می‌کند.
        
        Returns:
            int: تعداد رکوردهای OTP حذف‌شده.
main
        """
        cutoff = timezone.now() - timedelta(hours=24)
        deleted_count = OTPRequest.objects.filter(
            created_at__lt=cutoff
        ).delete()[0]
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired OTP requests")
        
        return deleted_count