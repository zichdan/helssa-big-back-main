import re
from typing import Tuple, Optional
from django.core.exceptions import ValidationError


def validate_phone_number(phone: str) -> Tuple[bool, Optional[str]]:
    """اعتبارسنجی شماره موبایل ایران
    
    Args:
        phone: شماره تلفن
        
    Returns:
        (is_valid, cleaned_number)
    """
    # حذف کاراکترهای غیرعددی
    cleaned = re.sub(r'\D', '', phone)
    
    # بررسی فرمت‌های مختلف
    # 09123456789
    if re.match(r'^09\d{9}$', cleaned):
        return True, cleaned
        
    # 989123456789
    if re.match(r'^989\d{9}$', cleaned):
        return True, '0' + cleaned[2:]
        
    # +989123456789
    if re.match(r'^(\+98)?9\d{9}$', phone):
        cleaned = re.sub(r'\D', '', phone)
        return True, '0' + cleaned[-10:]
        
    return False, None


def validate_national_code(code: str) -> bool:
    """اعتبارسنجی کد ملی ایران
    
    Args:
        code: کد ملی
        
    Returns:
        صحت کد ملی
    """
    # حذف کاراکترهای غیرعددی
    code = re.sub(r'\D', '', code)
    
    # بررسی طول
    if len(code) != 10:
        return False
        
    # بررسی یکسان نبودن همه ارقام
    if len(set(code)) == 1:
        return False
        
    # الگوریتم اعتبارسنجی کد ملی
    check_sum = 0
    for i in range(9):
        check_sum += int(code[i]) * (10 - i)
        
    remainder = check_sum % 11
    check_digit = int(code[9])
    
    if remainder < 2:
        return check_digit == remainder
    else:
        return check_digit == 11 - remainder


def validate_prescription_data(medications: list) -> Tuple[bool, list]:
    """اعتبارسنجی داده‌های نسخه
    
    Args:
        medications: لیست داروها
        
    Returns:
        (is_valid, errors)
    """
    errors = []
    
    if not medications:
        errors.append("نسخه باید حداقل یک دارو داشته باشد")
        return False, errors
        
    required_fields = ['name', 'dosage', 'frequency', 'duration']
    
    for idx, med in enumerate(medications):
        for field in required_fields:
            if field not in med or not med[field]:
                errors.append(f"دارو {idx + 1}: فیلد {field} الزامی است")
                
        # بررسی دوز
        if 'dosage' in med:
            if not re.match(r'^\d+(\.\d+)?\s*(mg|g|ml|mcg|IU)', med['dosage'], re.IGNORECASE):
                errors.append(f"دارو {idx + 1}: فرمت دوز نامعتبر است")
                
    return len(errors) == 0, errors


def validate_visit_duration(duration_minutes: int) -> bool:
    """اعتبارسنجی مدت زمان ویزیت
    
    حداقل: 5 دقیقه
    حداکثر: 180 دقیقه (3 ساعت)
    """
    return 5 <= duration_minutes <= 180


def validate_chief_complaint(complaint: str) -> Tuple[bool, Optional[str]]:
    """اعتبارسنجی شکایت اصلی
    
    Args:
        complaint: شکایت اصلی
        
    Returns:
        (is_valid, error_message)
    """
    if not complaint or len(complaint.strip()) < 3:
        return False, "شکایت اصلی باید حداقل 3 کاراکتر باشد"
        
    if len(complaint) > 500:
        return False, "شکایت اصلی نباید بیش از 500 کاراکتر باشد"
        
    # بررسی کاراکترهای غیرمجاز
    if re.search(r'[<>]', complaint):
        return False, "شکایت اصلی حاوی کاراکترهای غیرمجاز است"
        
    return True, None


def validate_file_size(size_bytes: int, max_size_mb: int = 100) -> bool:
    """اعتبارسنجی حجم فایل
    
    Args:
        size_bytes: حجم فایل به بایت
        max_size_mb: حداکثر حجم مجاز به مگابایت
        
    Returns:
        صحت حجم فایل
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    return 0 < size_bytes <= max_size_bytes


def validate_audio_chunk_index(index: int, total_chunks: int) -> bool:
    """اعتبارسنجی شماره قطعه صوتی"""
    return 0 <= index < total_chunks


def validate_soap_sections(soap_data: dict) -> Tuple[bool, list]:
    """اعتبارسنجی بخش‌های گزارش SOAP
    
    Args:
        soap_data: داده‌های SOAP
        
    Returns:
        (is_valid, errors)
    """
    errors = []
    required_sections = ['subjective', 'objective', 'assessment', 'plan']
    
    for section in required_sections:
        if section not in soap_data:
            errors.append(f"بخش {section} الزامی است")
        elif not soap_data[section] or len(soap_data[section].strip()) < 10:
            errors.append(f"بخش {section} باید حداقل 10 کاراکتر باشد")
            
    return len(errors) == 0, errors


def validate_icd_code(code: str) -> bool:
    """اعتبارسنجی کد ICD-10
    
    فرمت: حرف + 2-6 عدد و نقطه
    مثال: A00, B12.3, C18.1
    """
    pattern = r'^[A-Z]\d{2}(\.\d{1,4})?$'
    return bool(re.match(pattern, code.upper()))


def validate_encounter_status_transition(current_status: str, new_status: str) -> bool:
    """اعتبارسنجی تغییر وضعیت ملاقات
    
    بررسی مجاز بودن انتقال از وضعیت فعلی به وضعیت جدید
    """
    allowed_transitions = {
        'scheduled': ['confirmed', 'cancelled'],
        'confirmed': ['in_progress', 'cancelled', 'no_show'],
        'in_progress': ['completed'],
        'completed': [],  # نمی‌توان تغییر داد
        'cancelled': [],  # نمی‌توان تغییر داد
        'no_show': []     # نمی‌توان تغییر داد
    }
    
    return new_status in allowed_transitions.get(current_status, [])