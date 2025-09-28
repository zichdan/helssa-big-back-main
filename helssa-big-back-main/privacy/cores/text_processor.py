"""
هسته پردازش متن برای ماژول Privacy
Text Processing Core for Privacy Module
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from ..services.redactor import default_redactor, phi_redactor

logger = logging.getLogger(__name__)


@dataclass
class TextProcessingResult:
    """
    نتیجه پردازش متن
    """
    original_text: str
    processed_text: str
    redacted_items: List[Dict[str, Any]]
    privacy_score: float
    contains_sensitive_data: bool
    processing_metadata: Dict[str, Any]


class PrivacyTextProcessorCore:
    """
    هسته پردازش متن برای عملیات حریم خصوصی
    """
    
    def __init__(self):
        self.redactor = default_redactor
        self.phi_redactor = phi_redactor
        self.logger = logger
        
        # الگوهای خاص برای تشخیص متن حساس
        self.sensitive_patterns = {
            'medical_terms': [
                r'\b(?:بیماری|درد|عفونت|التهاب|آلرژی|دیابت|فشار خون|قلبی)\b',
                r'\b(?:دارو|قرص|آمپول|سرم|تزریق|عمل جراحی)\b',
                r'\b(?:آزمایش|رادیولوژی|سونوگرافی|ام‌آر‌آی|سی‌تی‌اسکن)\b'
            ],
            'personal_identifiers': [
                r'\b(?:نام|نام خانوادگی|پدر|مادر|همسر)\b',
                r'\b(?:آدرس|محل سکونت|محل کار|شغل)\b',
                r'\b(?:تاریخ تولد|سن|سال تولد)\b'
            ],
            'contact_info': [
                r'\b(?:تلفن|موبایل|ایمیل|آدرس الکترونیک)\b',
                r'\b(?:آی‌دی|شناسه|رمز عبور|کلمه عبور)\b'
            ]
        }
    
    def process_medical_text(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        redaction_level: str = 'standard'
    ) -> TextProcessingResult:
        """
        پردازش متن پزشکی با حفظ حریم خصوصی
        
        Args:
            text: متن ورودی
            context: زمینه اضافی
            redaction_level: سطح پنهان‌سازی ('none', 'standard', 'strict')
            
        Returns:
            TextProcessingResult: نتیجه پردازش
        """
        try:
            if not text or not isinstance(text, str):
                return TextProcessingResult(
                    original_text=text or '',
                    processed_text=text or '',
                    redacted_items=[],
                    privacy_score=0.0,
                    contains_sensitive_data=False,
                    processing_metadata={'error': 'Invalid input text'}
                )
            
            # شناسایی داده‌های حساس
            sensitive_data = self._identify_sensitive_data(text)
            
            # محاسبه امتیاز حریم خصوصی
            privacy_score = self._calculate_privacy_score(text, sensitive_data)
            
            # پنهان‌سازی بر اساس سطح
            processed_text = text
            redacted_items = []
            
            if redaction_level != 'none':
                processed_text, redacted_items = self._apply_redaction(
                    text=text,
                    level=redaction_level,
                    context=context,
                    sensitive_data=sensitive_data
                )
            
            # تولید metadata
            metadata = {
                'processing_time': self._get_processing_time(),
                'redaction_level': redaction_level,
                'sensitive_patterns_found': len(sensitive_data),
                'text_length': len(text),
                'processed_length': len(processed_text),
                'context': context or {}
            }
            
            return TextProcessingResult(
                original_text=text,
                processed_text=processed_text,
                redacted_items=redacted_items,
                privacy_score=privacy_score,
                contains_sensitive_data=len(sensitive_data) > 0,
                processing_metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"خطا در پردازش متن پزشکی: {str(e)}")
            return TextProcessingResult(
                original_text=text,
                processed_text=text,
                redacted_items=[],
                privacy_score=0.0,
                contains_sensitive_data=False,
                processing_metadata={'error': str(e)}
            )
    
    def process_general_text(
        self,
        text: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> TextProcessingResult:
        """
        پردازش متن عمومی
        
        Args:
            text: متن ورودی
            user_id: شناسه کاربر
            context: زمینه اضافی
            
        Returns:
            TextProcessingResult: نتیجه پردازش
        """
        try:
            # استفاده از redactor عمومی
            processed_text, redacted_items = self.redactor.redact_text(
                text=text,
                user_id=user_id,
                context=context
            )
            
            # شناسایی داده‌های حساس
            sensitive_data = self._identify_sensitive_data(text)
            
            # محاسبه امتیاز حریم خصوصی
            privacy_score = self._calculate_privacy_score(text, sensitive_data)
            
            metadata = {
                'processing_time': self._get_processing_time(),
                'redaction_method': 'general',
                'user_id': user_id,
                'context': context or {}
            }
            
            return TextProcessingResult(
                original_text=text,
                processed_text=processed_text,
                redacted_items=redacted_items,
                privacy_score=privacy_score,
                contains_sensitive_data=len(redacted_items) > 0,
                processing_metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"خطا در پردازش متن عمومی: {str(e)}")
            return TextProcessingResult(
                original_text=text,
                processed_text=text,
                redacted_items=[],
                privacy_score=0.0,
                contains_sensitive_data=False,
                processing_metadata={'error': str(e)}
            )
    
    def _identify_sensitive_data(self, text: str) -> List[Dict[str, Any]]:
        """
        شناسایی داده‌های حساس در متن
        """
        sensitive_items = []
        
        for category, patterns in self.sensitive_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    sensitive_items.append({
                        'category': category,
                        'pattern': pattern,
                        'match': match.group(),
                        'position': match.span(),
                        'confidence': self._calculate_match_confidence(match.group(), pattern)
                    })
        
        return sensitive_items
    
    def _calculate_privacy_score(
        self,
        text: str,
        sensitive_data: List[Dict[str, Any]]
    ) -> float:
        """
        محاسبه امتیاز حریم خصوصی (0-100)
        
        Args:
            text: متن اصلی
            sensitive_data: داده‌های حساس یافت شده
            
        Returns:
            float: امتیاز حریم خصوصی
        """
        if not text:
            return 0.0
        
        # عوامل موثر در امتیاز
        text_length = len(text)
        sensitive_count = len(sensitive_data)
        
        # امتیاز پایه بر اساس تعداد داده‌های حساس
        base_score = min(sensitive_count * 10, 50)
        
        # امتیاز اضافی بر اساس نوع داده‌های حساس
        category_weights = {
            'medical_terms': 15,
            'personal_identifiers': 20,
            'contact_info': 10
        }
        
        category_score = 0
        for item in sensitive_data:
            category = item.get('category', '')
            confidence = item.get('confidence', 0.5)
            weight = category_weights.get(category, 5)
            category_score += weight * confidence
        
        # محاسبه امتیاز نهایی
        total_score = min(base_score + category_score, 100)
        
        return round(total_score, 2)
    
    def _calculate_match_confidence(self, match_text: str, pattern: str) -> float:
        """
        محاسبه اطمینان تطبیق الگو
        """
        # منطق ساده برای محاسبه اطمینان
        base_confidence = 0.7
        
        # افزایش اطمینان بر اساس طول تطبیق
        if len(match_text) > 10:
            base_confidence += 0.2
        elif len(match_text) > 5:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _apply_redaction(
        self,
        text: str,
        level: str,
        context: Optional[Dict[str, Any]],
        sensitive_data: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict]]:
        """
        اعمال پنهان‌سازی بر اساس سطح
        """
        if level == 'strict':
            # پنهان‌سازی سخت‌گیرانه
            return self.phi_redactor.redact_text(
                text=text,
                user_id=context.get('user_id') if context else None,
                context=context
            )
        else:
            # پنهان‌سازی استاندارد
            return self.redactor.redact_text(
                text=text,
                user_id=context.get('user_id') if context else None,
                context=context
            )
    
    def _get_processing_time(self) -> str:
        """
        دریافت زمان پردازش
        """
        from django.utils import timezone
        return timezone.now().isoformat()
    
    def analyze_text_privacy_risks(
        self,
        text: str,
        include_suggestions: bool = True
    ) -> Dict[str, Any]:
        """
        تحلیل ریسک‌های حریم خصوصی در متن
        
        Args:
            text: متن مورد تحلیل
            include_suggestions: شامل پیشنهادات بهبود
            
        Returns:
            Dict: گزارش تحلیل ریسک
        """
        try:
            # شناسایی داده‌های حساس
            sensitive_data = self._identify_sensitive_data(text)
            
            # محاسبه امتیاز ریسک
            risk_score = self._calculate_privacy_score(text, sensitive_data)
            
            # تعیین سطح ریسک
            if risk_score >= 70:
                risk_level = 'high'
                risk_description = 'ریسک بالا - نیاز به پنهان‌سازی فوری'
            elif risk_score >= 40:
                risk_level = 'medium'
                risk_description = 'ریسک متوسط - بررسی بیشتر توصیه می‌شود'
            elif risk_score >= 10:
                risk_level = 'low'
                risk_description = 'ریسک پایین - مراقبت معمولی کافی است'
            else:
                risk_level = 'minimal'
                risk_description = 'ریسک بسیار کم - داده‌های حساس شناسایی نشد'
            
            # آماده‌سازی گزارش
            analysis = {
                'risk_score': risk_score,
                'risk_level': risk_level,
                'risk_description': risk_description,
                'sensitive_items': sensitive_data,
                'total_sensitive_items': len(sensitive_data),
                'categories_found': list(set([item['category'] for item in sensitive_data])),
                'text_length': len(text),
                'analyzed_at': self._get_processing_time()
            }
            
            # اضافه کردن پیشنهادات
            if include_suggestions:
                suggestions = self._generate_privacy_suggestions(sensitive_data, risk_level)
                analysis['suggestions'] = suggestions
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"خطا در تحلیل ریسک‌های حریم خصوصی: {str(e)}")
            return {
                'error': str(e),
                'risk_score': 0,
                'risk_level': 'unknown'
            }
    
    def _generate_privacy_suggestions(
        self,
        sensitive_data: List[Dict[str, Any]],
        risk_level: str
    ) -> List[str]:
        """
        تولید پیشنهادات بهبود حریم خصوصی
        """
        suggestions = []
        
        # پیشنهادات کلی بر اساس سطح ریسک
        if risk_level == 'high':
            suggestions.extend([
                'فوری: تمام اطلاعات شخصی را حذف یا پنهان کنید',
                'از سیستم‌های رمزگذاری قوی استفاده کنید',
                'دسترسی به این داده‌ها را محدود کنید'
            ])
        elif risk_level == 'medium':
            suggestions.extend([
                'اطلاعات شناسایی شخصی را بررسی و در صورت نیاز حذف کنید',
                'از سیستم کنترل دسترسی استفاده کنید'
            ])
        
        # پیشنهادات خاص بر اساس نوع داده‌های یافت شده
        categories = [item['category'] for item in sensitive_data]
        
        if 'medical_terms' in categories:
            suggestions.append('اطلاعات پزشکی نیاز به حفاظت ویژه دارند')
        
        if 'personal_identifiers' in categories:
            suggestions.append('اطلاعات شناسایی شخصی را با الگوهای عمومی جایگزین کنید')
        
        if 'contact_info' in categories:
            suggestions.append('اطلاعات تماس را حذف یا ناشناس کنید')
        
        return suggestions


# نمونه‌ای از text processor core برای استفاده در سایر بخش‌ها
privacy_text_processor = PrivacyTextProcessorCore()