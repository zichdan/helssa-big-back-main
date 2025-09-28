"""
دستور مدیریت برای بارگذاری داده‌های اولیه چت‌بات
Management command to load initial chatbot data
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from chatbot.models import ChatbotResponse


class Command(BaseCommand):
    """
    دستور بارگذاری داده‌های اولیه چت‌بات
    """
    help = 'بارگذاری داده‌های اولیه چت‌بات شامل پاسخ‌های از پیش تعریف شده'
    
    def add_arguments(self, parser):
        """
        افزودن آرگومان‌های خط فرمان برای دستور مدیریت.
        
        این متد دو آرگومان CLI را به parser اضافه می‌کند:
        - --reset: فلگ بولی (action='store_true') که در صورت تعیین، قبل از بارگذاری فیکسچر همه رکوردهای ChatbotResponse را حذف می‌کند.
        - --fixture: نام فایل فیکسچر (رشته) برای بارگذاری؛ مقدار پیش‌فرض 'initial_responses.json'.
        
        پارامترها:
        - parser: نمونهٔ argparse-like که آرگومان‌ها به آن اضافه می‌شوند.
        """
        parser.add_argument(
            '--reset',
            action='store_true',
            help='حذف داده‌های موجود قبل از بارگذاری',
        )
        
        parser.add_argument(
            '--fixture',
            type=str,
            default='initial_responses.json',
            help='نام فایل fixture برای بارگذاری',
        )
    
    def handle(self, *args, **options):
        """
        اجرای فرمان مدیریت برای بارگذاری داده‌های اولیه چت‌بات.
        
        این متد:
        - به‌صورت اختیاری تمام رکوردهای مدل ChatbotResponse را در صورت فعال بودن گزینه `reset` حذف می‌کند.
        - فایل fixture مشخص‌شده توسط گزینه `fixture` را از مسیر `chatbot/fixtures/{fixture}` با استفاده از `loaddata` بارگذاری می‌کند.
        - پس از بارگذاری، آمار کلی را محاسبه و به خروجی می‌نویسد (تعداد کل پاسخ‌ها و تعداد پاسخ‌های فعال).
        - آمار تفکیک‌شده‌ بر اساس دسته‌بندی‌ها را با فراخوانی `_show_category_stats()` نمایش می‌دهد.
        - در صورت وقوع هرگونه استثنا هنگام بارگذاری، پیام خطا را به خروجی می‌نویسد و اجرای متد را خاتمه می‌دهد.
        
        گزینه‌های ورودی (در دیکشنری `options`):
        - `reset` (bool): اگر True باشد، پیش از بارگذاری fixture همهٔ پاسخ‌های موجود حذف می‌شوند.
        - `fixture` (str): نام فایل fixture که از مسیر `chatbot/fixtures/` بارگذاری می‌شود.
        
        اثرات جانبی:
        - حذف سطرهای جدول ChatbotResponse در صورت فعال‌بودن `reset`.
        - تغییر داده‌های پایگاه‌داده با اجرای فرمان `loaddata`.
        - نوشتن پیام‌های وضعیت و آمار در خروجی استاندارد فرمان مدیریت.
        """
        self.stdout.write(
            self.style.SUCCESS('شروع بارگذاری داده‌های اولیه چت‌بات...')
        )
        
        # حذف داده‌های موجود در صورت درخواست
        if options['reset']:
            self.stdout.write('حذف پاسخ‌های موجود...')
            ChatbotResponse.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS('✓ پاسخ‌های موجود حذف شدند')
            )
        
        # بارگذاری fixture
        try:
            fixture_path = f'chatbot/fixtures/{options["fixture"]}'
            call_command('loaddata', fixture_path)
            
            # آمارگیری
            total_responses = ChatbotResponse.objects.count()
            active_responses = ChatbotResponse.objects.filter(is_active=True).count()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ داده‌های اولیه با موفقیت بارگذاری شد\n'
                    f'  - تعداد کل پاسخ‌ها: {total_responses}\n'
                    f'  - پاسخ‌های فعال: {active_responses}'
                )
            )
            
            # نمایش آمار بر اساس دسته‌بندی
            self._show_category_stats()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'خطا در بارگذاری داده‌ها: {str(e)}')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS('\n🎉 فرآیند بارگذاری با موفقیت تکمیل شد!')
        )
    
    def _show_category_stats(self):
        """
        هدر و آمار دسته‌بندی‌شده پاسخ‌های چت‌بات را در خروجی مدیریت چاپ می‌کند.
        
        این متد:
        - یک عنوان برای «آمار بر اساس دسته‌بندی» در خروجی (self.stdout) می‌نویسد.
        - همه مقادیر یکتای فیلد `category` را از مدل `ChatbotResponse` واکشی می‌کند.
        - برای هر دسته، شمار پاسخ‌های فعال (`is_active=True`) را محاسبه می‌کند.
        - کلید دسته‌ها را به یک برچسب فارسی قابل‌فهم نگاشت می‌کند و در صورت نبود نگاشت، از کلید خام استفاده می‌کند.
        - هر خط آمار را به شکل "  - {برچسب}: {تعداد} پاسخ" به خروجی می‌نویسد.
        
        تأثیرات جانبی:
        - خروجی متنی به `self.stdout` می‌نویسد.
        - از مدل پایگاه‌داده `ChatbotResponse` خواندن (queries) انجام می‌دهد؛ هیچ تغییر یا حذف داده‌ای انجام نمی‌دهد.
        """
        self.stdout.write('\nآمار بر اساس دسته‌بندی:')
        
        categories = ChatbotResponse.objects.values_list('category', flat=True).distinct()
        
        for category in categories:
            count = ChatbotResponse.objects.filter(
                category=category, 
                is_active=True
            ).count()
            
            category_display = {
                'greeting': 'خوشامدگویی',
                'symptom_inquiry': 'پرسش علائم',
                'medication_info': 'اطلاعات دارو',
                'appointment': 'نوبت‌گیری',
                'emergency': 'اورژانس',
                'general_health': 'سلامت عمومی',
                'farewell': 'خداحافظی',
                'error': 'خطا',
                'unknown': 'نامشخص'
            }.get(category, category)
            
            self.stdout.write(f'  - {category_display}: {count} پاسخ')