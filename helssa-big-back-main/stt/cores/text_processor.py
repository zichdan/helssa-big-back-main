"""
هسته پردازش متن برای بهبود کیفیت تبدیل گفتار به متن
"""
import logging
import re
from typing import List, Dict, Tuple, Optional
import json

logger = logging.getLogger(__name__)


class TextProcessorCore:
    """
    پردازش و بهبود متن تبدیل شده از گفتار
    
    وظایف:
    - تصحیح اصطلاحات پزشکی
    - نرمال‌سازی متن
    - شناسایی موجودیت‌ها (Named Entity Recognition)
    - بهبود علائم نگارشی
    """
    
    def __init__(self):
        self.logger = logger
        self._load_medical_dictionary()
        self._load_correction_rules()
    
    def _load_medical_dictionary(self):
        """بارگذاری دیکشنری اصطلاحات پزشکی"""
        # در حالت واقعی از فایل یا دیتابیس خوانده می‌شود
        self.medical_terms = {
            # داروها
            'استامینوفن': ['استامینوفن', 'اسیتامینوفن', 'تایلنول'],
            'آموکسی‌سیلین': ['آموکسی سیلین', 'اموکسی سیلین', 'آموکسیسیلین'],
            'متفورمین': ['متفورمین', 'گلوکوفاژ'],
            'لوزارتان': ['لوزارتان', 'کوزار'],
            'آتورواستاتین': ['آتورواستاتین', 'لیپیتور'],
            
            # بیماری‌ها
            'دیابت': ['دیابت', 'قند خون', 'شوگر'],
            'فشار خون': ['فشار خون', 'پرفشاری خون', 'هایپرتنشن'],
            'آسم': ['آسم', 'تنگی نفس مزمن'],
            'میگرن': ['میگرن', 'سردرد میگرنی'],
            
            # علائم
            'سرفه': ['سرفه', 'کاف'],
            'تب': ['تب', 'فیور'],
            'سرگیجه': ['سرگیجه', 'گیجی', 'ورتیگو'],
            'تهوع': ['تهوع', 'حالت تهوع'],
            
            # اعضای بدن
            'قلب': ['قلب', 'هارت'],
            'ریه': ['ریه', 'لانگ'],
            'کبد': ['کبد', 'لیور'],
            'کلیه': ['کلیه', 'کیدنی'],
        }
        
        # دیکشنری برعکس برای جستجوی سریع
        self.medical_variations = {}
        for correct_term, variations in self.medical_terms.items():
            for variation in variations:
                self.medical_variations[variation.lower()] = correct_term
    
    def _load_correction_rules(self):
        """بارگذاری قوانین تصحیح متن"""
        self.correction_rules = [
            # اعداد فارسی به انگلیسی برای دوز دارو
            (r'([۰-۹]+)', self._convert_persian_numbers),
            
            # فاصله‌گذاری صحیح
            (r'(\d+)\s*(میلی\s*گرم|گرم|سی\s*سی)', r'\1 \2'),
            
            # حذف فاصله‌های اضافی
            (r'\s+', ' '),
            
            # اصلاح علائم نگارشی
            (r'\s*([،؛:؟!])\s*', r'\1 '),
            (r'([.،])\s*$', r'\1'),
        ]
    
    def process_transcription(self, text: str, context_type: str = 'general') -> Dict[str, any]:
        """
        پردازش متن تبدیل شده
        
        Args:
            text: متن خام تبدیل شده
            context_type: نوع محتوا (general, medical, prescription, symptoms)
            
        Returns:
            dict: نتیجه پردازش شامل متن بهبود یافته و اطلاعات اضافی
        """
        try:
            # نرمال‌سازی اولیه
            processed_text = self._normalize_text(text)
            
            # تصحیح بر اساس نوع محتوا
            if context_type in ['medical', 'prescription', 'symptoms']:
                processed_text = self._correct_medical_terms(processed_text)
                medical_entities = self._extract_medical_entities(processed_text)
            else:
                medical_entities = []
            
            # اعمال قوانین تصحیح
            processed_text = self._apply_correction_rules(processed_text)
            
            # استخراج اطلاعات مهم
            extracted_info = self._extract_important_info(processed_text, context_type)
            
            # محاسبه امتیاز کیفیت
            quality_score = self._calculate_quality_score(text, processed_text)
            
            return {
                'original_text': text,
                'processed_text': processed_text,
                'medical_entities': medical_entities,
                'extracted_info': extracted_info,
                'quality_score': quality_score,
                'corrections_made': self._get_corrections_made(text, processed_text),
            }
            
        except Exception as e:
            self.logger.error(f"Error in process_transcription: {str(e)}")
            return {
                'original_text': text,
                'processed_text': text,
                'error': str(e)
            }
    
    def _normalize_text(self, text: str) -> str:
        """نرمال‌سازی متن"""
        # حذف فضای خالی ابتدا و انتها
        text = text.strip()
        
        # تبدیل حروف عربی به فارسی
        arabic_to_persian = {
            'ك': 'ک',
            'ي': 'ی',
            'ٱ': 'ا',
            'أ': 'ا',
            'إ': 'ا',
            'ؤ': 'و',
            'ئ': 'ی',
            'ة': 'ه',
        }
        
        for arabic, persian in arabic_to_persian.items():
            text = text.replace(arabic, persian)
        
        # حذف کاراکترهای کنترلی
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        return text
    
    def _correct_medical_terms(self, text: str) -> str:
        """تصحیح اصطلاحات پزشکی"""
        words = text.split()
        corrected_words = []
        
        i = 0
        while i < len(words):
            # بررسی کلمات چندتایی (مثل "فشار خون")
            found = False
            for j in range(min(3, len(words) - i), 0, -1):
                phrase = ' '.join(words[i:i+j]).lower()
                if phrase in self.medical_variations:
                    corrected_words.append(self.medical_variations[phrase])
                    i += j
                    found = True
                    break
            
            if not found:
                # بررسی تک کلمه
                word_lower = words[i].lower()
                if word_lower in self.medical_variations:
                    corrected_words.append(self.medical_variations[word_lower])
                else:
                    corrected_words.append(words[i])
                i += 1
        
        return ' '.join(corrected_words)
    
    def _extract_medical_entities(self, text: str) -> List[Dict[str, str]]:
        """استخراج موجودیت‌های پزشکی"""
        entities = []
        
        # الگوهای regex برای شناسایی
        patterns = {
            'دارو': r'([\w\s]+)\s+(\d+)\s*(میلی\s*گرم|گرم|واحد|قرص|کپسول)',
            'دوز': r'(\d+)\s*(میلی\s*گرم|گرم|سی\s*سی|واحد)',
            'زمان': r'(روزی|شبانه\s*روز)\s*(\d+)\s*(بار|مرتبه|نوبت)',
            'مدت': r'(به\s*مدت|برای)\s*(\d+)\s*(روز|هفته|ماه)',
        }
        
        for entity_type, pattern in patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'type': entity_type,
                    'value': match.group(0),
                    'start': match.start(),
                    'end': match.end()
                })
        
        # شناسایی اصطلاحات پزشکی
        for term in self.medical_terms.keys():
            if term in text:
                start = text.find(term)
                entities.append({
                    'type': 'اصطلاح_پزشکی',
                    'value': term,
                    'start': start,
                    'end': start + len(term)
                })
        
        # مرتب‌سازی بر اساس موقعیت
        entities.sort(key=lambda x: x['start'])
        
        return entities
    
    def _apply_correction_rules(self, text: str) -> str:
        """اعمال قوانین تصحیح متن"""
        for pattern, replacement in self.correction_rules:
            if callable(replacement):
                text = re.sub(pattern, replacement, text)
            else:
                text = re.sub(pattern, replacement, text)
        
        return text.strip()
    
    def _convert_persian_numbers(self, match):
        """تبدیل اعداد فارسی به انگلیسی"""
        persian_to_english = {
            '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
            '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
        }
        
        number = match.group(0)
        for persian, english in persian_to_english.items():
            number = number.replace(persian, english)
        
        return number
    
    def _extract_important_info(self, text: str, context_type: str) -> Dict[str, any]:
        """استخراج اطلاعات مهم بر اساس نوع محتوا"""
        info = {}
        
        if context_type == 'prescription':
            # استخراج اطلاعات نسخه
            info['medications'] = self._extract_medications(text)
            info['instructions'] = self._extract_instructions(text)
            
        elif context_type == 'symptoms':
            # استخراج علائم
            info['symptoms'] = self._extract_symptoms(text)
            info['duration'] = self._extract_duration(text)
            info['severity'] = self._extract_severity(text)
        
        return info
    
    def _extract_medications(self, text: str) -> List[Dict[str, str]]:
        """استخراج داروها از نسخه"""
        medications = []
        
        # الگوی شناسایی دارو با دوز
        pattern = r'([\w\s]+?)\s+(\d+)\s*(میلی\s*گرم|گرم|واحد)\s*[،,]?\s*(روزی|شبانه\s*روز)?\s*(\d+)?\s*(بار|مرتبه|نوبت)?'
        
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            med = {
                'name': match.group(1).strip(),
                'dose': f"{match.group(2)} {match.group(3)}",
            }
            
            if match.group(5):
                med['frequency'] = f"{match.group(5)} {match.group(6) or 'بار'}"
            
            medications.append(med)
        
        return medications
    
    def _extract_symptoms(self, text: str) -> List[str]:
        """استخراج علائم از متن"""
        symptom_keywords = [
            'درد', 'تب', 'سرفه', 'تهوع', 'استفراغ', 'سرگیجه',
            'خستگی', 'ضعف', 'لرز', 'تنگی نفس', 'خارش', 'تورم',
            'قرمزی', 'سوزش', 'گرفتگی', 'بی‌حسی'
        ]
        
        found_symptoms = []
        text_lower = text.lower()
        
        for symptom in symptom_keywords:
            if symptom in text_lower:
                found_symptoms.append(symptom)
        
        return found_symptoms
    
    def _extract_duration(self, text: str) -> Optional[str]:
        """استخراج مدت زمان علائم"""
        duration_pattern = r'(از|به\s*مدت|حدود)\s*(\d+)\s*(روز|هفته|ماه|سال)\s*(پیش|قبل|است)?'
        
        match = re.search(duration_pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
        
        return None
    
    def _extract_severity(self, text: str) -> Optional[str]:
        """استخراج شدت علائم"""
        severity_keywords = {
            'خفیف': ['خفیف', 'کم', 'جزئی'],
            'متوسط': ['متوسط', 'معمولی'],
            'شدید': ['شدید', 'زیاد', 'خیلی', 'بسیار'],
        }
        
        text_lower = text.lower()
        
        for severity, keywords in severity_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return severity
        
        return None
    
    def _calculate_quality_score(self, original: str, processed: str) -> float:
        """محاسبه امتیاز کیفیت پردازش"""
        if not original:
            return 0.0
        
        # معیارهای کیفیت
        scores = []
        
        # نسبت طول (نباید خیلی تغییر کند)
        length_ratio = len(processed) / len(original)
        length_score = 1.0 - abs(1.0 - length_ratio)
        scores.append(length_score)
        
        # تعداد کلمات پزشکی شناسایی شده
        medical_count = sum(1 for term in self.medical_terms.keys() if term in processed)
        medical_score = min(medical_count / 10, 1.0)  # حداکثر 10 کلمه
        scores.append(medical_score)
        
        # وجود ساختار مناسب (نقطه‌گذاری)
        punctuation_score = 0.0
        if any(p in processed for p in ['.', '،', '؛']):
            punctuation_score = 0.5
        if processed.count('.') > 1:
            punctuation_score = 1.0
        scores.append(punctuation_score)
        
        # میانگین امتیازها
        return sum(scores) / len(scores)
    
    def _get_corrections_made(self, original: str, processed: str) -> List[Dict[str, str]]:
        """لیست تصحیحات انجام شده"""
        corrections = []
        
        # مقایسه کلمه به کلمه
        original_words = original.split()
        processed_words = processed.split()
        
        # الگوریتم ساده برای یافتن تغییرات
        for i, (orig, proc) in enumerate(zip(original_words, processed_words)):
            if orig.lower() != proc.lower():
                corrections.append({
                    'position': i,
                    'original': orig,
                    'corrected': proc,
                    'type': 'word_correction'
                })
        
        return corrections[:10]  # حداکثر 10 تصحیح
    
    def suggest_improvements(self, text: str, context_type: str) -> List[str]:
        """پیشنهاد بهبودهای ممکن برای متن"""
        suggestions = []
        
        # بررسی طول جملات
        sentences = re.split(r'[.!?]', text)
        long_sentences = [s for s in sentences if len(s.split()) > 30]
        if long_sentences:
            suggestions.append("جملات طولانی وجود دارد. پیشنهاد می‌شود جملات کوتاه‌تر استفاده شود.")
        
        # بررسی وضوح
        if context_type == 'prescription' and 'دوز' not in text and 'میلی گرم' not in text:
            suggestions.append("دوز دارو مشخص نشده است.")
        
        # بررسی کامل بودن اطلاعات
        if context_type == 'symptoms':
            if 'روز' not in text and 'هفته' not in text:
                suggestions.append("مدت زمان علائم مشخص نشده است.")
        
        return suggestions