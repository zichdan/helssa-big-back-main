"""
Serializers برای تنظیمات feedback app
"""

from rest_framework import serializers
from ..models import FeedbackSettings

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


class FeedbackSettingsCreateSerializer(serializers.Serializer):
    """
    سریالایزر ایجاد تنظیمات feedback
    """
    
    key = serializers.CharField(
        max_length=100,
        help_text="کلید تنظیمات"
    )
    
    value = serializers.JSONField(
        help_text="مقدار تنظیمات"
    )
    
    description = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="توضیحات"
    )
    
    setting_type = serializers.ChoiceField(
        choices=FeedbackSettings.SETTING_TYPES,
        default='general',
        help_text="نوع تنظیمات"
    )
    
    def validate_key(self, value):
        """اعتبارسنجی کلید"""
        # بررسی فرمت کلید
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise serializers.ValidationError(
                "کلید فقط می‌تواند شامل حروف، اعداد، _ و - باشد"
            )
        
        # بررسی یکتا بودن (در پیاده‌سازی واقعی)
        # if FeedbackSettings.objects.filter(key=value).exists():
        #     raise serializers.ValidationError("این کلید قبلاً وجود دارد")
        
        return value.lower()
    
    def validate_value(self, value):
        """اعتبارسنجی مقدار"""
        # بررسی که مقدار قابل سریالیز به JSON باشد
        try:
            import json
            json.dumps(value)
        except (TypeError, ValueError):
            raise serializers.ValidationError("مقدار باید قابل تبدیل به JSON باشد")
        
        return value


class FeedbackSettingsUpdateSerializer(serializers.Serializer):
    """
    سریالایزر ویرایش تنظیمات feedback
    """
    
    value = serializers.JSONField(
        required=False,
        help_text="مقدار تنظیمات"
    )
    
    description = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="توضیحات"
    )
    
    is_active = serializers.BooleanField(
        required=False,
        help_text="فعال بودن"
    )


