from django.db import models
import uuid


class Transcript(models.Model):
    """مدل رونویسی صوت"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    audio_chunk = models.OneToOneField(
        'AudioChunk',
        on_delete=models.CASCADE,
        related_name='transcript',
        verbose_name='قطعه صوتی'
    )
    
    # متن رونویسی
    text = models.TextField(
        verbose_name='متن رونویسی',
        help_text="متن رونویسی شده"
    )
    language = models.CharField(
        max_length=5,
        default='fa',
        verbose_name='زبان',
        help_text="زبان تشخیص داده شده"
    )
    
    # کیفیت و دقت
    confidence_score = models.FloatField(
        default=0.0,
        verbose_name='امتیاز اطمینان',
        help_text="امتیاز اطمینان (0-1)"
    )
    word_timestamps = models.JSONField(
        default=list,
        verbose_name='زمان‌بندی کلمات',
        help_text="زمان‌بندی کلمات"
    )
    
    # Speaker Diarization
    speakers = models.JSONField(
        default=dict,
        verbose_name='گوینده‌ها',
        help_text="تشخیص گوینده‌ها"
    )
    
    # پردازش‌های اضافی
    medical_entities = models.JSONField(
        default=dict,
        verbose_name='موجودیت‌های پزشکی',
        help_text="موجودیت‌های پزشکی استخراج شده"
    )
    corrections = models.JSONField(
        default=list,
        verbose_name='اصلاحات',
        help_text="اصلاحات دستی"
    )
    
    # metadata
    stt_model = models.CharField(
        max_length=50,
        default='whisper-1',
        verbose_name='مدل STT'
    )
    processing_time = models.FloatField(
        null=True,
        blank=True,
        verbose_name='زمان پردازش',
        help_text="زمان پردازش به ثانیه"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ایجاد'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاریخ به‌روزرسانی'
    )
    
    class Meta:
        db_table = 'transcripts'
        verbose_name = 'رونویسی'
        verbose_name_plural = 'رونویسی‌ها'
        indexes = [
            models.Index(fields=['audio_chunk', 'language']),
        ]
        
    def __str__(self):
        return f"رونویسی قطعه {self.audio_chunk.chunk_index}"
        
    @property
    def word_count(self) -> int:
        """تعداد کلمات"""
        return len(self.text.split())
        
    @property
    def has_medical_entities(self) -> bool:
        """آیا موجودیت پزشکی دارد"""
        return bool(self.medical_entities.get('entities', []))
        
    @property
    def is_high_confidence(self) -> bool:
        """آیا اطمینان بالایی دارد"""
        return self.confidence_score >= 0.8
        
    def add_correction(self, original_text: str, corrected_text: str, corrected_by: str):
        """افزودن اصلاح به رونویسی"""
        correction = {
            'original': original_text,
            'corrected': corrected_text,
            'corrected_by': corrected_by,
            'corrected_at': timezone.now().isoformat()
        }
        self.corrections.append(correction)
        
        # اعمال اصلاح در متن اصلی
        self.text = self.text.replace(original_text, corrected_text)
        self.save()