"""
Serializers برای نظرسنجی‌ها
"""

from rest_framework import serializers
from django.utils import timezone
from ..models import Survey, SurveyResponse

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


class SurveyQuestionSerializer(serializers.Serializer):
    """
    سریالایزر سوالات نظرسنجی
    """
    
    id = serializers.CharField(
        max_length=50,
        help_text="شناسه سوال"
    )
    
    text = serializers.CharField(
        max_length=500,
        help_text="متن سوال"
    )
    
    type = serializers.ChoiceField(
        choices=[
            ('text', 'متن'),
            ('textarea', 'متن طولانی'),
            ('number', 'عدد'),
            ('rating', 'امتیاز'),
            ('choice', 'چندگزینه‌ای'),
            ('multiple_choice', 'چندگزینه‌ای (چند انتخاب)'),
            ('boolean', 'بله/خیر'),
            ('date', 'تاریخ'),
        ],
        help_text="نوع سوال"
    )
    
    required = serializers.BooleanField(
        default=True,
        help_text="اجباری بودن"
    )
    
    options = serializers.ListField(
        child=serializers.CharField(max_length=200),
        required=False,
        help_text="گزینه‌ها (برای سوالات چندگزینه‌ای)"
    )
    
    min_value = serializers.IntegerField(
        required=False,
        help_text="حداقل مقدار (برای عدد و امتیاز)"
    )
    
    max_value = serializers.IntegerField(
        required=False,
        help_text="حداکثر مقدار (برای عدد و امتیاز)"
    )
    
    placeholder = serializers.CharField(
        max_length=200,
        required=False,
        help_text="متن راهنما"
    )
    
    def validate(self, data):
        """اعتبارسنجی سوال"""
        
        question_type = data.get('type')
        
        # بررسی گزینه‌ها برای سوالات چندگزینه‌ای
        if question_type in ['choice', 'multiple_choice']:
            if not data.get('options') or len(data['options']) < 2:
                raise serializers.ValidationError(
                    "سوالات چندگزینه‌ای باید حداقل 2 گزینه داشته باشند"
                )
        
        # بررسی محدوده برای امتیاز
        if question_type == 'rating':
            min_val = data.get('min_value', 1)
            max_val = data.get('max_value', 5)
            
            if min_val >= max_val:
                raise serializers.ValidationError(
                    "حداقل مقدار باید کمتر از حداکثر مقدار باشد"
                )
        
        return data


class SurveyCreateSerializer(serializers.Serializer):
    """
    سریالایزر ایجاد نظرسنجی
    """
    
    title = serializers.CharField(
        max_length=200,
        help_text="عنوان نظرسنجی"
    )
    
    description = serializers.CharField(
        max_length=1000,
        help_text="توضیحات نظرسنجی"
    )
    
    survey_type = serializers.ChoiceField(
        choices=Survey.SURVEY_TYPES,
        default='general',
        help_text="نوع نظرسنجی"
    )
    
    target_users = serializers.ChoiceField(
        choices=[
            ('all', 'همه کاربران'),
            ('patients', 'بیماران'),
            ('doctors', 'پزشکان'),
            ('premium', 'کاربران ویژه'),
        ],
        default='all',
        help_text="کاربران هدف"
    )
    
    questions = serializers.ListField(
        child=SurveyQuestionSerializer(),
        min_length=1,
        help_text="فهرست سوالات"
    )
    
    start_date = serializers.DateTimeField(
        required=False,
        help_text="تاریخ شروع"
    )
    
    end_date = serializers.DateTimeField(
        required=False,
        help_text="تاریخ پایان"
    )
    
    max_responses = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="حداکثر تعداد پاسخ"
    )
    
    allow_anonymous = serializers.BooleanField(
        default=False,
        help_text="امکان پاسخ ناشناس"
    )
    
    is_active = serializers.BooleanField(
        default=True,
        help_text="فعال بودن"
    )
    
    def validate(self, data):
        """اعتبارسنجی کلی"""
        
        # بررسی تاریخ‌ها
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise serializers.ValidationError(
                    "تاریخ شروع باید قبل از تاریخ پایان باشد"
                )
        
        # بررسی شناسه‌های یکتا برای سوالات
        question_ids = [q.get('id') for q in data.get('questions', [])]
        if len(question_ids) != len(set(question_ids)):
            raise serializers.ValidationError(
                "شناسه سوالات باید یکتا باشند"
            )
        
        return data
    
    def validate_title(self, value):
        """اعتبارسنجی عنوان"""
        if len(value.strip()) < 5:
            raise serializers.ValidationError(
                "عنوان نظرسنجی باید حداقل 5 کاراکتر باشد"
            )
        return value.strip()


