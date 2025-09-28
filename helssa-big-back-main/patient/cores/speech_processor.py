"""
هسته Speech Processor برای سیستم مدیریت بیماران
Patient Management Speech Processing Core
"""

import logging
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from django.core.cache import cache
from django.conf import settings
import aiohttp
import io
from pydub import AudioSegment

logger = logging.getLogger(__name__)


class PatientSpeechProcessor:
    """
    هسته پردازش گفتار برای مدیریت اطلاعات بیماران
    Speech processing core for patient information management
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supported_formats = ['mp3', 'wav', 'webm', 'ogg', 'm4a']
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.chunk_duration = 30  # seconds
        self.overlap_duration = 2  # seconds
        
        # تنظیمات STT
        self.stt_config = {
            'language': 'fa',  # فارسی
            'model': 'whisper-1',
            'response_format': 'json',
            'temperature': 0.2
        }
        
        # کلمات کلیدی پزشکی برای بهبود دقت
        self.medical_vocabulary = [
            'درد', 'تب', 'سردرد', 'شکم', 'سینه', 'قلب', 'ریه',
            'فشار خون', 'قند خون', 'آزمایش', 'دارو', 'قرص',
            'تنگی نفس', 'سرفه', 'تهوع', 'استفراغ', 'اسهال'
        ]
    
    async def process_patient_audio(
        self,
        audio_file: bytes,
        audio_format: str,
        processing_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        پردازش فایل صوتی بیمار
        Process patient audio file
        
        Args:
            audio_file: فایل صوتی (bytes)
            audio_format: فرمت فایل صوتی
            processing_options: تنظیمات اضافی پردازش
            
        Returns:
            Dict: نتیجه پردازش شامل متن، تحلیل و metadata
        """
        try:
            # اعتبارسنجی ورودی
            validation_result = await self._validate_audio_input(
                audio_file, audio_format
            )
            if not validation_result['valid']:
                return validation_result
            
            # پیش‌پردازش صوت
            preprocessed_audio = await self._preprocess_audio(
                audio_file, audio_format
            )
            
            # تقسیم به قطعات در صورت نیاز
            audio_chunks = await self._split_audio_if_needed(preprocessed_audio)
            
            # پردازش STT برای هر قطعه
            transcription_results = []
            for i, chunk in enumerate(audio_chunks):
                chunk_result = await self._process_audio_chunk(
                    chunk, i, processing_options
                )
                transcription_results.append(chunk_result)
            
            # ادغام نتایج
            final_transcription = await self._merge_transcription_results(
                transcription_results
            )
            
            # تحلیل محتوای پزشکی
            medical_analysis = await self._analyze_medical_speech_content(
                final_transcription
            )
            
            # بهبود کیفیت متن
            improved_text = await self._improve_transcription_quality(
                final_transcription, medical_analysis
            )
            
            # استخراج اطلاعات ساختاریافته
            structured_data = await self._extract_structured_speech_data(
                improved_text
            )
            
            return {
                'success': True,
                'transcription': {
                    'text': improved_text['final_text'],
                    'confidence': final_transcription.get('confidence', 0.8),
                    'language': final_transcription.get('language', 'fa'),
                    'segments': final_transcription.get('segments', [])
                },
                'medical_analysis': medical_analysis,
                'structured_data': structured_data,
                'audio_metadata': {
                    'format': audio_format,
                    'size': len(audio_file),
                    'duration': preprocessed_audio.get('duration', 0),
                    'chunks_count': len(audio_chunks),
                    'processing_time': improved_text.get('processing_time', 0)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Speech processing error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'message': 'خطا در پردازش فایل صوتی'
            }
    
    async def process_live_audio_stream(
        self,
        audio_stream: asyncio.Queue,
        session_id: str,
        callback_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        پردازش جریان صوتی زنده
        Process live audio stream
        
        Args:
            audio_stream: صف داده‌های صوتی
            session_id: شناسه جلسه
            callback_url: آدرس callback برای نتایج
            
        Returns:
            Dict: اطلاعات جلسه پردازش
        """
        try:
            session_data = {
                'session_id': session_id,
                'status': 'active',
                'chunks_processed': 0,
                'total_text': '',
                'start_time': asyncio.get_event_loop().time()
            }
            
            # ذخیره اطلاعات جلسه در کش
            cache.set(f"speech_session:{session_id}", session_data, timeout=3600)
            
            # شروع پردازش جریان
            asyncio.create_task(
                self._process_stream_chunks(
                    audio_stream, session_id, callback_url
                )
            )
            
            return {
                'success': True,
                'session_id': session_id,
                'status': 'started',
                'message': 'پردازش جریان صوتی شروع شد'
            }
            
        except Exception as e:
            self.logger.error(f"Live stream processing error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'خطا در شروع پردازش جریان صوتی'
            }
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        دریافت وضعیت جلسه پردازش
        Get processing session status
        """
        session_data = cache.get(f"speech_session:{session_id}")
        
        if not session_data:
            return {
                'success': False,
                'message': 'جلسه یافت نشد'
            }
        
        return {
            'success': True,
            'session_data': session_data
        }
    
    async def _validate_audio_input(
        self,
        audio_file: bytes,
        audio_format: str
    ) -> Dict[str, Any]:
        """
        اعتبارسنجی ورودی صوتی
        Validate audio input
        """
        # بررسی فرمت
        if audio_format.lower() not in self.supported_formats:
            return {
                'valid': False,
                'error': 'Unsupported format',
                'message': f'فرمت {audio_format} پشتیبانی نمی‌شود'
            }
        
        # بررسی حجم فایل
        if len(audio_file) > self.max_file_size:
            return {
                'valid': False,
                'error': 'File too large',
                'message': f'حجم فایل نباید بیش از {self.max_file_size // (1024*1024)} مگابایت باشد'
            }
        
        # بررسی محتوای فایل
        try:
            audio_segment = AudioSegment.from_file(
                io.BytesIO(audio_file),
                format=audio_format
            )
            
            # بررسی مدت زمان
            duration = len(audio_segment) / 1000  # تبدیل به ثانیه
            if duration < 1:
                return {
                    'valid': False,
                    'error': 'Audio too short',
                    'message': 'مدت زمان صوت باید حداقل 1 ثانیه باشد'
                }
            
            if duration > 1800:  # 30 minutes
                return {
                    'valid': False,
                    'error': 'Audio too long',
                    'message': 'مدت زمان صوت نباید بیش از 30 دقیقه باشد'
                }
            
        except Exception as e:
            return {
                'valid': False,
                'error': 'Invalid audio file',
                'message': 'فایل صوتی معتبر نیست'
            }
        
        return {'valid': True}
    
    async def _preprocess_audio(
        self,
        audio_file: bytes,
        audio_format: str
    ) -> Dict[str, Any]:
        """
        پیش‌پردازش فایل صوتی
        Preprocess audio file
        """
        try:
            # بارگذاری فایل صوتی
            audio_segment = AudioSegment.from_file(
                io.BytesIO(audio_file),
                format=audio_format
            )
            
            # نرمال‌سازی صدا
            # تنظیم sample rate به 16kHz (استاندارد STT)
            if audio_segment.frame_rate != 16000:
                audio_segment = audio_segment.set_frame_rate(16000)
            
            # تبدیل به mono
            if audio_segment.channels > 1:
                audio_segment = audio_segment.set_channels(1)
            
            # نرمال‌سازی حجم صدا
            audio_segment = audio_segment.normalize()
            
            # حذف سکوت از ابتدا و انتها
            audio_segment = audio_segment.strip_silence(
                silence_thresh=-40,  # dB
                silence_len=1000,    # ms
                padding=500          # ms
            )
            
            # تبدیل به فرمت مناسب STT (معمولاً WAV)
            output_buffer = io.BytesIO()
            audio_segment.export(output_buffer, format='wav')
            processed_audio = output_buffer.getvalue()
            
            return {
                'audio_data': processed_audio,
                'duration': len(audio_segment) / 1000,  # ثانیه
                'sample_rate': audio_segment.frame_rate,
                'channels': audio_segment.channels,
                'format': 'wav'
            }
            
        except Exception as e:
            self.logger.error(f"Audio preprocessing error: {str(e)}")
            raise
    
    async def _split_audio_if_needed(
        self,
        preprocessed_audio: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        تقسیم صوت به قطعات در صورت نیاز
        Split audio into chunks if needed
        """
        duration = preprocessed_audio['duration']
        
        # اگر مدت زمان کم است، نیازی به تقسیم نیست
        if duration <= self.chunk_duration:
            return [preprocessed_audio]
        
        chunks = []
        audio_data = preprocessed_audio['audio_data']
        
        try:
            audio_segment = AudioSegment.from_file(
                io.BytesIO(audio_data),
                format='wav'
            )
            
            # تقسیم با همپوشانی
            start_time = 0
            chunk_index = 0
            
            while start_time < duration:
                end_time = min(start_time + self.chunk_duration, duration)
                
                # استخراج قطعه
                start_ms = int(start_time * 1000)
                end_ms = int(end_time * 1000)
                chunk_segment = audio_segment[start_ms:end_ms]
                
                # تبدیل به bytes
                chunk_buffer = io.BytesIO()
                chunk_segment.export(chunk_buffer, format='wav')
                chunk_data = chunk_buffer.getvalue()
                
                chunks.append({
                    'audio_data': chunk_data,
                    'duration': len(chunk_segment) / 1000,
                    'sample_rate': chunk_segment.frame_rate,
                    'channels': chunk_segment.channels,
                    'format': 'wav',
                    'chunk_index': chunk_index,
                    'start_time': start_time,
                    'end_time': end_time
                })
                
                # حرکت به قطعه بعدی با همپوشانی
                start_time = end_time - self.overlap_duration
                chunk_index += 1
                
                # جلوگیری از حلقه بی‌نهایت
                if start_time >= duration - self.overlap_duration:
                    break
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"Audio splitting error: {str(e)}")
            # در صورت خطا، صوت اصلی را برگردان
            return [preprocessed_audio]
    
    async def _process_audio_chunk(
        self,
        chunk: Dict[str, Any],
        chunk_index: int,
        processing_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        پردازش یک قطعه صوتی
        Process a single audio chunk
        """
        try:
            # ارسال به سرویس STT
            stt_result = await self._send_to_stt_service(
                chunk['audio_data'],
                processing_options or {}
            )
            
            # پس‌پردازش نتیجه
            processed_result = await self._post_process_stt_result(
                stt_result, chunk_index
            )
            
            return {
                'chunk_index': chunk_index,
                'start_time': chunk.get('start_time', 0),
                'end_time': chunk.get('end_time', 0),
                'duration': chunk['duration'],
                'transcription': processed_result,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(
                f"Chunk processing error (chunk {chunk_index}): {str(e)}"
            )
            return {
                'chunk_index': chunk_index,
                'error': str(e),
                'success': False
            }
    
    async def _send_to_stt_service(
        self,
        audio_data: bytes,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        ارسال به سرویس STT
        Send to STT service
        """
        try:
            # تنظیمات STT
            stt_config = self.stt_config.copy()
            stt_config.update(options)
            
            # ارسال درخواست به OpenAI Whisper API یا سرویس STT محلی
            if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
                return await self._send_to_openai_whisper(audio_data, stt_config)
            else:
                # استفاده از سرویس STT محلی
                return await self._send_to_local_stt(audio_data, stt_config)
                
        except Exception as e:
            self.logger.error(f"STT service error: {str(e)}")
            raise
    
    async def _send_to_openai_whisper(
        self,
        audio_data: bytes,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        ارسال به OpenAI Whisper API
        Send to OpenAI Whisper API
        """
        try:
            headers = {
                'Authorization': f'Bearer {settings.OPENAI_API_KEY}'
            }
            
            # آماده‌سازی فایل برای ارسال
            files = {
                'file': ('audio.wav', audio_data, 'audio/wav'),
                'model': (None, config.get('model', 'whisper-1')),
                'language': (None, config.get('language', 'fa')),
                'response_format': (None, config.get('response_format', 'json')),
                'temperature': (None, str(config.get('temperature', 0.2)))
            }
            
            # اضافه کردن واژگان پزشکی
            if self.medical_vocabulary:
                files['prompt'] = (None, ' '.join(self.medical_vocabulary[:10]))
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.openai.com/v1/audio/transcriptions',
                    headers=headers,
                    data=files
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        error_text = await response.text()
                        raise Exception(f"OpenAI API error: {error_text}")
                        
        except Exception as e:
            self.logger.error(f"OpenAI Whisper error: {str(e)}")
            raise
    
    async def _send_to_local_stt(
        self,
        audio_data: bytes,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        ارسال به سرویس STT محلی
        Send to local STT service
        """
        try:
            # اتصال به سرویس STT محلی (Whisper self-hosted)
            local_stt_url = getattr(settings, 'LOCAL_STT_URL', 'http://localhost:8000')
            
            files = {
                'audio': ('audio.wav', audio_data, 'audio/wav')
            }
            
            data = {
                'language': config.get('language', 'fa'),
                'model': config.get('model', 'base'),
                'task': 'transcribe'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{local_stt_url}/transcribe",
                    data=data,
                    data=files
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        # در صورت عدم دسترسی به سرویس، از یک پاسخ فرضی استفاده کن
                        return {
                            'text': '[STT service unavailable]',
                            'confidence': 0.1,
                            'language': 'fa'
                        }
                        
        except Exception as e:
            self.logger.error(f"Local STT error: {str(e)}")
            # پاسخ پیش‌فرض در صورت خطا
            return {
                'text': '[Processing error]',
                'confidence': 0.0,
                'language': 'fa'
            }
    
    async def _post_process_stt_result(
        self,
        stt_result: Dict[str, Any],
        chunk_index: int
    ) -> Dict[str, Any]:
        """
        پس‌پردازش نتیجه STT
        Post-process STT result
        """
        text = stt_result.get('text', '').strip()
        
        # تمیز کردن متن
        if text:
            # حذف کاراکترهای اضافی
            text = ' '.join(text.split())
            
            # تصحیح املای پایه کلمات پزشکی رایج
            text = await self._correct_medical_terms(text)
        
        return {
            'text': text,
            'confidence': stt_result.get('confidence', 0.8),
            'language': stt_result.get('language', 'fa'),
            'segments': stt_result.get('segments', []),
            'chunk_index': chunk_index
        }
    
    async def _merge_transcription_results(
        self,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        ادغام نتایج رونویسی قطعات
        Merge transcription results from chunks
        """
        try:
            # فیلتر قطعات موفق
            successful_chunks = [r for r in results if r.get('success', False)]
            
            if not successful_chunks:
                return {
                    'text': '',
                    'confidence': 0.0,
                    'language': 'fa',
                    'segments': []
                }
            
            # مرتب‌سازی بر اساس chunk_index
            successful_chunks.sort(key=lambda x: x['chunk_index'])
            
            # ادغام متن‌ها
            full_text = ""
            all_segments = []
            total_confidence = 0
            
            for i, chunk in enumerate(successful_chunks):
                transcription = chunk['transcription']
                chunk_text = transcription.get('text', '').strip()
                
                if chunk_text:
                    # حذف همپوشانی در صورت وجود
                    if i > 0 and full_text:
                        chunk_text = await self._remove_overlap(
                            full_text, chunk_text
                        )
                    
                    if full_text and not full_text.endswith(' '):
                        full_text += ' '
                    full_text += chunk_text
                
                # جمع‌آوری segments
                segments = transcription.get('segments', [])
                if segments:
                    # تنظیم زمان‌ها بر اساس موقعیت قطعه
                    start_offset = chunk.get('start_time', 0)
                    for segment in segments:
                        adjusted_segment = segment.copy()
                        if 'start' in adjusted_segment:
                            adjusted_segment['start'] += start_offset
                        if 'end' in adjusted_segment:
                            adjusted_segment['end'] += start_offset
                        all_segments.append(adjusted_segment)
                
                # محاسبه میانگین confidence
                total_confidence += transcription.get('confidence', 0.8)
            
            avg_confidence = total_confidence / len(successful_chunks) if successful_chunks else 0.0
            
            return {
                'text': full_text.strip(),
                'confidence': round(avg_confidence, 3),
                'language': successful_chunks[0]['transcription'].get('language', 'fa'),
                'segments': all_segments,
                'chunks_count': len(successful_chunks)
            }
            
        except Exception as e:
            self.logger.error(f"Transcription merging error: {str(e)}")
            return {
                'text': '',
                'confidence': 0.0,
                'language': 'fa',
                'segments': []
            }
    
    async def _remove_overlap(self, previous_text: str, current_text: str) -> str:
        """
        حذف همپوشانی بین متن‌ها
        Remove overlap between texts
        """
        # الگوریتم ساده برای حذف همپوشانی
        words_prev = previous_text.split()
        words_curr = current_text.split()
        
        # جستجوی بزرگترین همپوشانی در انتهای متن قبلی و ابتدای متن فعلی
        max_overlap = min(len(words_prev), len(words_curr), 10)  # حداکثر 10 کلمه
        
        for overlap_len in range(max_overlap, 0, -1):
            if words_prev[-overlap_len:] == words_curr[:overlap_len]:
                # همپوشانی یافت شد، حذف از ابتدای متن فعلی
                return ' '.join(words_curr[overlap_len:])
        
        # همپوشانی یافت نشد
        return current_text
    
    async def _analyze_medical_speech_content(
        self,
        transcription: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        تحلیل محتوای پزشکی گفتار
        Analyze medical speech content
        """
        text = transcription.get('text', '')
        if not text:
            return {'medical_score': 0, 'entities': []}
        
        # استفاده از Text Processor برای تحلیل
        from .text_processor import PatientTextProcessor
        text_processor = PatientTextProcessor()
        
        # استخراج موجودیت‌های پزشکی
        entities = await text_processor.extract_medical_entities(text)
        
        # تحلیل محتوای پزشکی
        medical_analysis = await text_processor._analyze_medical_content(text)
        
        return {
            'medical_score': medical_analysis.get('medical_score', 0),
            'entities': entities,
            'urgency_level': medical_analysis.get('urgency_level', 'normal'),
            'completeness_score': medical_analysis.get('completeness_score', 0),
            'categories': medical_analysis.get('categories', [])
        }
    
    async def _improve_transcription_quality(
        self,
        transcription: Dict[str, Any],
        medical_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        بهبود کیفیت رونویسی
        Improve transcription quality
        """
        start_time = asyncio.get_event_loop().time()
        
        text = transcription.get('text', '')
        if not text:
            return {
                'final_text': '',
                'improvements': [],
                'processing_time': 0
            }
        
        improvements = []
        improved_text = text
        
        # تصحیح کلمات پزشکی رایج
        improved_text = await self._correct_medical_terms(improved_text)
        if improved_text != text:
            improvements.append('medical_terms_correction')
        
        # تصحیح نقطه‌گذاری
        punctuated_text = await self._add_punctuation(improved_text)
        if punctuated_text != improved_text:
            improvements.append('punctuation_added')
            improved_text = punctuated_text
        
        # تصحیح گرامر پایه
        grammar_corrected = await self._basic_grammar_correction(improved_text)
        if grammar_corrected != improved_text:
            improvements.append('grammar_correction')
            improved_text = grammar_corrected
        
        processing_time = asyncio.get_event_loop().time() - start_time
        
        return {
            'final_text': improved_text.strip(),
            'improvements': improvements,
            'processing_time': round(processing_time, 3)
        }
    
    async def _correct_medical_terms(self, text: str) -> str:
        """
        تصحیح کلمات پزشکی
        Correct medical terms
        """
        # دیکشنری تصحیحات رایج
        corrections = {
            'درد سر': 'سردرد',
            'فشار خوون': 'فشار خون',
            'قند خوون': 'قند خون',
            'تنگی نفس': 'تنگی نفس',
            'گلو درد': 'گلودرد',
            'شکم درد': 'شکم درد',
            'سینه درد': 'قفسه سینه درد'
        }
        
        corrected_text = text
        for wrong, correct in corrections.items():
            corrected_text = corrected_text.replace(wrong, correct)
        
        return corrected_text
    
    async def _add_punctuation(self, text: str) -> str:
        """
        اضافه کردن نقطه‌گذاری پایه
        Add basic punctuation
        """
        # الگوریتم ساده برای اضافه کردن نقطه‌گذاری
        sentences = text.split('.')
        improved_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                # اضافه کردن نقطه در انتهای جملات
                if not sentence.endswith(('.', '!', '?')):
                    sentence += '.'
                improved_sentences.append(sentence)
        
        return ' '.join(improved_sentences)
    
    async def _basic_grammar_correction(self, text: str) -> str:
        """
        تصحیح گرامر پایه
        Basic grammar correction
        """
        # تصحیحات پایه زبان فارسی
        corrected = text
        
        # تصحیح فاصله‌ها
        corrected = ' '.join(corrected.split())
        
        # حذف فاصله‌های اضافی قبل از علائم نگارشی
        corrected = corrected.replace(' .', '.')
        corrected = corrected.replace(' ,', ',')
        corrected = corrected.replace(' !', '!')
        corrected = corrected.replace(' ?', '?')
        
        return corrected
    
    async def _extract_structured_speech_data(
        self,
        improved_text: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        استخراج داده‌های ساختاریافته از گفتار
        Extract structured data from speech
        """
        text = improved_text.get('final_text', '')
        
        # استفاده از Text Processor برای استخراج داده‌ها
        from .text_processor import PatientTextProcessor
        text_processor = PatientTextProcessor()
        
        # پردازش متن برای استخراج اطلاعات
        processed_data = await text_processor.process_patient_text(
            text, 'medical_record'
        )
        
        return {
            'extracted_data': processed_data.get('extracted_data', {}),
            'medical_entities': processed_data.get('medical_analysis', {}).get('entities', {}),
            'confidence_score': processed_data.get('processing_metadata', {}).get('confidence_score', 0)
        }
    
    async def _process_stream_chunks(
        self,
        audio_stream: asyncio.Queue,
        session_id: str,
        callback_url: Optional[str] = None
    ):
        """
        پردازش قطعات جریان صوتی
        Process stream chunks
        """
        try:
            chunk_buffer = b''
            chunk_counter = 0
            
            while True:
                try:
                    # دریافت داده از صف با timeout
                    chunk_data = await asyncio.wait_for(
                        audio_stream.get(), timeout=5.0
                    )
                    
                    if chunk_data is None:  # سیگنال پایان
                        break
                    
                    chunk_buffer += chunk_data
                    
                    # پردازش اگر بافر به اندازه کافی پر شد
                    if len(chunk_buffer) >= 32768:  # 32KB
                        result = await self._process_stream_chunk(
                            chunk_buffer, chunk_counter, session_id
                        )
                        
                        # ارسال نتیجه به callback
                        if callback_url and result.get('success'):
                            await self._send_callback(callback_url, result)
                        
                        chunk_buffer = b''
                        chunk_counter += 1
                        
                except asyncio.TimeoutError:
                    # Timeout - چک کردن وضعیت جلسه
                    session_data = cache.get(f"speech_session:{session_id}")
                    if not session_data or session_data.get('status') != 'active':
                        break
                    continue
                    
        except Exception as e:
            self.logger.error(f"Stream processing error: {str(e)}")
        finally:
            # پردازش باقی‌مانده بافر
            if chunk_buffer:
                await self._process_stream_chunk(
                    chunk_buffer, chunk_counter, session_id
                )
            
            # بروزرسانی وضعیت جلسه
            session_data = cache.get(f"speech_session:{session_id}")
            if session_data:
                session_data['status'] = 'completed'
                cache.set(f"speech_session:{session_id}", session_data, timeout=3600)
    
    async def _process_stream_chunk(
        self,
        chunk_data: bytes,
        chunk_index: int,
        session_id: str
    ) -> Dict[str, Any]:
        """
        پردازش یک قطعه از جریان
        Process a single stream chunk
        """
        try:
            # پردازش مشابه فایل صوتی عادی
            result = await self.process_patient_audio(
                chunk_data, 'wav', {'stream_mode': True}
            )
            
            # بروزرسانی اطلاعات جلسه
            session_data = cache.get(f"speech_session:{session_id}")
            if session_data:
                session_data['chunks_processed'] += 1
                if result.get('success'):
                    transcription = result.get('transcription', {})
                    text = transcription.get('text', '')
                    if text:
                        session_data['total_text'] += ' ' + text
                
                cache.set(f"speech_session:{session_id}", session_data, timeout=3600)
            
            return {
                'success': True,
                'session_id': session_id,
                'chunk_index': chunk_index,
                'result': result
            }
            
        except Exception as e:
            self.logger.error(f"Stream chunk processing error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'chunk_index': chunk_index
            }
    
    async def _send_callback(self, callback_url: str, data: Dict[str, Any]):
        """
        ارسال نتیجه به callback URL
        Send result to callback URL
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    callback_url,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        self.logger.warning(
                            f"Callback failed: {response.status}"
                        )
        except Exception as e:
            self.logger.error(f"Callback error: {str(e)}")