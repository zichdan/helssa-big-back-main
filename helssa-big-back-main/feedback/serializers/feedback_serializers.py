"""
Serializers برای بازخورد پیام‌ها
"""

from rest_framework import serializers
from ..models import MessageFeedback

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


class MessageFeedbackCreateSerializer(serializers.Serializer):
    """
    سریالایزر ایجاد بازخورد پیام
    """
    
    message_id = serializers.UUIDField(
        help_text="شناسه پیام چت"
    )
    
    feedback_type = serializers.ChoiceField(
        choices=MessageFeedback.FEEDBACK_TYPES,
        help_text="نوع بازخورد"
    )
    
    is_helpful = serializers.BooleanField(
        required=False,
        allow_null=True,
        help_text="آیا پاسخ مفید بود"
    )
    
    detailed_feedback = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="بازخورد تفصیلی"
    )
    
    expected_response = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="پاسخ مورد انتظار"
    )
    
    def validate(self, data):
        """اعتبارسنجی کلی داده‌ها"""
        
        # بررسی وجود فیلدهای اجباری
        if not data.get('message_id'):
            raise serializers.ValidationError({
                'message_id': 'شناسه پیام اجباری است'
            })
        
        if not data.get('feedback_type'):
            raise serializers.ValidationError({
                'feedback_type': 'نوع بازخورد اجباری است'
            })
        
        # تمیز کردن متن‌ها
        text_fields = ['detailed_feedback', 'expected_response']
        for field in text_fields:
            if field in data and data[field]:
                data[field] = data[field].strip()
        
        # بررسی منطقی
        feedback_type = data.get('feedback_type')
        is_helpful = data.get('is_helpful')
        
        # اگر نوع بازخورد "مفید" است، is_helpful باید True باشد
        if feedback_type == 'helpful' and is_helpful is False:
            raise serializers.ValidationError({
                'is_helpful': 'برای بازخورد مفید، این فیلد باید True باشد'
            })
        
        # اگر نوع بازخورد "غیرمفید" است، is_helpful باید False باشد
        if feedback_type == 'not_helpful' and is_helpful is True:
            raise serializers.ValidationError({
                'is_helpful': 'برای بازخورد غیرمفید، این فیلد باید False باشد'
            })
        
        return data
    
    def validate_message_id(self, value):
        """اعتبارسنجی شناسه پیام"""
        # در پیاده‌سازی واقعی، بررسی می‌شود که پیام وجود دارد
        if not value:
            raise serializers.ValidationError("شناسه پیام نامعتبر است")
        return value
    
    def validate_detailed_feedback(self, value):
        """اعتبارسنجی بازخورد تفصیلی"""
        if value and len(value.strip()) < 5:
            raise serializers.ValidationError("بازخورد تفصیلی باید حداقل 5 کاراکتر باشد")
        return value


class MessageFeedbackUpdateSerializer(serializers.Serializer):
    """
    سریالایزر ویرایش بازخورد پیام
    """
    
    feedback_type = serializers.ChoiceField(
        choices=MessageFeedback.FEEDBACK_TYPES,
        required=False,
        help_text="نوع بازخورد"
    )
    
    is_helpful = serializers.BooleanField(
        required=False,
        allow_null=True,
        help_text="آیا پاسخ مفید بود"
    )
    
    detailed_feedback = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="بازخورد تفصیلی"
    )
    
    expected_response = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="پاسخ مورد انتظار"
    )


