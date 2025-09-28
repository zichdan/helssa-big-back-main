"""
هسته پردازش صوت پنل ادمین
AdminPortal Speech Processor Core
"""

import logging
from typing import Dict, Optional, Tuple, Any
from django.core.files.base import ContentFile
from django.core.cache import cache
from django.utils import timezone
import base64
import json


class SpeechProcessorCore:
    """
    هسته پردازش صوت برای پنل ادمین
    مسئول تبدیل گفتار به متن، تحلیل صوت و پردازش فایل‌های صوتی
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache_prefix = 'admin_speech_processor'
        self.supported_formats = ['wav', 'mp3', 'ogg', 'webm', 'm4a']
        self.max_file_size = 10 * 1024 * 1024  # 10 MB
        self.max_duration = 300  # 5 minutes
    
    def process_voice_command(self, audio_data: bytes, format: str = 'wav') -> Dict:
        """
        پردازش دستور صوتی ادمین
        
        Args:
            audio_data: داده‌های صوتی
            format: فرمت فایل صوتی
            
        Returns:
            Dict: نتیجه پردازش
        """
        try:
            # اعتبارسنجی ورودی
            validation_result = self._validate_audio_input(audio_data, format)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['error'],
                    'message': validation_result['message']
                }
            
            # تبدیل گفتار به متن
            transcription_result = self._speech_to_text(audio_data, format)
            if not transcription_result['success']:
                return transcription_result
            
            text = transcription_result['text']
            confidence = transcription_result.get('confidence', 0.0)
            
            # تحلیل دستور
            command_analysis = self._analyze_voice_command(text)
            
            # ثبت لاگ
            self._log_voice_command(text, command_analysis, confidence)
            
            result = {
                'success': True,
                'transcription': {
                    'text': text,
                    'confidence': confidence,
                    'language': 'fa-IR'
                },
                'command_analysis': command_analysis,
                'processed_at': timezone.now().isoformat(),
                'audio_info': {
                    'format': format,
                    'size': len(audio_data),
                    'duration': validation_result.get('duration')
                }
            }
            
            self.logger.info(f"Voice command processed: '{text}' with confidence {confidence}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Voice command processing error: {str(e)}")
            return {
                'success': False,
                'error': 'processing_failed',
                'message': f'خطا در پردازش دستور صوتی: {str(e)}'
            }
    
    def transcribe_admin_note(self, audio_data: bytes, note_context: str = None) -> Dict:
        """
        تبدیل یادداشت صوتی ادمین به متن
        
        Args:
            audio_data: داده‌های صوتی
            note_context: زمینه یادداشت (ticket, operation, meeting)
            
        Returns:
            Dict: نتیجه تبدیل
        """
        try:
            # اعتبارسنجی
            validation_result = self._validate_audio_input(audio_data, 'wav')
            if not validation_result['valid']:
                return validation_result
            
            # تبدیل به متن
            transcription_result = self._speech_to_text(audio_data, 'wav')
            if not transcription_result['success']:
                return transcription_result
            
            text = transcription_result['text']
            
            # پردازش متن بر اساس زمینه
            processed_text = self._process_note_text(text, note_context)
            
            # استخراج کلمات کلیدی
            keywords = self._extract_audio_keywords(text)
            
            # تحلیل احساسات صوتی (ساده)
            sentiment = self._analyze_voice_sentiment(text)
            
            result = {
                'success': True,
                'original_text': text,
                'processed_text': processed_text,
                'keywords': keywords,
                'sentiment': sentiment,
                'context': note_context,
                'metadata': {
                    'confidence': transcription_result.get('confidence', 0.0),
                    'word_count': len(text.split()),
                    'estimated_duration': validation_result.get('duration'),
                    'processed_at': timezone.now().isoformat()
                }
            }
            
            self.logger.info(f"Admin note transcribed: {len(text)} characters, context: {note_context}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Admin note transcription error: {str(e)}")
            return {
                'success': False,
                'error': 'transcription_failed',
                'message': f'خطا در تبدیل یادداشت صوتی: {str(e)}'
            }
    
    def analyze_call_recording(self, audio_data: bytes, call_info: Dict = None) -> Dict:
        """
        تحلیل ضبط تماس پشتیبانی
        
        Args:
            audio_data: داده‌های صوتی تماس
            call_info: اطلاعات تماس
            
        Returns:
            Dict: نتایج تحلیل
        """
        try:
            # تبدیل کل تماس به متن
            transcription_result = self._speech_to_text(audio_data, 'wav')
            if not transcription_result['success']:
                return transcription_result
            
            full_text = transcription_result['text']
            
            # تقسیم بندی گفتگو (ساده)
            conversation_parts = self._segment_conversation(full_text)
            
            # تحلیل کیفیت پشتیبانی
            quality_analysis = self._analyze_support_quality(full_text)
            
            # استخراج مسائل مطرح شده
            identified_issues = self._extract_issues_from_call(full_text)
            
            # تحلیل احساسات مشتری
            customer_sentiment = self._analyze_customer_sentiment(full_text)
            
            # تولید خلاصه تماس
            call_summary = self._generate_call_summary(full_text, call_info)
            
            result = {
                'success': True,
                'call_info': call_info or {},
                'transcription': {
                    'full_text': full_text,
                    'word_count': len(full_text.split()),
                    'confidence': transcription_result.get('confidence', 0.0)
                },
                'conversation_analysis': {
                    'parts': conversation_parts,
                    'quality_score': quality_analysis['score'],
                    'quality_factors': quality_analysis['factors']
                },
                'issue_analysis': {
                    'identified_issues': identified_issues,
                    'customer_sentiment': customer_sentiment,
                    'resolution_status': self._assess_resolution_status(full_text)
                },
                'summary': call_summary,
                'recommendations': self._generate_support_recommendations(quality_analysis, identified_issues),
                'processed_at': timezone.now().isoformat()
            }
            
            self.logger.info(f"Call recording analyzed: {len(full_text)} characters, quality: {quality_analysis['score']}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Call recording analysis error: {str(e)}")
            return {
                'success': False,
                'error': 'analysis_failed',
                'message': f'خطا در تحلیل ضبط تماس: {str(e)}'
            }
    
    def generate_voice_summary(self, text_content: str, target_language: str = 'fa') -> Dict:
        """
        تولید خلاصه صوتی از متن
        
        Args:
            text_content: متن برای تبدیل به صوت
            target_language: زبان هدف
            
        Returns:
            Dict: نتیجه تولید صوت
        """
        try:
            # خلاصه‌سازی متن برای صوت
            summarized_text = self._prepare_text_for_speech(text_content)
            
            # تولید صوت (فعلاً شبیه‌سازی)
            audio_result = self._text_to_speech(summarized_text, target_language)
            
            if not audio_result['success']:
                return audio_result
            
            result = {
                'success': True,
                'original_text': text_content,
                'summarized_text': summarized_text,
                'audio_data': audio_result['audio_data'],
                'audio_info': {
                    'format': 'wav',
                    'duration': audio_result['duration'],
                    'size': len(audio_result['audio_data']),
                    'language': target_language
                },
                'generated_at': timezone.now().isoformat()
            }
            
            self.logger.info(f"Voice summary generated: {len(summarized_text)} characters")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Voice summary generation error: {str(e)}")
            return {
                'success': False,
                'error': 'generation_failed',
                'message': f'خطا در تولید خلاصه صوتی: {str(e)}'
            }
    
    def _validate_audio_input(self, audio_data: bytes, format: str) -> Dict:
        """اعتبارسنجی ورودی صوتی"""
        try:
            if not audio_data:
                return {
                    'valid': False,
                    'error': 'empty_audio',
                    'message': 'فایل صوتی خالی است'
                }
            
            if len(audio_data) > self.max_file_size:
                return {
                    'valid': False,
                    'error': 'file_too_large',
                    'message': f'حجم فایل بیش از {self.max_file_size // (1024*1024)} مگابایت'
                }
            
            if format.lower() not in self.supported_formats:
                return {
                    'valid': False,
                    'error': 'unsupported_format',
                    'message': f'فرمت {format} پشتیبانی نمی‌شود'
                }
            
            # تخمین مدت زمان (ساده)
            estimated_duration = len(audio_data) / (16000 * 2)  # 16kHz, 16-bit
            
            if estimated_duration > self.max_duration:
                return {
                    'valid': False,
                    'error': 'duration_too_long',
                    'message': f'مدت زمان فایل بیش از {self.max_duration} ثانیه'
                }
            
            return {
                'valid': True,
                'duration': estimated_duration,
                'size': len(audio_data)
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': 'validation_error',
                'message': f'خطا در اعتبارسنجی: {str(e)}'
            }
    
    def _speech_to_text(self, audio_data: bytes, format: str) -> Dict:
        """تبدیل گفتار به متن - شبیه‌سازی"""
        try:
            # در پیاده‌سازی واقعی، باید از سرویس STT استفاده شود
            # فعلاً شبیه‌سازی می‌کنیم
            
            # شبیه‌سازی تاخیر پردازش
            import time
            time.sleep(0.1)
            
            # متن نمونه بر اساس سایز فایل
            sample_texts = [
                "لطفاً وضعیت تیکت شماره یک دو سه را بررسی کنید",
                "نیاز به بررسی سیستم پرداخت داریم",
                "مشکل کاربر در بخش ورود به سیستم",
                "گزارش عملکرد روزانه را آماده کنید",
                "بررسی شکایت کاربر از سرویس پشتیبانی"
            ]
            
            # انتخاب متن بر اساس سایز
            size_index = min(len(audio_data) // 1000, len(sample_texts) - 1)
            text = sample_texts[size_index]
            
            # شبیه‌سازی confidence
            confidence = 0.85 + (0.1 * (size_index / len(sample_texts)))
            
            return {
                'success': True,
                'text': text,
                'confidence': min(confidence, 0.95),
                'language': 'fa-IR'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': 'stt_failed',
                'message': f'خطا در تبدیل گفتار به متن: {str(e)}'
            }
    
    def _analyze_voice_command(self, text: str) -> Dict:
        """تحلیل دستور صوتی"""
        command_patterns = {
            'search': ['جستجو', 'پیدا کن', 'بگرد'],
            'create': ['ایجاد', 'بساز', 'جدید'],
            'update': ['بروزرسانی', 'تغییر', 'ویرایش'],
            'delete': ['حذف', 'پاک کن'],
            'view': ['نمایش', 'نشان بده', 'ببین'],
            'report': ['گزارش', 'آمار', 'تحلیل']
        }
        
        detected_command = 'unknown'
        entities = []
        confidence = 0.0
        
        text_lower = text.lower()
        
        for command, patterns in command_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    detected_command = command
                    confidence = 0.8
                    break
            if confidence > 0:
                break
        
        # استخراج موجودیت‌ها
        import re
        numbers = re.findall(r'\d+', text)
        if numbers:
            entities.extend([{'type': 'number', 'value': num} for num in numbers])
        
        return {
            'command': detected_command,
            'confidence': confidence,
            'entities': entities,
            'raw_text': text
        }
    
    def _process_note_text(self, text: str, context: str) -> str:
        """پردازش متن یادداشت"""
        # تمیز کردن متن
        processed = text.strip()
        
        # افزودن برچسب زمینه
        if context:
            processed = f"[{context}] {processed}"
        
        # افزودن timestamp
        processed += f" - {timezone.now().strftime('%Y/%m/%d %H:%M')}"
        
        return processed
    
    def _extract_audio_keywords(self, text: str) -> list:
        """استخراج کلمات کلیدی از متن صوتی"""
        stop_words = {'و', 'در', 'به', 'از', 'که', 'با', 'برای', 'این', 'آن'}
        words = text.split()
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        return list(set(keywords))[:10]  # حداکثر 10 کلمه
    
    def _analyze_voice_sentiment(self, text: str) -> str:
        """تحلیل احساسات از متن صوتی"""
        positive_indicators = ['خوب', 'عالی', 'راضی', 'موثر']
        negative_indicators = ['بد', 'مشکل', 'خطا', 'ناراضی']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_indicators if word in text_lower)
        negative_count = sum(1 for word in negative_indicators if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        return 'neutral'
    
    def _segment_conversation(self, text: str) -> list:
        """تقسیم‌بندی گفتگو"""
        # تقسیم ساده بر اساس علامت‌های نقطه
        sentences = text.split('.')
        return [{'speaker': 'unknown', 'text': s.strip()} for s in sentences if s.strip()]
    
    def _analyze_support_quality(self, text: str) -> Dict:
        """تحلیل کیفیت پشتیبانی"""
        quality_indicators = {
            'politeness': ['لطفاً', 'متشکرم', 'خواهش می‌کنم'],
            'professionalism': ['بررسی می‌کنم', 'راه‌حل', 'پیگیری'],
            'responsiveness': ['فوراً', 'سریع', 'بلافاصله']
        }
        
        score = 0
        factors = {}
        
        text_lower = text.lower()
        for factor, indicators in quality_indicators.items():
            count = sum(1 for indicator in indicators if indicator in text_lower)
            factors[factor] = count
            score += count
        
        # نرمال‌سازی امتیاز
        max_possible = sum(len(indicators) for indicators in quality_indicators.values())
        normalized_score = min(score / max_possible * 100, 100) if max_possible > 0 else 0
        
        return {
            'score': round(normalized_score, 2),
            'factors': factors
        }
    
    def _extract_issues_from_call(self, text: str) -> list:
        """استخراج مسائل از تماس"""
        issue_keywords = ['مشکل', 'خطا', 'نمی‌توانم', 'کار نمی‌کند', 'قطع', 'کند']
        issues = []
        
        sentences = text.split('.')
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in issue_keywords):
                issues.append(sentence.strip())
        
        return issues[:5]  # حداکثر 5 مسئله
    
    def _analyze_customer_sentiment(self, text: str) -> Dict:
        """تحلیل احساسات مشتری"""
        satisfaction_indicators = {
            'very_satisfied': ['عالی', 'فوق‌العاده', 'بی‌نظیر'],
            'satisfied': ['خوب', 'راضی', 'مناسب'],
            'neutral': ['معمولی', 'متوسط'],
            'dissatisfied': ['بد', 'ناراضی', 'ضعیف'],
            'very_dissatisfied': ['افتضاح', 'وحشتناک', 'غیرقابل قبول']
        }
        
        text_lower = text.lower()
        sentiment_scores = {}
        
        for level, indicators in satisfaction_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text_lower)
            sentiment_scores[level] = score
        
        # تشخیص احساسات غالب
        dominant_sentiment = max(sentiment_scores, key=sentiment_scores.get)
        confidence = sentiment_scores[dominant_sentiment] / max(sum(sentiment_scores.values()), 1)
        
        return {
            'sentiment': dominant_sentiment,
            'confidence': round(confidence, 2),
            'scores': sentiment_scores
        }
    
    def _assess_resolution_status(self, text: str) -> str:
        """ارزیابی وضعیت حل مسئله"""
        resolution_indicators = ['حل شد', 'برطرف شد', 'رفع شد', 'درست شد']
        pending_indicators = ['بررسی می‌کنم', 'پیگیری', 'بعداً']
        
        text_lower = text.lower()
        
        if any(indicator in text_lower for indicator in resolution_indicators):
            return 'resolved'
        elif any(indicator in text_lower for indicator in pending_indicators):
            return 'pending'
        else:
            return 'unresolved'
    
    def _generate_call_summary(self, text: str, call_info: Dict) -> str:
        """تولید خلاصه تماس"""
        word_count = len(text.split())
        summary = f"تماس با {word_count} کلمه"
        
        if call_info:
            if 'duration' in call_info:
                summary += f"، مدت زمان: {call_info['duration']} ثانیه"
            if 'caller_id' in call_info:
                summary += f"، تماس‌گیرنده: {call_info['caller_id']}"
        
        return summary
    
    def _generate_support_recommendations(self, quality_analysis: Dict, issues: list) -> list:
        """تولید پیشنهادات بهبود پشتیبانی"""
        recommendations = []
        
        if quality_analysis['score'] < 50:
            recommendations.append("نیاز به بهبود کیفیت پشتیبانی")
        
        if len(issues) > 3:
            recommendations.append("تعداد زیادی مسئله مطرح شده - نیاز به بررسی دقیق‌تر")
        
        if quality_analysis['factors'].get('politeness', 0) < 2:
            recommendations.append("افزایش ادب و احترام در گفتگو")
        
        return recommendations
    
    def _prepare_text_for_speech(self, text: str) -> str:
        """آماده‌سازی متن برای تبدیل به صوت"""
        # خلاصه‌سازی متن طولانی
        if len(text) > 500:
            sentences = text.split('.')
            summarized = '. '.join(sentences[:3])
            return summarized + '.'
        return text
    
    def _text_to_speech(self, text: str, language: str) -> Dict:
        """تبدیل متن به صوت - شبیه‌سازی"""
        try:
            # شبیه‌سازی تولید صوت
            fake_audio_data = b'fake_audio_data_' + text.encode('utf-8')
            estimated_duration = len(text) * 0.1  # تخمین 0.1 ثانیه به ازای هر کاراکتر
            
            return {
                'success': True,
                'audio_data': fake_audio_data,
                'duration': estimated_duration,
                'format': 'wav'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': 'tts_failed',
                'message': f'خطا در تولید صوت: {str(e)}'
            }
    
    def _log_voice_command(self, text: str, analysis: Dict, confidence: float):
        """ثبت لاگ دستور صوتی"""
        self.logger.info(
            f"Voice command: '{text}' | "
            f"Command: {analysis['command']} | "
            f"Confidence: {confidence}"
        )