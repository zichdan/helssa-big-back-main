"""
هسته Text Processor - پردازش متن‌ها
"""
import logging
import json
from typing import Dict, List, Tuple, Any, Optional
from django.conf import settings


logger = logging.getLogger(__name__)


class TextProcessorCore:
    """
    هسته پردازش متن‌ها
    
    این کلاس مسئول پردازش، تحلیل و transformation متن‌ها است
    """
    
    def __init__(self):
        """مقداردهی اولیه هسته Text Processor"""
        self.logger = logging.getLogger(__name__)
        self.max_text_length = getattr(settings, 'MAX_TEXT_LENGTH', 50000)
        self.supported_languages = ['fa', 'en', 'ar']
        
    def process_text(self, text: str, options: Optional[Dict[str, Any]] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        پردازش اصلی متن
        
        Args:
            text: متن ورودی
            options: تنظیمات اضافی پردازش
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (موفقیت، نتیجه/خطا)
        """
        try:
            if not text or not isinstance(text, str):
                return False, {
                    'error': 'Invalid text input',
                    'message': 'متن ورودی نامعتبر است'
                }
            
            # بررسی طول متن
            if len(text) > self.max_text_length:
                return False, {
                    'error': 'Text too long',
                    'message': 'متن بیش از حد مجاز بلند است',
                    'max_length': self.max_text_length,
                    'actual_length': len(text)
                }
            
            options = options or {}
            
            # انجام پردازش‌های مختلف
            result = {
                'original_text': text,
                'length': len(text),
                'language': self._detect_language(text),
                'cleaned_text': self._clean_text(text),
                'keywords': self._extract_keywords(text),
                'sentiment': self._analyze_sentiment(text),
                'entities': self._extract_entities(text),
                'summary': self._generate_summary(text, options.get('summary_length', 100))
            }
            
            # پردازش‌های اضافی بر اساس options
            if options.get('include_stats', False):
                result['stats'] = self._get_text_stats(text)
            
            if options.get('normalize', False):
                result['normalized_text'] = self._normalize_text(text)
            
            self.logger.info(
                'Text processed successfully',
                extra={
                    'text_length': len(text),
                    'language': result['language'],
                    'keywords_count': len(result['keywords'])
                }
            )
            
            return True, result
            
        except Exception as e:
            self.logger.error(f"Text processing error: {str(e)}")
            return False, {
                'error': 'Processing failed',
                'message': 'خطا در پردازش متن',
                'details': str(e)
            }
    
    def _detect_language(self, text: str) -> str:
        """
        تشخیص زبان متن
        
        Args:
            text: متن ورودی
            
        Returns:
            str: کد زبان تشخیص داده شده
        """
        try:
            # الگوریتم ساده تشخیص زبان بر اساس کاراکترها
            persian_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
            arabic_chars = sum(1 for c in text if '\u0750' <= c <= '\u077F')
            english_chars = sum(1 for c in text if c.isascii() and c.isalpha())
            
            total_chars = persian_chars + arabic_chars + english_chars
            
            if total_chars == 0:
                return 'unknown'
            
            if persian_chars / total_chars > 0.3:
                return 'fa'
            elif arabic_chars / total_chars > 0.3:
                return 'ar'
            elif english_chars / total_chars > 0.5:
                return 'en'
            else:
                return 'mixed'
                
        except Exception:
            return 'unknown'
    
    def _clean_text(self, text: str) -> str:
        """
        پاکسازی متن از کاراکترهای ناخواسته
        
        Args:
            text: متن ورودی
            
        Returns:
            str: متن پاکسازی شده
        """
        try:
            import re
            
            # حذف کاراکترهای کنترلی
            text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
            
            # نرمال‌سازی فاصله‌ها
            text = re.sub(r'\s+', ' ', text)
            
            # حذف فاصله‌های ابتدا و انتها
            text = text.strip()
            
            return text
            
        except Exception:
            return text
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        استخراج کلیدواژه‌ها از متن
        
        Args:
            text: متن ورودی
            
        Returns:
            List[str]: لیست کلیدواژه‌ها
        """
        try:
            import re
            
            # الگوریتم ساده استخراج کلیدواژه
            words = re.findall(r'\b\w{3,}\b', text.lower())
            
            # حذف stop words فارسی و انگلیسی
            stop_words = {
                'fa': {'از', 'به', 'در', 'با', 'که', 'این', 'آن', 'را', 'است', 'های', 'برای', 'تا'},
                'en': {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            }
            
            language = self._detect_language(text)
            stop_set = stop_words.get(language, set()) | stop_words.get('en', set())
            
            # فیلتر کردن کلمات
            keywords = [word for word in words if word not in stop_set and len(word) > 2]
            
            # شمارش فراوانی و برگرداندن محبوب‌ترین‌ها
            from collections import Counter
            word_counts = Counter(keywords)
            
            return [word for word, count in word_counts.most_common(10)]
            
        except Exception:
            return []
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        تحلیل احساسات متن
        
        Args:
            text: متن ورودی
            
        Returns:
            Dict[str, Any]: نتیجه تحلیل احساسات
        """
        try:
            # الگوریتم ساده تحلیل احساسات
            positive_words = {'خوب', 'عالی', 'بهترین', 'موفق', 'good', 'great', 'excellent', 'amazing'}
            negative_words = {'بد', 'بدترین', 'ضعیف', 'ناموفق', 'bad', 'terrible', 'awful', 'poor'}
            
            words = text.lower().split()
            
            positive_count = sum(1 for word in words if word in positive_words)
            negative_count = sum(1 for word in words if word in negative_words)
            
            total_sentiment_words = positive_count + negative_count
            
            if total_sentiment_words == 0:
                return {
                    'sentiment': 'neutral',
                    'confidence': 0.5,
                    'positive_score': 0,
                    'negative_score': 0
                }
            
            positive_ratio = positive_count / total_sentiment_words
            
            if positive_ratio > 0.6:
                sentiment = 'positive'
                confidence = positive_ratio
            elif positive_ratio < 0.4:
                sentiment = 'negative'  
                confidence = 1 - positive_ratio
            else:
                sentiment = 'neutral'
                confidence = 0.5
            
            return {
                'sentiment': sentiment,
                'confidence': confidence,
                'positive_score': positive_count,
                'negative_score': negative_count
            }
            
        except Exception:
            return {
                'sentiment': 'unknown',
                'confidence': 0,
                'positive_score': 0,
                'negative_score': 0
            }
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        استخراج موجودیت‌ها از متن
        
        Args:
            text: متن ورودی
            
        Returns:
            List[Dict[str, Any]]: لیست موجودیت‌های استخراج شده
        """
        try:
            import re
            entities = []
            
            # تشخیص شماره تلفن
            phone_pattern = r'09\d{9}'
            phones = re.findall(phone_pattern, text)
            for phone in phones:
                entities.append({
                    'type': 'phone',
                    'value': phone,
                    'confidence': 0.9
                })
            
            # تشخیص ایمیل
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, text)
            for email in emails:
                entities.append({
                    'type': 'email',
                    'value': email,
                    'confidence': 0.95
                })
            
            # تشخیص تاریخ فارسی
            date_pattern = r'\d{4}/\d{1,2}/\d{1,2}'
            dates = re.findall(date_pattern, text)
            for date in dates:
                entities.append({
                    'type': 'date',
                    'value': date,
                    'confidence': 0.8
                })
            
            return entities
            
        except Exception:
            return []
    
    def _generate_summary(self, text: str, max_length: int = 100) -> str:
        """
        تولید خلاصه از متن
        
        Args:
            text: متن ورودی
            max_length: حداکثر طول خلاصه
            
        Returns:
            str: خلاصه متن
        """
        try:
            if len(text) <= max_length:
                return text
            
            # الگوریتم ساده خلاصه‌سازی
            sentences = text.split('.')
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if not sentences:
                return text[:max_length] + '...'
            
            # انتخاب جملات مهم بر اساس طول و موقعیت
            important_sentences = []
            current_length = 0
            
            # اولویت به جملات اول و آخر
            priority_sentences = [sentences[0]]
            if len(sentences) > 1:
                priority_sentences.append(sentences[-1])
            
            for sentence in priority_sentences:
                if current_length + len(sentence) <= max_length:
                    important_sentences.append(sentence)
                    current_length += len(sentence)
                else:
                    break
            
            summary = '. '.join(important_sentences)
            if len(summary) > max_length:
                summary = summary[:max_length] + '...'
            
            return summary
            
        except Exception:
            return text[:max_length] + '...' if len(text) > max_length else text
    
    def _get_text_stats(self, text: str) -> Dict[str, Any]:
        """
        دریافت آمار متن
        
        Args:
            text: متن ورودی
            
        Returns:
            Dict[str, Any]: آمار متن
        """
        try:
            import re
            
            words = re.findall(r'\b\w+\b', text)
            sentences = text.split('.')
            paragraphs = text.split('\n\n')
            
            return {
                'characters': len(text),
                'characters_no_spaces': len(text.replace(' ', '')),
                'words': len(words),
                'sentences': len([s for s in sentences if s.strip()]),
                'paragraphs': len([p for p in paragraphs if p.strip()]),
                'avg_word_length': sum(len(word) for word in words) / len(words) if words else 0,
                'avg_sentence_length': len(words) / len(sentences) if sentences else 0
            }
            
        except Exception:
            return {}
    
    def _normalize_text(self, text: str) -> str:
        """
        نرمال‌سازی متن
        
        Args:
            text: متن ورودی
            
        Returns:
            str: متن نرمال‌سازی شده
        """
        try:
            import re
            
            # نرمال‌سازی فاصله‌ها
            text = re.sub(r'\s+', ' ', text)
            
            # نرمال‌سازی نقطه‌گذاری
            text = re.sub(r'[۰-۹]', lambda m: str(ord(m.group()) - ord('۰')), text)  # تبدیل اعداد فارسی
            
            # نرمال‌سازی یای فارسی
            text = text.replace('ي', 'ی').replace('ك', 'ک')
            
            return text.strip()
            
        except Exception:
            return text