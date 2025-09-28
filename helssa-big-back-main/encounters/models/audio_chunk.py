from django.db import models
from django.utils import timezone
import uuid


class AudioChunk(models.Model):
    """مدل قطعات صوتی ضبط شده"""
    
    TRANSCRIPTION_STATUS = [
        ('pending', 'در انتظار'),
        ('processing', 'در حال پردازش'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق'),
    ]
    
    AUDIO_FORMATS = [
        ('webm', 'WebM'),
        ('mp3', 'MP3'),
        ('wav', 'WAV'),
        ('ogg', 'OGG'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    encounter = models.ForeignKey(
        'Encounter',
        on_delete=models.CASCADE,
        related_name='audio_chunks',
        verbose_name='ملاقات'
    )
    
    # مشخصات فایل
    chunk_index = models.IntegerField(
        verbose_name='شماره قطعه',
        help_text="شماره ترتیبی قطعه"
    )
    file_url = models.URLField(
        verbose_name='آدرس فایل',
        help_text="آدرس فایل در MinIO"
    )
    file_size = models.IntegerField(
        verbose_name='حجم فایل',
        help_text="حجم فایل به بایت"
    )
    duration_seconds = models.FloatField(
        verbose_name='مدت زمان',
        help_text="مدت زمان قطعه به ثانیه"
    )
    
    # فرمت و کیفیت
    format = models.CharField(
        max_length=10,
        default='webm',
        choices=AUDIO_FORMATS,
        verbose_name='فرمت'
    )
    sample_rate = models.IntegerField(
        default=48000,
        verbose_name='نرخ نمونه‌برداری'
    )
    bit_rate = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='نرخ بیت'
    )
    
    # وضعیت پردازش
    is_processed = models.BooleanField(
        default=False,
        verbose_name='پردازش شده'
    )
    transcription_status = models.CharField(
        max_length=20,
        choices=TRANSCRIPTION_STATUS,
        default='pending',
        verbose_name='وضعیت رونویسی'
    )
    
    # رمزنگاری
    is_encrypted = models.BooleanField(
        default=True,
        verbose_name='رمزنگاری شده'
    )
    encryption_metadata = models.JSONField(
        default=dict,
        verbose_name='اطلاعات رمزنگاری',
        help_text="اطلاعات رمزنگاری"
    )
    
    # زمان‌ها
    recorded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='زمان ضبط'
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان پردازش'
    )
    
    class Meta:
        db_table = 'audio_chunks'
        verbose_name = 'قطعه صوتی'
        verbose_name_plural = 'قطعات صوتی'
        unique_together = [['encounter', 'chunk_index']]
        ordering = ['encounter', 'chunk_index']
        
    def __str__(self):
        return f"قطعه {self.chunk_index} از ملاقات {self.encounter_id}"
        
    @property
    def is_ready_for_transcription(self) -> bool:
        """آیا قطعه آماده رونویسی است"""
        return (
            self.is_encrypted and 
            self.file_url and 
            self.transcription_status == 'pending'
        )
        
    def mark_as_processed(self):
        """علامت‌گذاری به عنوان پردازش شده"""
        self.is_processed = True
        self.processed_at = timezone.now()
        self.save(update_fields=['is_processed', 'processed_at'])