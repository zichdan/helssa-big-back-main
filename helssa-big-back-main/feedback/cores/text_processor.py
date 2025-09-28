"""
Text Processor Core برای feedback app
پردازش متن و تحلیل محتوای بازخورد
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

# Import core if available
try:
    from app_standards.four_cores.text_processor import TextProcessorCore, TextProcessingResult
except ImportError:
    # Fallback if app_standards doesn't exist
    @dataclass
    class TextProcessingResult:
        processed_text: str
        sentiment: Optional[str] = None
        keywords: List[str] = None
        metadata: Dict[str, Any] = None
    
    class TextProcessorCore:
        def __init__(self):
            self.logger = logging.getLogger(__name__)


class FeedbackTextProcessorCore(TextProcessorCore):
    """
    هسته پردازش متن برای تحلیل بازخورد و نظرات
    """
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # کلمات کلیدی مثبت فارسی
        self.positive_keywords = [
            'عالی', 'خوب', 'مفید', 'سریع', 'دقیق', 'کامل', 'راضی', 'موثر',
            'پاسخگو', 'حرفه‌ای', 'کیفیت', 'بهترین', 'فوق‌العاده', 'ممتاز',
            'توصیه', 'راحت', 'آسان', 'مناسب', 'کافی', 'رضایت‌بخش'
        ]
        
        # کلمات کلیدی منفی فارسی
        self.negative_keywords = [
            'بد', 'ضعیف', 'کند', 'نادرست', 'ناکامل', 'غیرمفید', 'مشکل',
            'خطا', 'اشتباه', 'نامناسب', 'ناراضی', 'کیفیت پایین', 'ضعیف',
            'بهبود', 'مشکل‌دار', 'ناکارآمد', 'غیرحرفه‌ای', 'سخت', 'پیچیده'
        ]
        
        # کلمات کلیدی مرتبط با درد و علائم
        self.medical_keywords = [
            'درد', 'تب', 'سردرد', 'تهوع', 'استفراغ', 'سرفه', 'تنگی نفس',
            'خستگی', 'ضعف', 'گیجی', 'سرگیجه', 'اسهال', 'یبوست', 'خارش',
            'ورم', 'قرمزی', 'خونریزی', 'مفصل', 'عضله', 'اضطراب', 'افسردگی'
        ]
    
    def analyze_feedback_sentiment(self, text: str) -> Dict[str, Any]:
        """
        تحلیل احساسات متن بازخورد
        
        Args:
            text: متن بازخورد
            
        Returns:
            dict: نتیجه تحلیل احساسات
        """
        try:
            if not text or not text.strip():
                return {
                    'sentiment': 'neutral',
                    'confidence': 0.0,
                    'positive_score': 0.0,
                    'negative_score': 0.0
                }
            
            text_clean = self._clean_text(text)
            words = text_clean.split()
            
            # شمارش کلمات مثبت و منفی
            positive_count = sum(1 for word in words if word in self.positive_keywords)
            negative_count = sum(1 for word in words if word in self.negative_keywords)
            
            total_words = len(words)
            positive_score = positive_count / total_words if total_words > 0 else 0
            negative_score = negative_count / total_words if total_words > 0 else 0
            
            # تعیین احساس کلی
            if positive_score > negative_score:
                sentiment = 'positive'
                confidence = positive_score
            elif negative_score > positive_score:
                sentiment = 'negative'
                confidence = negative_score
            else:
                sentiment = 'neutral'
                confidence = 0.5
            
            return {
                'sentiment': sentiment,
                'confidence': min(confidence * 2, 1.0),  # نرمال‌سازی
                'positive_score': positive_score,
                'negative_score': negative_score,
                'positive_words': positive_count,
                'negative_words': negative_count
            }
            
        except Exception as e:
            self.logger.error(f"Error in sentiment analysis: {str(e)}")
            return {
                'sentiment': 'neutral',
                'confidence': 0.0,
                'positive_score': 0.0,
                'negative_score': 0.0
            }
    
    def extract_feedback_keywords(self, text: str) -> List[str]:
        """
        استخراج کلمات کلیدی از متن بازخورد
        
        Args:
            text: متن بازخورد
            
        Returns:
            list: فهرست کلمات کلیدی
        """
        try:
            if not text or not text.strip():
                return []
            
            text_clean = self._clean_text(text)
            words = text_clean.split()
            
            # استخراج کلمات کلیدی
            keywords = []
            
            # کلمات مثبت و منفی
            for word in words:
                if word in self.positive_keywords or word in self.negative_keywords:
                    keywords.append(word)
            
            # کلمات پزشکی
            for word in words:
                if word in self.medical_keywords:
                    keywords.append(word)
            
            # حذف تکراری
            keywords = list(set(keywords))
            
            return keywords
            
        except Exception as e:
            self.logger.error(f"Error extracting keywords: {str(e)}")
            return []
    
    def analyze_improvement_suggestions(self, text: str) -> Dict[str, Any]:
        """
        تحلیل پیشنهادات بهبود در متن
        
        Args:
            text: متن حاوی پیشنهادات
            
        Returns:
            dict: تحلیل پیشنهادات
        """
        try:
            if not text or not text.strip():
                return {
                    'has_suggestions': False,
                    'categories': [],
                    'urgency': 'low'
                }
            
            text_clean = self._clean_text(text)
            
            # الگوهای پیشنهاد
            suggestion_patterns = [
                r'پیشنهاد\s+می‌?کنم',
                r'بهتر\s+است',
                r'باید\s+.*\s+شود',
                r'لازم\s+است',
                r'بهبود\s+.*\s+نیاز',
                r'اضافه\s+کردن',
                r'حذف\s+کردن'
            ]
            
            has_suggestions = any(re.search(pattern, text_clean) for pattern in suggestion_patterns)
            
            # دسته‌بندی پیشنهادات
            categories = []
            category_keywords = {
                'ui_ux': ['رابط', 'طراحی', 'نمایش', 'دکمه', 'منو', 'صفحه'],
                'performance': ['سرعت', 'کندی', 'بارگذاری', 'انتظار', 'تاخیر'],
                'content': ['محتوا', 'اطلاعات', 'متن', 'توضیح', 'راهنما'],
                'features': ['قابلیت', 'امکان', 'ویژگی', 'عملکرد', 'کارکرد'],
                'medical': ['پزشکی', 'تشخیص', 'درمان', 'دارو', 'بیماری']
            }
            
            for category, keywords in category_keywords.items():
                if any(keyword in text_clean for keyword in keywords):
                    categories.append(category)
            
            # تعیین فوریت
            urgency_keywords = {
                'high': ['فوری', 'ضروری', 'بحرانی', 'خطرناک', 'مهم'],
                'medium': ['لازم', 'مفید', 'بهتر', 'ترجیح'],
                'low': ['پیشنهاد', 'ممکن', 'اختیاری']
            }
            
            urgency = 'low'
            for level, keywords in urgency_keywords.items():
                if any(keyword in text_clean for keyword in keywords):
                    urgency = level
                    break
            
            return {
                'has_suggestions': has_suggestions,
                'categories': categories,
                'urgency': urgency,
                'keywords_found': self.extract_feedback_keywords(text)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing suggestions: {str(e)}")
            return {
                'has_suggestions': False,
                'categories': [],
                'urgency': 'low'
            }
    
    def detect_medical_concerns(self, text: str) -> Dict[str, Any]:
        """
        تشخیص نگرانی‌های پزشکی در متن
        
        Args:
            text: متن بازخورد
            
        Returns:
            dict: تحلیل نگرانی‌های پزشکی
        """
        try:
            if not text or not text.strip():
                return {
                    'has_medical_concerns': False,
                    'symptoms_mentioned': [],
                    'urgency_level': 0
                }
            
            text_clean = self._clean_text(text)
            
            # تشخیص علائم ذکر شده
            symptoms_mentioned = []
            for symptom in self.medical_keywords:
                if symptom in text_clean:
                    symptoms_mentioned.append(symptom)
            
            # تعیین سطح فوریت
            urgent_patterns = [
                r'درد\s+شدید', r'تب\s+بالا', r'تنگی\s+نفس\s+شدید',
                r'خونریزی', r'بیهوشی', r'تشنج'
            ]
            
            urgency_level = 0
            if any(re.search(pattern, text_clean) for pattern in urgent_patterns):
                urgency_level = 3  # فوری
            elif len(symptoms_mentioned) > 2:
                urgency_level = 2  # متوسط
            elif len(symptoms_mentioned) > 0:
                urgency_level = 1  # پایین
            
            return {
                'has_medical_concerns': len(symptoms_mentioned) > 0,
                'symptoms_mentioned': symptoms_mentioned,
                'urgency_level': urgency_level,
                'requires_followup': urgency_level >= 2
            }
            
        except Exception as e:
            self.logger.error(f"Error detecting medical concerns: {str(e)}")
            return {
                'has_medical_concerns': False,
                'symptoms_mentioned': [],
                'urgency_level': 0
            }
    
    def process_feedback_text(self, text: str, feedback_type: str = 'general') -> TextProcessingResult:
        """
        پردازش کامل متن بازخورد
        
        Args:
            text: متن بازخورد
            feedback_type: نوع بازخورد
            
        Returns:
            TextProcessingResult: نتیجه پردازش
        """
        try:
            if not text or not text.strip():
                return TextProcessingResult(
                    processed_text="",
                    sentiment="neutral",
                    keywords=[],
                    metadata={}
                )
            
            # تمیز کردن متن
            processed_text = self._clean_text(text)
            
            # تحلیل احساسات
            sentiment_analysis = self.analyze_feedback_sentiment(text)
            
            # استخراج کلمات کلیدی
            keywords = self.extract_feedback_keywords(text)
            
            # تحلیل پیشنهادات
            suggestions_analysis = self.analyze_improvement_suggestions(text)
            
            # تشخیص نگرانی‌های پزشکی
            medical_analysis = self.detect_medical_concerns(text)
            
            # متادیتا
            metadata = {
                'sentiment_analysis': sentiment_analysis,
                'suggestions': suggestions_analysis,
                'medical_concerns': medical_analysis,
                'text_length': len(text),
                'word_count': len(text.split()),
                'feedback_type': feedback_type
            }
            
            return TextProcessingResult(
                processed_text=processed_text,
                sentiment=sentiment_analysis['sentiment'],
                keywords=keywords,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Error processing feedback text: {str(e)}")
            return TextProcessingResult(
                processed_text=text,
                sentiment="neutral",
                keywords=[],
                metadata={'error': str(e)}
            )
    
    def _clean_text(self, text: str) -> str:
        """
        تمیز کردن متن
        
        Args:
            text: متن خام
            
        Returns:
            str: متن تمیز شده
        """
        if not text:
            return ""
        
        # حذف کاراکترهای اضافی
        text = re.sub(r'\s+', ' ', text)  # چندین space به یکی
        text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)  # حفظ فارسی و انگلیسی
        text = text.strip()
        
        return text
    
    def summarize_feedback_batch(self, feedbacks: List[str]) -> Dict[str, Any]:
        """
        خلاصه‌سازی مجموعه‌ای از بازخوردها
        
        Args:
            feedbacks: فهرست بازخوردها
            
        Returns:
            dict: خلاصه تحلیل
        """
        try:
            if not feedbacks:
                return {
                    'total_count': 0,
                    'sentiment_summary': {},
                    'common_keywords': [],
                    'improvement_areas': []
                }
            
            # تحلیل تمام بازخوردها
            all_sentiments = []
            all_keywords = []
            all_categories = []
            
            for feedback in feedbacks:
                result = self.process_feedback_text(feedback)
                all_sentiments.append(result.sentiment)
                all_keywords.extend(result.keywords)
                
                if result.metadata and 'suggestions' in result.metadata:
                    all_categories.extend(result.metadata['suggestions']['categories'])
            
            # خلاصه احساسات
            sentiment_counts = {}
            for sentiment in all_sentiments:
                sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
            
            # کلمات پرتکرار
            keyword_counts = {}
            for keyword in all_keywords:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
            
            common_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # حوزه‌های بهبود
            category_counts = {}
            for category in all_categories:
                category_counts[category] = category_counts.get(category, 0) + 1
            
            improvement_areas = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
            
            return {
                'total_count': len(feedbacks),
                'sentiment_summary': sentiment_counts,
                'common_keywords': common_keywords,
                'improvement_areas': improvement_areas,
                'positive_percentage': (sentiment_counts.get('positive', 0) / len(feedbacks)) * 100,
                'negative_percentage': (sentiment_counts.get('negative', 0) / len(feedbacks)) * 100
            }
            
        except Exception as e:
            self.logger.error(f"Error summarizing feedback batch: {str(e)}")
            return {
                'total_count': 0,
                'sentiment_summary': {},
                'common_keywords': [],
                'improvement_areas': [],
                'error': str(e)
            }