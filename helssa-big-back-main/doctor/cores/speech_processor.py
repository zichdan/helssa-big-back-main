"""
هسته پردازش صوت اپ Doctor
Doctor App Speech Processor Core
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class AudioSegment:
    """بخش صوتی"""
    start_time: float
    end_time: float
    text: str
    confidence: float
    speaker_id: Optional[str] = None


@dataclass
class SpeechProcessingResult:
    """نتیجه پردازش صوت"""
    audio_file_path: str
    transcription: str
    segments: List[AudioSegment]
    language: str
    confidence: float
    duration: float
    medical_entities: List[Dict[str, Any]]
    processing_time: float


class DoctorSpeechProcessorCore:
    """
    هسته پردازش صوت برای اپ Doctor
    مسئول رونویسی صوت، استخراج اطلاعات پزشکی از گفتار و پردازش صوتی
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.supported_formats = ['wav', 'mp3', 'ogg', 'm4a', 'flac']
        self.max_file_size = 100 * 1024 * 1024  # 100 MB
        self.max_duration = 3600  # 60 minutes
    
    def transcribe_medical_audio(self, audio_file_path: str, 
                               language: str = 'fa',
                               medical_mode: bool = True) -> SpeechProcessingResult:
        """
        رونویسی صوت پزشکی
        
        Args:
            audio_file_path: مسیر فایل صوتی
            language: زبان صوت
            medical_mode: حالت پزشکی برای دقت بیشتر
            
        Returns:
            SpeechProcessingResult object
        """
        start_time = datetime.now()
        
        try:
            # اعتبارسنجی فایل صوتی
            is_valid, error_msg = self._validate_audio_file(audio_file_path)
            if not is_valid:
                raise ValueError(error_msg)
            
            # دریافت اطلاعات فایل
            duration = self._get_audio_duration(audio_file_path)
            
            # رونویسی اصلی
            transcription_result = self._perform_transcription(
                audio_file_path, language, medical_mode
            )
            
            # پردازش اضافی برای محتوای پزشکی
            if medical_mode:
                medical_entities = self._extract_medical_entities_from_speech(
                    transcription_result['text']
                )
                transcription_result['text'] = self._enhance_medical_transcription(
                    transcription_result['text']
                )
            else:
                medical_entities = []
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return SpeechProcessingResult(
                audio_file_path=audio_file_path,
                transcription=transcription_result['text'],
                segments=transcription_result['segments'],
                language=language,
                confidence=transcription_result['confidence'],
                duration=duration,
                medical_entities=medical_entities,
                processing_time=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"Error transcribing medical audio: {str(e)}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return SpeechProcessingResult(
                audio_file_path=audio_file_path,
                transcription="خطا در رونویسی صوت",
                segments=[],
                language=language,
                confidence=0.0,
                duration=0.0,
                medical_entities=[],
                processing_time=processing_time
            )
    
    def extract_soap_from_audio(self, audio_file_path: str) -> Dict[str, str]:
        """
        استخراج اجزای SOAP از صوت
        
        Args:
            audio_file_path: مسیر فایل صوتی
            
        Returns:
            دیکشنری شامل اجزای SOAP
        """
        try:
            # رونویسی صوت
            result = self.transcribe_medical_audio(audio_file_path)
            
            # استخراج SOAP از متن رونویسی شده
            from .text_processor import DoctorTextProcessorCore
            text_processor = DoctorTextProcessorCore()
            
            soap_components = text_processor.extract_soap_components(result.transcription)
            
            # اضافه کردن اطلاعات صوتی
            soap_components['_audio_metadata'] = {
                'duration': result.duration,
                'confidence': result.confidence,
                'segments_count': len(result.segments),
                'processing_time': result.processing_time
            }
            
            return soap_components
            
        except Exception as e:
            self.logger.error(f"Error extracting SOAP from audio: {str(e)}")
            return {
                'subjective': '',
                'objective': '',
                'assessment': '',
                'plan': '',
                '_audio_metadata': {'error': str(e)}
            }
    
    def analyze_speaker_patterns(self, audio_file_path: str) -> Dict[str, Any]:
        """
        تحلیل الگوهای گوینده (پزشک/بیمار)
        
        Args:
            audio_file_path: مسیر فایل صوتی
            
        Returns:
            اطلاعات الگوهای گوینده
        """
        try:
            result = self.transcribe_medical_audio(audio_file_path)
            
            analysis = {
                'total_speakers': self._count_speakers(result.segments),
                'doctor_segments': [],
                'patient_segments': [],
                'conversation_flow': [],
                'speaking_time_ratio': {}
            }
            
            # شناسایی و تفکیک گوینده‌ها
            for segment in result.segments:
                speaker_type = self._identify_speaker_type(segment.text)
                
                segment_info = {
                    'start_time': segment.start_time,
                    'end_time': segment.end_time,
                    'duration': segment.end_time - segment.start_time,
                    'text': segment.text,
                    'confidence': segment.confidence
                }
                
                if speaker_type == 'doctor':
                    analysis['doctor_segments'].append(segment_info)
                else:
                    analysis['patient_segments'].append(segment_info)
                
                analysis['conversation_flow'].append({
                    'time': segment.start_time,
                    'speaker': speaker_type,
                    'duration': segment.end_time - segment.start_time
                })
            
            # محاسبه نسبت زمان صحبت
            doctor_time = sum(s['duration'] for s in analysis['doctor_segments'])
            patient_time = sum(s['duration'] for s in analysis['patient_segments'])
            total_time = doctor_time + patient_time
            
            if total_time > 0:
                analysis['speaking_time_ratio'] = {
                    'doctor_percentage': (doctor_time / total_time) * 100,
                    'patient_percentage': (patient_time / total_time) * 100
                }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing speaker patterns: {str(e)}")
            return {'error': str(e)}
    
    def generate_audio_summary(self, audio_file_path: str) -> Dict[str, Any]:
        """
        تولید خلاصه از فایل صوتی
        
        Args:
            audio_file_path: مسیر فایل صوتی
            
        Returns:
            خلاصه صوتی
        """
        try:
            result = self.transcribe_medical_audio(audio_file_path)
            
            # استخراج اطلاعات کلیدی
            from .text_processor import DoctorTextProcessorCore
            text_processor = DoctorTextProcessorCore()
            
            # تولید خلاصه متنی
            text_summary = text_processor.generate_medical_summary(result.transcription)
            
            # استخراج علائم و داروها
            symptoms = text_processor.extract_symptoms_from_text(result.transcription)
            medications = text_processor.extract_medications_from_text(result.transcription)
            
            summary = {
                'audio_info': {
                    'duration': result.duration,
                    'language': result.language,
                    'confidence': result.confidence,
                    'file_path': audio_file_path
                },
                'text_summary': text_summary,
                'key_findings': {
                    'symptoms': symptoms,
                    'medications': medications,
                    'medical_entities': result.medical_entities
                },
                'transcription': result.transcription,
                'processing_metadata': {
                    'processing_time': result.processing_time,
                    'segments_count': len(result.segments),
                    'created_at': datetime.now().isoformat()
                }
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating audio summary: {str(e)}")
            return {'error': str(e)}
    
    def validate_audio_quality(self, audio_file_path: str) -> Dict[str, Any]:
        """
        بررسی کیفیت فایل صوتی
        
        Args:
            audio_file_path: مسیر فایل صوتی
            
        Returns:
            گزارش کیفیت صوت
        """
        try:
            quality_report = {
                'file_valid': True,
                'issues': [],
                'recommendations': [],
                'technical_info': {},
                'quality_score': 0.0
            }
            
            # بررسی وجود فایل
            import os
            if not os.path.exists(audio_file_path):
                quality_report['file_valid'] = False
                quality_report['issues'].append('فایل وجود ندارد')
                return quality_report
            
            # بررسی اندازه فایل
            file_size = os.path.getsize(audio_file_path)
            quality_report['technical_info']['file_size'] = file_size
            
            if file_size > self.max_file_size:
                quality_report['issues'].append(f'اندازه فایل بیش از حد مجاز ({self.max_file_size} بایت)')
            
            # بررسی مدت زمان
            duration = self._get_audio_duration(audio_file_path)
            quality_report['technical_info']['duration'] = duration
            
            if duration > self.max_duration:
                quality_report['issues'].append(f'مدت زمان بیش از حد مجاز ({self.max_duration} ثانیه)')
            
            if duration < 5:
                quality_report['issues'].append('فایل کوتاه است (کمتر از 5 ثانیه)')
            
            # بررسی فرمت فایل
            file_extension = os.path.splitext(audio_file_path)[1].lower().replace('.', '')
            quality_report['technical_info']['format'] = file_extension
            
            if file_extension not in self.supported_formats:
                quality_report['issues'].append(f'فرمت فایل پشتیبانی نمی‌شود. فرمت‌های مجاز: {", ".join(self.supported_formats)}')
            
            # محاسبه امتیاز کیفیت
            score = 100.0
            score -= len(quality_report['issues']) * 20
            quality_report['quality_score'] = max(0.0, min(100.0, score))
            
            # ارائه توصیه‌ها
            if quality_report['quality_score'] < 70:
                quality_report['recommendations'].append('کیفیت فایل صوتی مطلوب نیست')
            
            if file_size < 1024 * 100:  # کمتر از 100KB
                quality_report['recommendations'].append('حجم فایل کم است، احتمالاً کیفیت پایینی دارد')
            
            return quality_report
            
        except Exception as e:
            self.logger.error(f"Error validating audio quality: {str(e)}")
            return {
                'file_valid': False,
                'issues': [f'خطا در بررسی کیفیت: {str(e)}'],
                'quality_score': 0.0
            }
    
    def _validate_audio_file(self, audio_file_path: str) -> Tuple[bool, str]:
        """اعتبارسنجی فایل صوتی"""
        import os
        
        if not os.path.exists(audio_file_path):
            return False, "فایل وجود ندارد"
        
        file_size = os.path.getsize(audio_file_path)
        if file_size > self.max_file_size:
            return False, f"اندازه فایل بیش از حد مجاز ({self.max_file_size} بایت)"
        
        if file_size == 0:
            return False, "فایل خالی است"
        
        file_extension = os.path.splitext(audio_file_path)[1].lower().replace('.', '')
        if file_extension not in self.supported_formats:
            return False, f"فرمت فایل پشتیبانی نمی‌شود. فرمت‌های مجاز: {', '.join(self.supported_formats)}"
        
        return True, ""
    
    def _get_audio_duration(self, audio_file_path: str) -> float:
        """دریافت مدت زمان فایل صوتی"""
        try:
            # در پیاده‌سازی واقعی از librosa یا ffmpeg استفاده می‌شود
            # اینجا یک مقدار شبیه‌سازی شده برمی‌گردانیم
            import os
            file_size = os.path.getsize(audio_file_path)
            # تخمین تقریبی بر اساس اندازه فایل (فرض: 128kbps)
            estimated_duration = file_size / (128 * 1024 / 8)  # تقریبی
            return min(estimated_duration, self.max_duration)
        except:
            return 0.0
    
    def _perform_transcription(self, audio_file_path: str, 
                             language: str, medical_mode: bool) -> Dict[str, Any]:
        """انجام رونویسی اصلی"""
        # در پیاده‌سازی واقعی، اینجا از Whisper یا سرویس‌های STT استفاده می‌شود
        
        # شبیه‌سازی نتیجه رونویسی
        mock_transcription = "بیمار شکایت از سردرد و تب دارد. معاینه فیزیکی طبیعی است. تشخیص: سرماخوردگی ساده. درمان: استراحت و مایعات فراوان."
        
        # شبیه‌سازی segments
        segments = [
            AudioSegment(
                start_time=0.0,
                end_time=5.0,
                text="بیمار شکایت از سردرد و تب دارد.",
                confidence=0.9,
                speaker_id="patient"
            ),
            AudioSegment(
                start_time=5.0,
                end_time=10.0,
                text="معاینه فیزیکی طبیعی است.",
                confidence=0.95,
                speaker_id="doctor"
            ),
            AudioSegment(
                start_time=10.0,
                end_time=15.0,
                text="تشخیص: سرماخوردگی ساده. درمان: استراحت و مایعات فراوان.",
                confidence=0.88,
                speaker_id="doctor"
            )
        ]
        
        return {
            'text': mock_transcription,
            'segments': segments,
            'confidence': 0.91
        }
    
    def _extract_medical_entities_from_speech(self, transcription: str) -> List[Dict[str, Any]]:
        """استخراج موجودیت‌های پزشکی از رونویسی"""
        # استفاده از text processor برای استخراج
        from .text_processor import DoctorTextProcessorCore
        text_processor = DoctorTextProcessorCore()
        
        symptoms = text_processor.extract_symptoms_from_text(transcription)
        medications = text_processor.extract_medications_from_text(transcription)
        
        entities = []
        entities.extend([{**s, 'source': 'speech'} for s in symptoms])
        entities.extend([{**m, 'source': 'speech'} for m in medications])
        
        return entities
    
    def _enhance_medical_transcription(self, transcription: str) -> str:
        """بهبود رونویسی برای اصطلاحات پزشکی"""
        # تصحیح اصطلاحات پزشکی رایج
        medical_corrections = {
            'سر درد': 'سردرد',
            'درد سر': 'سردرد',
            'استامینو فن': 'استامینوفن',
            'ای بو پروفن': 'ایبوپروفن',
            'آنتی بیوتیک': 'آنتی‌بیوتیک',
        }
        
        enhanced_text = transcription
        for wrong, correct in medical_corrections.items():
            enhanced_text = enhanced_text.replace(wrong, correct)
        
        return enhanced_text
    
    def _count_speakers(self, segments: List[AudioSegment]) -> int:
        """شمارش تعداد گوینده‌ها"""
        speakers = set()
        for segment in segments:
            if segment.speaker_id:
                speakers.add(segment.speaker_id)
        return len(speakers)
    
    def _identify_speaker_type(self, text: str) -> str:
        """شناسایی نوع گوینده (پزشک/بیمار)"""
        # الگوهای ساده برای تشخیص
        doctor_phrases = [
            'معاینه', 'تشخیص', 'درمان', 'نسخه', 'توصیه می‌کنم',
            'بررسی کنیم', 'آزمایش', 'دارو'
        ]
        
        patient_phrases = [
            'درد دارم', 'احساس می‌کنم', 'مشکل دارم', 'ناراحتم',
            'شکایت دارم', 'بدحالم'
        ]
        
        doctor_score = sum(1 for phrase in doctor_phrases if phrase in text)
        patient_score = sum(1 for phrase in patient_phrases if phrase in text)
        
        if doctor_score > patient_score:
            return 'doctor'
        else:
            return 'patient'