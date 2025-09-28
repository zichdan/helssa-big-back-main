#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """
    اجرای وظایف مدیریتی (management) پروژه Django از خط فرمان.
    
    این تابع متغیر محیطی `DJANGO_SETTINGS_MODULE` را به `'helssa.settings'` مقداردهی پیش‌فرض می‌کند، سپس تلاش می‌نماید `execute_from_command_line` را از `django.core.management` بارگیری کند. در صورت عدم نصب Django یا نبودن آن در مسیرهای پایتون، یک `ImportError` با پیغام راهنمایی‌کننده مجدداً پرتاب می‌شود. در نهایت تابع، آرگومان‌های خط فرمان (`sys.argv`) را به `execute_from_command_line` می‌سپارد تا فرمان‌های مدیریتی (مانند اجرای سرور توسعه، مهاجرت‌ها، ایجاد اپلیکیشن و غیره) اجرا شوند.
    
    تأثیرات جانبی:
    - ممکن است متغیر محیطی `DJANGO_SETTINGS_MODULE` را تنظیم کند.
    - اجرای مستقیم دستورهای مدیریتی پروژه بر مبنای `sys.argv`.
    
    استفاده معمول: به‌عنوان نقطه ورود اسکریپت `manage.py` برای اجرای ابزارهای مدیریتی Django.
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'helssa.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
