"""
ویوهای تکمیلی سیستم احراز هویت OTP
Extended OTP Authentication Views
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
import logging

from .serializers import (
    OTPStatusSerializer,
    RateLimitStatusSerializer,
    RegisterSerializer,
    UserInfoSerializer
)
from .services import OTPService, AuthService
from .models import OTPRequest, OTPRateLimit
from .services.kavenegar_service import KavenegarService

logger = logging.getLogger(__name__)


# ====================================
# OTP Status Endpoint
# ====================================

@api_view(['GET'])
@permission_classes([AllowAny])
def otp_status(request, otp_id):
    """

    دریافت وضعیت یک درخواست OTP بر اساس شناسه.
    
    جزییات:
    - از مدل OTPRequest نمونه‌ای با id برابر otp_id را می‌گیرد. اگر نمونه وجود داشته باشد آن را با OTPStatusSerializer سریالایز کرده و در پاسخ برمی‌گرداند. در غیر این صورت پاسخ 404 با کد خطای `not_found` بازگردانده می‌شود. در صورت بروز خطای داخلی سرور پاسخ 500 با کد خطای `internal_error` برگردانده می‌شود.
    
    پارامترها:
        otp_id (int | str): شناسه (PK) درخواست OTP که باید وضعیت آن بازیابی شود.
    
    مقادیر بازگشتی:
    - HTTP 200: بدنه شامل {'success': True, 'data': ...} حاوی داده‌های سریالایز شده OTP.
    - HTTP 404: بدنه شامل {'error': 'not_found', 'message': 'OTP یافت نشد'} وقتی آیتم پیدا نشود.
    - HTTP 500: بدنه شامل {'success': False, 'error': 'internal_error', 'message': 'خطای سیستمی'} در صورت وقوع خطای غیرمنتظره.

    """
    try:
        otp_request = OTPRequest.objects.filter(id=otp_id).first()
        
        if not otp_request:
            return Response(
                {
                    'error': 'not_found',
                    'message': 'OTP یافت نشد'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = OTPStatusSerializer(otp_request)
        
        return Response(
            {
                'success': True,
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error in otp_status: {str(e)}")
        return Response(
            {
                'success': False,
                'error': 'internal_error',
                'message': 'خطای سیستمی'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ====================================
# Rate Limit Status Endpoint
# ====================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rate_limit_status(request, phone_number):
    """

    دریافت و برگرداندن وضعیت محدودیت ارسال OTP برای یک شماره موبایل.
    
    این نما (view) شماره موبایل را با KavenegarService نرمال‌سازی می‌کند، رکورد مربوط به OTPRateLimit را دریافت یا ایجاد می‌کند، پنجره‌های شمارش محدودیت را به‌روز می‌کند و وضعیت فعلی ارسال OTP را محاسبه می‌نماید. به صورت ضمنی ممکن است یک رکورد OTPRateLimit جدید در پایگاه داده ایجاد شود و مقادیر شمارش (minute_count، hour_count) و وضعیت بلاک (is_blocked، blocked_until) بسته به منطق مدل به‌روز شوند.
    
    Parameters:
        phone_number (str): شماره موبایل خام که پیش از محاسبه وضعیت با KavenegarService فرمت و نرمال‌سازی می‌شود.
    
    Returns:
        Response: پاسخ HTTP با ساختار JSON که در حالت موفق شامل {'success': True, 'data': {...}} است. کلیدهای مهم در دادهٔ سریال‌شده:
            - can_send (bool): آیا در حال حاضر امکان ارسال OTP وجود دارد.
            - message (str): پیام توضیحی در مورد وضعیت ارسال (مثلاً دلیل مسدودی).
            - minute_limit (int): محدودیت تعداد OTP در درون یک دقیقه (مقدار پیکربندی‌شده، مثال: 1).
            - minute_remaining (int): تعداد مجاز باقیمانده در پنجره دقیقه‌ای.
            - hour_limit (int): محدودیت تعداد OTP در یک ساعت (مثال: 5).
            - hour_remaining (int): تعداد مجاز باقیمانده در پنجره ساعتی.
            - is_blocked (bool): آیا شماره در حال حاضر مسدود است.
            - blocked_until (datetime|None): زمان پایان مسدودی در صورت وجود؛ در غیر این صورت None.
    
    توضیحات تکمیلی:
        - این نما معمولاً تحت مجوز احراز هویت اجرا می‌شود (IsAuthenticated).
        - هرگونه خطای سیستمی به صورت پاسخ 500 با شناسه خطا بازگردانده می‌شود؛ جزئیات داخلی خطا لاگ می‌شود.

    """
    try:
        # بررسی فرمت شماره
        formatted_phone = KavenegarService.format_phone_number(phone_number)
        
        # دریافت rate limit
        rate_limit, created = OTPRateLimit.objects.get_or_create(
            phone_number=formatted_phone
        )
        
        # بررسی وضعیت
        rate_limit.check_and_update_windows()
        can_send, message = rate_limit.can_send_otp()
        
        data = {
            'can_send': can_send,
            'message': message,
            'minute_limit': 1,
            'minute_remaining': max(0, 1 - rate_limit.minute_count),
            'hour_limit': 5,
            'hour_remaining': max(0, 5 - rate_limit.hour_count),
            'is_blocked': rate_limit.is_blocked,
            'blocked_until': rate_limit.blocked_until
        }
        
        serializer = RateLimitStatusSerializer(data)
        
        return Response(
            {
                'success': True,
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error in rate_limit_status: {str(e)}")
        return Response(
            {
                'success': False,
                'error': 'internal_error',
                'message': 'خطای سیستمی'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ====================================
# User Sessions Endpoint
# ====================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_sessions(request):
    """

    بازگرداندن فهرست نشست‌های فعال کاربر احرازشده.
    
    این نما (view) نشست‌های فعال مرتبط با کاربر حاضر (request.user) را از AuthService می‌گیرد و آن‌ها را همراه با تعدادشان در قالب یک پاسخ JSON بازمی‌گرداند. در صورت بروز خطای غیرمنتظره، پاسخ خطای سیستمی با کد 500 برگردانده می‌شود.
    
    پارامترها:
        request: شیء درخواست Django REST Framework که باید کاربر را در request.user داشته باشد (نمای مورد انتظار با مجوز IsAuthenticated استفاده شود).
    
    مقدار بازگشتی:
        Response حاوی ساختار JSON:
          - موفقیت‌آمیز (HTTP 200):
              {
                "success": True,
                "data": {
                  "sessions": <لیست نشست‌ها>,
                  "count": <تعداد نشست‌ها>
                }
              }
          - خطای سرور (HTTP 500):
              {
                "success": False,
                "error": "internal_error",
                "message": "خطای سیستمی"
              }

    """
    try:
        sessions = AuthService.get_active_sessions(request.user)
        
        return Response(
            {
                'success': True,
                'data': {
                    'sessions': sessions,
                    'count': len(sessions)
                }
            },
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error in user_sessions: {str(e)}")
        return Response(
            {
                'success': False,
                'error': 'internal_error',
                'message': 'خطای سیستمی'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ====================================
# Revoke Session Endpoint
# ====================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_session(request, session_id):
    """

    درخواست لغو یک نشست کاربر مشخص را پردازش می‌کند.
    
    این تابع با استفاده از AuthService تلاش می‌کند نشست مشخص‌شده توسط `session_id` را برای کاربر جاری (`request.user`) لغو (revoked) کند. اگر عملیات لغو موفق باشد، پاسخ موفقیت‌آمیز (HTTP 200) برمی‌گرداند؛ اگر نشست وجود نداشته یا قبلاً لغو شده باشد، پاسخ خطای یافت‌نشدن (HTTP 404) برمی‌گرداند. در صورت بروز هرگونه خطای داخلی غیرمنتظره، پاسخ خطای سرور (HTTP 500) بازگردانده می‌شود.
    
    پارامترها:
        session_id (str): شناسه یکتای نشست که باید لغو شود — تنها پارامتری که معنا و نقش آن خارج از نامش نیاز به توضیح دارد.
    
    خروجی‌ها:
        - HTTP 200: {'success': True, 'message': 'نشست با موفقیت لغو شد'} — لغو با موفقیت انجام شد.
        - HTTP 404: {'success': False, 'error': 'not_found', 'message': 'نشست یافت نشد یا قبلاً لغو شده'} — نشست موردنظر وجود ندارد یا قبلاً لغو شده است.
        - HTTP 500: {'success': False, 'error': 'internal_error', 'message': 'خطای سیستمی'} — خطای داخلی سرویس یا استثنای غیرمنتظره.
    
    نکات عملیاتی:
        - تابع تصمیم‌گیری و اجرای لغو را به AuthService تفویض می‌کند؛ هرگونه منطق بررسی مجوزها یا وضعیت نشست توسط آن سرویس انجام می‌شود.
        - این تابع خود کاربر را از درخواست می‌گیرد (request.user) و بنابراین باید توسط یک نماینده‌ی احراز هویت‌شده فراخوانی شود تا session_id متعلق به همان کاربر باشد یا AuthService بررسی‌های لازم را انجام دهد.

    """
    try:
        success = AuthService.revoke_session(request.user, session_id)
        
        if success:
            return Response(
                {
                    'success': True,
                    'message': 'نشست با موفقیت لغو شد'
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    'success': False,
                    'error': 'not_found',
                    'message': 'نشست یافت نشد یا قبلاً لغو شده'
                },
                status=status.HTTP_404_NOT_FOUND
            )
            
    except Exception as e:
        logger.error(f"Error in revoke_session: {str(e)}")
        return Response(
            {
                'success': False,
                'error': 'internal_error',
                'message': 'خطای سیستمی'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ====================================
# Register Endpoint (Optional)
# ====================================

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """

    ثبت‌نام کاربر جدید پس از تأیید موفق OTP.
    
    این تابع یک کاربر جدید ایجاد می‌کند با داده‌های ارسالی در بدنهٔ درخواست؛ قبل از فراخوانی این endpoint باید فرایند OTP برای شمارهٔ مربوطه تکمیل و تأیید شده باشد (مثلاً با یک session یا توکن موقت که نشان‌دهندهٔ تأیید OTP است). ورودی‌های مورد انتظار در request.data:
    - phone_number: شماره موبایل (الزامی، باید پیش‌تر با OTP تأیید شده باشد)
    - user_type: نوع کاربر (مثلاً "patient" یا "doctor")
    - first_name: نام
    - last_name: نام خانوادگی
    - email: ایمیل (اختیاری/بسته به اعتبارسنجی)
    
    رفتار و نتایج:
    - در صورت اعتبارسنجی موفق، کاربر جدید ساخته شده و پاسخ 201 با شیء کاربر سریالایز شده (UserInfoSerializer) و پیام موفقیت بازگردانده می‌شود.
    - در صورت خطای اعتبارسنجی ورودی، پاسخ 400 حاوی کد خطا، پیام و جزئیات خطا (serializer.errors) بازگردانده می‌شود.
    - در صورت بروز خطای داخلی یا استثنا، پاسخ 500 با پیام خطای سیستمی بازگردانده می‌شود.
    
    تأثیر جانبی:
    - ایجاد رکورد جدید کاربر در پایگاه داده.
    
    نکتهٔ مهم:
    - خود تابع مسئول تأیید OTP نیست؛ باید از مکانیسمی خارج از این تابع (session، توکن موقت یا مشابه) برای اطمینان از اینکه شمارهٔ موبایل پیش‌تر با OTP تأیید شده استفاده شود.

    """
    try:
        # این endpoint فقط برای کاربرانی که OTP تأیید کرده‌اند
        # می‌توانید از session یا token موقت برای بررسی استفاده کنید
        
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'validation_error',
                    'message': 'داده‌های ورودی نامعتبر',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ایجاد کاربر
        user = serializer.save()
        
        return Response(
            {
                'success': True,
                'data': UserInfoSerializer(user).data,
                'message': 'ثبت‌نام با موفقیت انجام شد'
            },
            status=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        logger.error(f"Error in register: {str(e)}")
        return Response(
            {
                'success': False,
                'error': 'internal_error',
                'message': 'خطای سیستمی در ثبت‌نام'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ====================================
# Resend OTP Endpoint
# ====================================

@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp(request):
    """

    ارسال مجدد کد OTP با ارجاع مستقیم به همان view اصلی ارسال OTP.
    
    این تابع درخواست را بدون تغییر به send_otp در همان ماژول ارسال می‌کند تا منطق یکسان ارسال/اعتبارسنجی OTP دوباره استفاده شود. برای درخواست باید بدنه شامل فیلدهای زیر باشد:
    - phone_number: شماره موبایل (الزامی)
    - purpose: هدف عملیات؛ نمونه‌ها: "login", "register", "reset_password", "verify_phone"
    - sent_via: کانال ارسال؛ نمونه‌ها: "sms", "call" (اختیاری بسته به تنظیمات)
    
    رفتار و نتایج مورد انتظار (بر اساس ارسال‌کننده اصلی):
    - 201: کد OTP با موفقیت ارسال شد
    - 400: خطای اعتبارسنجی ورودی
    - 429: محدودیت نرخ (rate limit) اعمال شده
    - 500: خطای داخلی سرور
    
    تاثیر جانبی: ممکن است موجب ایجاد/به‌روزرسانی رکوردهای مرتبط با درخواست‌های OTP و شمارش‌های نرخ محدودیت شود و اقدام ارسال پیامک/تماس برای کاربر را آغاز کند.

    """
    # از همان send_otp استفاده می‌کنیم
    from .views import send_otp as send_otp_view
    return send_otp_view(request)