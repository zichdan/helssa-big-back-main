"""
Serializers برای ماژول Privacy
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    DataClassification,
    DataField,
    DataAccessLog,
    ConsentRecord,
    DataRetentionPolicy
)

User = get_user_model()


class DataClassificationSerializer(serializers.ModelSerializer):
    """
    Serializer برای طبقه‌بندی داده‌ها
    """
    
    class Meta:
        model = DataClassification
        fields = [
            'id', 'name', 'classification_type', 'description',
            'retention_period_days', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_retention_period_days(self, value):
        """اعتبارسنجی مدت نگهداری"""
        if value < 1:
            raise serializers.ValidationError("مدت نگهداری باید حداقل یک روز باشد")
        if value > 36500:  # 100 سال
            raise serializers.ValidationError("مدت نگهداری نمی‌تواند بیش از 100 سال باشد")
        return value


class DataFieldSerializer(serializers.ModelSerializer):
    """
    Serializer برای فیلدهای داده
    """
    classification_name = serializers.CharField(
        source='classification.name',
        read_only=True
    )
    classification_type = serializers.CharField(
        source='classification.classification_type',
        read_only=True
    )
    
    class Meta:
        model = DataField
        fields = [
            'id', 'field_name', 'model_name', 'app_name', 'classification',
            'classification_name', 'classification_type', 'redaction_pattern',
            'replacement_text', 'is_encrypted', 'encryption_algorithm',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_redaction_pattern(self, value):
        """اعتبارسنجی الگوی پنهان‌سازی"""
        if value:
            try:
                import re
                re.compile(value)
            except re.error:
                raise serializers.ValidationError("الگوی regex نامعتبر است")
        return value
    
    def validate(self, attrs):
        """اعتبارسنجی کلی"""
        # بررسی یکتا بودن ترکیب فیلد
        field_name = attrs.get('field_name')
        model_name = attrs.get('model_name')
        app_name = attrs.get('app_name')
        
        if self.instance:
            # در حالت ویرایش
            existing = DataField.objects.filter(
                field_name=field_name,
                model_name=model_name,
                app_name=app_name
            ).exclude(id=self.instance.id)
        else:
            # در حالت ایجاد
            existing = DataField.objects.filter(
                field_name=field_name,
                model_name=model_name,
                app_name=app_name
            )
        
        if existing.exists():
            raise serializers.ValidationError(
                "این ترکیب فیلد، مدل و اپلیکیشن قبلاً ثبت شده است"
            )
        
        return attrs


class DataAccessLogSerializer(serializers.ModelSerializer):
    """
    Serializer برای لاگ دسترسی به داده‌ها
    """
    username = serializers.CharField(source='user.username', read_only=True)
    data_field_name = serializers.CharField(
        source='data_field.field_name',
        read_only=True
    )
    data_field_full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DataAccessLog
        fields = [
            'id', 'user', 'username', 'session_id', 'data_field',
            'data_field_name', 'data_field_full_name', 'action_type',
            'record_id', 'ip_address', 'user_agent', 'purpose',
            'was_redacted', 'original_value_hash', 'context_data', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']
    
    def get_data_field_full_name(self, obj):
        """نام کامل فیلد داده"""
        if obj.data_field:
            return f"{obj.data_field.app_name}.{obj.data_field.model_name}.{obj.data_field.field_name}"
        return None


class ConsentRecordSerializer(serializers.ModelSerializer):
    """
    Serializer برای رکورد رضایت‌ها
    """
    username = serializers.CharField(source='user.username', read_only=True)
    is_active = serializers.ReadOnlyField()
    data_categories_info = serializers.SerializerMethodField()
    
    class Meta:
        model = ConsentRecord
        fields = [
            'id', 'user', 'username', 'consent_type', 'status', 'purpose',
            'data_categories', 'data_categories_info', 'granted_at',
            'expires_at', 'withdrawn_at', 'withdrawal_reason',
            'ip_address', 'user_agent', 'legal_basis', 'version', 'is_active'
        ]
        read_only_fields = ['id', 'granted_at', 'is_active']
    
    def get_data_categories_info(self, obj):
        """اطلاعات دسته‌بندی‌های داده"""
        return [
            {
                'id': str(category.id),
                'name': category.name,
                'type': category.classification_type,
                'type_display': category.get_classification_type_display()
            }
            for category in obj.data_categories.all()
        ]
    
    def validate(self, attrs):
        """اعتبارسنجی کلی"""
        expires_at = attrs.get('expires_at')
        
        # بررسی تاریخ انقضا
        if expires_at:
            from django.utils import timezone
            if expires_at <= timezone.now():
                raise serializers.ValidationError(
                    "تاریخ انقضا نمی‌تواند در گذشته باشد"
                )
        
        return attrs


class DataRetentionPolicySerializer(serializers.ModelSerializer):
    """
    Serializer برای سیاست‌های نگهداری داده
    """
    classification_name = serializers.CharField(
        source='classification.name',
        read_only=True
    )
    
    class Meta:
        model = DataRetentionPolicy
        fields = [
            'id', 'name', 'classification', 'classification_name',
            'retention_period_days', 'auto_delete', 'archive_before_delete',
            'notification_days_before', 'description', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_retention_period_days(self, value):
        """اعتبارسنجی مدت نگهداری"""
        if value < 1:
            raise serializers.ValidationError("مدت نگهداری باید حداقل یک روز باشد")
        return value
    
    def validate_notification_days_before(self, value):
        """اعتبارسنجی روزهای اطلاع‌رسانی"""
        if value < 0:
            raise serializers.ValidationError("روزهای اطلاع‌رسانی نمی‌تواند منفی باشد")
        return value


# Serializers برای API های خاص

class TextRedactionRequestSerializer(serializers.Serializer):
    """
    Serializer برای درخواست پنهان‌سازی متن
    """
    text = serializers.CharField(
        max_length=10000,
        help_text="متن مورد نظر برای پنهان‌سازی"
    )
    redaction_level = serializers.ChoiceField(
        choices=['none', 'standard', 'strict'],
        default='standard',
        help_text="سطح پنهان‌سازی"
    )
    context = serializers.JSONField(
        required=False,
        help_text="اطلاعات زمینه‌ای اضافی"
    )
    log_access = serializers.BooleanField(
        default=True,
        help_text="آیا دسترسی لاگ شود؟"
    )
    
    def validate_text(self, value):
        """اعتبارسنجی متن"""
        if not value.strip():
            raise serializers.ValidationError("متن نمی‌تواند خالی باشد")
        return value


class TextRedactionResponseSerializer(serializers.Serializer):
    """
    Serializer برای پاسخ پنهان‌سازی متن
    """
    original_text = serializers.CharField()
    processed_text = serializers.CharField()
    redacted_items = serializers.ListField()
    privacy_score = serializers.FloatField()
    contains_sensitive_data = serializers.BooleanField()
    processing_metadata = serializers.JSONField()


class ConsentGrantRequestSerializer(serializers.Serializer):
    """
    Serializer برای درخواست اعطای رضایت
    """
    consent_type = serializers.ChoiceField(
        choices=ConsentRecord.CONSENT_TYPES,
        help_text="نوع رضایت"
    )
    purpose = serializers.CharField(
        max_length=500,
        help_text="هدف از استفاده از داده‌ها"
    )
    data_categories = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="لیست شناسه‌های دسته‌بندی داده‌ها"
    )
    legal_basis = serializers.CharField(
        max_length=200,
        help_text="مبنای قانونی پردازش"
    )
    expires_in_days = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=36500,
        help_text="تعداد روز تا انقضا (اختیاری)"
    )
    version = serializers.CharField(
        default="1.0",
        max_length=20,
        help_text="نسخه سیاست حریم خصوصی"
    )


class ConsentWithdrawRequestSerializer(serializers.Serializer):
    """
    Serializer برای درخواست پس‌گیری رضایت
    """
    consent_type = serializers.ChoiceField(
        choices=ConsentRecord.CONSENT_TYPES,
        help_text="نوع رضایت"
    )
    reason = serializers.CharField(
        max_length=500,
        help_text="دلیل پس‌گیری رضایت"
    )


class PrivacyAnalysisRequestSerializer(serializers.Serializer):
    """
    Serializer برای درخواست تحلیل حریم خصوصی
    """
    text = serializers.CharField(
        max_length=10000,
        help_text="متن مورد تحلیل"
    )
    include_suggestions = serializers.BooleanField(
        default=True,
        help_text="شامل پیشنهادات بهبود"
    )
    
    def validate_text(self, value):
        """اعتبارسنجی متن"""
        if not value.strip():
            raise serializers.ValidationError("متن نمی‌تواند خالی باشد")
        return value


class PrivacyAnalysisResponseSerializer(serializers.Serializer):
    """
    Serializer برای پاسخ تحلیل حریم خصوصی
    """
    risk_score = serializers.FloatField()
    risk_level = serializers.CharField()
    risk_description = serializers.CharField()
    sensitive_items = serializers.ListField()
    total_sensitive_items = serializers.IntegerField()
    categories_found = serializers.ListField()
    text_length = serializers.IntegerField()
    analyzed_at = serializers.CharField()
    suggestions = serializers.ListField(required=False)