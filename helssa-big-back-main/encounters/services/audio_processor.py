from typing import List, Dict, Optional
import io
import asyncio
from asgiref.sync import sync_to_async
from django.utils import timezone

from ..models import Encounter, AudioChunk
from ..utils.encryption import encrypt_data, decrypt_data


class AudioProcessingService:
    """سرویس پردازش صوت ویزیت‌ها"""
    
    def __init__(self):
        self.chunk_size_mb = 10  # حجم هر قطعه
        self.overlap_seconds = 2  # همپوشانی بین قطعات
        
    async def process_visit_audio(
        self,
        encounter_id: str,
        audio_stream: bytes,
        chunk_index: int
    ) -> AudioChunk:
        """پردازش یک قطعه صوتی"""
        
        encounter = await sync_to_async(Encounter.objects.get)(id=encounter_id)
        
        # رمزنگاری صوت
        encrypted_audio = await encrypt_data(
            audio_stream,
            encounter.encryption_key
        )
        
        # آپلود به MinIO
        file_name = f"encounters/{encounter_id}/chunk_{chunk_index:04d}.webm"
        file_url = await self._upload_to_storage(
            file_name,
            encrypted_audio,
            content_type='audio/webm'
        )
        
        # تحلیل صوت
        audio_info = await self._analyze_audio(audio_stream)
        
        # ایجاد رکورد AudioChunk
        audio_chunk = await sync_to_async(AudioChunk.objects.create)(
            encounter=encounter,
            chunk_index=chunk_index,
            file_url=file_url,
            file_size=len(encrypted_audio),
            duration_seconds=audio_info['duration'],
            format='webm',
            sample_rate=audio_info['sample_rate'],
            bit_rate=audio_info.get('bit_rate'),
            is_encrypted=True,
            encryption_metadata={
                'algorithm': 'AES-256-GCM',
                'key_id': encounter.encryption_key[:8]
            }
        )
        
        # شروع پردازش STT در پس‌زمینه
        asyncio.create_task(
            self._process_stt_async(str(audio_chunk.id))
        )
        
        return audio_chunk
        
    async def merge_audio_chunks(
        self,
        encounter_id: str
    ) -> str:
        """ادغام قطعات صوتی"""
        
        # بازیابی همه قطعات
        chunks = await sync_to_async(list)(
            AudioChunk.objects.filter(
                encounter_id=encounter_id
            ).order_by('chunk_index')
        )
        
        if not chunks:
            raise ValueError("هیچ قطعه صوتی یافت نشد")
            
        # دانلود و رمزگشایی
        audio_segments = []
        for chunk in chunks:
            encrypted_data = await self._download_from_storage(
                chunk.file_url
            )
            
            decrypted_data = await decrypt_data(
                encrypted_data,
                chunk.encounter.encryption_key
            )
            
            audio_segments.append({
                'data': decrypted_data,
                'index': chunk.chunk_index,
                'duration': chunk.duration_seconds
            })
            
        # ادغام با حذف همپوشانی‌ها
        merged_audio = await self._merge_with_overlap_removal(
            audio_segments,
            self.overlap_seconds
        )
        
        # رمزنگاری و آپلود فایل نهایی
        encounter = await sync_to_async(Encounter.objects.get)(id=encounter_id)
        encrypted_final = await encrypt_data(
            merged_audio,
            encounter.encryption_key
        )
        
        final_url = await self._upload_to_storage(
            f"encounters/{encounter_id}/full_recording.mp3",
            encrypted_final,
            content_type='audio/mp3'
        )
        
        return final_url
        
    async def extract_audio_segment(
        self,
        encounter_id: str,
        start_time: float,
        end_time: float
    ) -> bytes:
        """استخراج بخشی از صوت"""
        
        # پیدا کردن قطعات مربوطه
        chunks = await sync_to_async(list)(
            AudioChunk.objects.filter(
                encounter_id=encounter_id
            ).order_by('chunk_index')
        )
        
        # محاسبه قطعات مورد نیاز
        relevant_chunks = []
        current_time = 0
        
        for chunk in chunks:
            chunk_start = current_time
            chunk_end = current_time + chunk.duration_seconds
            
            if chunk_end >= start_time and chunk_start <= end_time:
                relevant_chunks.append(chunk)
                
            current_time = chunk_end
            
        # دانلود و استخراج بخش مورد نظر
        segment_data = await self._extract_segment_from_chunks(
            relevant_chunks,
            start_time,
            end_time
        )
        
        return segment_data
        
    async def _analyze_audio(self, audio_data: bytes) -> Dict:
        """تحلیل مشخصات صوت"""
        
        # TODO: استفاده از کتابخانه‌هایی مثل pydub برای تحلیل
        # فعلاً مقادیر پیش‌فرض
        return {
            'duration': 30.0,  # 30 ثانیه
            'sample_rate': 48000,
            'channels': 1,
            'bit_rate': 128000,
            'format': 'webm'
        }
        
    async def _merge_with_overlap_removal(
        self,
        segments: List[Dict],
        overlap_seconds: float
    ) -> bytes:
        """ادغام با حذف همپوشانی"""
        
        # TODO: پیاده‌سازی الگوریتم ادغام با pydub
        # فعلاً فقط قطعات را به هم می‌چسبانیم
        merged = b''
        for segment in segments:
            merged += segment['data']
            
        return merged
        
    async def _extract_segment_from_chunks(
        self,
        chunks: List[AudioChunk],
        start_time: float,
        end_time: float
    ) -> bytes:
        """استخراج بخش صوتی از قطعات"""
        
        # TODO: پیاده‌سازی با pydub
        return b''
        
    async def _upload_to_storage(
        self,
        file_path: str,
        data: bytes,
        content_type: str
    ) -> str:
        """آپلود به MinIO"""
        
        # TODO: اتصال به MinIO service
        # فعلاً URL ساختگی
        return f"https://storage.helssa.ir/{file_path}"
        
    async def _download_from_storage(
        self,
        file_url: str
    ) -> bytes:
        """دانلود از MinIO"""
        
        # TODO: اتصال به MinIO service
        # فعلاً داده ساختگی
        return b''
        
    async def _process_stt_async(self, chunk_id: str):
        """پردازش STT به صورت async"""
        
        # TODO: ارسال به صف Celery
        pass
        
    async def get_audio_quality_metrics(
        self,
        encounter_id: str
    ) -> Dict:
        """دریافت معیارهای کیفیت صوت"""
        
        chunks = await sync_to_async(list)(
            AudioChunk.objects.filter(
                encounter_id=encounter_id
            ).values('duration_seconds', 'file_size', 'bit_rate', 'sample_rate')
        )
        
        if not chunks:
            return {}
            
        total_duration = sum(c['duration_seconds'] for c in chunks)
        total_size = sum(c['file_size'] for c in chunks)
        avg_bitrate = sum(c['bit_rate'] or 0 for c in chunks) / len(chunks)
        
        return {
            'total_duration_seconds': total_duration,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'average_bitrate': avg_bitrate,
            'chunk_count': len(chunks),
            'sample_rate': chunks[0]['sample_rate'] if chunks else 0
        }