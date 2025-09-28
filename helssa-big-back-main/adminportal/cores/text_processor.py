"""
هسته پردازش متن پنل ادمین
AdminPortal Text Processor Core
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from django.utils import timezone
from django.core.cache import cache
import json


class TextProcessorCore:
    """
    هسته پردازش متن برای پنل ادمین
    مسئول تحلیل متن، جستجو، فیلتر و پردازش محتوا
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache_prefix = 'admin_text_processor'
        self.stop_words = [
            'و', 'در', 'به', 'از', 'که', 'با', 'برای', 'این', 'آن', 'یک', 'را', 'است',
            'کرد', 'شد', 'بود', 'های', 'خود', 'تا', 'بر', 'نیز', 'دو', 'چه', 'یا'
        ]
    
    def process_search_query(self, query: str, search_type: str = 'general') -> Dict:
        """
        پردازش query جستجو برای بهینه‌سازی
        
        Args:
            query: متن جستجو
            search_type: نوع جستجو (general, user, ticket, operation)
            
        Returns:
            Dict: query پردازش شده و متادیتا
        """
        try:
            # تمیز کردن query
            cleaned_query = self._clean_text(query)
            
            # تجزیه کلمات کلیدی
            keywords = self._extract_keywords(cleaned_query)
            
            # شناسایی فیلترها
            filters = self._extract_filters(query, search_type)
            
            # تولید regex patterns
            patterns = self._generate_search_patterns(keywords)
            
            result = {
                'original_query': query,
                'cleaned_query': cleaned_query,
                'keywords': keywords,
                'filters': filters,
                'patterns': patterns,
                'search_type': search_type,
                'processed_at': timezone.now().isoformat()
            }
            
            self.logger.info(f"Search query processed: {query} -> {len(keywords)} keywords")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Search query processing error: {str(e)}")
            return {
                'original_query': query,
                'error': str(e),
                'keywords': [query] if query else []
            }
    
    def analyze_admin_content(self, content: str, content_type: str = 'general') -> Dict:
        """
        تحلیل محتوای متنی برای ادمین
        
        Args:
            content: متن برای تحلیل
            content_type: نوع محتوا (ticket, operation, log, comment)
            
        Returns:
            Dict: نتایج تحلیل
        """
        try:
            analysis = {
                'content_type': content_type,
                'length': len(content),
                'word_count': len(content.split()),
                'keywords': [],
                'sentiment': 'neutral',
                'priority_indicators': [],
                'security_alerts': [],
                'entities': {},
                'summary': ''
            }
            
            # استخراج کلمات کلیدی
            analysis['keywords'] = self._extract_keywords(content)
            
            # تحلیل احساسات ساده
            analysis['sentiment'] = self._simple_sentiment_analysis(content)
            
            # شناسایی نشانه‌های اولویت
            analysis['priority_indicators'] = self._detect_priority_indicators(content)
            
            # هشدارهای امنیتی
            analysis['security_alerts'] = self._detect_security_alerts(content)
            
            # استخراج موجودیت‌ها
            analysis['entities'] = self._extract_entities(content)
            
            # خلاصه‌سازی
            analysis['summary'] = self._generate_summary(content)
            
            self.logger.info(f"Content analyzed: {content_type} - {analysis['word_count']} words")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Content analysis error: {str(e)}")
            return {'error': str(e), 'content_type': content_type}
    
    def filter_sensitive_content(self, content: str, filter_level: str = 'medium') -> Dict:
        """
        فیلتر محتوای حساس
        
        Args:
            content: متن برای فیلتر
            filter_level: سطح فیلتر (low, medium, high)
            
        Returns:
            Dict: محتوای فیلتر شده و گزارش
        """
        try:
            # الگوهای حساس
            sensitive_patterns = {
                'low': [
                    r'\b\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\b',  # شماره کارت
                    r'\b\d{10,11}\b',  # شماره موبایل
                ],
                'medium': [
                    r'\b\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\b',  # شماره کارت
                    r'\b\d{10,11}\b',  # شماره موبایل
                    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # ایمیل
                    r'\bکد\s*ملی\s*:?\s*\d{10}\b',  # کد ملی
                ],
                'high': [
                    r'\b\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\b',  # شماره کارت
                    r'\b\d{10,11}\b',  # شماره موبایل
                    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # ایمیل
                    r'\bکد\s*ملی\s*:?\s*\d{10}\b',  # کد ملی
                    r'\bرمز\s*عبور\s*:?\s*\S+\b',  # رمز عبور
                    r'\bpassword\s*:?\s*\S+\b',  # password
                ]
            }
            
            patterns = sensitive_patterns.get(filter_level, sensitive_patterns['medium'])
            filtered_content = content
            detected_items = []
            
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    detected_items.append({
                        'type': self._classify_sensitive_data(match.group()),
                        'position': match.span(),
                        'text': match.group()
                    })
                    # جایگزینی با ستاره
                    filtered_content = re.sub(
                        pattern, 
                        lambda m: '*' * len(m.group()), 
                        filtered_content, 
                        flags=re.IGNORECASE
                    )
            
            result = {
                'original_content': content,
                'filtered_content': filtered_content,
                'filter_level': filter_level,
                'detected_items': detected_items,
                'is_sensitive': len(detected_items) > 0,
                'processed_at': timezone.now().isoformat()
            }
            
            if detected_items:
                self.logger.warning(f"Sensitive content detected: {len(detected_items)} items")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Content filtering error: {str(e)}")
            return {
                'original_content': content,
                'filtered_content': content,
                'error': str(e)
            }
    
    def generate_report_summary(self, data: List[Dict], report_type: str) -> Dict:
        """
        تولید خلاصه گزارش از داده‌ها
        
        Args:
            data: لیست داده‌ها
            report_type: نوع گزارش
            
        Returns:
            Dict: خلاصه گزارش
        """
        try:
            summary = {
                'report_type': report_type,
                'total_items': len(data),
                'generated_at': timezone.now().isoformat(),
                'statistics': {},
                'key_insights': [],
                'recommendations': []
            }
            
            if report_type == 'support_tickets':
                summary.update(self._summarize_tickets(data))
            elif report_type == 'system_operations':
                summary.update(self._summarize_operations(data))
            elif report_type == 'user_activities':
                summary.update(self._summarize_user_activities(data))
            elif report_type == 'system_metrics':
                summary.update(self._summarize_metrics(data))
            
            self.logger.info(f"Report summary generated: {report_type} - {len(data)} items")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Report summary generation error: {str(e)}")
            return {'error': str(e), 'report_type': report_type}
    
    def _clean_text(self, text: str) -> str:
        """تمیز کردن متن"""
        if not text:
            return ""
        
        # حذف کاراکترهای اضافی
        text = re.sub(r'\s+', ' ', text.strip())
        
        # حذف کاراکترهای خاص
        text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)
        
        return text
    
    def _extract_keywords(self, text: str) -> List[str]:
        """استخراج کلمات کلیدی"""
        if not text:
            return []
        
        words = text.split()
        keywords = []
        
        for word in words:
            word = word.strip()
            if len(word) > 2 and word not in self.stop_words:
                keywords.append(word)
        
        # حذف تکراری‌ها
        return list(set(keywords))
    
    def _extract_filters(self, query: str, search_type: str) -> Dict:
        """استخراج فیلترها از query"""
        filters = {}
        
        # الگوهای فیلتر
        filter_patterns = {
            'date': r'تاریخ\s*:?\s*(\d{4}[-/]\d{2}[-/]\d{2})',
            'status': r'وضعیت\s*:?\s*(\w+)',
            'priority': r'اولویت\s*:?\s*(\w+)',
            'user': r'کاربر\s*:?\s*(\w+)',
            'type': r'نوع\s*:?\s*(\w+)'
        }
        
        for filter_name, pattern in filter_patterns.items():
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                filters[filter_name] = match.group(1)
        
        return filters
    
    def _generate_search_patterns(self, keywords: List[str]) -> List[str]:
        """تولید patterns جستجو"""
        patterns = []
        
        for keyword in keywords:
            # Pattern دقیق
            patterns.append(rf'\b{re.escape(keyword)}\b')
            
            # Pattern فازی (برای کلمات فارسی)
            if len(keyword) > 3:
                patterns.append(rf'{re.escape(keyword[:-1])}.*')
        
        return patterns
    
    def _simple_sentiment_analysis(self, content: str) -> str:
        """تحلیل ساده احساسات"""
        positive_words = ['خوب', 'عالی', 'مثبت', 'راضی', 'موافق', 'بهتر']
        negative_words = ['بد', 'ضعیف', 'منفی', 'ناراضی', 'مخالف', 'مشکل', 'خطا']
        
        content_lower = content.lower()
        
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _detect_priority_indicators(self, content: str) -> List[str]:
        """شناسایی نشانه‌های اولویت"""
        high_priority_patterns = [
            r'\bفوری\b', r'\bضروری\b', r'\bبحرانی\b', r'\bخطا\b',
            r'\bمشکل\s+جدی\b', r'\bخرابی\b', r'\bقطع\s+سرویس\b'
        ]
        
        indicators = []
        content_lower = content.lower()
        
        for pattern in high_priority_patterns:
            if re.search(pattern, content_lower):
                indicators.append(pattern.replace('\\b', '').replace('\\s+', ' '))
        
        return indicators
    
    def _detect_security_alerts(self, content: str) -> List[str]:
        """شناسایی هشدارهای امنیتی"""
        security_patterns = [
            r'\bهک\b', r'\bنفوذ\b', r'\bباج\s*افزار\b', r'\bویروس\b',
            r'\bدسترسی\s+غیرمجاز\b', r'\bنقض\s+امنیت\b', r'\bداده\s+درز\b'
        ]
        
        alerts = []
        content_lower = content.lower()
        
        for pattern in security_patterns:
            if re.search(pattern, content_lower):
                alerts.append(pattern.replace('\\b', '').replace('\\s+', ' '))
        
        return alerts
    
    def _extract_entities(self, content: str) -> Dict:
        """استخراج موجودیت‌ها"""
        entities = {
            'phone_numbers': [],
            'emails': [],
            'dates': [],
            'numbers': []
        }
        
        # شماره تلفن
        phone_pattern = r'\b09\d{9}\b'
        entities['phone_numbers'] = re.findall(phone_pattern, content)
        
        # ایمیل
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        entities['emails'] = re.findall(email_pattern, content, re.IGNORECASE)
        
        # تاریخ
        date_pattern = r'\b\d{4}[-/]\d{2}[-/]\d{2}\b'
        entities['dates'] = re.findall(date_pattern, content)
        
        # اعداد
        number_pattern = r'\b\d+\b'
        entities['numbers'] = re.findall(number_pattern, content)
        
        return entities
    
    def _generate_summary(self, content: str, max_length: int = 200) -> str:
        """تولید خلاصه متن"""
        if len(content) <= max_length:
            return content
        
        sentences = content.split('.')
        summary = ""
        
        for sentence in sentences:
            if len(summary + sentence) <= max_length:
                summary += sentence + "."
            else:
                break
        
        return summary.strip() or content[:max_length] + "..."
    
    def _classify_sensitive_data(self, text: str) -> str:
        """تشخیص نوع داده حساس"""
        if re.match(r'\b\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\b', text):
            return 'card_number'
        elif re.match(r'\b09\d{9}\b', text):
            return 'phone_number'
        elif re.match(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text):
            return 'email'
        elif 'کد ملی' in text or 'ملی' in text:
            return 'national_id'
        elif 'رمز' in text or 'password' in text.lower():
            return 'password'
        else:
            return 'unknown'
    
    def _summarize_tickets(self, tickets: List[Dict]) -> Dict:
        """خلاصه‌سازی تیکت‌ها"""
        status_counts = {}
        priority_counts = {}
        category_counts = {}
        
        for ticket in tickets:
            status = ticket.get('status', 'unknown')
            priority = ticket.get('priority', 'unknown')
            category = ticket.get('category', 'unknown')
            
            status_counts[status] = status_counts.get(status, 0) + 1
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            'statistics': {
                'by_status': status_counts,
                'by_priority': priority_counts,
                'by_category': category_counts
            },
            'key_insights': [
                f"بیشترین تیکت‌ها در وضعیت {max(status_counts, key=status_counts.get)}",
                f"اولویت غالب: {max(priority_counts, key=priority_counts.get)}"
            ]
        }
    
    def _summarize_operations(self, operations: List[Dict]) -> Dict:
        """خلاصه‌سازی عملیات"""
        type_counts = {}
        status_counts = {}
        
        for op in operations:
            op_type = op.get('operation_type', 'unknown')
            status = op.get('status', 'unknown')
            
            type_counts[op_type] = type_counts.get(op_type, 0) + 1
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'statistics': {
                'by_type': type_counts,
                'by_status': status_counts
            }
        }
    
    def _summarize_user_activities(self, activities: List[Dict]) -> Dict:
        """خلاصه‌سازی فعالیت‌های کاربری"""
        return {'statistics': {'total_activities': len(activities)}}
    
    def _summarize_metrics(self, metrics: List[Dict]) -> Dict:
        """خلاصه‌سازی متریک‌ها"""
        return {'statistics': {'total_metrics': len(metrics)}}