class FeedbackSettingsSerializer(BaseModelSerializer):
    """
    سریالایزر نمایش تنظیمات feedback
    """
    
    setting_type_display = serializers.CharField(
        source='get_setting_type_display',
        read_only=True,
        help_text="نمایش نوع تنظیمات"
    )
    
    value_summary = serializers.SerializerMethodField(
        help_text="خلاصه مقدار"
    )
    
    class Meta:
        model = FeedbackSettings
        fields = [
            'id', 'key', 'value', 'value_summary', 'description',
            'setting_type', 'setting_type_display', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_value_summary(self, obj):
        """خلاصه مقدار برای نمایش"""
        if not obj.value:
            return None
        
        value_type = type(obj.value).__name__
        
        if isinstance(obj.value, dict):
            return {
                'type': 'object',
                'keys_count': len(obj.value),
                'sample_keys': list(obj.value.keys())[:3]
            }
        elif isinstance(obj.value, list):
            return {
                'type': 'array',
                'length': len(obj.value),
                'sample_items': obj.value[:3] if obj.value else []
            }
        elif isinstance(obj.value, str):
            return {
                'type': 'string',
                'length': len(obj.value),
                'preview': obj.value[:50] + ('...' if len(obj.value) > 50 else '')
            }
        else:
            return {
                'type': value_type.lower(),
                'value': obj.value
            }


class FeedbackSettingsListSerializer(serializers.ModelSerializer):
    """
    سریالایزر فهرست تنظیمات (سبک‌تر)
    """
    
    setting_type_display = serializers.CharField(
        source='get_setting_type_display',
        read_only=True
    )
    
    class Meta:
        model = FeedbackSettings
        fields = [
            'id', 'key', 'setting_type', 'setting_type_display',
            'description', 'is_active', 'updated_at'
        ]


class FeedbackConfigurationSerializer(serializers.Serializer):
    """
    سریالایزر تنظیمات جامع feedback
    """
    
    # تنظیمات عمومی
    general_settings = serializers.DictField(
        help_text="تنظیمات عمومی"
    )
    
    # تنظیمات امتیازدهی
    rating_settings = serializers.DictField(
        help_text="تنظیمات امتیازدهی"
    )
    
    # تنظیمات نظرسنجی
    survey_settings = serializers.DictField(
        help_text="تنظیمات نظرسنجی"
    )
    
    # تنظیمات اعلان‌ها
    notification_settings = serializers.DictField(
        help_text="تنظیمات اعلان‌ها"
    )


class DefaultSettingsSerializer(serializers.Serializer):
    """
    سریالایزر تنظیمات پیش‌فرض
    """
    
    # تنظیمات امتیازدهی
    rating_enabled = serializers.BooleanField(
        default=True,
        help_text="فعال بودن امتیازدهی"
    )
    
    rating_required_fields = serializers.ListField(
        child=serializers.CharField(),
        default=['overall_rating'],
        help_text="فیلدهای اجباری امتیازدهی"
    )
    
    rating_scale_max = serializers.IntegerField(
        default=5,
        min_value=3,
        max_value=10,
        help_text="حداکثر مقیاس امتیازدهی"
    )
    
    # تنظیمات بازخورد
    feedback_enabled = serializers.BooleanField(
        default=True,
        help_text="فعال بودن بازخورد"
    )
    
    voice_feedback_enabled = serializers.BooleanField(
        default=True,
        help_text="فعال بودن بازخورد صوتی"
    )
    
    max_feedback_length = serializers.IntegerField(
        default=500,
        min_value=100,
        max_value=2000,
        help_text="حداکثر طول بازخورد"
    )
    
    # تنظیمات نظرسنجی
    survey_enabled = serializers.BooleanField(
        default=True,
        help_text="فعال بودن نظرسنجی"
    )
    
    anonymous_survey_allowed = serializers.BooleanField(
        default=False,
        help_text="امکان نظرسنجی ناشناس"
    )
    
    max_survey_questions = serializers.IntegerField(
        default=20,
        min_value=5,
        max_value=50,
        help_text="حداکثر تعداد سوالات نظرسنجی"
    )
    
    # تنظیمات اعلان
    notification_enabled = serializers.BooleanField(
        default=True,
        help_text="فعال بودن اعلان‌ها"
    )
    
    email_notifications = serializers.BooleanField(
        default=False,
        help_text="اعلان‌های ایمیل"
    )
    
    sms_notifications = serializers.BooleanField(
        default=True,
        help_text="اعلان‌های پیامک"
    )
    
    # تنظیمات تحلیل
    analytics_enabled = serializers.BooleanField(
        default=True,
        help_text="فعال بودن آنالیتیک"
    )
    
    sentiment_analysis_enabled = serializers.BooleanField(
        default=True,
        help_text="فعال بودن تحلیل احساسات"
    )
    
    auto_followup_enabled = serializers.BooleanField(
        default=True,
        help_text="فعال بودن پیگیری خودکار"
    )


class BulkSettingsUpdateSerializer(serializers.Serializer):
    """
    سریالایزر ویرایش گروهی تنظیمات
    """
    
    settings = serializers.DictField(
        child=serializers.JSONField(),
        help_text="فهرست تنظیمات برای ویرایش"
    )
    
    def validate_settings(self, value):
        """اعتبارسنجی تنظیمات گروهی"""
        if not value:
            raise serializers.ValidationError("حداقل یک تنظیمات باید ارسال شود")
        
        # بررسی کلیدهای معتبر
        valid_keys = [
            'rating_enabled', 'feedback_enabled', 'survey_enabled',
            'notification_enabled', 'analytics_enabled'
        ]
        
        for key in value.keys():
            if key not in valid_keys:
                raise serializers.ValidationError(f"کلید '{key}' معتبر نیست")
        
        return value


class SettingsExportSerializer(serializers.Serializer):
    """
    سریالایزر صادرات تنظیمات
    """
    
    export_type = serializers.ChoiceField(
        choices=[
            ('json', 'JSON'),
            ('yaml', 'YAML'),
            ('env', 'Environment Variables'),
        ],
        default='json',
        help_text="نوع صادرات"
    )
    
    include_sensitive = serializers.BooleanField(
        default=False,
        help_text="شامل تنظیمات حساس"
    )
    
    categories = serializers.MultipleChoiceField(
        choices=FeedbackSettings.SETTING_TYPES,
        required=False,
        help_text="دسته‌های مورد نظر"
    )


class SettingsImportSerializer(serializers.Serializer):
    """
    سریالایزر وارد کردن تنظیمات
    """
    
    settings_file = serializers.FileField(
        help_text="فایل تنظیمات"
    )
    
    import_type = serializers.ChoiceField(
        choices=[
            ('json', 'JSON'),
            ('yaml', 'YAML'),
        ],
        default='json',
        help_text="نوع فایل"
    )
    
    overwrite_existing = serializers.BooleanField(
        default=False,
        help_text="بازنویسی تنظیمات موجود"
    )
    
    def validate_settings_file(self, value):
        """اعتبارسنجی فایل تنظیمات"""
        if not value:
            raise serializers.ValidationError("فایل تنظیمات اجباری است")
        
        # بررسی اندازه (حداکثر 1MB)
        max_size = 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("حجم فایل نباید بیش از 1 مگابایت باشد")
        
        # بررسی فرمت
        allowed_extensions = ['json', 'yaml', 'yml']
        file_extension = value.name.split('.')[-1].lower() if '.' in value.name else ''
        
        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(
                f"فرمت فایل پشتیبانی نمی‌شود. فرمت‌های مجاز: {', '.join(allowed_extensions)}"
            )
        
        return value