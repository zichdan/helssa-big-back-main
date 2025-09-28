"""
مدل پایه برای سیستم مالی
Base Model for Financial System
"""

from django.db import models
from django.utils import timezone
import uuid


class BaseModel(models.Model):
    """مدل پایه برای تمام مدل‌های سیستم مالی"""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='شناسه'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='زمان ایجاد'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='زمان آخرین به‌روزرسانی'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='متادیتا'
    )
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.__class__.__name__} - {self.id}"
        
    def save(self, *args, **kwargs):
        """ذخیره با به‌روزرسانی زمان"""
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)