class MessageFeedbackSerializer(BaseModelSerializer):
    """
    سریالایزر نمایش بازخورد پیام
    """
    
    user_display = serializers.SerializerMethodField(
        help_text="نمایش کاربر"
    )
    
    feedback_type_display = serializers.CharField(
        source='get_feedback_type_display',
        read_only=True,
        help_text="نمایش نوع بازخورد"
    )
    
    sentiment_analysis = serializers.SerializerMethodField(
        help_text="تحلیل احساسات"
    )
    
    class Meta:
        model = MessageFeedback
        fields = [
            'id', 'message_id', 'user', 'user_display',
            'feedback_type', 'feedback_type_display', 'is_helpful',
            'detailed_feedback', 'expected_response',
            'sentiment_analysis', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']
    
    def get_user_display(self, obj):
        """نمایش اطلاعات کاربر"""
        if hasattr(obj, 'user') and obj.user:
            return {
                'id': str(obj.user.id),
                'name': getattr(obj.user, 'get_full_name', lambda: 'کاربر')() or 'کاربر'
            }
        return None
    
    def get_sentiment_analysis(self, obj):
        """تحلیل احساسات بازخورد"""
        # در پیاده‌سازی واقعی، از text processor استفاده می‌شود
        if obj.detailed_feedback:
            # شبیه‌سازی تحلیل احساسات
            text = obj.detailed_feedback.lower()
            if any(word in text for word in ['خوب', 'عالی', 'مفید']):
                return {'sentiment': 'positive', 'confidence': 0.8}
            elif any(word in text for word in ['بد', 'ضعیف', 'غیرمفید']):
                return {'sentiment': 'negative', 'confidence': 0.8}
            else:
                return {'sentiment': 'neutral', 'confidence': 0.6}
        return None


class MessageFeedbackListSerializer(serializers.ModelSerializer):
    """
    سریالایزر فهرست بازخوردها (سبک‌تر)
    """
    
    user_name = serializers.SerializerMethodField()
    feedback_type_display = serializers.CharField(
        source='get_feedback_type_display',
        read_only=True
    )
    
    class Meta:
        model = MessageFeedback
        fields = [
            'id', 'message_id', 'user_name', 'feedback_type',
            'feedback_type_display', 'is_helpful', 'created_at'
        ]
    
    def get_user_name(self, obj):
        """نام کاربر"""
        if hasattr(obj, 'user') and obj.user:
            return getattr(obj.user, 'get_full_name', lambda: 'کاربر')() or 'کاربر'
        return 'کاربر'


class MessageFeedbackStatsSerializer(serializers.Serializer):
    """
    سریالایزر آمار بازخورد پیام‌ها
    """
    
    total_feedbacks = serializers.IntegerField(
        help_text="تعداد کل بازخوردها"
    )
    
    helpful_percentage = serializers.FloatField(
        help_text="درصد بازخوردهای مفید"
    )
    
    feedback_type_distribution = serializers.DictField(
        help_text="توزیع انواع بازخورد"
    )
    
    sentiment_distribution = serializers.DictField(
        help_text="توزیع احساسات"
    )
    
    common_issues = serializers.ListField(
        child=serializers.CharField(),
        help_text="مشکلات رایج"
    )
    
    improvement_suggestions = serializers.ListField(
        child=serializers.CharField(),
        help_text="پیشنهادات بهبود"
    )


class VoiceFeedbackSerializer(serializers.Serializer):
    """
    سریالایزر بازخورد صوتی
    """
    
    message_id = serializers.UUIDField(
        help_text="شناسه پیام"
    )
    
    audio_file = serializers.FileField(
        help_text="فایل صوتی بازخورد"
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
        
        # بررسی اندازه (حداکثر 5MB برای بازخورد)
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("حجم فایل نباید بیش از 5 مگابایت باشد")
        
        return value


class FeedbackAnalyticsSerializer(serializers.Serializer):
    """
    سریالایزر آنالیتیک جامع بازخورد
    """
    
    date_range = serializers.DictField(
        help_text="بازه زمانی"
    )
    
    total_messages = serializers.IntegerField(
        help_text="تعداد کل پیام‌ها"
    )
    
    feedback_coverage = serializers.FloatField(
        help_text="درصد پوشش بازخورد"
    )
    
    satisfaction_metrics = serializers.DictField(
        help_text="شاخص‌های رضایت"
    )
    
    trending_issues = serializers.ListField(
        child=serializers.DictField(),
        help_text="مسائل در حال رشد"
    )
    
    user_engagement = serializers.DictField(
        help_text="تعامل کاربران"
    )
    
    ai_performance = serializers.DictField(
        help_text="عملکرد هوش مصنوعی"
    )


class BulkFeedbackSerializer(serializers.Serializer):
    """
    سریالایزر بازخورد گروهی
    """
    
    feedbacks = serializers.ListField(
        child=MessageFeedbackCreateSerializer(),
        min_length=1,
        max_length=50,
        help_text="فهرست بازخوردها (حداکثر 50)"
    )
    
    def validate_feedbacks(self, value):
        """اعتبارسنجی فهرست بازخوردها"""
        message_ids = [item.get('message_id') for item in value]
        
        # بررسی تکراری نبودن
        if len(message_ids) != len(set(message_ids)):
            raise serializers.ValidationError("شناسه پیام‌ها نباید تکراری باشند")
        
        return value