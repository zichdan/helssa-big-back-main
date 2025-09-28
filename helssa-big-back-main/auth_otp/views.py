"""
ویوهای سیستم احراز هویت OTP
OTP Authentication System Views
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
import logging

from .serializers import (
    OTPRequestSerializer,
    OTPVerifySerializer,
    OTPLoginResponseSerializer,
    RefreshTokenSerializer,
    TokenSerializer,
    OTPStatusSerializer,
    RateLimitStatusSerializer,
    RegisterSerializer,
    LogoutSerializer,
    UserInfoSerializer
)
from .services import OTPService, AuthService
from .models import OTPRequest, OTPRateLimit

logger = logging.getLogger(__name__)


# ====================================
# OTP Send Endpoint
# ====================================

@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp(request):
    """

    ارسال کد یک‌بارمصرف (OTP) به شماره موبایل برای اهداف مختلف احراز هویت.
    
    جزئیات:
    - ورودی‌های مورد انتظار در بدنه درخواست: `phone_number` (فرمت شماره موبایل)، `purpose` (یکی از 'login', 'register', 'reset_password', 'verify_phone') و اختیاری `sent_via` ('sms' یا 'call').
    - عملکرد: ورودی را اعتبارسنجی می‌کند، آدرس IP و User-Agent درخواست را استخراج می‌کند و درخواست ارسال OTP را به سرویس مربوطه می‌فرستد.
    - پاسخ‌ها:
      - 201: OTP با موفقیت ارسال شده و داده‌های مرتبط در فیلد `data` بازگردانده می‌شود.
      - 400: ورودی نامعتبر یا خطای تجاری دیگر — در بدنه پاسخ فیلدهای `error`, `message` و `details` توضیح داده می‌شوند.
      - 429: در صورت عبور از محدودیت نرخ (`error` = 'rate_limit_exceeded').
      - 500: خطای داخلی سرور (پیغام کلی به مشتری بازگردانده می‌شود).
    - اثر جانبی ضروری: ایجاد و ثبت درخواست ارسال OTP (از طریق سرویس OTP) و ثبت خطا در لاگر در صورت بروز استثنا.
    
    پارامترهای بدنه (خلاصه):
    - phone_number: شماره موبایل دریافت‌کننده (الزامی).
    - purpose: هدف استفاده از OTP؛ یکی از مقادیر مجاز: 'login', 'register', 'reset_password', 'verify_phone' (الزامی).
    - sent_via: روش ارسال؛ پیش‌فرض 'sms'، مقدار مجاز شامل 'sms' و 'call' (اختیاری).
    
    محتوای پاسخ موفق:
    {
        "success": True,
        "data": {...}  # اطلاعات مربوط به درخواست OTP (مثلاً شناسه درخواست، زمان انقضا و ...)
    }
    
    محتوای پاسخ خطا:
    {
        "success": False,
        "error": "<error_code>",
        "message": "<human_readable_message>",
        "details": {...}  # در صورت وجود، جزئیات خطا یا خطاهای اعتبارسنجی
    }

    """
    try:
        # اعتبارسنجی ورودی
        serializer = OTPRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'validation_error',
                    'message': 'داده‌های ورودی نامعتبر',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # دریافت IP و User Agent
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # ارسال OTP
        otp_service = OTPService()
        success, result = otp_service.send_otp(
            phone_number=serializer.validated_data['phone_number'],
            purpose=serializer.validated_data['purpose'],
            sent_via=serializer.validated_data.get('sent_via', 'sms'),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if success:
            return Response(
                {
                    'success': True,
                    'data': result
                },
                status=status.HTTP_201_CREATED
            )
        else:
            # تعیین کد وضعیت بر اساس نوع خطا
            if result.get('error') == 'rate_limit_exceeded':
                status_code = status.HTTP_429_TOO_MANY_REQUESTS
            else:
                status_code = status.HTTP_400_BAD_REQUEST
            
            return Response(
                {
                    'success': False,
                    'error': result.get('error'),
                    'message': result.get('message'),
                    'details': result
                },
                status=status_code
            )
            
    except Exception as e:
        logger.error(f"Error in send_otp: {str(e)}")
        return Response(
            {
                'success': False,
                'error': 'internal_error',
                'message': 'خطای سیستمی در ارسال کد تأیید'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ====================================
# OTP Verify Endpoint
# ====================================

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """

    تأیید کد OTP و ورود یا ثبت‌نام کاربر با تولید توکن و ثبت جلسه (verification record).
    
    این تابع ورودی درخواست را با OTPVerifySerializer اعتبارسنجی می‌کند، کد OTP را از طریق OTPService تأیید می‌کند و در صورت موفقیت:
    - کاربر را با AuthService.create_user_if_not_exists ایجاد یا بازیابی می‌کند (نوع پیش‌فرض 'patient').
    - توکن‌های دسترسی و رفرش را با AuthService.generate_tokens تولید می‌کند.
    - رکورد تأیید (verification record) را با AuthService.create_verification_record شامل otp_request، کاربر، توکن‌ها و اطلاعات دستگاه/جلسه ایجاد می‌کند.
    - در پاسخ، توکن‌ها، اطلاعات کاربر (UserInfoSerializer)، پرچم is_new_user و پیام مناسب بازگردانده می‌شوند.
    
    رفتار بازگشتی (HTTP):
    - 200 OK: تأیید موفق؛ بدنه شامل { "success": True, "data": { "tokens", "user", "is_new_user", "message" } }.
    - 400 Bad Request: خطای اعتبارسنجی ورودی یا عدم موفقیت در تأیید OTP؛ بدنه شامل اطلاعات خطا (error, message, details).
    - 500 Internal Server Error: خطای سیستمی ثبت‌شده در لاگ؛ بدنه شامل { "success": False, "error": "internal_error", "message": "خطای سیستمی در تأیید کد" }.
    
    نکات پیاده‌سازی:
    - پارامترهای device_id و device_name از داده‌های اعتبارسنجی‌شده استخراج و session_key از request.session خوانده می‌شود (در صورت وجود).
    - خطاها لاگ می‌شوند و هیچ استثنایی به فراخواننده پرتاب نمی‌شود (همه با پاسخ 500 مدیریت می‌شوند).
 خطای داخلی سرور — بدنه شامل {'success': False, 'error': 'internal_error', 'message': 'خطای سیستمی در تأیید کد'}.

    """
    try:
        # اعتبارسنجی ورودی
        serializer = OTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'validation_error',
                    'message': 'داده‌های ورودی نامعتبر',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # تأیید OTP
        otp_service = OTPService()
        success, result = otp_service.verify_otp(
            phone_number=serializer.validated_data['phone_number'],
            otp_code=serializer.validated_data['otp_code'],
            purpose=serializer.validated_data['purpose']
        )
        
        if not success:
            return Response(
                {
                    'success': False,
                    'error': result.get('error'),
                    'message': result.get('message'),
                    'details': result
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # OTP تأیید شد
        otp_request = result['otp_request']
        
        # ایجاد یا دریافت کاربر
        user, is_new = AuthService.create_user_if_not_exists(
            phone_number=otp_request.phone_number,
            user_type='patient'  # نوع پیش‌فرض
        )
        
        # تولید توکن‌ها
        tokens = AuthService.generate_tokens(user)
        
        # ایجاد رکورد verification
        verification = AuthService.create_verification_record(
            otp_request=otp_request,
            user=user,
            tokens=tokens,
            device_id=serializer.validated_data.get('device_id'),
            device_name=serializer.validated_data.get('device_name'),
            session_key=request.session.session_key if hasattr(request, 'session') else None
        )
        
        # آماده‌سازی پاسخ
        response_data = {
            'tokens': tokens,
            'user': UserInfoSerializer(user).data,
            'is_new_user': is_new,
            'message': 'ورود موفقیت‌آمیز' if not is_new else 'ثبت‌نام و ورود موفقیت‌آمیز'
        }
        
        return Response(
            {
                'success': True,
                'data': response_data
            },
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error in verify_otp: {str(e)}")
        return Response(
            {
                'success': False,
                'error': 'internal_error',
                'message': 'خطای سیستمی در تأیید کد'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ====================================
# Token Refresh Endpoint
# ====================================

@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """

    تازه‌سازی Access Token با استفاده از Refresh Token.
    
    دسکریپشن:
        این endpoint یک Refresh Token معتبر می‌پذیرد و در صورت اعتبار موفق، یک Access Token جدید (و در صورت نیاز داده‌های مرتبط با توکن) برمی‌گرداند.
        - ورودی: بدنه درخواست باید شامل فیلد `refresh` (رشته) باشد.
        - منطق: از سرویس AuthService.refresh_access_token برای انجام عملیات تازه‌سازی استفاده می‌شود.
        - خطاها:
            - اگر ورودی نامعتبر باشد پاسخ 400 با کلیدهای `error: "validation_error"` و جزییات اعتبارسنجی بازگردانده می‌شود.
            - اگر Refresh Token نامعتبر یا منقضی باشد پاسخ 401 با `error` و `message` از AuthService برمی‌گردد.
            - در صورت بروز استثناهای داخلی، پاسخ 500 با `error: "internal_error"` و پیام خطای سیستمی بازگردانده می‌شود.
    
    پاسخ‌ها (خلاصه):
        200: { "success": True, "data": <توکن‌ها یا داده‌های مرتبط> }
        400: { "error": "validation_error", "message": "...", "details": <خطاهای اعتبارسنجی> }
        401: { "success": False, "error": <کد خطای سرویس>, "message": <پیام سرویس> }
        500: { "success": False, "error": "internal_error", "message": "خطای سیستمی در تازه‌سازی توکن" }

    """
    try:
        # اعتبارسنجی ورودی
        serializer = RefreshTokenSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'validation_error',
                    'message': 'داده‌های ورودی نامعتبر',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # تازه‌سازی توکن
        success, result = AuthService.refresh_access_token(
            refresh_token=serializer.validated_data['refresh']
        )
        
        if success:
            return Response(
                {
                    'success': True,
                    'data': result
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    'success': False,
                    'error': result.get('error'),
                    'message': result.get('message')
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
            
    except Exception as e:
        logger.error(f"Error in refresh_token: {str(e)}")
        return Response(
            {
                'success': False,
                'error': 'internal_error',
                'message': 'خطای سیستمی در تازه‌سازی توکن'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ====================================
# Logout Endpoint
# ====================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """

    خروج کاربر از جلسه فعلی یا از همه دستگاه‌ها با استفاده از توکنِ رفرش.
    
    این تابع درخواست POST را می‌پذیرد، ورودی را از طریق LogoutSerializer اعتبارسنجی می‌کند و سپس از AuthService برای خروج استفاده می‌کند. در صورت موفقیت، توکن رفرش داده‌شده (و در صورت درخواست، همه جلسات کاربر) نامعتبر می‌شود.
    
    ورودی (در بدنه درخواست):
        - refresh: (str) توکن رفرش که باید باطل شود.
        - logout_all_devices: (bool، اختیاری) اگر True باشد، تمامی جلسات/دستگاه‌های کاربر نیز خاتمه داده می‌شوند.
    
    رفتار بازگشتی:
        - 200: خروج موفق
          ساختار پاسخ: {"success": True, "message": "<متن پیام متناسب با نوع خروج>"}
        - 400: داده‌های ورودی نامعتبر یا شکست در عملیات خروج
          ساختار پاسخ در اعتبارسنجی: {"error": "validation_error", "message": "داده‌های ورودی نامعتبر", "details": {...}}
          ساختار پاسخ در شکست خروج: {"success": False, "error": "logout_failed", "message": "خطا در خروج از سیستم"}
        - 500: خطای داخلی سرور (استثناها ثبت و یک پیام عمومی بازگردانده می‌شود)
          ساختار پاسخ: {"success": False, "error": "internal_error", "message": "خطای سیستمی در خروج"}
    
    نیازمندی‌ها و فرض‌ها:
        - کاربر باید احراز هویت شده باشد (request.user موجود و معتبر).
        - منطق واقعی باطل‌سازیِ توکن و مدیریت جلسات در AuthService.logout قرار دارد.
    
    تاثیرات جانبی:
        - باطل‌شدن توکنِ رفرش و در صورت درخواست، حذف/غیرفعال‌سازی جلسات دیگر کاربر در سیستم.

    """
    try:
        # اعتبارسنجی ورودی
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'validation_error',
                    'message': 'داده‌های ورودی نامعتبر',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # خروج
        success = AuthService.logout(
            user=request.user,
            refresh_token=serializer.validated_data['refresh'],
            logout_all=serializer.validated_data.get('logout_all_devices', False)
        )
        
        if success:
            message = 'خروج موفقیت‌آمیز'
            if serializer.validated_data.get('logout_all_devices'):
                message = 'خروج از همه دستگاه‌ها موفقیت‌آمیز'
            
            return Response(
                {
                    'success': True,
                    'message': message
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    'success': False,
                    'error': 'logout_failed',
                    'message': 'خطا در خروج از سیستم'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Error in logout: {str(e)}")
        return Response(
            {
                'success': False,
                'error': 'internal_error',
                'message': 'خطای سیستمی در خروج'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )