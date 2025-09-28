"""
Serializers برای امتیازدهی جلسات
"""

from rest_framework import serializers
from django.core.validators import MinValueValidator, MaxValueValidator
from ..models import SessionRating

# Import base serializer if available
try:
    from app_standards.serializers.base_serializers import BaseModelSerializer
except ImportError:
    # Fallback if app_standards doesn't exist
    from rest_framework import serializers
    
    class BaseModelSerializer(serializers.ModelSerializer):
        """سریالایزر پایه موقت"""
        
        class Meta:
            abstract = True
            read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')


class SessionRatingCreateSerializer(serializers.Serializer):
    """
    سریالایزر ایجاد امتیازدهی جلسه
    """
    
    session_id = serializers.UUIDField(
        help_text="شناسه جلسه چت"
    )
    
    overall_rating = serializers.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="امتیاز کلی از 1 تا 5"
    )
    
    response_quality = serializers.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        required=False,
        allow_null=True,
        help_text="امتیاز کیفیت پاسخ‌ها"
    )
    
    response_speed = serializers.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        required=False,
        allow_null=True,
        help_text="امتیاز سرعت پاسخگویی"
    )
    
    helpfulness = serializers.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        required=False,
        allow_null=True,
        help_text="امتیاز مفید بودن"
    )
    
    comment = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
        help_text="نظر تفصیلی"
    )
    
    suggestions = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
        help_text="پیشنهادات بهبود"
    )
    
    would_recommend = serializers.BooleanField(
        required=False,
        allow_null=True,
        help_text="توصیه به دیگران"
    )
    
    def validate(self, data):
        """اعتبارسنجی کلی داده‌ها"""
        
        # بررسی اینکه حداقل امتیاز کلی وجود دارد
        if not data.get('overall_rating'):
            raise serializers.ValidationError({
                'overall_rating': 'امتیاز کلی اجباری است'
            })
        
        # بررسی منطقی بودن امتیازات
        rating_fields = ['overall_rating', 'response_quality', 'response_speed', 'helpfulness']
        for field in rating_fields:
            value = data.get(field)
            if value is not None and (value < 1 or value > 5):
                raise serializers.ValidationError({
                    field: 'امتیاز باید بین 1 تا 5 باشد'
                })
        
        # تمیز کردن متن‌ها
        text_fields = ['comment', 'suggestions']
        for field in text_fields:
            if field in data and data[field]:
                data[field] = data[field].strip()
        
        return data
    
    def validate_session_id(self, value):
        """اعتبارسنجی شناسه جلسه"""
        # در پیاده‌سازی واقعی، بررسی می‌شود که جلسه وجود دارد
        if not value:
            raise serializers.ValidationError("شناسه جلسه نامعتبر است")
        return value
    
    def validate_comment(self, value):
        """اعتبارسنجی نظر"""
        if value and len(value.strip()) < 3:
            raise serializers.ValidationError("نظر باید حداقل 3 کاراکتر باشد")
        return value


class SessionRatingUpdateSerializer(serializers.Serializer):
    """
    سریالایزر ویرایش امتیازدهی جلسه
    """
    
    overall_rating = serializers.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        required=False,
        help_text="امتیاز کلی از 1 تا 5"
    )
    
    response_quality = serializers.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        required=False,
        allow_null=True,
        help_text="امتیاز کیفیت پاسخ‌ها"
    )
    
    response_speed = serializers.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        required=False,
        allow_null=True,
        help_text="امتیاز سرعت پاسخگویی"
    )
    
    helpfulness = serializers.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        required=False,
        allow_null=True,
        help_text="امتیاز مفید بودن"
    )
    
    comment = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
        help_text="نظر تفصیلی"
    )
    
    suggestions = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
        help_text="پیشنهادات بهبود"
    )
    
    would_recommend = serializers.BooleanField(
        required=False,
        allow_null=True,
        help_text="توصیه به دیگران"
    )


class SessionRatingSerializer(BaseModelSerializer):
    """
    سریالایزر نمایش امتیازدهی جلسه
    """
    
    user_display = serializers.SerializerMethodField(
        help_text="نمایش کاربر"
    )
    
    rating_summary = serializers.SerializerMethodField(
        help_text="خلاصه امتیازدهی"
    )
    
    class Meta:
        model = SessionRating
        fields = [
            'id', 'session_id', 'user', 'user_display',
            'overall_rating', 'response_quality', 'response_speed', 'helpfulness',
            'comment', 'suggestions', 'would_recommend',
            'rating_summary', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']
    
    def get_user_display(self, obj):
        """نمایش اطلاعات کاربر"""
        if hasattr(obj, 'user') and obj.user:
            return {
                'id': str(obj.user.id),
                'name': getattr(obj.user, 'get_full_name', lambda: 'کاربر')() or 'کاربر',
                'phone': getattr(obj.user, 'phone_number', None)
            }
        return None
    
    def get_rating_summary(self, obj):
        """خلاصه امتیازدهی"""
        detailed_ratings = []
        if obj.response_quality:
            detailed_ratings.append(obj.response_quality)
        if obj.response_speed:
            detailed_ratings.append(obj.response_speed)
        if obj.helpfulness:
            detailed_ratings.append(obj.helpfulness)
        
        average_detailed = sum(detailed_ratings) / len(detailed_ratings) if detailed_ratings else None
        
        return {
            'overall': obj.overall_rating,
            'average_detailed': round(average_detailed, 1) if average_detailed else None,
            'has_comment': bool(obj.comment),
            'has_suggestions': bool(obj.suggestions),
            'recommends': obj.would_recommend
        }


class SessionRatingListSerializer(serializers.ModelSerializer):
    """
    سریالایزر فهرست امتیازدهی‌ها (سبک‌تر)
    """
    
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = SessionRating
        fields = [
            'id', 'session_id', 'user_name', 'overall_rating',
            'would_recommend', 'created_at'
        ]
    
    def get_user_name(self, obj):
        """نام کاربر"""
        if hasattr(obj, 'user') and obj.user:
            return getattr(obj.user, 'get_full_name', lambda: 'کاربر')() or 'کاربر'
        return 'کاربر'


class SessionRatingStatsSerializer(serializers.Serializer):
    """
    سریالایزر آمار امتیازدهی
    """
    
    total_ratings = serializers.IntegerField(
        help_text="تعداد کل امتیازدهی‌ها"
    )
    
    average_overall = serializers.FloatField(
        help_text="میانگین امتیاز کلی"
    )
    
    average_quality = serializers.FloatField(
        allow_null=True,
        help_text="میانگین امتیاز کیفیت"
    )
    
    average_speed = serializers.FloatField(
        allow_null=True,
        help_text="میانگین امتیاز سرعت"
    )
    
    average_helpfulness = serializers.FloatField(
        allow_null=True,
        help_text="میانگین امتیاز مفید بودن"
    )
    
    recommendation_rate = serializers.FloatField(
        help_text="درصد توصیه"
    )
    
    rating_distribution = serializers.DictField(
        help_text="توزیع امتیازات"
    )
    
    recent_comments = serializers.ListField(
        child=serializers.CharField(),
        help_text="آخرین نظرات"
    )


class VoiceRatingSerializer(serializers.Serializer):
    """
    سریالایزر امتیازدهی صوتی
    """
    
    session_id = serializers.UUIDField(
        help_text="شناسه جلسه"
    )
    
    audio_file = serializers.FileField(
        help_text="فایل صوتی امتیازدهی"
    )
    
    def validate_audio_file(self, value):
        """اعتبارسنجی فایل صوتی"""
        if not value:
            raise serializers.ValidationError("فایل صوتی اجباری است")
        
        # بررسی فرمت
        allowed_formats = ['wav', 'mp3', 'webm', 'ogg']
        file_extension = value.name.split('.')[-1].lower() if '.' in value.name else ''
        
        if file_extension not in allowed_formats:
            raise serializers.ValidationError(
                f"فرمت فایل پشتیبانی نمی‌شود. فرمت‌های مجاز: {', '.join(allowed_formats)}"
            )
        
        # بررسی اندازه (حداکثر 10MB)
        max_size = 10 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("حجم فایل نباید بیش از 10 مگابایت باشد")
        
        return value