"""
ادمین پنل برای سیستم احراز هویت OTP
Admin Panel for OTP Authentication System
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import OTPRequest, OTPVerification, OTPRateLimit, TokenBlacklist


@admin.register(OTPRequest)
class OTPRequestAdmin(admin.ModelAdmin):
    """
    مدیریت درخواست‌های OTP
    """
    list_display = [
        'phone_number',
        'purpose',
        'otp_code_display',
        'is_used',
        'is_expired_display',
        'attempts',
        'sent_via',
        'created_at',
        'expires_at'
    ]
    
    list_filter = [
        'purpose',
        'is_used',
        'sent_via',
        'created_at'
    ]
    
    search_fields = [
        'phone_number',
        'otp_code',
        'kavenegar_message_id'
    ]
    
    readonly_fields = [
        'id',
        'otp_code',
        'expires_at',
        'created_at',
        'ip_address',
        'user_agent',
        'kavenegar_message_id',
        'metadata'
    ]
    
    ordering = ['-created_at']
    
    def otp_code_display(self, obj):
        """

        نمایش محافظت‌شدهٔ کد OTP برای نمایش در ستون‌های پنل ادمین.
        
        این متد یک رشتهٔ قابل‌نمایش برمی‌گرداند که وضعیت یا نمایشی امن از کد OTP را ارائه می‌دهد:
        - اگر otp_request.is_used باشد، یک برچسب خاکستری "استفاده شده" (به‌صورت HTML span) بازگردانده می‌شود.
        - اگر otp_request.is_expired باشد، یک برچسب قرمز "منقضی شده" (به‌صورت HTML span) بازگردانده می‌شود.
        - در غیر این صورت، نمایشی محافظت‌شده از کد بازگردانده می‌شود که فقط چهار رقم آخر کد را نشان می‌دهد و با `**` پیش‌وند می‌شود (مثلاً `**1234`) تا از نمایش کامل کد جلوگیری شود.
        
        پارامترها:
            obj: نمونه‌ای از مدل OTPRequest که دارای صفات `is_used`، `is_expired` و `otp_code` است.
        
        مقدار بازگشتی:
            str: رشتهٔ نمایشی؛ در دو حالت اول حاوی HTML امن (تولیدشده توسط `format_html`) و در حالت آخر یک متن ماسک‌شده است.

        """
        if obj.is_used:
            return format_html('<span style="color: gray;">استفاده شده</span>')
        elif obj.is_expired:
            return format_html('<span style="color: red;">منقضی شده</span>')
        else:
            # نمایش جزئی کد برای امنیت
            return f"**{obj.otp_code[-4:]}"
    otp_code_display.short_description = 'کد OTP'
    
    def is_expired_display(self, obj):
        """

        یک خط خلاصه:
            نمایش HTML وضعیت انقضأ یک رکورد به‌صورت نماد رنگی.
        
        توضیح:
            برای استفاده در لیست ادمین: این متد مقدار صریح `obj.is_expired` را بررسی می‌کند و یک قطعه HTML ایمن‌شده تولید می‌نماید که وضعیت را با یک علامت ضربدر قرمز (منقضی شده) یا یک علامت تیک سبز (فعال) نشان می‌دهد.
        
        پارامترها:
            obj: شیء مدل حاوی ویژگی بولی `is_expired` که نشان‌دهنده وضعیت انقضا است.
        
        مقدار بازگشتی:
            str: یک رشته HTML ایمن‌شده (از طریق `format_html`) که نماد وضعیت را شامل می‌شود و برای نمایش در ستون ادمین مناسب است.

        """
        if obj.is_expired:
            return format_html('<span style="color: red;">✗</span>')
        else:
            return format_html('<span style="color: green;">✓</span>')
    is_expired_display.short_description = 'منقضی شده'


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    """
    مدیریت تأییدیه‌های OTP
    """
    list_display = [
        'get_phone_number',
        'user',
        'device_name',
        'is_active',
        'verified_at'
    ]
    
    list_filter = [
        'is_active',
        'verified_at'
    ]
    
    search_fields = [
        'user__username',
        'user__first_name',
        'user__last_name',
        'device_id',
        'device_name'
    ]
    
    readonly_fields = [
        'id',
        'otp_request',
        'user',
        'verified_at',
        'access_token',
        'refresh_token',
        'device_id',
        'device_name',
        'session_key'
    ]
    
    ordering = ['-verified_at']
    
    def get_phone_number(self, obj):
        """

        شماره تلفن مرتبط با درخواست OTP مربوط به رکورد تأیید را برمی‌گرداند.
        
        پارامترها:
            obj: نمونه‌ای از مدل OTPVerification که فیلد رابطه‌ای `otp_request` را دارد.
        
        بازگشت:
            str: مقدار `phone_number` استخراج‌شده از `obj.otp_request`.
        """
        return obj.otp_request.phone_number
    get_phone_number.short_description = 'شماره موبایل'
    
    actions = ['deactivate_sessions']
    
    def deactivate_sessions(self, request, queryset):
        """

        غیرفعال‌سازی نشست‌های انتخاب‌شده در پنل ادمین.
        
        این عملیات برای رکوردهای انتخاب‌شده در queryset یک به‌روزرسانی دسته‌ای انجام می‌دهد و همهٔ نمونه‌هایی را که فیلد `is_active` آنها برابر True است به `False` تغییر می‌دهد. پس از اجرا تعداد نشست‌هایی که وضعیت‌شان تغییر کرده با استفاده از `message_user` به کاربر ادمین اطلاع‌رسانی می‌شود.
        
        تأثیرات جانبی:
        - انجام یک به‌روزرسانی دیتابیسی دسته‌ای (bulk update) روی فیلد `is_active`.
        - پیغام نتیجه در رابط ادمین نمایش داده می‌شود.
        
        نکات:
        - تنها رکوردهایی که هم‌اکنون فعال هستند (`is_active=True`) تغییر می‌کنند.
        - تابع مقدار بازگشتی ندارد (None).
        """
        count = queryset.filter(is_active=True).update(is_active=False)
        self.message_user(request, f'{count} نشست غیرفعال شد.')
    deactivate_sessions.short_description = 'غیرفعال کردن نشست‌ها'


@admin.register(OTPRateLimit)
class OTPRateLimitAdmin(admin.ModelAdmin):
    """
    مدیریت محدودیت‌های نرخ OTP
    """
    list_display = [
        'phone_number',
        'minute_count',
        'hour_count',
        'daily_count',
        'is_blocked',
        'blocked_until',
        'failed_attempts',
        'last_request'
    ]
    
    list_filter = [
        'is_blocked',
        'last_request'
    ]
    
    search_fields = [
        'phone_number'
    ]
    
    readonly_fields = [
        'minute_window_start',
        'hour_window_start',
        'daily_window_start',
        'last_request'
    ]
    
    ordering = ['-last_request']
    
    actions = ['unblock_numbers', 'reset_counters']
    
    def unblock_numbers(self, request, queryset):
        """

        رفع مسدودیت دسته‌ای برای رکوردهای انتخاب‌شدهٔ محدودیت نرخ (rate limit).
        
        برای رکوردهای انتخاب‌شده در پنل ادمین، فقط آن‌هایی که در حال حاضر is_blocked=True هستند در پایگاه‌داده به‌روزرسانی می‌شوند: is_blocked به False تنظیم می‌شود، blocked_until پاک می‌گردد (None) و failed_attempts به 0 بازنشانی می‌شود. پس از انجام عملیات، تعداد رکوردهای تغییر یافته به‌صورت پیام مدیریتی در رابط ادمین نمایش داده          

        """
        count = queryset.filter(is_blocked=True).update(
            is_blocked=False,
            blocked_until=None,
            failed_attempts=0
        )
        self.message_user(request, f'{count} شماره از مسدودیت خارج شد.')
    unblock_numbers.short_description = 'رفع مسدودیت'
    
    def reset_counters(self, request, queryset):
        """

        ریست‌شدن شمارنده‌های نرخ محدودیت برای رکوردهای انتخاب‌شده.
        
        این عملیات تمام فیلدهای شمارشی مربوط به پنجره‌های زمانی را برای تمامی رکوردهای موجود در queryset به مقدار صفر بازنشانی می‌کند و زمان شروع پنجره‌های minute/hour/daily را برابر با زمان فعلی سرور قرار می‌دهد. پس از اجرای به‌روزرسانی، تعداد رکوردهای اصلاح‌شده به‌صورت پیام به کاربر ادمین گزارش می‌شود.
        
        پارامترها:
            queryset: مجموعه رکوردهایی از مدل OTPRateLimit که باید شمارنده‌های آن‌ها ریست شوند.
        
        اثر جانبی:
            - به‌روزرسانی مستقیم پایگاه‌داده روی فیلدهای minute_count، hour_count، daily_count و تاریخ‌های شروع پنجره‌ها.
            - ارسال پیام اطلاع‌رسانی به رابط ادمین حاوی تعداد رکوردهای به‌روزرسانی‌شده.
        
        بازگشت:
            هیچ‌چیز (None).

        """
        now = timezone.now()
        count = queryset.update(
            minute_count=0,
            hour_count=0,
            daily_count=0,
            minute_window_start=now,
            hour_window_start=now,
            daily_window_start=now
        )
        self.message_user(request, f'شمارنده‌های {count} شماره ریست شد.')
    reset_counters.short_description = 'ریست شمارنده‌ها'


@admin.register(TokenBlacklist)
class TokenBlacklistAdmin(admin.ModelAdmin):
    """
    مدیریت توکن‌های مسدود شده
    """
    list_display = [
        'get_token_preview',
        'token_type',
        'user',
        'reason',
        'blacklisted_at',
        'expires_at',
        'is_expired_display'
    ]
    
    list_filter = [
        'token_type',
        'blacklisted_at',
        'expires_at'
    ]
    
    search_fields = [
        'user__username',
        'reason'
    ]
    
    readonly_fields = [
        'token',
        'token_type',
        'user',
        'blacklisted_at',
        'reason',
        'expires_at'
    ]
    
    ordering = ['-blacklisted_at']
    
    def get_token_preview(self, obj):
        """

        یک پیش‌نمایش امن از مقدار توکن برمی‌گرداند.
        
        شرح:
            مقدار توکن را به حداکثر ۲۰ کاراکتر اول محدود کرده و برای جلوگیری از افشای کامل توکن سه نقطه الحاق می‌کند. اگر طول توکن کمتر از ۲۰ کاراکتر باشد، باز هم سه نقطه در انتها اضافه می‌شود.
        
        Parameters:
            obj: شیٔی که به‌عنوان فیلد مدل شامل صفت `token` است؛ `obj.token` باید یک رشته باشد.
        
        Returns:
            str: پیش‌نمایش توکن (حداکثر ۲۰ کاراکتر به‌علاوه '...') برای نمایش در رابط ادمین بدون افشای مقدار کامل.

        """
        return f"{obj.token[:20]}..." if len(obj.token) > 20 else obj.token
    get_token_preview.short_description = 'توکن'
    
    def is_expired_display(self, obj):
        """

        نمایش وضعیت انقضا به‌صورت برچسب HTML رنگی.
        
        برمی‌گرداند یک رشته HTML ایمن (با استفاده از format_html) که وضعیت انقضای شیٔ داده‌شده را نمایش می‌دهد: اگر زمان کنونی (timezone.now()) بزرگ‌تر از obj.expires_at باشد، برچسب «منقضی» به رنگ خاکستری و در غیر این صورت «فعال» به رنگ سبز بازگردانده می‌شود.
        
        پارامترها:
            obj: شی‌ای که دارای صفت `expires_at` از نوع datetime است؛ این مقدار باید قابل مقایسه با `django.utils.timezone.now()` باشد.
        
        بازگشت:
            str: رشته HTML ایمن که برای نمایش در رابط ادمین مناسب است.

        """
        if timezone.now() > obj.expires_at:
            return format_html('<span style="color: gray;">منقضی</span>')
        else:
            return format_html('<span style="color: green;">فعال</span>')
    is_expired_display.short_description = 'وضعیت'
    
    def has_add_permission(self, request):
        """

        همیشه اجازهٔ افزودن دستی را در رابط ادمین غیرفعال می‌کند.
        
        این متد نادیده‌گیر (override)ِ ModelAdmin.has_add_permission است و به‌طور قطعی ایجاد رکورد جدید از طریق پنل مدیریت Django را غیرمجاز می‌کند (مثلاً برای TokenBlacklist که نباید دستی ساخته شود). این رفتار تنها دسترسی ادمین برای افزودن را قطع می‌کند و تأثیری بر ایجاد یا مدیریت رکوردها از طریق کد یا مهاجرت‌ها ندارد.
        
        Returns:
            bool: همیشه False — افزودن از طریق ادمین مجاز نیست.

        """
        return False