from django.db import models
import uuid


class EncounterFile(models.Model):
    """مدل فایل‌های مرتبط با ملاقات"""
    
    FILE_TYPES = [
        ('audio', 'صوتی'),
        ('image', 'تصویر'),
        ('document', 'سند'),
        ('video', 'ویدیو'),
        ('lab_result', 'نتیجه آزمایش'),
        ('radiology', 'رادیولوژی'),
        ('other', 'سایر'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    encounter = models.ForeignKey(
        'Encounter',
        on_delete=models.CASCADE,
        related_name='files',
        verbose_name='ملاقات'
    )
    
    # اطلاعات فایل
    file_name = models.CharField(
        max_length=255,
        verbose_name='نام فایل'
    )
    file_type = models.CharField(
        max_length=20,
        choices=FILE_TYPES,
        verbose_name='نوع فایل'
    )
    mime_type = models.CharField(
        max_length=100,
        verbose_name='نوع MIME'
    )
    file_url = models.URLField(
        verbose_name='آدرس فایل'
    )
    file_size = models.IntegerField(
        verbose_name='حجم فایل',
        help_text="حجم به بایت"
    )
    file_hash = models.CharField(
        max_length=64,
        verbose_name='هش فایل',
        help_text="SHA256 hash"
    )
    
    # آپلود کننده
    uploaded_by = models.ForeignKey(
        'unified_auth.UnifiedUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_encounter_files',
        verbose_name='آپلود کننده'
    )
    
    # امنیت
    is_encrypted = models.BooleanField(
        default=True,
        verbose_name='رمزنگاری شده'
    )
    
    # توضیحات
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='توضیحات'
    )
    
    # metadata
    metadata = models.JSONField(
        default=dict,
        verbose_name='اطلاعات اضافی'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ آپلود'
    )
    
    class Meta:
        db_table = 'encounter_files'
        verbose_name = 'فایل ملاقات'
        verbose_name_plural = 'فایل‌های ملاقات'
        indexes = [
            models.Index(fields=['encounter', 'file_type']),
            models.Index(fields=['file_hash']),
        ]
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.file_name} - {self.get_file_type_display()}"
        
    @property
    def file_size_mb(self) -> float:
        """حجم فایل به مگابایت"""
        return round(self.file_size / (1024 * 1024), 2)
        
    @property
    def is_medical_document(self) -> bool:
        """آیا سند پزشکی است"""
        return self.file_type in ['lab_result', 'radiology']