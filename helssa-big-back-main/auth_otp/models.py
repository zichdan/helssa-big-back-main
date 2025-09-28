"""
مدل‌های سیستم احراز هویت OTP
OTP Authentication System Models
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import RegexValidator
from datetime import timedelta
import secrets
import uuid

User = get_user_model()


class OTPRequest(models.Model):
    """
    درخواست‌های OTP ارسال شده
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    phone_number = models.CharField(
        max_length=11,
        validators=[RegexValidator(r'^09\d{9}$', 'شماره موبایل باید با 09 شروع شود و 11 رقم باشد')],
        verbose_name='شماره موبایل',
        db_index=True
    )
    
    otp_code = models.CharField(
        max_length=6,
        verbose_name='کد OTP'
    )
    
    purpose = models.CharField(
        max_length=20,
        choices=[
            ('login', 'ورود'),
            ('register', 'ثبت‌نام'),
            ('reset_password', 'بازیابی رمز عبور'),
            ('verify_phone', 'تأیید شماره تلفن'),
        ],
        default='login',
        verbose_name='هدف'
    )
    
    is_used = models.BooleanField(
        default=False,
        verbose_name='استفاده شده'
    )
    
    attempts = models.IntegerField(
        default=0,
        verbose_name='تعداد تلاش'
    )
    
    expires_at = models.DateTimeField(
        verbose_name='زمان انقضا'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='زمان ایجاد'
    )
    
    # اطلاعات ارسال
    sent_via = models.CharField(
        max_length=20,
        choices=[
            ('sms', 'پیامک'),
            ('call', 'تماس صوتی'),
        ],
        default='sms',
        verbose_name='روش ارسال'
    )
    
    kavenegar_message_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='شناسه پیام کاوه‌نگار'
    )
    
    # IP و User Agent برای امنیت
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='آدرس IP'
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    
    # متادیتا
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='اطلاعات اضافی'
    )
    
    class Meta:
        verbose_name = 'درخواست OTP'
        verbose_name_plural = 'درخواست‌های OTP'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number', 'created_at']),
            models.Index(fields=['otp_code', 'is_used']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        """

        نمایشٔ متنی شیء OTPRequest.
        
        یک رشته انسانی خوانا برمی‌گرداند که شامل شمارهٔ تلفن و هدف (purpose) درخواست OTP است، به صورت:
        "OTP {phone_number} - {purpose}".
        """
        return f"OTP {self.phone_number} - {self.purpose}"
    
    def save(self, *args, **kwargs):
        """

        ذخیرهٔ نمونهٔ OTPRequest با مقداردهی پیش‌فرض برای فیلدهای حیاتی در صورت عدم وجود.
        
        اگر مقدار otp_code تهی باشد، یک کد شش‌رقمی جدید از generate_otp_code() تولید و تنظیم می‌کند. اگر expires_at تهی باشد، زمان انقضا را روی اکنون به‌اضافهٔ ۳ دقیقه قرار می‌دهد. سپس رفتار ذخیره‌سازی استاندارد مدل را با فراخوانی super().save(*args, **kwargs) اجرا می‌کند.
        
        نکات مهم:
        - مقداردهی فقط زمانی انجام می‌شود که فیلدها مقدار نداشته باشند؛ مقادیر موجود دست‌نخورده باقی می‌مانند.
        - زمان مرجع با timezone.now() تعیین می‌شود.

        """
        if not self.otp_code:
            self.otp_code = self.generate_otp_code()
        
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=3)
        
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_otp_code():
        """

        تولید یک کد OTP عددی ۶ رقمی ایمن (cryptographically secure).
        
        تابع هیچ پارامتری نمی‌گیرد و با استفاده از ماژول `secrets` یک عدد تصادفی در بازهٔ 100000 تا 999999 تولید می‌کند و آن را به صورت رشتهٔ شش‌رقمی بازمی‌گرداند. خروجی برای استفاده به عنوان کد یک‌بارمصرف مناسب است و هیچ وابستگی یا حالت جانبی ندارد.
        
        Returns:
            str: کد OTP شش‌رقمی به صورت رشته (مثال: '395821').
        str: یک رشته حاوی ۶ رقم (مثلاً `"482905"`).
        """
        return f"{secrets.randbelow(900000) + 100000:06d}"
    
    @property
    def is_expired(self):
        """

        بررسی می‌کند آیا OTP منقضی شده است.
        
        برمی‌گرداند True اگر زمان فعلی (با استفاده از django.utils.timezone.now، حساس به timezone) بعد از مقدار expires_at باشد، در غیر این صورت False.

        بررسی می‌کند که آیا کد OTP منقضی شده است.
        
        تابع زمان کنونی را با expires_at مقایسه می‌کند و در صورتی که زمان فعلی (timezone.now()) بعد از expires_at باشد مقدار True بازمی‌گرداند، در غیر این صورت False.
        Returns:
        	bool: True اگر OTP منقضی شده باشد، False در غیر این صورت.

        """
        return timezone.now() > self.expires_at
    
    @property
    def can_verify(self):
        """

        بررسی می‌کند که آیا این کد OTP هنوز قابل‌تأیید است.
        
        تابع مقدار بولی برمی‌گرداند که نشان می‌دهد OTP قابل‌استفاده برای فرآیند تأیید می‌باشد یا خیر. شرط‌های لازم:
        - هنوز مصرف نشده باشد (is_used=False)
        - منقضی نشده باشد (is_expired=False)
        - تعداد تلاش‌ها کمتر از ۳ باشد (attempts < 3)
        
        Returns:
            bool: True اگر OTP قابل‌تأیید باشد، در غیر این صورت False. هیچ اثر جانبی‌ای ندارد.
             """
        return not self.is_used and not self.is_expired and self.attempts < 3
    
    def increment_attempts(self):
        """

        تعداد تلاش‌های (attempts) ثبت‌شده برای همین نمونه را یک واحد افزایش می‌دهد و تغییر را در پایگاه‌داده ذخیره می‌کند.
        
        این متد مقدار فیلد `attempts` را به‌صورت اتمیک افزایش نمی‌دهد بلکه مقدار فعلی را در نمونه افزایش داده و فقط فیلد `attempts` را در دیتابیس بروزرسانی می‌کند (با استفاده از `save(update_fields=['attempts'])`). مقدار بازگشتی ندارد. این فراخوانی ممکن است وضعیت قابل‌تأیید بودن کد OTP (مثلاً مقدار `can_verify`) را تحت‌تأثیر قرار دهد، اما خودِ متد هیچ بررسی یا بلاک‌کننده‌ای انجام نمی‌دهد.
        """
        self.attempts += 1
        self.save(update_fields=['attempts'])
    
    def mark_as_used(self):
        """

        علامت‌گذاری درخواست OTP به‌عنوان مورد استفاده قرار گرفته و ذخیرهٔ تغییریافته‌اش در دیتابیس.
        
        این متد فیلد `is_used` را به `True` تنظیم کرده و فقط همین فیلد را با استفاده از `save(update_fields=['is_used'])` در پایگاه‌داده به‌روز می‌کند تا از به‌روزرسانی‌های غیرضروری جلوگیری شود. (هیچ مقداری بازگشتی ندارد.)
        """
        self.is_used = True
        self.save(update_fields=['is_used'])