class SurveyUpdateSerializer(serializers.Serializer):
    """
    سریالایزر ویرایش نظرسنجی
    """
    
    title = serializers.CharField(
        max_length=200,
        required=False,
        help_text="عنوان نظرسنجی"
    )
    
    description = serializers.CharField(
        max_length=1000,
        required=False,
        help_text="توضیحات نظرسنجی"
    )
    
    is_active = serializers.BooleanField(
        required=False,
        help_text="فعال بودن"
    )
    
    start_date = serializers.DateTimeField(
        required=False,
        help_text="تاریخ شروع"
    )
    
    end_date = serializers.DateTimeField(
        required=False,
        help_text="تاریخ پایان"
    )
    
    max_responses = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="حداکثر تعداد پاسخ"
    )


class SurveySerializer(BaseModelSerializer):
    """
    سریالایزر نمایش نظرسنجی
    """
    
    survey_type_display = serializers.CharField(
        source='get_survey_type_display',
        read_only=True,
        help_text="نمایش نوع نظرسنجی"
    )
    
    questions_count = serializers.SerializerMethodField(
        help_text="تعداد سوالات"
    )
    
    responses_count = serializers.SerializerMethodField(
        help_text="تعداد پاسخ‌ها"
    )
    
    is_available = serializers.SerializerMethodField(
        help_text="در دسترس بودن"
    )
    
    completion_rate = serializers.SerializerMethodField(
        help_text="نرخ تکمیل"
    )
    
    class Meta:
        model = Survey
        fields = [
            'id', 'title', 'description', 'survey_type', 'survey_type_display',
            'target_users', 'questions', 'start_date', 'end_date',
            'max_responses', 'allow_anonymous', 'is_active',
            'questions_count', 'responses_count', 'is_available', 'completion_rate',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_questions_count(self, obj):
        """تعداد سوالات"""
        return len(obj.questions) if obj.questions else 0
    
    def get_responses_count(self, obj):
        """تعداد پاسخ‌ها"""
        return obj.responses.count() if hasattr(obj, 'responses') else 0
    
    def get_is_available(self, obj):
        """بررسی در دسترس بودن"""
        now = timezone.now()
        
        # بررسی فعال بودن
        if not obj.is_active:
            return False
        
        # بررسی تاریخ شروع
        if obj.start_date and now < obj.start_date:
            return False
        
        # بررسی تاریخ پایان
        if obj.end_date and now > obj.end_date:
            return False
        
        # بررسی حداکثر پاسخ
        if obj.max_responses:
            responses_count = self.get_responses_count(obj)
            if responses_count >= obj.max_responses:
                return False
        
        return True
    
    def get_completion_rate(self, obj):
        """نرخ تکمیل"""
        # در پیاده‌سازی واقعی، محاسبه دقیق‌تر انجام می‌شود
        return 85.5  # مقدار نمونه


class SurveyListSerializer(serializers.ModelSerializer):
    """
    سریالایزر فهرست نظرسنجی‌ها (سبک‌تر)
    """
    
    survey_type_display = serializers.CharField(
        source='get_survey_type_display',
        read_only=True
    )
    
    responses_count = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    
    class Meta:
        model = Survey
        fields = [
            'id', 'title', 'survey_type', 'survey_type_display',
            'target_users', 'is_active', 'responses_count', 'is_available',
            'created_at'
        ]
    
    def get_responses_count(self, obj):
        return obj.responses.count() if hasattr(obj, 'responses') else 0
    
    def get_is_available(self, obj):
        now = timezone.now()
        if not obj.is_active:
            return False
        if obj.start_date and now < obj.start_date:
            return False
        if obj.end_date and now > obj.end_date:
            return False
        return True


class SurveyResponseCreateSerializer(serializers.Serializer):
    """
    سریالایزر ایجاد پاسخ نظرسنجی
    """
    
    survey_id = serializers.UUIDField(
        help_text="شناسه نظرسنجی"
    )
    
    answers = serializers.JSONField(
        help_text="پاسخ‌های کاربر"
    )
    
    completion_time = serializers.DurationField(
        required=False,
        help_text="زمان تکمیل"
    )
    
    def validate_answers(self, value):
        """اعتبارسنجی پاسخ‌ها"""
        if not isinstance(value, dict) or not value:
            raise serializers.ValidationError("پاسخ‌ها باید یک object غیرخالی باشند")
        
        return value
    
    def validate(self, data):
        """اعتبارسنجی کلی"""
        survey_id = data.get('survey_id')
        answers = data.get('answers', {})
        
        # در پیاده‌سازی واقعی، نظرسنجی از دیتابیس بارگذاری و اعتبارسنجی می‌شود
        
        return data


class SurveyResponseSerializer(BaseModelSerializer):
    """
    سریالایزر نمایش پاسخ نظرسنجی
    """
    
    survey_title = serializers.SerializerMethodField(
        help_text="عنوان نظرسنجی"
    )
    
    user_display = serializers.SerializerMethodField(
        help_text="نمایش کاربر"
    )
    
    answers_summary = serializers.SerializerMethodField(
        help_text="خلاصه پاسخ‌ها"
    )
    
    class Meta:
        model = SurveyResponse
        fields = [
            'id', 'survey', 'survey_title', 'user', 'user_display',
            'answers', 'answers_summary', 'overall_score', 'completion_time',
            'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']
    
    def get_survey_title(self, obj):
        """عنوان نظرسنجی"""
        return obj.survey.title if obj.survey else None
    
    def get_user_display(self, obj):
        """نمایش کاربر"""
        if obj.user:
            return {
                'id': str(obj.user.id),
                'name': getattr(obj.user, 'get_full_name', lambda: 'کاربر')() or 'کاربر'
            }
        return {'name': 'ناشناس'}
    
    def get_answers_summary(self, obj):
        """خلاصه پاسخ‌ها"""
        if not obj.answers:
            return {}
        
        summary = {
            'total_questions': len(obj.answers),
            'answered_questions': len([v for v in obj.answers.values() if v]),
            'text_responses': len([v for v in obj.answers.values() if isinstance(v, str) and v.strip()]),
            'numeric_responses': len([v for v in obj.answers.values() if isinstance(v, (int, float))])
        }
        
        summary['completion_percentage'] = (
            summary['answered_questions'] / summary['total_questions'] * 100
            if summary['total_questions'] > 0 else 0
        )
        
        return summary


class SurveyStatsSerializer(serializers.Serializer):
    """
    سریالایزر آمار نظرسنجی
    """
    
    total_responses = serializers.IntegerField(
        help_text="تعداد کل پاسخ‌ها"
    )
    
    completion_rate = serializers.FloatField(
        help_text="نرخ تکمیل"
    )
    
    average_score = serializers.FloatField(
        help_text="میانگین امتیاز"
    )
    
    average_completion_time = serializers.DurationField(
        help_text="میانگین زمان تکمیل"
    )
    
    response_distribution = serializers.DictField(
        help_text="توزیع پاسخ‌ها"
    )
    
    demographic_breakdown = serializers.DictField(
        help_text="تفکیک جمعیت‌شناختی"
    )
    
    text_analysis = serializers.DictField(
        help_text="تحلیل پاسخ‌های متنی"
    )


class SurveyAnalyticsSerializer(serializers.Serializer):
    """
    سریالایزر آنالیتیک نظرسنجی
    """
    
    survey_performance = serializers.DictField(
        help_text="عملکرد نظرسنجی"
    )
    
    user_engagement = serializers.DictField(
        help_text="تعامل کاربران"
    )
    
    content_analysis = serializers.DictField(
        help_text="تحلیل محتوا"
    )
    
    trends = serializers.ListField(
        child=serializers.DictField(),
        help_text="روندها"
    )
    
    recommendations = serializers.ListField(
        child=serializers.CharField(),
        help_text="توصیه‌ها"
    )