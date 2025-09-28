"""
هسته پردازش صوت سیستم مالی
Financial System Speech Processing Core
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal
import json


class BillingSpeechProcessorCore:
    """
    هسته پردازش صوت برای سیستم مالی
    مسئول تبدیل صوت به متن و تحلیل محتوای مالی صوتی
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._initialize_financial_vocabulary()
        
    def _initialize_financial_vocabulary(self):
        """مقداردهی واژگان مالی برای بهبود تشخیص"""
        self.financial_vocabulary = {
            # اعداد فارسی
            'numbers': {
                'صفر': '0', 'یک': '1', 'دو': '2', 'سه': '3', 'چهار': '4',
                'پنج': '5', 'شش': '6', 'هفت': '7', 'هشت': '8', 'نه': '9',
                'ده': '10', 'بیست': '20', 'سی': '30', 'چهل': '40', 'پنجاه': '50',
                'شصت': '60', 'هفتاد': '70', 'هشتاد': '80', 'نود': '90',
                'یکصد': '100', 'هزار': '1000', 'میلیون': '1000000',
                'میلیارد': '1000000000'
            },
            
            # واحدهای پولی
            'currency': {
                'ریال': 'rial',
                'تومان': 'toman',
                'درهم': 'dirham',
                'دلار': 'dollar',
                'یورو': 'euro'
            },
            
            # عملیات مالی
            'operations': {
                'پرداخت': 'payment',
                'واریز': 'deposit',
                'برداشت': 'withdrawal',
                'انتقال': 'transfer',
                'شارژ': 'topup',
                'خرید': 'purchase'
            },
            
            # روش‌های پرداخت
            'payment_methods': {
                'کارت': 'card',
                'کیف پول': 'wallet',
                'اینترنتی': 'online',
                'نقدی': 'cash'
            }
        }
        
    def transcribe_financial_audio(
        self, 
        audio_file: Any, 
        language: str = 'fa',
        enhance_financial_terms: bool = True
    ) -> Dict[str, Any]:
        """
        تبدیل صوت مالی به متن
        
        Args:
            audio_file: فایل صوتی
            language: زبان (fa برای فارسی)
            enhance_financial_terms: بهبود تشخیص اصطلاحات مالی
            
        Returns:
            Dict: نتیجه رونویسی با اطلاعات مالی
        """
        try:
            # شبیه‌سازی تبدیل صوت به متن
            # در پیاده‌سازی واقعی از سرویس‌های STT استفاده می‌شود
            
            result = {
                'transcription': '',
                'confidence': 0.0,
                'segments': [],
                'financial_entities': {},
                'detected_language': language,
                'processing_time': 0.0
            }
            
            # پردازش فایل صوتی (شبیه‌سازی)
            transcription_result = self._mock_speech_to_text(audio_file)
            
            result['transcription'] = transcription_result['text']
            result['confidence'] = transcription_result['confidence']
            result['segments'] = transcription_result['segments']
            result['processing_time'] = transcription_result['processing_time']
            
            # بهبود متن با واژگان مالی
            if enhance_financial_terms:
                enhanced_text = self._enhance_financial_terms(result['transcription'])
                result['transcription'] = enhanced_text
                
            # استخراج موجودیت‌های مالی از متن
            result['financial_entities'] = self._extract_financial_entities_from_speech(
                result['transcription']
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"خطا در تبدیل صوت به متن: {str(e)}")
            return {
                'transcription': '',
                'confidence': 0.0,
                'segments': [],
                'financial_entities': {},
                'error': str(e)
            }
    
    def _mock_speech_to_text(self, audio_file: Any) -> Dict[str, Any]:
        """
        شبیه‌سازی تبدیل صوت به متن
        در پیاده‌سازی واقعی این متد با سرویس واقعی جایگزین می‌شود
        """
        # نمونه متن‌های مالی برای تست
        sample_texts = [
            "لطفاً مبلغ یکصد هزار ریال را به حساب من واریز کنید",
            "برداشت پنجاه تومان از کیف پول انجام شد",
            "پرداخت فاکتور به مبلغ دویست تومان موفق بود",
            "انتقال بیست هزار ریال به شماره کارت انجام شده",
            "شارژ کیف پول با مبلغ صد تومان",
        ]
        
        # انتخاب تصادفی یک نمونه
        import random
        selected_text = random.choice(sample_texts)
        
        return {
            'text': selected_text,
            'confidence': 0.85,
            'segments': [
                {
                    'start': 0.0,
                    'end': 3.5,
                    'text': selected_text,
                    'confidence': 0.85
                }
            ],
            'processing_time': 1.2
        }
    
    def _enhance_financial_terms(self, text: str) -> str:
        """
        بهبود متن با تصحیح اصطلاحات مالی
        
        Args:
            text: متن اولیه
            
        Returns:
            str: متن بهبود یافته
        """
        enhanced_text = text
        
        # تبدیل اعداد گفتاری به عددی
        for word, number in self.financial_vocabulary['numbers'].items():
            enhanced_text = enhanced_text.replace(word, number)
        
        # تصحیح واحدهای پولی
        for word, currency in self.financial_vocabulary['currency'].items():
            if word in enhanced_text:
                enhanced_text = enhanced_text.replace(word, f"{word} ({currency})")
        
        return enhanced_text
    
    def _extract_financial_entities_from_speech(self, text: str) -> Dict[str, Any]:
        """
        استخراج موجودیت‌های مالی از متن صوتی
        
        Args:
            text: متن رونویسی شده
            
        Returns:
            Dict: موجودیت‌های مالی
        """
        from .text_processor import BillingTextProcessorCore
        
        # استفاده از هسته پردازش متن
        text_processor = BillingTextProcessorCore()
        entities = text_processor.extract_financial_entities(text)
        
        # افزودن اطلاعات خاص صوت
        entities['speech_quality'] = self._assess_speech_quality(text)
        entities['spoken_numbers'] = self._extract_spoken_numbers(text)
        
        return entities
    
    def _assess_speech_quality(self, text: str) -> Dict[str, Any]:
        """
        ارزیابی کیفیت تشخیص صوت
        
        Args:
            text: متن رونویسی شده
            
        Returns:
            Dict: اطلاعات کیفیت
        """
        # شاخص‌های کیفیت
        word_count = len(text.split())
        
        # تشخیص اعداد مالی
        financial_numbers = 0
        for word in text.split():
            if any(char.isdigit() for char in word):
                financial_numbers += 1
        
        # تشخیص واژگان مالی
        financial_terms = 0
        for vocab_type, terms in self.financial_vocabulary.items():
            for term in terms.keys():
                if term in text:
                    financial_terms += 1
        
        quality_score = min(1.0, (financial_numbers + financial_terms) / max(word_count, 1))
        
        return {
            'word_count': word_count,
            'financial_numbers': financial_numbers,
            'financial_terms': financial_terms,
            'quality_score': quality_score,
            'clarity': 'high' if quality_score > 0.7 else 'medium' if quality_score > 0.4 else 'low'
        }
    
    def _extract_spoken_numbers(self, text: str) -> List[Dict[str, Any]]:
        """
        استخراج اعداد گفته شده در صوت
        
        Args:
            text: متن رونویسی شده
            
        Returns:
            List: فهرست اعداد یافت شده
        """
        spoken_numbers = []
        
        # جستجوی اعداد فارسی
        for word, value in self.financial_vocabulary['numbers'].items():
            if word in text:
                spoken_numbers.append({
                    'spoken_form': word,
                    'numeric_value': int(value),
                    'position': text.find(word)
                })
        
        # جستجوی اعداد عددی
        import re
        number_pattern = r'\d+'
        for match in re.finditer(number_pattern, text):
            spoken_numbers.append({
                'spoken_form': match.group(),
                'numeric_value': int(match.group()),
                'position': match.start()
            })
        
        return spoken_numbers
    
    def analyze_voice_payment_command(self, transcription: str) -> Dict[str, Any]:
        """
        تحلیل دستور پرداخت صوتی
        
        Args:
            transcription: متن رونویسی شده
            
        Returns:
            Dict: نتایج تحلیل دستور
        """
        try:
            analysis = {
                'command_type': 'unknown',
                'amount': None,
                'currency': None,
                'recipient': None,
                'method': None,
                'confidence': 0.0,
                'parameters': {}
            }
            
            # تشخیص نوع دستور
            analysis['command_type'] = self._detect_voice_command_type(transcription)
            
            # استخراج مبلغ
            amount_info = self._extract_amount_from_voice(transcription)
            if amount_info:
                analysis['amount'] = amount_info['value']
                analysis['currency'] = amount_info['currency']
            
            # تشخیص گیرنده
            analysis['recipient'] = self._detect_recipient_from_voice(transcription)
            
            # تشخیص روش پرداخت
            analysis['method'] = self._detect_payment_method_from_voice(transcription)
            
            # محاسبه اعتماد
            analysis['confidence'] = self._calculate_voice_command_confidence(analysis)
            
            # پارامترهای اضافی
            analysis['parameters'] = {
                'urgency': self._detect_urgency(transcription),
                'confirmation_required': self._needs_confirmation(analysis),
                'estimated_completion_time': self._estimate_completion_time(analysis)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"خطا در تحلیل دستور صوتی: {str(e)}")
            return {}
    
    def _detect_voice_command_type(self, text: str) -> str:
        """تشخیص نوع دستور صوتی"""
        command_keywords = {
            'payment': ['پرداخت', 'پرداخت کن', 'بپرداز'],
            'transfer': ['انتقال', 'انتقال بده', 'ارسال کن'],
            'deposit': ['واریز', 'واریز کن', 'شارژ'],
            'withdrawal': ['برداشت', 'برداشت کن', 'بردار'],
            'balance': ['موجودی', 'اعتبار', 'چقدر دارم'],
            'history': ['تاریخچه', 'فهرست', 'لیست تراکنش']
        }
        
        for command_type, keywords in command_keywords.items():
            if any(keyword in text for keyword in keywords):
                return command_type
        
        return 'unknown'
    
    def _extract_amount_from_voice(self, text: str) -> Optional[Dict[str, Any]]:
        """استخراج مبلغ از دستور صوتی"""
        # جستجوی الگوهای مبلغ
        import re
        
        # الگوی عددی + واحد
        pattern = r'(\d+(?:,\d{3})*)\s*(ریال|تومان)'
        match = re.search(pattern, text)
        
        if match:
            amount_str = match.group(1).replace(',', '')
            currency = match.group(2)
            amount = int(amount_str)
            
            # تبدیل تومان به ریال
            if currency == 'تومان':
                amount *= 10
                
            return {
                'value': amount,
                'currency': 'rial',
                'original_text': match.group(0)
            }
        
        # جستجوی اعداد فارسی
        for word, value in self.financial_vocabulary['numbers'].items():
            if word in text:
                # تشخیص واحد
                currency = 'rial'
                if 'تومان' in text:
                    currency = 'toman'
                    
                amount = int(value)
                if currency == 'toman':
                    amount *= 10
                    
                return {
                    'value': amount,
                    'currency': 'rial',
                    'original_text': word
                }
        
        return None
    
    def _detect_recipient_from_voice(self, text: str) -> Optional[str]:
        """تشخیص گیرنده از دستور صوتی"""
        # الگوهای شماره موبایل
        import re
        mobile_pattern = r'09\d{9}'
        match = re.search(mobile_pattern, text)
        
        if match:
            return match.group(0)
        
        # الگوهای نام کاربری یا شناسه
        if 'به' in text:
            parts = text.split('به')
            if len(parts) > 1:
                recipient_part = parts[1].strip()
                # استخراج اولین کلمه یا عبارت
                return recipient_part.split()[0] if recipient_part else None
        
        return None
    
    def _detect_payment_method_from_voice(self, text: str) -> Optional[str]:
        """تشخیص روش پرداخت از دستور صوتی"""
        for method_fa, method_en in self.financial_vocabulary['payment_methods'].items():
            if method_fa in text:
                return method_en
        
        return 'wallet'  # پیش‌فرض: کیف پول
    
    def _calculate_voice_command_confidence(self, analysis: Dict[str, Any]) -> float:
        """محاسبه اعتماد برای دستور صوتی"""
        confidence = 0.0
        
        # نوع دستور مشخص
        if analysis['command_type'] != 'unknown':
            confidence += 0.3
        
        # مبلغ مشخص
        if analysis['amount']:
            confidence += 0.4
        
        # گیرنده مشخص
        if analysis['recipient']:
            confidence += 0.2
        
        # روش پرداخت مشخص
        if analysis['method']:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _detect_urgency(self, text: str) -> str:
        """تشخیص فوریت از دستور صوتی"""
        urgent_keywords = ['فوری', 'سریع', 'عجله', 'زود']
        
        if any(keyword in text for keyword in urgent_keywords):
            return 'high'
        
        return 'normal'
    
    def _needs_confirmation(self, analysis: Dict[str, Any]) -> bool:
        """تشخیص نیاز به تأیید"""
        # برای مبالغ بالا تأیید لازم است
        if analysis.get('amount', 0) > 1000000:  # بیش از 1 میلیون ریال
            return True
        
        # برای دستورات انتقال تأیید لازم است
        if analysis.get('command_type') in ['transfer', 'payment']:
            return True
        
        return False
    
    def _estimate_completion_time(self, analysis: Dict[str, Any]) -> int:
        """تخمین زمان تکمیل عملیات (ثانیه)"""
        command_type = analysis.get('command_type', 'unknown')
        
        times = {
            'balance': 1,
            'history': 2,
            'deposit': 10,
            'payment': 15,
            'transfer': 30,
            'withdrawal': 60
        }
        
        return times.get(command_type, 30)
    
    def generate_voice_confirmation(self, analysis: Dict[str, Any]) -> str:
        """
        تولید متن تأیید برای دستور صوتی
        
        Args:
            analysis: نتایج تحلیل دستور
            
        Returns:
            str: متن تأیید
        """
        try:
            command_type = analysis.get('command_type', 'unknown')
            amount = analysis.get('amount', 0)
            recipient = analysis.get('recipient', 'نامشخص')
            
            confirmations = {
                'payment': f"آیا مایل هستید مبلغ {amount:,} ریال پرداخت شود؟",
                'transfer': f"آیا مایل هستید مبلغ {amount:,} ریال به {recipient} انتقال یابد؟",
                'deposit': f"آیا مایل هستید مبلغ {amount:,} ریال به کیف پول واریز شود؟",
                'withdrawal': f"آیا مایل هستید مبلغ {amount:,} ریال از کیف پول برداشت شود؟"
            }
            
            return confirmations.get(command_type, "آیا از انجام این عملیات اطمینان دارید؟")
            
        except Exception as e:
            self.logger.error(f"خطا در تولید تأیید صوتی: {str(e)}")
            return "لطفاً دستور خود را مجدداً بیان کنید"