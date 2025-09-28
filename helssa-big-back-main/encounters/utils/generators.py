import random
import string
from datetime import datetime
from django.utils import timezone


def generate_prescription_number() -> str:
    """تولید شماره نسخه یکتا
    
    فرمت: RX-YYYYMMDD-XXXXXX
    - RX: پیشوند ثابت
    - YYYYMMDD: تاریخ
    - XXXXXX: کد تصادفی 6 رقمی
    """
    date_part = timezone.now().strftime('%Y%m%d')
    random_part = ''.join(random.choices(string.digits, k=6))
    
    return f"RX-{date_part}-{random_part}"


def generate_access_code(length: int = 6) -> str:
    """تولید کد دسترسی برای ویزیت
    
    پیش‌فرض: کد 6 رقمی
    """
    return ''.join(random.choices(string.digits, k=length))


def generate_room_id(encounter_id: str) -> str:
    """تولید شناسه اتاق ویدیو
    
    فرمت: helssa-XXXXXXXX
    """
    # استفاده از 8 کاراکتر اول encounter_id
    short_id = encounter_id.replace('-', '')[:8]
    return f"helssa-{short_id}"


def generate_file_name(original_name: str, prefix: str = '') -> str:
    """تولید نام فایل یکتا
    
    Args:
        original_name: نام اصلی فایل
        prefix: پیشوند اختیاری
        
    Returns:
        نام فایل با timestamp
    """
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    
    # استخراج پسوند فایل
    if '.' in original_name:
        name_parts = original_name.rsplit('.', 1)
        base_name = name_parts[0]
        extension = name_parts[1]
    else:
        base_name = original_name
        extension = ''
        
    # حذف کاراکترهای غیرمجاز
    safe_base_name = ''.join(c for c in base_name if c.isalnum() or c in '-_')
    
    # ترکیب اجزا
    parts = [prefix, safe_base_name, timestamp]
    file_name = '_'.join(part for part in parts if part)
    
    if extension:
        file_name = f"{file_name}.{extension}"
        
    return file_name


def generate_session_id() -> str:
    """تولید شناسه جلسه برای ضبط
    
    فرمت: SES-YYYYMMDD-HHMM-XXXX
    """
    timestamp = timezone.now().strftime('%Y%m%d-%H%M')
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    
    return f"SES-{timestamp}-{random_part}"


def generate_report_number(report_type: str = 'SOAP') -> str:
    """تولید شماره گزارش
    
    Args:
        report_type: نوع گزارش (SOAP, LAB, RAD, ...)
        
    Returns:
        شماره گزارش یکتا
    """
    date_part = timezone.now().strftime('%Y%m%d')
    sequence = ''.join(random.choices(string.digits, k=5))
    
    return f"{report_type}-{date_part}-{sequence}"


def generate_confirmation_code() -> str:
    """تولید کد تایید 6 رقمی"""
    return ''.join(random.choices(string.digits, k=6))


def generate_otp() -> str:
    """تولید رمز یکبار مصرف 6 رقمی"""
    return ''.join(random.choices(string.digits, k=6))