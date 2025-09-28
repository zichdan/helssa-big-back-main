"""
هسته پردازش صوت برای تبدیل گفتار به متن با استفاده از Whisper
"""
import logging
import os
import tempfile
from typing import Dict, Tuple, Optional, Any
import whisper
import numpy as np
import ffmpeg
import wave
import json
from pathlib import Path
import torch

logger = logging.getLogger(__name__)


class SpeechProcessorCore:
    """
    پردازش فایل‌های صوتی و تبدیل گفتار به متن
    
    وظایف:
    - تبدیل فرمت‌های صوتی
    - پیش‌پردازش صوت (نویزگیری، نرمال‌سازی)
    - تبدیل گفتار به متن با Whisper
    - تحلیل کیفیت صوت
    """
    
    def __init__(self):
        self.logger = logger
        self.models = {}
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.logger.info(f"Using device: {self.device}")
        
        # پیکربندی Whisper
        self.model_configs = {
            'tiny': {'name': 'tiny', 'vram': 1, 'relative_speed': 39},
            'base': {'name': 'base', 'vram': 1, 'relative_speed': 16},
            'small': {'name': 'small', 'vram': 2, 'relative_speed': 6},
            'medium': {'name': 'medium', 'vram': 5, 'relative_speed': 2},
            'large': {'name': 'large-v3', 'vram': 10, 'relative_speed': 1},
        }
        
        # تنظیمات پیش‌فرض
        self.default_model = 'base'
        self.sample_rate = 16000  # Whisper needs 16kHz
        
    def load_model(self, model_size: str = 'base') -> whisper.Whisper:
        """
        بارگذاری مدل Whisper
        
        Args:
            model_size: اندازه مدل (tiny, base, small, medium, large)
            
        Returns:
            whisper.Whisper: مدل بارگذاری شده
        """
        if model_size not in self.models:
            try:
                model_name = self.model_configs[model_size]['name']
                self.logger.info(f"Loading Whisper model: {model_name}")
                
                self.models[model_size] = whisper.load_model(
                    model_name,
                    device=self.device
                )
                
                self.logger.info(f"Model {model_name} loaded successfully")
            except Exception as e:
                self.logger.error(f"Error loading model {model_size}: {str(e)}")
                # بازگشت به مدل پیش‌فرض
                if model_size != self.default_model:
                    return self.load_model(self.default_model)
                raise
        
        return self.models[model_size]
    
    def process_audio_file(self, audio_file_path: str, language: str = 'fa',
                          model_size: str = 'base') -> Dict[str, Any]:
        """
        پردازش فایل صوتی و تبدیل به متن
        
        Args:
            audio_file_path: مسیر فایل صوتی
            language: زبان گفتار
            model_size: اندازه مدل
            
        Returns:
            dict: نتیجه تبدیل شامل متن و اطلاعات اضافی
        """
        try:
            # تحلیل کیفیت صوت
            audio_quality = self._analyze_audio_quality(audio_file_path)
            
            # پیش‌پردازش صوت
            processed_audio_path = self._preprocess_audio(audio_file_path)
            
            # بارگذاری مدل
            model = self.load_model(model_size)
            
            # تنظیمات تبدیل
            options = {
                'language': language if language != 'auto' else None,
                'task': 'transcribe',
                'temperature': 0.0,  # برای نتایج قطعی‌تر
                'compression_ratio_threshold': 2.4,
                'logprob_threshold': -1.0,
                'no_speech_threshold': 0.6,
                'condition_on_previous_text': True,
                'initial_prompt': self._get_initial_prompt(language),
                'word_timestamps': True,
            }
            
            # تبدیل گفتار به متن
            self.logger.info(f"Starting transcription with model {model_size}")
            result = model.transcribe(processed_audio_path, **options)
            
            # پاکسازی فایل موقت
            if processed_audio_path != audio_file_path:
                os.remove(processed_audio_path)
            
            # پردازش نتیجه
            processed_result = self._process_transcription_result(result, audio_quality)
            
            return processed_result
            
        except Exception as e:
            self.logger.error(f"Error in process_audio_file: {str(e)}")
            raise
    
    def _analyze_audio_quality(self, audio_path: str) -> Dict[str, Any]:
        """
        تحلیل کیفیت فایل صوتی
        
        Args:
            audio_path: مسیر فایل صوتی
            
        Returns:
            dict: اطلاعات کیفیت صوت
        """
        try:
            # اطلاعات پایه با ffprobe
            probe = ffmpeg.probe(audio_path)
            audio_stream = next(
                (stream for stream in probe['streams'] if stream['codec_type'] == 'audio'),
                None
            )
            
            if not audio_stream:
                raise ValueError("No audio stream found in file")
            
            # استخراج اطلاعات
            duration = float(probe['format']['duration'])
            bitrate = int(probe['format']['bit_rate'])
            sample_rate = int(audio_stream['sample_rate'])
            channels = audio_stream['channels']
            
            # خواندن داده‌های صوتی برای تحلیل عمیق‌تر
            audio_data, sr = self._load_audio(audio_path)
            
            # محاسبه معیارهای کیفیت
            rms_energy = np.sqrt(np.mean(audio_data**2))
            silence_ratio = np.sum(np.abs(audio_data) < 0.01) / len(audio_data)
            
            # تخمین سطح نویز (ساده)
            noise_level = self._estimate_noise_level(audio_data, sr)
            
            # امتیاز کیفیت کلی
            quality_score = self._calculate_audio_quality_score(
                bitrate, sample_rate, silence_ratio, noise_level
            )
            
            return {
                'duration': duration,
                'bitrate': bitrate,
                'sample_rate': sample_rate,
                'channels': channels,
                'rms_energy': float(rms_energy),
                'silence_ratio': float(silence_ratio),
                'noise_level': noise_level,
                'quality_score': quality_score,
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing audio quality: {str(e)}")
            return {
                'duration': 0,
                'quality_score': 0.5,
                'error': str(e)
            }
    
    def _preprocess_audio(self, audio_path: str) -> str:
        """
        پیش‌پردازش فایل صوتی
        
        Args:
            audio_path: مسیر فایل ورودی
            
        Returns:
            str: مسیر فایل پردازش شده
        """
        try:
            # ایجاد فایل موقت
            temp_file = tempfile.NamedTemporaryFile(
                suffix='.wav',
                delete=False
            )
            output_path = temp_file.name
            temp_file.close()
            
            # تبدیل به فرمت مناسب برای Whisper
            stream = ffmpeg.input(audio_path)
            stream = ffmpeg.output(
                stream,
                output_path,
                acodec='pcm_s16le',
                ac=1,  # تبدیل به مونو
                ar=self.sample_rate,  # 16kHz
                loglevel='error'
            )
            
            # اعمال فیلترهای صوتی
            stream = stream.global_args(
                '-af',
                'highpass=f=100,lowpass=f=8000,afftdn=nf=-20'  # حذف نویز پایه
            )
            
            ffmpeg.run(stream, overwrite_output=True)
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error preprocessing audio: {str(e)}")
            # در صورت خطا، فایل اصلی را برگردان
            return audio_path
    
    def _load_audio(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """بارگذاری داده‌های صوتی"""
        try:
            # استفاده از ffmpeg برای خواندن صوت
            out, _ = (
                ffmpeg.input(audio_path)
                .output('-', format='s16le', acodec='pcm_s16le', ac=1, ar=self.sample_rate)
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            # تبدیل به numpy array
            audio_data = np.frombuffer(out, np.int16).astype(np.float32) / 32768.0
            
            return audio_data, self.sample_rate
            
        except Exception as e:
            self.logger.error(f"Error loading audio: {str(e)}")
            raise
    
    def _estimate_noise_level(self, audio_data: np.ndarray, sample_rate: int) -> str:
        """
        تخمین سطح نویز پس‌زمینه
        
        Args:
            audio_data: داده‌های صوتی
            sample_rate: نرخ نمونه‌برداری
            
        Returns:
            str: سطح نویز (low, medium, high)
        """
        # محاسبه انرژی در بخش‌های کوتاه
        frame_length = int(0.02 * sample_rate)  # 20ms frames
        frames = [
            audio_data[i:i+frame_length]
            for i in range(0, len(audio_data)-frame_length, frame_length)
        ]
        
        # انرژی هر فریم
        frame_energies = [np.sqrt(np.mean(frame**2)) for frame in frames]
        
        # تخمین نویز از کم‌انرژی‌ترین فریم‌ها
        sorted_energies = sorted(frame_energies)
        noise_floor = np.mean(sorted_energies[:len(sorted_energies)//10])
        
        # طبقه‌بندی سطح نویز
        if noise_floor < 0.01:
            return 'low'
        elif noise_floor < 0.03:
            return 'medium'
        else:
            return 'high'
    
    def _calculate_audio_quality_score(self, bitrate: int, sample_rate: int,
                                     silence_ratio: float, noise_level: str) -> float:
        """محاسبه امتیاز کیفیت صوت"""
        score = 0.0
        
        # امتیاز بر اساس bitrate
        if bitrate >= 128000:
            score += 0.3
        elif bitrate >= 64000:
            score += 0.2
        else:
            score += 0.1
        
        # امتیاز بر اساس sample rate
        if sample_rate >= 44100:
            score += 0.2
        elif sample_rate >= 16000:
            score += 0.15
        else:
            score += 0.05
        
        # امتیاز بر اساس نسبت سکوت
        if silence_ratio < 0.3:
            score += 0.2
        elif silence_ratio < 0.5:
            score += 0.1
        
        # امتیاز بر اساس سطح نویز
        noise_scores = {'low': 0.3, 'medium': 0.2, 'high': 0.1}
        score += noise_scores.get(noise_level, 0.1)
        
        return min(score, 1.0)
    
    def _get_initial_prompt(self, language: str) -> str:
        """
        دریافت prompt اولیه برای بهبود دقت
        
        Args:
            language: زبان
            
        Returns:
            str: متن prompt
        """
        prompts = {
            'fa': 'این یک مکالمه پزشکی به زبان فارسی است.',
            'en': 'This is a medical conversation in English.',
        }
        
        return prompts.get(language, '')
    
    def _process_transcription_result(self, result: dict, 
                                    audio_quality: dict) -> Dict[str, Any]:
        """
        پردازش نتیجه تبدیل Whisper
        
        Args:
            result: نتیجه خام Whisper
            audio_quality: اطلاعات کیفیت صوت
            
        Returns:
            dict: نتیجه پردازش شده
        """
        # استخراج متن
        transcription = result.get('text', '').strip()
        
        # محاسبه confidence score
        # Whisper مستقیماً confidence نمی‌دهد، از معیارهای دیگر استفاده می‌کنیم
        avg_logprob = np.mean([
            segment.get('avg_logprob', 0)
            for segment in result.get('segments', [])
        ])
        
        confidence_score = self._calculate_confidence_score(
            avg_logprob,
            audio_quality.get('quality_score', 0.5),
            len(transcription)
        )
        
        # استخراج بخش‌ها با timestamp
        segments = []
        for segment in result.get('segments', []):
            segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text'].strip(),
                'confidence': max(0, min(1, segment.get('avg_logprob', -1) + 1))
            })
        
        # شناسایی کلمات با اطمینان پایین
        low_confidence_words = self._identify_low_confidence_words(result)
        
        return {
            'transcription': transcription,
            'language': result.get('language', 'unknown'),
            'duration': audio_quality.get('duration', 0),
            'confidence_score': confidence_score,
            'segments': segments,
            'low_confidence_words': low_confidence_words,
            'audio_quality': audio_quality,
            'model_info': {
                'task': 'transcribe',
                'temperature': 0.0,
            }
        }
    
    def _calculate_confidence_score(self, avg_logprob: float, 
                                  audio_quality_score: float,
                                  text_length: int) -> float:
        """محاسبه امتیاز اطمینان کلی"""
        # نرمال‌سازی logprob (معمولاً بین -1 تا 0 است)
        logprob_score = max(0, min(1, avg_logprob + 1))
        
        # در نظر گرفتن طول متن (متن‌های خیلی کوتاه مشکوک هستند)
        length_factor = min(1.0, text_length / 50)
        
        # ترکیب امتیازها
        confidence = (
            0.5 * logprob_score +
            0.3 * audio_quality_score +
            0.2 * length_factor
        )
        
        return round(confidence, 3)
    
    def _identify_low_confidence_words(self, result: dict) -> list:
        """شناسایی کلمات با اطمینان پایین"""
        low_confidence_words = []
        
        # اگر word_timestamps فعال بود
        if 'words' in result:
            for word_info in result['words']:
                if word_info.get('probability', 1.0) < 0.5:
                    low_confidence_words.append({
                        'word': word_info['word'],
                        'start': word_info['start'],
                        'end': word_info['end'],
                        'probability': word_info['probability']
                    })
        
        return low_confidence_words
    
    def estimate_processing_time(self, duration: float, model_size: str) -> float:
        """
        تخمین زمان پردازش
        
        Args:
            duration: مدت زمان صوت (ثانیه)
            model_size: اندازه مدل
            
        Returns:
            float: زمان تخمینی (ثانیه)
        """
        # بر اساس تست‌های Whisper
        relative_speed = self.model_configs[model_size]['relative_speed']
        
        # فاکتور سخت‌افزار
        hardware_factor = 2.0 if self.device == 'cpu' else 0.5
        
        # تخمین زمان
        estimated_time = (duration / relative_speed) * hardware_factor
        
        # اضافه کردن زمان بارگذاری مدل اگر لود نشده
        if model_size not in self.models:
            estimated_time += 5  # 5 ثانیه برای بارگذاری
        
        return estimated_time