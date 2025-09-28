"""
سرویس مدیریت توکن‌ها و احراز هویت
Token Management and Authentication Service
"""

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from typing import Tuple, Optional, Dict
import jwt
import uuid
import logging

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from ..models import OTPVerification, TokenBlacklist

logger = logging.getLogger(__name__)
User = get_user_model()


class AuthService:
    """
    سرویس مدیریت احراز هویت و توکن‌ها
    """
    
    @staticmethod
    def create_user_if_not_exists(phone_number: str, user_type: str = 'patient') -> Tuple[User, bool]:
        """

        ایجاد یا واکشی یک کاربر براساس شماره تلفن و بازگرداندن نشانگر ایجاد جدید
        
        این تابع تلاش می‌کند کاربری با مقدار `phone_number` به‌عنوان `username` در مدل کاربر پیدا کند. اگر موجود باشد، آن کاربر برگردانده می‌شود و نشانگر `is_new` برابر False خواهد بود. در غیر این صورت کاربری جدید با `username=phone_number`، `user_type` مشخص‌شده و وضعیت فعال (`is_active=True`) ایجاد می‌شود و `is_new` برابر True برمی‌گردد.
        
        Parameters:
            phone_number (str): شماره موبایل که به‌عنوان `username` کاربر استفاده می‌شود.
            user_type (str): نوع کاربر برای فیلد `user_type` در مدل کاربر؛ مقدار پیش‌فرض `'patient'`.
        
        Returns:
            Tuple[User, bool]: تاپل شامل نمونه کاربر و یک بولین که نشان می‌دهد آیا کاربر جدید ایجاد شده (`True`) یا از قبل موجود بوده (`False`) .

        یک کاربر را با username برابر phone_number بازیابی می‌کند یا در صورت نبود، یک کاربر فعال جدید می‌سازد.
        
        شرح:
        - تلاش می‌کند کاربری را با username برابر شمارهٔ موبایل پیدا کند؛ در صورت وجود، همان کاربر بازگردانده می‌شود.
        - اگر کاربر پیدا نشود، یک کاربر جدید با username=phone_number، user_type مشخص و is_active=True ایجاد می‌کند و آن را بازمی‌گرداند.
        - در صورت ایجاد کاربر جدید، یک پیام اطلاعاتی در لاگ ثبت می‌شود.
        
        پارامترها:
            phone_number (str): شماره موبایل که به‌عنوان username استفاده می‌شود.
            user_type (str): نوع کاربر جدید در صورت ایجاد (پیش‌فرض 'patient').
        
        بازگشتی:
            Tuple[User, bool]: تاپل شامل شیء User و یک بولن که نشان می‌دهد آیا کاربر جدید ایجاد شده (True) یا کاربر موجود بازگردانده شده (False).

        """
        try:
            user = User.objects.get(username=phone_number)
            is_new = False
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=phone_number,
                user_type=user_type,
                is_active=True
            )
            is_new = True
            logger.info(f"New user created: {phone_number}, type: {user_type}")
        
        return user, is_new
    
    @staticmethod
    def generate_tokens(user: User) -> Dict[str, any]:
        """

        تولید توکن‌های JWT دسترسی و تازه‌سازی برای یک کاربر و بازگرداندن متادیتای مرتبط.
        
        این تابع یک RefreshToken برای کاربر ایجاد کرده و Claims اضافی `user_type` و `phone_number` را به آن می‌افزاید. زمان انقضای توکن‌ها از تنظیمات `SIMPLE_JWT` خوانده می‌شود و در صورت نبودن مقدار پیش‌فرض برای زمان دسترسی و تازه‌سازی به‌ترتیب ۵ دقیقه و ۷ روز در نظر گرفته می‌شود.
        
        پارامترها:
            user: شیء User که برای او توکن‌ها تولید می‌شود (از username به‌عنوان شماره تلفن استفاده می‌شود).
        
        بازگشت:
            dict شامل کلیدهای زیر:
            - access (str): توکن دسترسی (Access Token).
            - refresh (str): توکن تازه‌سازی (Refresh Token).
            - token_type (str): نوع توکن (معمولاً 'Bearer').
            - expires_in (int): طول عمر توکن دسترسی بر حسب ثانیه.
            - access_expires_at (str): زمان انقضای توکن دسترسی به صورت ISO 8601.
            - refresh_expires_at (str): زمان انقضای توکن تازه‌سازی به صورت ISO 8601.

        تولید توکن‌های JWT (دسترسی و رفرش) برای یک کاربر و بازگرداندن متادیتای مرتبط.
        
        توضیحات:
            این تابع یک RefreshToken برای کاربر می‌سازد، دو claim اضافی `user_type` و `phone_number`
            را به توکن رفرش اضافه می‌کند و سپس یک توکن دسترسی (access) و رفرش (refresh) به‌صورت رشته‌ای
            بازمی‌گرداند. همچنین زمان عمر توکن دسترسی به ثانیه و زمان پایان اعتبار هر دو توکن به‌صورت
            ISO-8601 ارائه می‌شود.
        
        پارامترها:
            user: نمونهٔ مدل User که برای آن توکن‌ها تولید می‌شود. فیلد `user_type` و `username`
                  (شماره تلفن) از این شیء برای افزودن claimها استفاده می‌شود.
        
        بازگشتی:
            dict شامل کلیدهای زیر:
              - access (str): توکن دسترسی به‌صورت رشته.
              - refresh (str): توکن رفرش به‌صورت رشته.
              - token_type (str): نوع توکن (مثلاً 'Bearer').
              - expires_in (int): مدت زمان اعتبار توکن دسترسی بر حسب ثانیه.
              - access_expires_at (str): زمان پایان اعتبار توکن دسترسی به‌صورت رشته ISO-8601.
              - refresh_expires_at (str): زمان پایان اعتبار توکن رفرش به‌صورت رشته ISO-8601.

        """
        refresh = RefreshToken.for_user(user)
        
        # افزودن claims اضافی
        refresh['user_type'] = user.user_type
        refresh['phone_number'] = user.username
        
        # محاسبه زمان انقضا
        access_lifetime = getattr(
            settings,
            'SIMPLE_JWT',
            {}
        ).get('ACCESS_TOKEN_LIFETIME', timedelta(minutes=5))
        
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'token_type': 'Bearer',
            'expires_in': int(access_lifetime.total_seconds()),
            'access_expires_at': (timezone.now() + access_lifetime).isoformat(),
            'refresh_expires_at': (
                timezone.now() + 
                getattr(settings, 'SIMPLE_JWT', {}).get(
                    'REFRESH_TOKEN_LIFETIME',
                    timedelta(days=7)
                )
            ).isoformat()
        }
    
    @staticmethod
    def create_verification_record(
        otp_request,
        user: User,
        tokens: Dict[str, str],
        device_id: str = None,
        device_name: str = None,
        session_key: str = None
    ) -> OTPVerification:
        """
<<< <<<< coderabbitai/docstrings/90aa429
        ایجاد و ذخیره یک رکورد OTPVerification که مرتبط با درخواست OTP، کاربر و جفت توکن‌های دسترسی/ریفرش است.
        
        این تابع یک ورودی OTPVerification در دیتابیس می‌سازد و مقادیر زیر را تنظیم می‌کند:
        - access_token و refresh_token از دیکشنری tokens (الزامی: کلیدهای 'access' و 'refresh' باید موجود باشند).
        - device_id: در صورت عدم‌ارائه، یک UUID جدید تولید می‌شود.
        - device_name: در صورت عدم‌ارائه مقدار پیش‌فرض 'Unknown Device' استفاده می‌شود.
        - session_key: در صورت عدم‌ارائه به صورت رشته خالی ذخیره می‌شود.
        
        عوارض جانبی:
        - رکورد در پایگاه داده ایجاد و لاگ‌گذاری می‌شود.
        
        Parameters:
            otp_request: شیء یا شناسه درخواست OTP که این تأیید به آن مرتبط است.
            user: نمونه User مرتبط با این تأیید.
            tokens (dict): دیکشنری شامل کلیدهای 'access' و 'refresh' با مقادیر توکن متناظر.
            device_id (str, optional): شناسه دستگاه؛ در صورت نبودن یک UUID تولید می‌شود.
             device_name (str, optional): نام دستگاه؛ پیش‌فرض 'Unknown Device'.
            session_key (str, optional): کلید نشست مرتبط؛ پیش‌فرض رشته خالی.
        
        Returns:
            OTPVerification: نمونهٔ ایجاد‌شدهٔ رکورد تأییدیه.
        """
        verification = OTPVerification.objects.create(
            otp_request=otp_request,
            user=user,
            access_token=tokens['access'],
            refresh_token=tokens['refresh'],
            device_id=device_id or str(uuid.uuid4()),
            device_name=device_name or 'Unknown Device',
            session_key=session_key or ''
        )
        
        logger.info(
            f"Verification record created for user: {user.username}, "
            f"device: {device_name}"
        )
        
        return verification
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> Tuple[bool, Dict[str, any]]:
        """

        یک Refresh Token را اعتبارسنجی و از آن یک Access Token جدید (و در صورت تنظیمات، Refresh Token جدید) صادر می‌کند.
        
        شرح:
        - اگر Refresh Token در لیست سیاه باشد، درخواست رد می‌شود.
        - توکن را بارگذاری کرده و کاربر مرتبط را بررسی می‌کند؛ در صورت عدم وجود یا غیرفعال بودن کاربر، خطای مربوط بازگردانده می‌شود.
        - یک Access Token جدید از payloadِ Refresh استخراج می‌شود.
        - در صورت فعال بودن تنظیمات SIMPLE_JWT.ROTATE_REFRESH_TOKENS (پیش‌فرض True) یک Refresh Token جدید برای کاربر ساخته می‌شود و در صورت روشن بودن SIMPLE_JWT.BLACKLIST_AFTER_ROTATION توکن قدیمی در جدول سیاه‌سازی ثبت می‌شود.
        - مقدار عمر (expires_in) از SIMPLE_JWT.ACCESS_TOKEN_LIFETIME خوانده می‌شود و در صورت عدم وجود مقدار پیش‌فرض ۵ دقیقه استفاده می‌شود.
        
        پارامترها:
            refresh_token (str): رشته‌ی Refresh Token دریافتی که باید تازه‌سازی شود.
        
        مقادیر بازگشتی:
            Tuple[bool, dict] — اگر موفق باشد مقدار True و دیکشنری شامل کلیدهای زیر بازگردانده می‌شود:
                - access (str): Access Token تازه.
                - token_type (str): نوع توکن ('Bearer').
                - expires_in (int): زمان انقضا به ثانیه برای Access Token.
                - refresh (str, اختیاری): در صورت فعال بودن چرخش توکن، Refresh Token جدید.
            در صورت شکست مقدار False و یک دیکشنری خطا با کلیدهای 'error' و 'message' بازگردانده می‌شود.    

        تازه‌سازی توکن دسترسی (Access Token) با استفاده از یک Refresh Token.
        
        این تابع یک Refresh Token را اعتبارسنجی می‌کند، اطمینان می‌دهد که توکن در فهرست سیاه نیست و کاربر مربوطه وجود دارد و فعال است، سپس یک Access Token جدید می‌سازد. بسته به تنظیمات SIMPLE_JWT می‌تواند عمل «چرخش» (rotation) را انجام دهد: توکن رفرش قدیمی را (در صورت فعال بودن BLACKLIST_AFTER_ROTATION) در لیست سیاه قرار می‌دهد و یک Refresh Token جدید برای کاربر صادر می‌کند. در صورت موفقیت، مقدار بازگشتی شامل توکن‌های مربوطه و زمان انقضای Access به ثانیه است؛ در غیر این‌صورت یک دیکشنری خطا با کد و پیام مناسب بازگردانده می‌شود.
        
        پارامترها:
            refresh_token (str): رشته‌ی Refresh Token که باید برای صدور Access جدید استفاده شود.
        
        مقدار بازگشتی:
            Tuple[bool, Dict[str, any]]: 
                - در صورت موفقیت: (True, payload) که payload شامل کلیدهای زیر است:
                    - 'access' (str): Access Token جدید
                    - 'refresh' (str, اختیاری): Refresh Token جدید (در صورت فعال بودن چرخش)
                    - 'token_type' (str): معمولاً 'Bearer'
                    - 'expires_in' (int): زمان باقی‌مانده‌ی اعتبار Access به ثانیه
                - در صورت خطا: (False, error_dict) که error_dict حداقل شامل:
                    - 'error' (str): کد خطا مانند 'token_blacklisted', 'user_inactive', 'user_not_found', 'invalid_token', 'internal_error'
                    - 'message' (str): توضیح کوتاه به فارسی
        
        حالات خطا مهم:
            - اگر توکن در لیست سیاه باشد، خطای 'token_blacklisted' بازگردانده می‌شود.
            - اگر کاربر مرتبط وجود نداشته یا غیرفعال باشد، خطاهای 'user_not_found' یا 'user_inactive' بازگردانده می‌شوند.
            - در صورت نامعتبر بودن توکن، 'invalid_token' بازگردانده می‌شود.
            - خطاهای داخلی سیستم با 'internal_error' گزارش می‌شوند.

        """
        try:
            # بررسی blacklist
            if TokenBlacklist.is_blacklisted(refresh_token):
                return False, {
                    'error': 'token_blacklisted',
                    'message': 'این توکن مسدود شده است'
                }
            
            # تولید توکن جدید
            refresh = RefreshToken(refresh_token)
            
            # بررسی اعتبار کاربر
            user_id = refresh.payload.get('user_id')
            try:
                user = User.objects.get(id=user_id)
                if not user.is_active:
                    return False, {
                        'error': 'user_inactive',
                        'message': 'حساب کاربری غیرفعال است'
                    }
            except User.DoesNotExist:
                return False, {
                    'error': 'user_not_found',
                    'message': 'کاربر یافت نشد'
                }
            
            # تولید access token جدید
            new_access = refresh.access_token
            
            # Rotate refresh token if configured
            if getattr(settings, 'SIMPLE_JWT', {}).get('ROTATE_REFRESH_TOKENS', True):
                # مسدود کردن refresh token قدیمی
                if getattr(settings, 'SIMPLE_JWT', {}).get('BLACKLIST_AFTER_ROTATION', True):
                    AuthService.blacklist_token(
                        refresh_token,
                        'refresh',
                        user,
                        'Token rotation'
                    )
                
                # تولید refresh token جدید
                new_refresh = RefreshToken.for_user(user)
                new_refresh['user_type'] = user.user_type
                new_refresh['phone_number'] = user.username
                
                return True, {
                    'access': str(new_access),
                    'refresh': str(new_refresh),
                    'token_type': 'Bearer',
                    'expires_in': int(
                        getattr(settings, 'SIMPLE_JWT', {}).get(
                            'ACCESS_TOKEN_LIFETIME',
                            timedelta(minutes=5)
                        ).total_seconds()
                    )
                }
            else:
                return True, {
                    'access': str(new_access),
                    'token_type': 'Bearer',
                    'expires_in': int(
                        getattr(settings, 'SIMPLE_JWT', {}).get(
                            'ACCESS_TOKEN_LIFETIME',
                            timedelta(minutes=5)
                        ).total_seconds()
                    )
                }
                
        except TokenError as e:
            logger.error(f"Token refresh error: {e}")
            return False, {
                'error': 'invalid_token',
                'message': 'توکن نامعتبر است'
            }
        except Exception as e:
            logger.error(f"Unexpected error in refresh_access_token: {e}")
            return False, {
                'error': 'internal_error',
                'message': 'خطای سیستمی'
            }
    
    @staticmethod
    def blacklist_token(
        token: str,
        token_type: str,
        user: User,
        reason: str = ''
    ) -> bool:
        """

        توکن مشخص را در جدول سیاه‌فهرست ذخیره می‌کند تا از استفادهٔ مجدد آن جلوگیری شود.
        
        این تابع با محاسبهٔ زمان انقضای توکن بر پایهٔ تنظیمات SIMPLE_JWT (یا مقدار پیش‌فرض: دسترسی ۵ دقیقه، رفرش ۷ روز)، یک ردیف TokenBlacklist ایجاد می‌کند که شامل مقدار توکن، نوع آن ('access' یا 'refresh')، کاربر مرتبط، دلیل و زمان انقضا است. عملیات موفق منجر به ثبت لاگ اطلاعاتی و بازگشت True می‌شود؛ در صورت بروز هرگونه خطا مقدار False بازگردانده می‌شود.
        
        Parameters:
            token (str): مقدار توکن که باید مسدود شود.
            token_type (str): نوع توکن — انتظار می‌رود 'access' یا 'refresh' باشد؛ بر اساس این مقدار زمان انقضا محاسبه می‌شود.
            user (User): نمونهٔ کاربر مرتبط با توکن.
            reason (str, optional): توضیح یا دلیل مسدودسازی؛ در لاگ و رکورد ذخیره می‌شود.
        
        Returns:
            bool: True اگر رکورد با موفقیت ایجاد شود، در غیر این صورت False (خطاهای داخلی را مصرف می‌کند و استثنا پرتاب نمی‌کند).
        
        Side effects:
            - ایجاد یک رکورد در مدل TokenBlacklist.
            - نوشتن لاگ اطلاعاتی یا اروری بسته به نتیجه.
        """
        try:
            # محاسبه زمان انقضا
            if token_type == 'access':
                expires_at = timezone.now() + getattr(
                    settings, 'SIMPLE_JWT', {}
                ).get('ACCESS_TOKEN_LIFETIME', timedelta(minutes=5))
            else:  # refresh
                expires_at = timezone.now() + getattr(
                    settings, 'SIMPLE_JWT', {}
                ).get('REFRESH_TOKEN_LIFETIME', timedelta(days=7))
            
            TokenBlacklist.objects.create(
                token=token,
                token_type=token_type,
                user=user,
                reason=reason,
                expires_at=expires_at
            )
            
            logger.info(
                f"Token blacklisted: type={token_type}, "
                f"user={user.username}, reason={reason}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error blacklisting token: {e}")
            return False
    
    @staticmethod
    def logout(user: User, refresh_token: str = None, logout_all: bool = False) -> bool:
        """

        خروج کاربر از جلسه(ها) و لغو توکن‌های مربوطه.
        
        اگر logout_all=True باشد، همه رکوردهای فعال OTPVerification کاربر غیرفعال شده و توکن‌های access و refresh مربوطه به فهرست سیاه افزوده می‌شوند.
        اگر refresh_token مشخص شده باشد و logout_all=False، همان توکن refresh خاص به فهرست سیاه اضافه شده و رکورد OTPVerification متناظر (در صورت فعال بودن) غیرفعال می‌شود.
        اگر هیچ‌کدام از پارامترها ارائه نشود، عملکرد بدون انجام تغییر خاصی موفقیت‌آمیز (noop) بازمی‌گردد.
        عملیات درونی خطاها را می‌گیرد و در صورت بروز هرگونه استثنا False بازمی‌گرداند.
        
        Parameters:
            user (User): کاربری که باید خارج شود.
            refresh_token (str, optional): در صورت ارائه، تنها همین توکن refresh مسدود و جلسه مرتبط غیرفعال می‌شود.
            logout_all (bool, optional): اگر True، همه جلسات فعال کاربر خاتمه داده و توکن‌ها سیاه‌فهرست می‌شوند.
        
        Returns:
            bool: True در صورت اجرای موفق (شامل حالت noop)، False در صورت بروز خطا.
        """
        try:
            if logout_all:
                # مسدود کردن همه توکن‌های فعال کاربر
                active_verifications = OTPVerification.objects.filter(
                    user=user,
                    is_active=True
                )
                
                for verification in active_verifications:
                    # مسدود کردن access token
                    AuthService.blacklist_token(
                        verification.access_token,
                        'access',
                        user,
                        'Logout all devices'
                    )
                    
                    # مسدود کردن refresh token
                    AuthService.blacklist_token(
                        verification.refresh_token,
                        'refresh',
                        user,
                        'Logout all devices'
                    )
                    
                    # غیرفعال کردن verification
                    verification.deactivate()
                
                logger.info(f"User {user.username} logged out from all devices")
                
            elif refresh_token:
                # مسدود کردن توکن خاص
                AuthService.blacklist_token(
                    refresh_token,
                    'refresh',
                    user,
                    'User logout'
                )
                
                # غیرفعال کردن verification مربوطه
                OTPVerification.objects.filter(
                    user=user,
                    refresh_token=refresh_token,
                    is_active=True
                ).update(is_active=False)
                
                logger.info(f"User {user.username} logged out from single device")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in logout: {e}")
            return False
    
    @staticmethod
    def get_active_sessions(user: User) -> list:
        """

        بازگرداندن فهرست نشست‌های فعال کاربر به صورت ساخت‌یافته.
        
        این تابع تمام رکوردهای OTPVerification مرتبط با کاربر که هنوز فعال هستند را واکشی کرده و برای هر نشست یک دیکشنری حاوی شناسه نشست، شناسه و نام دستگاه، زمان تأیید (verified_at) به شکل ISO، زمان آخرین فعالیت (فعلاً برابر با verified_at) و اطلاعات شبکه/عامل کاربر (ip_address و user_agent) تولید می‌کند. خروجی مناسب برای نمایش لیست جلسات در API یا رابط مدیریت نشست‌ها است.
        
        Parameters:
            user (User): نمونه کاربر که نشست‌های فعال آن باید بازیابی شود.
        
        Returns:
            list: لیستی از دیکشنری‌ها که هر کدام نمایانگر یک نشست فعال با کلیدهای
                - id (str): UUID نشست به صورت رشته
                - device_id (str): شناسه دستگاه
                - device_name (str): نام دستگاه یا توضیح
                - verified_at (str): زمان تأیید نشست به صورت ISO 8601
                - last_activity (str): زمان آخرین فعالیت (فعلاً برابر با verified_at)
                - ip_address (str): آدرس آی‌پی ارسال‌کننده درخواست OTP
                - user_agent (str): User-Agent ارسال‌شده با درخواست OTP
        
        Notes:
            - تابع فقط نشست‌هایی که فیلد is_active=True دارند را برمی‌گرداند.
            - مقدار last_activity فعلاً همان verified_at بازگردانده می‌شود؛ برای ثبت دقیق‌تر باید مکانیزم جداگانه‌ای برای ردیابی آخرین فعالیت پیاده‌سازی شود.
        """
        sessions = []
        
        verifications = OTPVerification.objects.filter(
            user=user,
            is_active=True
        ).order_by('-verified_at')
        
        for verification in verifications:
            sessions.append({
                'id': str(verification.id),
                'device_id': verification.device_id,
                'device_name': verification.device_name,
                'verified_at': verification.verified_at.isoformat(),
                'last_activity': verification.verified_at.isoformat(),  # TODO: track last activity
                'ip_address': verification.otp_request.ip_address,
                'user_agent': verification.otp_request.user_agent
            })
        
        return sessions
    
    @staticmethod
    def revoke_session(user: User, session_id: str) -> bool:
        """

        خلاصه: یک نشست فعال کاربر را با شناسه داده‌شده لغو می‌کند.
        
        توضیح: اگر نشست (OTPVerification) فعال متناظر با session_id و کاربر وجود داشته باشد، توکن‌های دسترسی و تازه‌سازی مربوطه را در فهرست سیاه قرار می‌دهد و رکورد verification را غیرفعال می‌کند. این عملیات باعث خاتمه فوری نشست مذکور می‌شود و از استفاده مجدد توکن‌های موجود جلوگیری می‌کند.
        
        پارامترها:
            user: نمونهٔ User صاحب نشست.
            session_id: شناسهٔ نشست (UUID یا رشته) که باید لغو شود.
        
        بازگشتی:
            bool: True در صورت موفقیت (نشست وجود داشته و لغو شده)، False در صورت نبودن نشست یا بروز خطای داخلی.
        
        تأثیرات جانبی:
            - ایجاد ورودی(های) TokenBlacklist برای access و refresh token مربوط به نشست.
            - فراخوانی متد deactivate روی شیٔ OTPVerification مربوطه.
        
        نکات خطا:
            - اگر نشست یافت نشود، تابع False برمی‌گرداند بدون اینکه استثنا بالا بیاید.
            - در صورت خطاهای غیرمنتظره، تابع False برمی‌گرداند.

        """
        try:
            verification = OTPVerification.objects.get(
                id=session_id,
                user=user,
                is_active=True
            )
            
            # مسدود کردن توکن‌ها
            AuthService.blacklist_token(
                verification.access_token,
                'access',
                user,
                'Session revoked'
            )
            
            AuthService.blacklist_token(
                verification.refresh_token,
                'refresh',
                user,
                'Session revoked'
            )
            
            # غیرفعال کردن verification
            verification.deactivate()
            
            logger.info(
                f"Session revoked: user={user.username}, "
                f"session={session_id}"
            )
            
            return True
            
        except OTPVerification.DoesNotExist:
            logger.warning(
                f"Session not found for revocation: "
                f"user={user.username}, session={session_id}"
            )
            return False
        except Exception as e:
            logger.error(f"Error revoking session: {e}")
            return False
    
    @staticmethod
    def cleanup_expired_blacklist():
        """

        پاکسازی رکوردهای منقضی‌شده از جدول TokenBlacklist و بازگرداندن تعداد حذف‌شده‌ها.
        
        این تابع تمامی رکوردهای لیست سیاه توکن را که فیلد `expires_at` آنها قبل از زمان فعلی است حذف می‌کند و تعداد رکوردهای حذف‌شده را برمی‌گرداند.

        یکپارچه‌سازی و حذف ورودی‌های منقضی‌شده از جدول TokenBlacklist.
        
        این تابع رکوردهای TokenBlacklist را که فیلد `expires_at` آنها کمتر از زمان جاری (timezone.now()) است حذف می‌کند و تعداد رکوردهای حذف‌شده را برمی‌گرداند. حذف به‌صورت دائمی در دیتابیس انجام می‌شود؛ در صورت حذف شدن هر رکورد، یک پیام لاگ اطلاع‌رسانی ثبت می‌شود.

        
        Returns:
            int: تعداد رکوردهای حذف‌شده از TokenBlacklist.
        """
        deleted_count = TokenBlacklist.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()[0]
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired blacklisted tokens")
        
        return deleted_count