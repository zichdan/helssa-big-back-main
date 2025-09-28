"""
هسته پردازش متن اپ Doctor
Doctor App Text Processor Core
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class MedicalEntity:
    """موجودیت پزشکی استخراج شده"""
    text: str
    entity_type: str
    confidence: float
    start_pos: int
    end_pos: int


@dataclass
class TextProcessingResult:
    """نتیجه پردازش متن"""
    original_text: str
    processed_text: str
    entities: List[MedicalEntity]
    keywords: List[str]
    sentiment: str
    language: str
    medical_relevance: float


class DoctorTextProcessorCore:
    """
    هسته پردازش متن برای اپ Doctor
    مسئول پردازش نوت‌های پزشکی، استخراج اطلاعات و تولید گزارش‌ها
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.medical_terms = self._load_medical_terms()
        self.symptom_keywords = self._load_symptom_keywords()
        self.drug_names = self._load_drug_names()
    
    def process_medical_note(self, text: str, context: Dict[str, Any] = None) -> TextProcessingResult:
        """
        پردازش یادداشت پزشکی
        
        Args:
            text: متن یادداشت پزشکی
            context: اطلاعات زمینه‌ای (بیمار، نوع ویزیت و...)
            
        Returns:
            TextProcessingResult object
        """
        try:
            # پاکسازی و استاندارد کردن متن
            processed_text = self._clean_and_normalize_text(text)
            
            # تشخیص زبان
            language = self._detect_language(processed_text)
            
            # استخراج موجودیت‌های پزشکی
            entities = self._extract_medical_entities(processed_text)
            
            # استخراج کلمات کلیدی
            keywords = self._extract_keywords(processed_text)
            
            # تحلیل احساسات (جهت بررسی وضعیت روحی بیمار)
            sentiment = self._analyze_sentiment(processed_text)
            
            # محاسبه میزان ارتباط با حوزه پزشکی
            medical_relevance = self._calculate_medical_relevance(processed_text, entities)
            
            return TextProcessingResult(
                original_text=text,
                processed_text=processed_text,
                entities=entities,
                keywords=keywords,
                sentiment=sentiment,
                language=language,
                medical_relevance=medical_relevance
            )
            
        except Exception as e:
            self.logger.error(f"Error processing medical note: {str(e)}")
            return TextProcessingResult(
                original_text=text,
                processed_text=text,
                entities=[],
                keywords=[],
                sentiment="neutral",
                language="fa",
                medical_relevance=0.0
            )
    
    def extract_symptoms_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        استخراج علائم از متن
        
        Args:
            text: متن ورودی
            
        Returns:
            لیست علائم استخراج شده
        """
        symptoms = []
        
        # الگوهای رایج برای علائم
        symptom_patterns = [
            r'سردرد|درد سر',
            r'تب|تپش',
            r'سرفه|کخه',
            r'درد شکم|درد معده',
            r'تهوع|حالت تهوع',
            r'سرگیجه|گیجی',
            r'ضعف|خستگی',
            r'درد قفسه سینه|درد سینه',
            r'تنگی نفس|مشکل تنفسی',
            r'اسهال|یبوست',
        ]
        
        for pattern in symptom_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                symptoms.append({
                    'symptom': match.group(),
                    'position': match.span(),
                    'confidence': 0.8
                })
        
        return symptoms
    
    def extract_medications_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        استخراج داروها از متن
        
        Args:
            text: متن ورودی
            
        Returns:
            لیست داروهای استخراج شده
        """
        medications = []
        
        # جستجو در لیست نام داروها
        for drug in self.drug_names:
            pattern = rf'\b{re.escape(drug)}\b'
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                medications.append({
                    'drug_name': match.group(),
                    'position': match.span(),
                    'confidence': 0.9
                })
        
        return medications
    
    def generate_medical_summary(self, text: str, max_length: int = 200) -> str:
        """
        تولید خلاصه پزشکی از متن
        
        Args:
            text: متن کامل
            max_length: حداکثر طول خلاصه
            
        Returns:
            خلاصه پزشکی
        """
        try:
            # استخراج جملات مهم
            sentences = self._split_into_sentences(text)
            important_sentences = self._rank_sentences_by_importance(sentences)
            
            # ساخت خلاصه
            summary = ""
            for sentence in important_sentences:
                if len(summary) + len(sentence) > max_length:
                    break
                summary += sentence + " "
            
            return summary.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating medical summary: {str(e)}")
            return text[:max_length] + "..." if len(text) > max_length else text
    
    def extract_soap_components(self, text: str) -> Dict[str, str]:
        """
        استخراج اجزای SOAP از متن
        
        Args:
            text: متن یادداشت پزشکی
            
        Returns:
            دیکشنری شامل اجزای SOAP
        """
        soap_components = {
            'subjective': '',
            'objective': '',
            'assessment': '',
            'plan': ''
        }
        
        try:
            # الگوهای شناسایی بخش‌های SOAP
            patterns = {
                'subjective': r'(شکایت|علائم|احساس بیمار|گفته بیمار)',
                'objective': r'(معاینه|یافته‌های فیزیکی|علائم حیاتی)',
                'assessment': r'(تشخیص|ارزیابی|نظر پزشک)',
                'plan': r'(برنامه درمان|نسخه|توصیه)'
            }
            
            # تقسیم متن به جملات
            sentences = self._split_into_sentences(text)
            
            # طبقه‌بندی جملات
            for sentence in sentences:
                max_score = 0
                best_category = 'subjective'  # پیش‌فرض
                
                for category, pattern in patterns.items():
                    if re.search(pattern, sentence, re.IGNORECASE):
                        score = len(re.findall(pattern, sentence, re.IGNORECASE))
                        if score > max_score:
                            max_score = score
                            best_category = category
                
                soap_components[best_category] += sentence + " "
            
            # پاکسازی
            for key in soap_components:
                soap_components[key] = soap_components[key].strip()
            
            return soap_components
            
        except Exception as e:
            self.logger.error(f"Error extracting SOAP components: {str(e)}")
            return soap_components
    
    def validate_medical_text(self, text: str) -> Tuple[bool, List[str]]:
        """
        اعتبارسنجی متن پزشکی
        
        Args:
            text: متن برای بررسی
            
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        
        # بررسی حداقل طول
        if len(text.strip()) < 10:
            issues.append("متن کوتاه است")
        
        # بررسی وجود محتوای پزشکی
        medical_relevance = self._calculate_medical_relevance(text, [])
        if medical_relevance < 0.3:
            issues.append("محتوای پزشکی کافی نیست")
        
        # بررسی استفاده از کلمات نامناسب
        inappropriate_words = self._check_inappropriate_content(text)
        if inappropriate_words:
            issues.append(f"کلمات نامناسب: {', '.join(inappropriate_words)}")
        
        # بررسی کیفیت زبان
        if self._has_poor_language_quality(text):
            issues.append("کیفیت زبان پایین است")
        
        return len(issues) == 0, issues
    
    def _clean_and_normalize_text(self, text: str) -> str:
        """پاکسازی و استاندارد کردن متن"""
        # حذف کاراکترهای اضافی
        text = re.sub(r'\s+', ' ', text)
        
        # استاندارد کردن اعداد فارسی
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        english_digits = '0123456789'
        for pd, ed in zip(persian_digits, english_digits):
            text = text.replace(pd, ed)
        
        # پاکسازی کاراکترهای غیرضروری
        text = re.sub(r'[^\w\s\u0600-\u06FF.,!?():]', '', text)
        
        return text.strip()
    
    def _detect_language(self, text: str) -> str:
        """تشخیص زبان متن"""
        # تشخیص ساده بر اساس کاراکترهای فارسی
        persian_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        if persian_chars > english_chars:
            return 'fa'
        elif english_chars > persian_chars:
            return 'en'
        else:
            return 'mixed'
    
    def _extract_medical_entities(self, text: str) -> List[MedicalEntity]:
        """استخراج موجودیت‌های پزشکی"""
        entities = []
        
        # استخراج علائم
        symptoms = self.extract_symptoms_from_text(text)
        for symptom in symptoms:
            entities.append(MedicalEntity(
                text=symptom['symptom'],
                entity_type='symptom',
                confidence=symptom['confidence'],
                start_pos=symptom['position'][0],
                end_pos=symptom['position'][1]
            ))
        
        # استخراج داروها
        medications = self.extract_medications_from_text(text)
        for med in medications:
            entities.append(MedicalEntity(
                text=med['drug_name'],
                entity_type='medication',
                confidence=med['confidence'],
                start_pos=med['position'][0],
                end_pos=med['position'][1]
            ))
        
        return entities
    
    def _extract_keywords(self, text: str) -> List[str]:
        """استخراج کلمات کلیدی"""
        # حذف کلمات ربطی
        stop_words = ['و', 'در', 'با', 'به', 'از', 'که', 'این', 'آن', 'است', 'بود']
        
        words = text.split()
        keywords = []
        
        for word in words:
            word = word.strip('.,!?():"')
            if (len(word) > 2 and 
                word not in stop_words and 
                word in self.medical_terms):
                keywords.append(word)
        
        return list(set(keywords))
    
    def _analyze_sentiment(self, text: str) -> str:
        """تحلیل احساسات متن"""
        # الگوهای ساده برای تحلیل احساسات
        positive_words = ['خوب', 'بهتر', 'مثبت', 'عالی', 'راحت']
        negative_words = ['بد', 'درد', 'مشکل', 'ناراحت', 'منفی', 'سخت']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _calculate_medical_relevance(self, text: str, entities: List[MedicalEntity]) -> float:
        """محاسبه میزان ارتباط با حوزه پزشکی"""
        medical_word_count = 0
        total_words = len(text.split())
        
        if total_words == 0:
            return 0.0
        
        # شمارش کلمات پزشکی
        for word in text.split():
            if word.strip('.,!?():"') in self.medical_terms:
                medical_word_count += 1
        
        # اضافه کردن امتیاز موجودیت‌ها
        entity_score = len(entities) * 0.1
        
        relevance = (medical_word_count / total_words) + entity_score
        return min(relevance, 1.0)
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """تقسیم متن به جملات"""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _rank_sentences_by_importance(self, sentences: List[str]) -> List[str]:
        """رتبه‌بندی جملات بر اساس اهمیت"""
        scored_sentences = []
        
        for sentence in sentences:
            score = 0
            
            # امتیاز بر اساس وجود کلمات پزشکی
            medical_words = sum(1 for word in sentence.split() 
                              if word.strip('.,!?():"') in self.medical_terms)
            score += medical_words * 2
            
            # امتیاز بر اساس طول جمله
            score += len(sentence.split()) * 0.1
            
            scored_sentences.append((score, sentence))
        
        # مرتب‌سازی بر اساس امتیاز
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        return [sentence for score, sentence in scored_sentences]
    
    def _check_inappropriate_content(self, text: str) -> List[str]:
        """بررسی محتوای نامناسب"""
        # لیست کلمات نامناسب (باید گسترده‌تر شود)
        inappropriate_words = ['کلمه نامناسب 1', 'کلمه نامناسب 2']
        
        found_words = []
        for word in inappropriate_words:
            if word in text.lower():
                found_words.append(word)
        
        return found_words
    
    def _has_poor_language_quality(self, text: str) -> bool:
        """بررسی کیفیت زبان"""
        # بررسی‌های ساده کیفیت
        
        # نسبت کاراکترهای تکراری
        repeated_chars = len(re.findall(r'(.)\1{3,}', text))
        if repeated_chars > len(text) * 0.1:
            return True
        
        # نسبت اعداد به حروف
        digit_ratio = len(re.findall(r'\d', text)) / max(len(text), 1)
        if digit_ratio > 0.3:
            return True
        
        return False
    
    def _load_medical_terms(self) -> set:
        """بارگذاری اصطلاحات پزشکی"""
        # در پیاده‌سازی واقعی، این از دیتابیس یا فایل بارگذاری می‌شود
        return {
            'پزشک', 'بیمار', 'درمان', 'دارو', 'بیمارستان', 'مطب',
            'معاینه', 'تشخیص', 'علائم', 'نسخه', 'آزمایش', 'رادیولوژی',
            'جراحی', 'عمل', 'بیهوشی', 'تب', 'سردرد', 'درد', 'سرفه',
            'تنگی نفس', 'فشار خون', 'دیابت', 'کلسترول', 'قلب'
        }
    
    def _load_symptom_keywords(self) -> set:
        """بارگذاری کلیدواژه‌های علائم"""
        return {
            'سردرد', 'تب', 'سرفه', 'درد شکم', 'تهوع', 'سرگیجه',
            'ضعف', 'خستگی', 'درد سینه', 'تنگی نفس', 'اسهال', 'یبوست'
        }
    
    def _load_drug_names(self) -> set:
        """بارگذاری نام داروها"""
        return {
            'استامینوفن', 'ایبوپروفن', 'آسپرین', 'آنتی‌بیوتیک',
            'قرص', 'شربت', 'آمپول', 'کپسول', 'قطره'
        }