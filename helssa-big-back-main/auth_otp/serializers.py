"""
سریالایزرهای سیستم احراز هویت OTP
OTP Authentication System Serializers
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from .models import OTPRequest, OTPVerification, TokenBlacklist

User = get_user_model()


class PhoneNumberSerializer(serializers.Serializer):
    """
    سریالایزر برای اعتبارسنجی شماره تلفن
    """
    phone_number = serializers.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                r'^09\d{9}$',
                'شماره موبایل باید با 09 شروع شود و 11 رقم باشد'
            )
        ],
        help_text='شماره موبایل به فرمت 09123456789'
    )


class OTPRequestSerializer(serializers.Serializer):
    """
    سریالایزر برای درخواست ارسال OTP
    """
    phone_number = serializers.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                r'^09\d{9}$',
                'شماره موبایل باید با 09 شروع شود و 11 رقم باشد'
            )
        ]
    )
    
    purpose = serializers.ChoiceField(
        choices=['login', 'register', 'reset_password', 'verify_phone'],
        default='login',
        help_text='هدف از ارسال OTP'
    )
    
    sent_via = serializers.ChoiceField(
        choices=['sms', 'call'],
        default='sms',
        help_text='روش ارسال OTP'
    )
    
    def validate_phone_number(self, value):
        """

        یک رشته شماره موبایل را پاک‌سازی و اعتبارسنجی می‌کند.
        
        این متد ورودی را trim کرده و فاصله‌ها و خط تیره‌ها را حذف می‌کند، سپس بررسی می‌کند که شماره پس از پاک‌سازی با '09' شروع شده و دقیقاً 11 رقم باشد. در صورت معتبر بودن، نسخهٔ پاک‌شدهٔ رشته برگردانده می‌شود.
        
        Parameters:
            value (str): رشتهٔ ورودی که نمایانگر شماره موبایل است؛ می‌تواند شامل فاصله یا خط تیره باشد.
        
        Returns:
            str: شماره موبایل پاک‌شده و به‌فرمت استاندارد (بدون فاصله یا خط تیره).
        
        Raises:
            serializers.ValidationError: اگر شماره با '09' شروع نشود یا طول آن 11 رقم نباشد.

        """
        # حذف فاصله‌ها و کاراکترهای اضافی
        value = value.strip().replace(' ', '').replace('-', '')
        
        # بررسی فرمت
        if not value.startswith('09') or len(value) != 11:
            raise serializers.ValidationError(
                'شماره موبایل باید با 09 شروع شود و 11 رقم باشد'
            )
        
        return value


class OTPVerifySerializer(serializers.Serializer):
    """
    سریالایزر برای تأیید OTP
    """
    phone_number = serializers.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                r'^09\d{9}$',
                'شماره موبایل باید با 09 شروع شود و 11 رقم باشد'
            )
        ]
    )
    
    otp_code = serializers.CharField(
        max_length=6,
        min_length=6,
        help_text='کد 6 رقمی ارسال شده'
    )
    
    purpose = serializers.ChoiceField(
        choices=['login', 'register', 'reset_password', 'verify_phone'],
        default='login'
    )
    
    # اطلاعات دستگاه (اختیاری)
    device_id = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text='شناسه یکتای دستگاه'
    )
    
    device_name = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        help_text='نام دستگاه'
    )
    
    def validate_otp_code(self, value):
        """

        اعتبارسنجی کد یک‌بارمصرف (OTP): بررسی می‌کند که مقدار وارد شده فقط شامل ارقام و دقیقاً ۶ رقم باشد.
        
        Parameters:
            value (str): رشته کد OTP ورودی.
        
        Returns:
            str: همان مقدار ورودی در صورت موفقیت‌آمیز بودن اعتبارسنجی.
        
        Raises:
            serializers.ValidationError: در صورتی که مقدار شامل کاراکتر غیرعددی باشد یا طول آن برابر با ۶ نباشد.

        اعتبارسنجی کد شش‌رقمی OTP.
        
        پارامترها:
            value (str): مقدار کد OTP که باید فقط شامل اعداد بوده و دقیقاً ۶ رقم باشد.
        
        رفتار:
            - اگر مقدار شامل کاراکتر غیرعددی باشد، ValidationError با پیام مناسب برمی‌گرداند.
            - اگر طول مقدار برابر با ۶ نباشد، ValidationError با پیام مناسب برمی‌گرداند.
        
        بازگشت:
            مقدار ورودی در صورت معتبر بودن (str).
        
        خطاها:
            serializers.ValidationError: در صورت غیرعددی بودن یا طول نامناسب کد.

        """
        # بررسی عددی بودن
        if not value.isdigit():
            raise serializers.ValidationError('کد OTP باید فقط شامل اعداد باشد')
        
        # بررسی طول
        if len(value) != 6:
            raise serializers.ValidationError('کد OTP باید 6 رقم باشد')
        
        return value


class TokenSerializer(serializers.Serializer):
    """
    سریالایزر برای توکن‌های احراز هویت
    """
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    token_type = serializers.CharField(read_only=True, default='Bearer')
    expires_in = serializers.IntegerField(
        read_only=True,
        help_text='زمان انقضا به ثانیه'
    )


class UserInfoSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای اطلاعات کاربر
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'user_type',
            'is_active',
            'created_at'
        ]
        read_only_fields = fields
    
    def get_full_name(self, obj):
        """

        بازگشت نام کامل کاربر یا نام کاربری در صورت نبود نام و نام خانوادگی.
        
        این متد نام و نام خانوادگی را با یک فاصله بین آنها ترکیب می‌کند و رشتهٔ نتیجه را پس از حذف فضاهای اضافی برمی‌گرداند. اگر هر دو فیلد first_name و last_name خالی باشند، مقدار username بازگردانده می‌شود.
        
        Parameters:
            obj: شیء کاربر (موجودیتی که دارای فیلدهای `first_name`, `last_name`, و `username` است).
        
        Returns:
            str: نام کامل (مثلاً "علی رضایی") یا در صورت نبود نام/نام‌خانوادگی، نام کاربری.
        """
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class OTPLoginResponseSerializer(serializers.Serializer):
    """
    سریالایزر برای پاسخ ورود موفق
    """
    tokens = TokenSerializer(read_only=True)
    user = UserInfoSerializer(read_only=True)
    is_new_user = serializers.BooleanField(
        read_only=True,
        help_text='آیا کاربر جدید است'
    )
    message = serializers.CharField(read_only=True)


class RefreshTokenSerializer(serializers.Serializer):
    """
    سریالایزر برای Refresh Token
    """
    refresh = serializers.CharField(
        required=True,
        help_text='Refresh token'
    )


class TokenBlacklistSerializer(serializers.Serializer):
    """
    سریالایزر برای مسدود کردن توکن
    """
    token = serializers.CharField(
        required=True,
        help_text='توکنی که باید مسدود شود'
    )
    
    token_type = serializers.ChoiceField(
        choices=['access', 'refresh'],
        default='access',
        help_text='نوع توکن'
    )
    
    reason = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text='دلیل مسدودسازی'
    )


class OTPStatusSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای وضعیت OTP
    """
    is_expired = serializers.BooleanField(read_only=True)
    can_verify = serializers.BooleanField(read_only=True)
    remaining_attempts = serializers.SerializerMethodField()
    expires_in_seconds = serializers.SerializerMethodField()
    
    class Meta:
        model = OTPRequest
        fields = [
            'id',
            'phone_number',
            'purpose',
            'is_used',
            'is_expired',
            'can_verify',
            'attempts',
            'remaining_attempts',
            'expires_at',
            'expires_in_seconds',
            'created_at'
        ]
        read_only_fields = fields
    
    def get_remaining_attempts(self, obj):
        """

        تعداد تلاش‌های معتبر باقی‌مانده برای تأیید OTP را محاسبه می‌کند.
        
        این متد مقدار صحیحی برمی‌گرداند که برابر با ماکزیممِ صفر و (۳ منهای تعداد تلاش‌های ثبت‌شده در `obj.attempts`) است. اگر `obj.attempts` برابر یا بیشتر از ۳ باشد، مقدار بازگشتی ۰ خواهد بود.
        
        Parameters:
            obj: شیئی مدل یا مشابه که دارای صفت عددی `attempts` است (تعداد تلاش‌های انجام‌شده).
        
        Returns:
            int: تعداد تلاش‌های باقی‌مانده (همیشه عددی غیرمنفی).
        """
        return max(0, 3 - obj.attempts)
    
    def get_expires_in_seconds(self, obj):
        """

        زمان باقی‌مانده تا انقضای شیء OTP را بر حسب ثانیه برمی‌گرداند.
        
        پارامترها:
            obj: نمونه‌ای از مدل OTPRequest (یا هر شیئی دارای فیلدهای `expires_at` و `is_expired`) که زمان انقضای آن محاسبه می‌شود.
        
        توضیحات:
            - اگر `obj.is_expired` مقدار True داشته باشد تابع 0 برمی‌گرداند.
            - در غیر این صورت اختلاف بین `obj.expires_at` و زمان کنونی (با استفاده از timezone ایزوله‌شدهٔ Django) به ثانیه محاسبه شده و به صورت عدد صحیح بازگردانده می‌شود.
            - مقادیر منفی به 0 محدود می‌شوند تا مقدار منفی برای زمان باقی‌مانده برنگردد.
        
        بازگشتی:
            int: تعداد ثانیه‌های باقی‌مانده تا انقضا (صفر یا عدد مثبت).
    int: تعداد ثانیه‌های باقیمانده تا انقضا (همیشه عدد غیرمنفی).
        """
        from django.utils import timezone
        if obj.is_expired:
            return 0
        
        remaining = (obj.expires_at - timezone.now()).total_seconds()
        return max(0, int(remaining))


