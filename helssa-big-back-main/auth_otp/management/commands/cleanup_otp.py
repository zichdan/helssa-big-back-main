"""
دستور مدیریت برای پاکسازی داده‌های منقضی OTP
Management Command for Cleaning Up Expired OTP Data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import logging

from auth_otp.services import OTPService, AuthService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    پاکسازی OTP ها و توکن‌های منقضی شده
    
    استفاده:
        python manage.py cleanup_otp
        python manage.py cleanup_otp --dry-run
    """
    help = 'پاکسازی OTP ها و توکن‌های منقضی شده'
    
    def add_arguments(self, parser):
        """
        ثبت آرگومان‌های خط فرمان برای دستور مدیریت:
        
        - افزودن گزینه `--dry-run` (flag): در صورتی که فعال باشد، عملیات حذف انجام نمی‌شود و تنها تعداد رکوردهایی که قابل حذف هستند نمایش داده می‌شود.
        - افزودن گزینه `--otp-age-hours` (int, پیش‌فرض 24): حداقل سن پیامک/OTP (بر حسب ساعت) که برای حذف در نظر گرفته می‌شود؛ رکوردهایی که زمان ایجادشان برابر یا بیشتر از این مقدار قدیمی‌تر باشد به‌عنوان قابل حذف در نظر گرفته می‌شوند.
        
        این متد به پارسر آرگومان‌ها (argparse) گزینه‌های مورد نیاز برای اجرای ایمن/آزمایشی و کنترل آستانه سنی OTP را اضافه می‌کند.

        """
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='نمایش تعداد رکوردهای قابل حذف بدون انجام عملیات',
        )
        
        parser.add_argument(
            '--otp-age-hours',
            type=int,
            default=24,
            help='حداقل سن OTP برای حذف (به ساعت)',
        )
    
    def handle(self, *args, **options):
        """

        اجرای فرمان پاکسازی OTPها و توکن‌های منقضی شده.
        
        این متد نقطه ورود فرمان مدیریت است؛ گزینه‌های ورودیِ `options` را خوانده، عملیات پاکسازی OTPهای قدیمی و توکن‌های منقضی‌شده در blacklist را اجرا (یا در حالت dry-run تنها شمارش می‌کند) و خلاصه نتایج را به خروجی می‌نویسد. در حالت غیر dry-run حذف واقعی با استفاده از متدهای داخلی `_cleanup_otps` و `_cleanup_tokens` انجام می‌شود.
        
        پارامترهای گزینه (در `options`):
        - dry_run (bool): اگر True باشد، هیچ داده‌ای حذف نمی‌شود و فقط شمارش آیتم‌های قابل حذف گزارش می‌شود.
        - otp_age_hours (int): حداقل سن (به ساعت) برای در نظر گرفتن یک OTP به‌عنوان "قدیمی" و واجد حذف.
        
        عوارض جانبی:
        - نوشتن پیام‌ها و خلاصه به stdout با استایل‌های مناسب.
        - در حالت غیر dry-run، اجرای حذف واقعی از طریق `_cleanup_otps` و `_cleanup_tokens` که تعداد حذف‌شده‌ها را بازمی‌گردانند.
    - بسته به مقدار `dry_run` ممکن است رکوردهایی از پایگاه داده حذف شوند (از طریق `_cleanup_otps` و `_cleanup_tokens`).
        """
        dry_run = options['dry_run']
        otp_age_hours = options['otp_age_hours']
        
        self.stdout.write(
            self.style.SUCCESS('شروع پاکسازی داده‌های منقضی...')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('حالت Dry Run - هیچ داده‌ای حذف نخواهد شد')
            )
        
        # پاکسازی OTP های قدیمی
        otp_count = self._cleanup_otps(dry_run, otp_age_hours)
        
        # پاکسازی توکن‌های منقضی از blacklist
        token_count = self._cleanup_tokens(dry_run)
        
        # نمایش خلاصه
        self.stdout.write(
            self.style.SUCCESS(
                f'\nخلاصه پاکسازی:\n'
                f'- OTP های حذف شده: {otp_count}\n'
                f'- توکن‌های حذف شده از blacklist: {token_count}'
            )
        )
    
    def _cleanup_otps(self, dry_run, age_hours):
        """

        یک خطی:
        پاک‌سازی یا شمارش OTPهای قدیمی بسته به حالت dry-run.
        
        توضیح کامل:
        اگر dry_run True باشد، تعداد رکوردهای OTPRequest با created_at قدیمی‌تر از (now - age_hours) شمارش و برگردانده می‌شود ولی هیچ حذف واقعی انجام نمی‌گیرد. اگر dry_run False باشد، عملیات حذف واقعی از طریق OTPService.cleanup_expired_otps() انجام شده و تعداد OTPهای حذف‌شده برگشت داده می‌شود.
        
        پارامترها:
            dry_run (bool): وقتی True است فقط شمارش انجام می‌شود و حذف صورت نمی‌گیرد.
            age_hours (int): حداقل سن (بر حسب ساعت) که یک OTP باید قدیمی‌تر از آن باشد تا برای حذف در نظر گرفته شود.
        
        بازگشت:
            int: تعداد OTPهای شمارش‌شده (در حالت dry-run) یا تعداد OTPهای حذف‌شده (در حالت واقعی).
        """
        if dry_run:
            from auth_otp.models import OTPRequest
            cutoff = timezone.now() - timedelta(hours=age_hours)
            count = OTPRequest.objects.filter(created_at__lt=cutoff).count()
            self.stdout.write(
                f'تعداد OTP های قابل حذف (قدیمی‌تر از {age_hours} ساعت): {count}'
            )
            return count
        else:
            count = OTPService.cleanup_expired_otps()
            self.stdout.write(
                self.style.SUCCESS(f'{count} OTP قدیمی حذف شد')
            )
            return count
    
    def _cleanup_tokens(self, dry_run):
        """
        یک‌خطی:

        توکن‌های منقضی‌شده در لیست سیاه را یا شمارش می‌کند (dry-run) یا حذف می‌کند.
        
        توضیح مفصل:
        اگر dry_run برابر True باشد، مدل TokenBlacklist به‌صورت پویا وارد شده و تعداد رکوردهایی که فیلد `expires_at` آنها قبل از زمان فعلی (timezone.now()) است شمرده می‌شود؛ هیچ حذف یا تغییری انجام نمی‌شود. اگر dry_run برابر False باشد، متد سرویس AuthService.cleanup_expired_blacklist() فراخوانی شده و توکن‌های منقضی از لیست سیاه حذف می‌شوند.
        
        پارامترها:
            dry_run (bool): وقتی True است عمل فقط شمارش انجام می‌شود و حذف صورت نمی‌گیرد.
        
        بازگشتی:
            int: تعداد توکن‌های منقضی که در حالت dry-run شمارش شدند یا تعداد توکن‌هایی که حذف شدند.
      int: تعداد توکن‌هایی که شناسایی شده‌اند (در حالت dry-run تعداد قابل حذف، در حالت واقعی تعداد حذف‌شده).
        """
        if dry_run:
            from auth_otp.models import TokenBlacklist
            count = TokenBlacklist.objects.filter(
                expires_at__lt=timezone.now()
            ).count()
            self.stdout.write(
                f'تعداد توکن‌های منقضی در blacklist: {count}'
            )
            return count
        else:
            count = AuthService.cleanup_expired_blacklist()
            self.stdout.write(
                self.style.SUCCESS(f'{count} توکن منقضی از blacklist حذف شد')
            )
            return count