"""
مدل‌های feedback app
برای ذخیره بازخورد کاربران، امتیازدهی جلسات و نظرسنجی‌ها
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

# Import BaseModel from app_standards
try:
    from app_standards.models.base_models import BaseModel, PatientRelatedModel
except ImportError:
    # Fallback if app_standards doesn't exist
    from django.db import models
    
    class BaseModel(models.Model):
        """مدل پایه موقت"""
        id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)
        is_active = models.BooleanField(default=True)
        
        class Meta:
            abstract = True

User = get_user_model()


class SessionRating(BaseModel):
    """
    مدل امتیازدهی جلسات چت
    برای ذخیره امتیاز و نظر کاربر درباره کیفیت جلسه
    """
    
    # اتصال به جلسه (فرض بر این است که ChatSession در chatbot app وجود دارد)
    session_id = models.UUIDField(
        verbose_name='شناسه جلسه',
        help_text='شناسه جلسه چت مرتبط'
    )
    
    # کاربر امتیازدهنده
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='session_ratings',
        verbose_name='کاربر'
    )
    
    # امتیاز کلی (1-5)
    overall_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='امتیاز کلی',
        help_text='امتیاز از 1 تا 5'
    )
    
    # امتیازات تفکیکی
    response_quality = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        verbose_name='کیفیت پاسخ‌ها',
        help_text='امتیاز کیفیت پاسخ‌های بات'
    )
    
    response_speed = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        verbose_name='سرعت پاسخ',
        help_text='امتیاز سرعت پاسخگویی'
    )
    
    helpfulness = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        verbose_name='مفید بودن',
        help_text='میزان مفید بودن جلسه'
    )
    
    # نظر متنی
    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name='نظر',
        help_text='نظر تفصیلی کاربر'
    )
    
    # پیشنهادات بهبود
    suggestions = models.TextField(
        blank=True,
        null=True,
        verbose_name='پیشنهادات',
        help_text='پیشنهادات کاربر برای بهبود'
    )
    
    # توصیه به دیگران
    would_recommend = models.BooleanField(
        null=True,
        blank=True,
        verbose_name='توصیه به دیگران',
        help_text='آیا این سرویس را به دیگران توصیه می‌کنید؟'
    )
    
    class Meta:
        verbose_name = 'امتیازدهی جلسه'
        verbose_name_plural = 'امتیازدهی جلسات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['user', 'overall_rating']),
            models.Index(fields=['created_at']),
        ]
        # یک کاربر فقط یک بار به هر جلسه امتیاز بدهد
        unique_together = ['session_id', 'user']
    
    def __str__(self):
        return f"امتیاز {self.overall_rating}/5 - جلسه {self.session_id} - {self.user}"


class MessageFeedback(BaseModel):
    """
    مدل بازخورد پیام‌های چت
    برای ذخیره بازخورد کاربر درباره پیام‌های خاص بات
    """
    
    # اتصال به پیام
    message_id = models.UUIDField(
        verbose_name='شناسه پیام',
        help_text='شناسه پیام چت مرتبط'
    )
    
    # کاربر بازخورددهنده
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='message_feedbacks',
        verbose_name='کاربر'
    )
    
    # نوع بازخورد
    FEEDBACK_TYPES = [
        ('helpful', 'مفید'),
        ('not_helpful', 'غیرمفید'),
        ('incorrect', 'نادرست'),
        ('incomplete', 'ناکامل'),
        ('inappropriate', 'نامناسب'),
        ('excellent', 'عالی'),
    ]
    
    feedback_type = models.CharField(
        max_length=20,
        choices=FEEDBACK_TYPES,
        verbose_name='نوع بازخورد'
    )
    
    # آیا پاسخ مفید بود
    is_helpful = models.BooleanField(
        null=True,
        blank=True,
        verbose_name='مفید بودن',
        help_text='آیا پاسخ مفید بود'
    )
    
    # نظر تفصیلی
    detailed_feedback = models.TextField(
        blank=True,
        null=True,
        verbose_name='بازخورد تفصیلی',
        help_text='توضیح تفصیلی بازخورد'
    )
    
    # پاسخ مورد انتظار
    expected_response = models.TextField(
        blank=True,
        null=True,
        verbose_name='پاسخ مورد انتظار',
        help_text='پاسخی که کاربر انتظار داشت'
    )
    
    class Meta:
        verbose_name = 'بازخورد پیام'
        verbose_name_plural = 'بازخوردهای پیام'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['message_id']),
            models.Index(fields=['user', 'feedback_type']),
            models.Index(fields=['is_helpful']),
        ]
        # یک کاربر فقط یک بار به هر پیام بازخورد بدهد
        unique_together = ['message_id', 'user']
    
    def __str__(self):
        return f"بازخورد {self.get_feedback_type_display()} - پیام {self.message_id} - {self.user}"


class Survey(BaseModel):
    """
    مدل نظرسنجی‌های سیستم
    برای ایجاد و مدیریت نظرسنجی‌های مختلف
    """
    
    # اطلاعات پایه نظرسنجی
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان نظرسنجی'
    )
    
    description = models.TextField(
        verbose_name='توضیحات',
        help_text='توضیح کامل نظرسنجی'
    )
    
    # تنظیمات نظرسنجی
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )
    
    start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاریخ شروع'
    )
    
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاریخ پایان'
    )
    
    # نوع نظرسنجی
    SURVEY_TYPES = [
        ('general', 'عمومی'),
        ('post_session', 'پس از جلسه'),
        ('periodic', 'دوره‌ای'),
        ('satisfaction', 'رضایت‌سنجی'),
        ('improvement', 'بهبود خدمات'),
    ]
    
    survey_type = models.CharField(
        max_length=20,
        choices=SURVEY_TYPES,
        default='general',
        verbose_name='نوع نظرسنجی'
    )
    
    # تنظیمات دسترسی
    target_users = models.CharField(
        max_length=20,
        choices=[
            ('all', 'همه کاربران'),
            ('patients', 'بیماران'),
            ('doctors', 'پزشکان'),
            ('premium', 'کاربران ویژه'),
        ],
        default='all',
        verbose_name='کاربران هدف'
    )
    
    # سوالات نظرسنجی (JSON field)
    questions = models.JSONField(
        default=list,
        verbose_name='سوالات',
        help_text='فهرست سوالات نظرسنجی'
    )
    
    # تنظیمات نمایش
    max_responses = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='حداکثر پاسخ',
        help_text='حداکثر تعداد پاسخ مجاز'
    )
    
    allow_anonymous = models.BooleanField(
        default=False,
        verbose_name='پاسخ ناشناس مجاز',
        help_text='آیا پاسخ ناشناس مجاز است؟'
    )
    
    class Meta:
        verbose_name = 'نظرسنجی'
        verbose_name_plural = 'نظرسنجی‌ها'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['survey_type', 'is_active']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['target_users']),
        ]
    
    def __str__(self):
        return self.title


class SurveyResponse(BaseModel):
    """
    مدل پاسخ‌های نظرسنجی
    برای ذخیره پاسخ‌های کاربران به نظرسنجی‌ها
    """
    
    # اتصال به نظرسنجی
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name='نظرسنجی'
    )
    
    # کاربر پاسخ‌دهنده
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='survey_responses',
        null=True,
        blank=True,
        verbose_name='کاربر',
        help_text='null در صورت پاسخ ناشناس'
    )
    
    # پاسخ‌ها
    answers = models.JSONField(
        default=dict,
        verbose_name='پاسخ‌ها',
        help_text='پاسخ‌های کاربر به سوالات'
    )
    
    # امتیاز کلی (در صورت وجود)
    overall_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name='امتیاز کلی',
        help_text='امتیاز محاسبه شده از پاسخ‌ها'
    )
    
    # زمان تکمیل
    completion_time = models.DurationField(
        null=True,
        blank=True,
        verbose_name='زمان تکمیل',
        help_text='مدت زمان صرف شده برای تکمیل'
    )
    
    # اطلاعات اضافی
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='متادیتا',
        help_text='اطلاعات اضافی مثل IP، user agent و...'
    )
    
    class Meta:
        verbose_name = 'پاسخ نظرسنجی'
        verbose_name_plural = 'پاسخ‌های نظرسنجی'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['survey', 'user']),
            models.Index(fields=['survey', 'overall_score']),
            models.Index(fields=['created_at']),
        ]
        # یک کاربر فقط یک بار به هر نظرسنجی پاسخ بدهد
        unique_together = ['survey', 'user']
    
    def __str__(self):
        user_display = self.user if self.user else 'ناشناس'
        return f"پاسخ به {self.survey.title} - {user_display}"


class FeedbackSettings(BaseModel):
    """
    مدل تنظیمات feedback app
    برای ذخیره تنظیمات مربوط به بازخورد و نظرسنجی‌ها
    """
    
    # نام تنظیمات
    key = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='کلید تنظیمات'
    )
    
    # مقدار
    value = models.JSONField(
        verbose_name='مقدار',
        help_text='مقدار تنظیمات'
    )
    
    # توضیحات
    description = models.TextField(
        blank=True,
        verbose_name='توضیحات'
    )
    
    # نوع تنظیمات
    SETTING_TYPES = [
        ('general', 'عمومی'),
        ('rating', 'امتیازدهی'),
        ('survey', 'نظرسنجی'),
        ('notification', 'اعلان‌ها'),
    ]
    
    setting_type = models.CharField(
        max_length=20,
        choices=SETTING_TYPES,
        default='general',
        verbose_name='نوع تنظیمات'
    )
    
    class Meta:
        verbose_name = 'تنظیمات بازخورد'
        verbose_name_plural = 'تنظیمات بازخورد'
        ordering = ['setting_type', 'key']
    
    def __str__(self):
        return f"{self.key} - {self.get_setting_type_display()}"