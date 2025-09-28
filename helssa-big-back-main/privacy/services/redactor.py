"""
سرویس پنهان‌سازی داده‌های حساس (PII/PHI Redactor)
"""

import re
import hashlib
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from ..models import DataField, DataAccessLog, DataClassification

logger = logging.getLogger(__name__)


class PIIRedactor:
    """
    کلاس اصلی برای پنهان‌سازی اطلاعات شخصی قابل شناسایی (PII)
    """
    
    # الگوهای پیش‌فرض برای تشخیص داده‌های حساس
    DEFAULT_PATTERNS = {
        'national_id': r'\b\d{10}\b',  # کد ملی ایرانی
        'phone_number': r'\b09\d{9}\b',  # شماره موبایل ایرانی
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        'iban': r'\bIR\d{22}\b',  # شماره شبا ایرانی
        'postal_code': r'\b\d{10}\b',  # کد پستی ایرانی
    }
    
    # متن‌های جایگزین پیش‌فرض
    DEFAULT_REPLACEMENTS = {
        'national_id': '[کد ملی حذف شده]',
        'phone_number': '[شماره تلفن حذف شده]',
        'email': '[ایمیل حذف شده]',
        'credit_card': '[شماره کارت حذف شده]',
        'iban': '[شماره شبا حذف شده]',
        'postal_code': '[کد پستی حذف شده]',
    }
    
    def __init__(self):
        self.cache_timeout = getattr(settings, 'PRIVACY_CACHE_TIMEOUT', 3600)
        self.patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict[str, Dict]:
        """
        بارگذاری الگوهای پنهان‌سازی از دیتابیس
        """
        cache_key = 'privacy:redaction_patterns'
        patterns = cache.get(cache_key)
        
        if patterns is None:
            patterns = {}
            
            try:
                # تلاش برای خواندن از دیتابیس
                data_fields = DataField.objects.filter(
                    is_active=True
                ).select_related('classification')
                
                for field in data_fields:
                    key = f"{field.app_name}.{field.model_name}.{field.field_name}"
                    patterns[key] = {
                        'pattern': field.redaction_pattern or self._get_default_pattern(field.field_name),
                        'replacement': field.replacement_text,
                        'classification': field.classification.classification_type,
                        'field_id': str(field.id),
                    }
            except Exception as e:
                # در صورت عدم وجود جدول یا خطای دیگر، از الگوهای پیش‌فرض استفاده کن
                logger.warning(f"خطا در بارگذاری الگوها از دیتابیس: {str(e)}")
            
            # اضافه کردن الگوهای پیش‌فرض
            for pattern_name, pattern in self.DEFAULT_PATTERNS.items():
                if pattern_name not in patterns:
                    patterns[pattern_name] = {
                        'pattern': pattern,
                        'replacement': self.DEFAULT_REPLACEMENTS.get(pattern_name, '[حذف شده]'),
                        'classification': 'pii',
                        'field_id': None,
                    }
            
            cache.set(cache_key, patterns, self.cache_timeout)
        
        return patterns
    
    def _get_default_pattern(self, field_name: str) -> str:
        """
        تخمین الگوی پیش‌فرض بر اساس نام فیلد
        """
        field_name_lower = field_name.lower()
        
        if 'national' in field_name_lower or 'melli' in field_name_lower:
            return self.DEFAULT_PATTERNS['national_id']
        elif 'phone' in field_name_lower or 'mobile' in field_name_lower:
            return self.DEFAULT_PATTERNS['phone_number']
        elif 'email' in field_name_lower:
            return self.DEFAULT_PATTERNS['email']
        elif 'card' in field_name_lower:
            return self.DEFAULT_PATTERNS['credit_card']
        elif 'iban' in field_name_lower or 'sheba' in field_name_lower:
            return self.DEFAULT_PATTERNS['iban']
        elif 'postal' in field_name_lower:
            return self.DEFAULT_PATTERNS['postal_code']
        
        return r'\b\w+\b'  # الگوی کلمات
    
    def redact_text(
        self,
        text: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        log_access: bool = True
    ) -> Tuple[str, List[Dict]]:
        """
        پنهان‌سازی متن
        
        Args:
            text: متن ورودی
            user_id: شناسه کاربر
            context: اطلاعات زمینه‌ای
            log_access: آیا دسترسی لاگ شود؟
            
        Returns:
            tuple: (متن پنهان‌سازی شده, لیست تطبیق‌های یافت شده)
        """
        if not text or not isinstance(text, str):
            return text, []
        
        redacted_text = text
        matches_found = []
        
        for pattern_name, pattern_info in self.patterns.items():
            pattern = pattern_info['pattern']
            replacement = pattern_info['replacement']
            
            matches = list(re.finditer(pattern, redacted_text, re.IGNORECASE))
            
            for match in matches:
                original_value = match.group()
                match_info = {
                    'pattern_name': pattern_name,
                    'original_value': original_value,
                    'replacement': replacement,
                    'position': match.span(),
                    'classification': pattern_info['classification'],
                }
                matches_found.append(match_info)
                
                # جایگزینی متن با regex
                redacted_text = re.sub(re.escape(original_value), replacement, redacted_text)
                
                # لاگ کردن دسترسی
                if log_access and pattern_info.get('field_id'):
                    try:
                        # بررسی وجود field قبل از لاگ
                        from ..models import DataField
                        if DataField.objects.filter(id=pattern_info['field_id']).exists():
                            self._log_redaction(
                                user_id=user_id,
                                field_id=pattern_info['field_id'],
                                original_value=original_value,
                                context=context
                            )
                    except Exception as e:
                        logger.warning(f"خطا در لاگ کردن: {str(e)}")
        
        return redacted_text, matches_found
    
    def redact_dict(
        self,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        log_access: bool = True
    ) -> Tuple[Dict[str, Any], List[Dict]]:
        """
        پنهان‌سازی دیکشنری داده
        
        Args:
            data: دیکشنری ورودی
            user_id: شناسه کاربر
            context: اطلاعات زمینه‌ای
            log_access: آیا دسترسی لاگ شود؟
            
        Returns:
            tuple: (دیکشنری پنهان‌سازی شده, لیست تطبیق‌های یافت شده)
        """
        if not isinstance(data, dict):
            return data, []
        
        redacted_data = {}
        all_matches = []
        
        for key, value in data.items():
            if isinstance(value, str):
                redacted_value, matches = self.redact_text(
                    value, user_id, context, log_access
                )
                redacted_data[key] = redacted_value
                all_matches.extend(matches)
            elif isinstance(value, dict):
                redacted_value, matches = self.redact_dict(
                    value, user_id, context, log_access
                )
                redacted_data[key] = redacted_value
                all_matches.extend(matches)
            elif isinstance(value, list):
                redacted_value, matches = self.redact_list(
                    value, user_id, context, log_access
                )
                redacted_data[key] = redacted_value
                all_matches.extend(matches)
            else:
                redacted_data[key] = value
        
        return redacted_data, all_matches
    
    def redact_list(
        self,
        data: List[Any],
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        log_access: bool = True
    ) -> Tuple[List[Any], List[Dict]]:
        """
        پنهان‌سازی لیست داده
        """
        if not isinstance(data, list):
            return data, []
        
        redacted_list = []
        all_matches = []
        
        for item in data:
            if isinstance(item, str):
                redacted_item, matches = self.redact_text(
                    item, user_id, context, log_access
                )
                redacted_list.append(redacted_item)
                all_matches.extend(matches)
            elif isinstance(item, dict):
                redacted_item, matches = self.redact_dict(
                    item, user_id, context, log_access
                )
                redacted_list.append(redacted_item)
                all_matches.extend(matches)
            elif isinstance(item, list):
                redacted_item, matches = self.redact_list(
                    item, user_id, context, log_access
                )
                redacted_list.append(redacted_item)
                all_matches.extend(matches)
            else:
                redacted_list.append(item)
        
        return redacted_list, all_matches
    
    def _log_redaction(
        self,
        user_id: Optional[str],
        field_id: str,
        original_value: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        لاگ کردن عملیات پنهان‌سازی
        """
        try:
            # محاسبه هش مقدار اصلی
            original_hash = hashlib.sha256(
                original_value.encode('utf-8')
            ).hexdigest()
            
            # ایجاد لاگ
            DataAccessLog.objects.create(
                user_id=user_id,
                data_field_id=field_id,
                action_type='redact',
                record_id=context.get('record_id', '') if context else '',
                ip_address=context.get('ip_address') if context else None,
                user_agent=context.get('user_agent', '') if context else '',
                purpose='Automatic PII/PHI redaction',
                was_redacted=True,
                original_value_hash=original_hash,
                context_data=context or {}
            )
            
        except Exception as e:
            logger.error(f"خطا در لاگ کردن پنهان‌سازی: {str(e)}")
    
    def validate_redaction_level(
        self,
        classification_type: str,
        user_role: str
    ) -> bool:
        """
        اعتبارسنجی سطح دسترسی کاربر به نوع داده
        
        Args:
            classification_type: نوع طبقه‌بندی داده
            user_role: نقش کاربر
            
        Returns:
            bool: آیا کاربر اجازه دسترسی دارد؟
        """
        # قوانین دسترسی بر اساس نقش کاربر
        access_rules = {
            'admin': ['public', 'internal', 'confidential', 'restricted', 'phi', 'pii'],
            'doctor': ['public', 'internal', 'confidential', 'phi'],
            'nurse': ['public', 'internal', 'phi'],
            'patient': ['public'],
            'anonymous': [],
        }
        
        allowed_types = access_rules.get(user_role, [])
        return classification_type in allowed_types
    
    def clear_cache(self):
        """
        پاک کردن کش الگوهای پنهان‌سازی
        """
        cache_key = 'privacy:redaction_patterns'
        cache.delete(cache_key)
        self.patterns = self._load_patterns()


class PHIRedactor(PIIRedactor):
    """
    کلاس تخصصی برای پنهان‌سازی اطلاعات سلامت محافظت‌شده (PHI)
    """
    
    # الگوهای اضافی برای PHI
    PHI_PATTERNS = {
        'medical_record_number': r'\bMR\d{6,10}\b',
        'insurance_number': r'\bINS\d{8,12}\b',
        'prescription_number': r'\bRX\d{8,12}\b',
        'lab_result_id': r'\bLAB\d{8,12}\b',
    }
    
    PHI_REPLACEMENTS = {
        'medical_record_number': '[شماره پرونده پزشکی حذف شده]',
        'insurance_number': '[شماره بیمه حذف شده]',
        'prescription_number': '[شماره نسخه حذف شده]',
        'lab_result_id': '[شناسه نتیجه آزمایش حذف شده]',
    }
    
    def __init__(self):
        super().__init__()
        # اضافه کردن الگوهای PHI
        self.patterns.update({
            name: {
                'pattern': pattern,
                'replacement': self.PHI_REPLACEMENTS.get(name, '[حذف شده]'),
                'classification': 'phi',
                'field_id': None,
            }
            for name, pattern in self.PHI_PATTERNS.items()
        })
    
    def redact_medical_text(
        self,
        text: str,
        patient_id: Optional[str] = None,
        doctor_id: Optional[str] = None,
        encounter_id: Optional[str] = None,
        log_access: bool = True
    ) -> Tuple[str, List[Dict]]:
        """
        پنهان‌سازی متن پزشکی با زمینه اضافی
        
        Args:
            text: متن پزشکی
            patient_id: شناسه بیمار
            doctor_id: شناسه دکتر
            encounter_id: شناسه جلسه
            log_access: آیا دسترسی لاگ شود؟
            
        Returns:
            tuple: (متن پنهان‌سازی شده, لیست تطبیق‌های یافت شده)
        """
        context = {
            'patient_id': patient_id,
            'doctor_id': doctor_id,
            'encounter_id': encounter_id,
            'redaction_type': 'medical',
        }
        
        return self.redact_text(
            text=text,
            user_id=doctor_id,
            context=context,
            log_access=log_access
        )


# نمونه‌ای از redactor برای استفاده در سایر بخش‌ها
default_redactor = PIIRedactor()
phi_redactor = PHIRedactor()