class RateLimitStatusSerializer(serializers.Serializer):
    """
    سریالایزر برای وضعیت محدودیت نرخ
    """
    can_send = serializers.BooleanField(
        read_only=True,
        help_text='آیا امکان ارسال وجود دارد'
    )
    
    message = serializers.CharField(
        read_only=True,
        help_text='پیام وضعیت'
    )
    
    minute_limit = serializers.IntegerField(
        read_only=True,
        default=1,
        help_text='محدودیت در دقیقه'
    )
    
    minute_remaining = serializers.IntegerField(
        read_only=True,
        help_text='تعداد باقی‌مانده در دقیقه'
    )
    
    hour_limit = serializers.IntegerField(
        read_only=True,
        default=5,
        help_text='محدودیت در ساعت'
    )
    
    hour_remaining = serializers.IntegerField(
        read_only=True,
        help_text='تعداد باقی‌مانده در ساعت'
    )
    
    is_blocked = serializers.BooleanField(
        read_only=True,
        help_text='آیا شماره مسدود است'
    )
    
    blocked_until = serializers.DateTimeField(
        read_only=True,
        allow_null=True,
        help_text='زمان رفع مسدودیت'
    )


class RegisterSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای ثبت‌نام کاربر جدید
    """
    phone_number = serializers.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                r'^09\d{9}$',
                'شماره موبایل باید با 09 شروع شود و 11 رقم باشد'
            )
        ]
    )
    
    user_type = serializers.ChoiceField(
        choices=['patient', 'doctor'],
        default='patient',
        help_text='نوع کاربر'
    )
    
    first_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True
    )
    
    last_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True
    )
    
    email = serializers.EmailField(
        required=False,
        allow_blank=True
    )
    
    class Meta:
        model = User
        fields = [
            'phone_number',
            'user_type',
            'first_name',
            'last_name',
            'email'
        ]
    
    def validate_phone_number(self, value):
        """

        بررسی یکتا بودن شماره موبایل در سیستم و بازگرداندن مقدار ورودی در صورت آزاد بودن.
        
        این متد بررسی می‌کند که مقدار `value` (شماره موبایل، فرضاً در قالب رشته) قبلاً به‌عنوان username یک کاربر در پایگاه‌داده ثبت نشده باشد. اگر شماره موجود باشد، یک ValidationError پرتاب می‌شود؛ در غیر این صورت همان مقدار ورودی بازگردانده می‌شود.
        
        Parameters:
            value (str): شماره موبایل برای بررسی یکتایی (انتظار می‌رود قبل از فراخوانی، به فرمت موردنظر—مثلاً بدون فضا/خط تیره—نرمال شده باشد).
        
        Returns:
            str: همان مقدار `value` در صورت آزاد بودن.
        
        Raises:
            serializers.ValidationError: در صورت وجود رکورد کاربری با username برابر `value`.
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                'این شماره موبایل قبلاً ثبت شده است'
            )
        return value
    
    def create(self, validated_data):
        """

        ایجاد و بازگردانی یک نمونه کاربر جدید در پایگاه داده.
        
        این متد از validated_data مقدار `phone_number` را جدا می‌کند و آن را به‌عنوان `username`
        برای ایجاد حساب کاربری با فراخوانی `User.objects.create_user` استفاده می‌نماید. سایر
        فیلدهای موجود در validated_data مستقیماً به متد ایجاد کاربر پاس داده می‌شوند.
        
        Parameters:
            validated_data (dict): دیکشنری اعتبارسنجی‌شده که باید شامل `phone_number` و هر
            فیلد معتبر مدل کاربر برای create_user باشد. مقدار `phone_number` از این دیکشنری
            حذف و به‌عنوان username مصرف می‌شود.
        
        Returns:
            User: نمونهٔ ایجادشدهٔ مدل کاربر.
        """
        phone_number = validated_data.pop('phone_number')
        
        user = User.objects.create_user(
            username=phone_number,
            **validated_data
        )
        
        return user


class LogoutSerializer(serializers.Serializer):
    """
    سریالایزر برای خروج از سیستم
    """
    refresh = serializers.CharField(
        required=True,
        help_text='Refresh token برای باطل کردن'
    )
    
    logout_all_devices = serializers.BooleanField(
        default=False,
        help_text='خروج از تمام دستگاه‌ها'
    )