class OTPVerification(models.Model):
    """
    تأییدیه‌های OTP موفق
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    otp_request = models.OneToOneField(
        OTPRequest,
        on_delete=models.CASCADE,
        related_name='verification',
        verbose_name='درخواست OTP'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='otp_verifications',
        verbose_name='کاربر'
    )
    
    verified_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='زمان تأیید'
    )
    
    # توکن‌های صادر شده
    access_token = models.TextField(
        verbose_name='Access Token'
    )
    
    refresh_token = models.TextField(
        verbose_name='Refresh Token'
    )
    
    # اطلاعات دستگاه
    device_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='شناسه دستگاه'
    )
    
    device_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='نام دستگاه'
    )
    
    # Session tracking
    session_key = models.CharField(
        max_length=40,
        blank=True,
        verbose_name='کلید نشست'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    
    class Meta:
        verbose_name = 'تأییدیه OTP'
        verbose_name_plural = 'تأییدیه‌های OTP'
        ordering = ['-verified_at']
    
    def __str__(self):
        """

        نمایش متنی رکورد تأیید OTP شامل شمارهٔ تلفن و زمان تأیید.
        
        این متد یک رشته برمی‌گرداند که شمارهٔ تلفن مرتبط با درخواست OTP و زمان ثبت تأیید (verified_at) را نمایش می‌دهد. برای نمایش در ادمن، لاگ‌ها یا دیباگ مناسب است.
        
        Returns:
        	str: رشته‌ای به فرمت `"Verification {phone_number} - {verified_at}"`.

        """
        return f"Verification {self.otp_request.phone_number} - {self.verified_at}"
    
    def deactivate(self):
        """
        غیرفعال‌سازی رکورد تأییدیه‌ی OTP و ذخیره تغییر در پایگاه‌داده.
        
        این متد فِلِد is_active را به False تنظیم می‌کند و تغییر را فورا با فراخوانی save ذخیره می‌کند. تنها فِلِد به‌روزرسانی‌شده در پایگاه‌داده is_active است (از طریق update_fields)، بنابراین فراخوانی ایمن و idempotent برای غیرفعال‌کردن همان رکورد محسوب می‌شود.
        """
        self.is_active = False
        self.save(update_fields=['is_active'])


class OTPRateLimit(models.Model):
    """
    محدودیت‌های نرخ ارسال OTP
    """
    phone_number = models.CharField(
        max_length=11,
        unique=True,
        validators=[RegexValidator(r'^09\d{9}$')],
        verbose_name='شماره موبایل'
    )
    
    # شمارنده‌ها
    minute_count = models.IntegerField(
        default=0,
        verbose_name='تعداد در دقیقه'
    )
    
    hour_count = models.IntegerField(
        default=0,
        verbose_name='تعداد در ساعت'
    )
    
    daily_count = models.IntegerField(
        default=0,
        verbose_name='تعداد روزانه'
    )
    
    # زمان‌های آخرین بروزرسانی
    minute_window_start = models.DateTimeField(
        default=timezone.now,
        verbose_name='شروع پنجره دقیقه'
    )
    
    hour_window_start = models.DateTimeField(
        default=timezone.now,
        verbose_name='شروع پنجره ساعت'
    )
    
    daily_window_start = models.DateTimeField(
        default=timezone.now,
        verbose_name='شروع پنجره روز'
    )
    
    # مسدودسازی
    is_blocked = models.BooleanField(
        default=False,
        verbose_name='مسدود شده'
    )
    
    blocked_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='مسدود تا'
    )
    
    failed_attempts = models.IntegerField(
        default=0,
        verbose_name='تلاش‌های ناموفق'
    )
    
    last_request = models.DateTimeField(
        auto_now=True,
        verbose_name='آخرین درخواست'
    )
    
    class Meta:
        verbose_name = 'محدودیت نرخ OTP'
        verbose_name_plural = 'محدودیت‌های نرخ OTP'
        indexes = [
            models.Index(fields=['phone_number', 'is_blocked']),
        ]
    
    def __str__(self):
        """
        نمایش متنی نمایندهٔ شیٔ محدودیت نرخ برای استفاده در نمایش‌ها و لاگ‌ها.
        
        برمی‌گرداند یک رشته مختصر حاوی شمارهٔ تلفن مرتبط با این شیء به شکل "Rate Limit {phone_number}" که در نمایش‌های اداری، لاگ‌ها و رابط‌های کاربری برای شناسایی سریع نمونهٔ محدودیت نرخ استفاده می‌شود.
        """
        return f"Rate Limit {self.phone_number}"
    
    def reset_minute_window(self):
        """

        پنجره‌ی شمارشِ دقیقه را بازنشانی می‌کند.
        
        این متد شمارنده‌ی minute_count را به صفر بازنشانی کرده و مقدار minute_window_start را به زمان فعلی (timezone.now()) تنظیم می‌کند تا پنجره‌ی یک‌دقیقه‌ای جدیدی آغاز شود. توجه داشته باشید که این متد خودِ مدل را ذخیره (save) نمی‌کند؛ در صورت نیاز به ماندگاری تغییرات در پایگاه‌داده، باید پس از فراخوانی آن save() صدا زده شود.

        """
        self.minute_count = 0
        self.minute_window_start = timezone.now()
    
    def reset_hour_window(self):
        """

        یک‌خطی:
        پنجره شمارش ساعتی را بازنشانی می‌کند.
        
        توضیح کامل:
        شمارنده مربوط به درخواست‌ها در بازهٔ ساعتی را به صفر بازنشانی کرده و زمان شروع پنجرهٔ ساعتی را به زمان جاری سیستم تنظیم می‌کند. این متد فقط فیلدهای مدل را در نمونه تغییر می‌دهد و خودِ متد ذخیره‌سازی (save) روی دیتابیس انجام نمی‌دهد؛ برای ثبت تغییرات باید نمونه را به‌صورت صریح ذخیره کنید (مثلاً با self.save(update_fields=['hour_count', 'hour_window_start'])).
        """
        self.hour_count = 0
        self.hour_window_start = timezone.now()
    
    def reset_daily_window(self):
        """
        پنجرهٔ شمارش روزانه را بازنشانی می‌کند.
        
        با تنظیم شمارندهٔ روزانه به صفر و قرار دادن زمان آغاز پنجرهٔ روزانه روی زمان کنونی، وضعیت شمارش روزانه را بازنشانی می‌کند. این متد مقدار فیلدهای مدل را در نمونهٔ جاری به‌روزرسانی می‌کند اما تغییرات را در پایگاه‌داده ذخیره (save) نمی‌کند — در صورت نیاز باید پس از فراخوانی، save() صدا زده شود.
        """
        self.daily_count = 0
        self.daily_window_start = timezone.now()
    
    def check_and_update_windows(self):
        """

        یک‌خطی:
        پنجره‌های زمانی شمارنده‌های نرخ ارسال را بررسی و در صورت سررسید، بازنشانی می‌کند و وضعیت مسدودی را به‌روز می‌نماید.
        
        توضیح دقیق:
        این متد زمان جاری را با شروع هر یک از پنجره‌های زمانی (دقیقه‌ای، ساعتی، روزانه) مقایسه می‌کند و اگر مدت مربوطه گذشته باشد، پنجره و شمارنده مربوطه را با فراخوانی متدهای reset_* بازنشانی می‌کند. علاوه بر این، اگر شماره در حالت مسدود باشد و زمان مسدودی (blocked_until) گذشته باشد، وضعیت is_blocked را برداشته، blocked_until را پاک می‌کند و شمارنده failed_attempts را به صفر بازنشانی می‌نماید.
        
        تأثیرات جانبی:
        - ممکن است minute_count/hour_count/daily_count و مقادیر شروع پنجره‌ها را تغییر دهد (از طریق reset_*).
        - ممکن است is_blocked، blocked_until و failed_attempts را تغییر دهد.
        
        توجه:
        برای محاسبه زمان جاری از timezone.now() استفاده می‌کند؛ هیچ خروجی یا استثنایی برنمی‌گرداند.

        """
        now = timezone.now()
        
        # بررسی پنجره دقیقه
        if now - self.minute_window_start > timedelta(minutes=1):
            self.reset_minute_window()
        
        # بررسی پنجره ساعت
        if now - self.hour_window_start > timedelta(hours=1):
            self.reset_hour_window()
        
        # بررسی پنجره روز
        if now - self.daily_window_start > timedelta(days=1):
            self.reset_daily_window()
        
        # بررسی مسدودیت
        if self.is_blocked and self.blocked_until and now > self.blocked_until:
            self.is_blocked = False
            self.blocked_until = None
            self.failed_attempts = 0
    
    def can_send_otp(self):
        """

        بررسی می‌کند که آیا در حال حاضر می‌توان برای این شماره OTP ارسال کرد.
        
        این متد ابتدا با فراخوانی check_and_update_windows وضعیت پنجره‌های زمانی (دقیقه/ساعت/روز) و وضعیت مسدودی را بررسی و در صورت نیاز بازنشانی یا رفع مسدودی می‌کند. سپس محدودیت‌های نرخ ارسال را مطابق قوانین زیر ارزیابی می‌کند:
        - حداکثر 1 درخواست در هر دقیقه
        - حداکثر 5 درخواست در هر ساعت
        - حداکثر 10 درخواست در هر روز
        
        در صورت وجود مسدودی فعلی، پیام همراه با زمان پایان مسدودی برگردانده می‌شود.
        
        Returns:
            tuple[bool, str]: زوجی شامل (قابل ارسال؟، پیام). مقدار True و پیام "OK" در صورت مجاز بودن ارسال؛ در غیر این صورت False و یک پیام توضیحی حاوی دلیل عدم مجاز بودن برگردانده می‌شود.

        """
        self.check_and_update_windows()
        
        if self.is_blocked:
            return False, f"شماره شما تا {self.blocked_until} مسدود است"
        
        if self.minute_count >= 1:
            return False, "حداکثر 1 درخواست در دقیقه مجاز است"
        
        if self.hour_count >= 5:
            return False, "حداکثر 5 درخواست در ساعت مجاز است"
        
        if self.daily_count >= 10:
            return False, "حداکثر 10 درخواست در روز مجاز است"
        
        return True, "OK"
    
    def increment_counters(self):
        """

        افزایش یک واحد برای شمارنده‌های بازه‌ای و ذخیرهٔ فوری مدل.
        
        این متد مقدار minute_count، hour_count و daily_count را هر کدام به‌صورت مستقل یک واحد افزایش می‌دهد و وضعیت تغییرات را با فراخوانی save() در دیتابیس ثبت می‌کند. متد هیچ مقدار بازگشتی ندارد و هیچگونه بررسی روی پنجره‌های زمانی (window) یا قفل‌گذاری انجام نمی‌دهد—بنابراین باید تنها وقتی فراخوانی شود که پیش‌شرایط‌های منطقی (مثلاً قبل از فراخوانی، بررسی و ریست پنجره‌ها توسط check_and_update_windows()) برآورده شده باشند.

        """
        self.minute_count += 1
        self.hour_count += 1
        self.daily_count += 1
        self.save()
    
    def add_failed_attempt(self):
        """

        تعداد تلاش‌های ناموفق ارسال/احراز برای این شماره را یک واحد افزایش می‌دهد و وضعیت مسدودی را در صورت رسیدن به آستانه به‌روز می‌کند.
        
        در عمل:
        - مقدار فیلد `failed_attempts` را یک واحد افزایش می‌دهد.
        - اگر شمارش پس از افزایش به 10 یا بیشتر برسد، فیلد `is_blocked` را به True تنظیم و `blocked_until` را برابر اکنون + 24 ساعت قرار می‌دهد (مسدودی 24 ساعته).
        - تغییرات را در پایگاه‌داده ذخیره می‌کند.
        
        بازگشتی ندارد؛ همه تغییرات بلافاصله با فراخوانی `save()` ذخیره می‌شوند.

        """
        self.failed_attempts += 1
        
        if self.failed_attempts >= 10:
            self.is_blocked = True
            self.blocked_until = timezone.now() + timedelta(hours=24)
        
        self.save()


class TokenBlacklist(models.Model):
    """
    لیست سیاه توکن‌ها
    """
    token = models.TextField(
        unique=True,
        verbose_name='توکن'
    )
    
    token_type = models.CharField(
        max_length=20,
        choices=[
            ('access', 'Access Token'),
            ('refresh', 'Refresh Token'),
        ],
        verbose_name='نوع توکن'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blacklisted_tokens',
        verbose_name='کاربر'
    )
    
    blacklisted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='زمان مسدودی'
    )
    
    reason = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='دلیل'
    )
    
    expires_at = models.DateTimeField(
        verbose_name='زمان انقضا'
    )
    
    class Meta:
        verbose_name = 'توکن مسدود'
        verbose_name_plural = 'توکن‌های مسدود'
        ordering = ['-blacklisted_at']
        indexes = [
            models.Index(fields=['token', 'expires_at']),
        ]
    
    def __str__(self):
        """

        نمایش متنی رکورد توکن مسدودشده.
        
        یک رشته انسانی‌خوان (human-readable) برمی‌گرداند که نوع توکن و صاحب آن را نشان می‌دهد، به شکل:
        "Blacklisted {token_type} - {user}".
        این متن در رابط‌های مدیریتی، لاگ‌ها و نمایش‌های کوتاه مدل استفاده می‌شود.
        
        Returns:
            str: رشته نمایشی حاوی نوع توکن و کاربر مربوط
        """
        return f"Blacklisted {self.token_type} - {self.user}"
    
    @classmethod
    def is_blacklisted(cls, token):
        """

        بررسی می‌کند آیا یک توکن مشخص هم‌اکنون در لیست سیاه فعال وجود دارد.
        
        این متد جستجو می‌کند که آیا رکوردی با مقدار `token` داده‌شده وجود دارد که زمان انقضای آن در آینده باشد (یعنی هنوز معتبر و مؤثر است). در عمل نشان می‌دهد آیا توکن قبلاً بلاک شده و بلاک آن هنوز منقضی نشده است.
        
        Parameters:
            token (str): مقدار توکن (رشته) که باید در لیست سیاه بررسی شود.
        
        Returns:
            bool: مقدار True اگر یک ورودی فعال در لیست سیاه برای توکن وجود داشته باشد، در غیر این صورت False.

        """
        return cls.objects.filter(
            token=token,
            expires_at__gt=timezone.now()
        ).exists()