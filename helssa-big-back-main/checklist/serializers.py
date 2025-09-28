"""
سریالایزرهای اپلیکیشن Checklist
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import (
    ChecklistCatalog,
    ChecklistTemplate,
    ChecklistEval,
    ChecklistAlert
)

User = get_user_model()


class ChecklistCatalogSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای آیتم‌های کاتالوگ چک‌لیست
    """
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = ChecklistCatalog
        fields = [
            'id', 'title', 'description', 'category', 'category_display',
            'priority', 'priority_display', 'keywords', 'question_template',
            'is_active', 'specialty', 'conditions', 'created_at', 'updated_at',
            'created_by', 'created_by_name'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    def validate_keywords(self, value):
        """
        اعتبارسنجی کلمات کلیدی
        """
        if value and len(value) > 20:
            raise serializers.ValidationError("تعداد کلمات کلیدی نمی‌تواند بیشتر از ۲۰ باشد.")
        return value


class ChecklistTemplateSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای قالب‌های چک‌لیست
    """
    catalog_items_count = serializers.IntegerField(source='catalog_items.count', read_only=True)
    catalog_items_detail = ChecklistCatalogSerializer(source='catalog_items', many=True, read_only=True)
    
    class Meta:
        model = ChecklistTemplate
        fields = [
            'id', 'name', 'description', 'catalog_items', 'catalog_items_count',
            'catalog_items_detail', 'specialty', 'chief_complaint', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    def validate_catalog_items(self, value):
        """
        اعتبارسنجی آیتم‌های کاتالوگ
        """
        if not value:
            raise serializers.ValidationError("قالب باید حداقل یک آیتم کاتالوگ داشته باشد.")
        return value


class ChecklistEvalSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای ارزیابی چک‌لیست
    """
    catalog_item_detail = ChecklistCatalogSerializer(source='catalog_item', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    encounter_date = serializers.DateTimeField(source='encounter.created_at', read_only=True)
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ChecklistEval
        fields = [
            'id', 'encounter', 'encounter_date', 'patient_name', 'doctor_name',
            'catalog_item', 'catalog_item_detail', 'status', 'status_display',
            'confidence_score', 'evidence_text', 'anchor_positions',
            'generated_question', 'doctor_response', 'is_acknowledged',
            'acknowledged_at', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'created_by', 'updated_by',
            'generated_question'
        ]
    
    def get_patient_name(self, obj):
        """
        دریافت نام بیمار
        """
        if hasattr(obj.encounter, 'patient'):
            return obj.encounter.patient.get_full_name()
        return None
    
    def get_doctor_name(self, obj):
        """
        دریافت نام پزشک
        """
        if hasattr(obj.encounter, 'doctor'):
            return obj.encounter.doctor.get_full_name()
        return None
    
    def validate_confidence_score(self, value):
        """
        اعتبارسنجی امتیاز اطمینان
        """
        if not 0 <= value <= 1:
            raise serializers.ValidationError("امتیاز اطمینان باید بین ۰ و ۱ باشد.")
        return value
    
    def update(self, instance, validated_data):
        """
        به‌روزرسانی ارزیابی
        """
        # اگر وضعیت تایید تغییر کرد، زمان آن را ثبت کن
        if 'is_acknowledged' in validated_data:
            if validated_data['is_acknowledged'] and not instance.is_acknowledged:
                validated_data['acknowledged_at'] = timezone.now()
            elif not validated_data['is_acknowledged'] and instance.is_acknowledged:
                validated_data['acknowledged_at'] = None
        
        return super().update(instance, validated_data)


class ChecklistEvalCreateSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای ایجاد ارزیابی چک‌لیست
    """
    class Meta:
        model = ChecklistEval
        fields = [
            'encounter', 'catalog_item', 'status', 'confidence_score',
            'evidence_text', 'anchor_positions', 'notes'
        ]
    
    def validate(self, attrs):
        """
        اعتبارسنجی داده‌ها
        """
        encounter = attrs.get('encounter')
        catalog_item = attrs.get('catalog_item')
        
        # بررسی تکراری نبودن
        if ChecklistEval.objects.filter(encounter=encounter, catalog_item=catalog_item).exists():
            raise serializers.ValidationError(
                "ارزیابی برای این آیتم در این ویزیت قبلاً ثبت شده است."
            )
        
        return attrs


class ChecklistAlertSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای هشدارهای چک‌لیست
    """
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    evaluation_detail = ChecklistEvalSerializer(source='evaluation', read_only=True)
    dismissed_by_name = serializers.CharField(source='dismissed_by.get_full_name', read_only=True)
    
    class Meta:
        model = ChecklistAlert
        fields = [
            'id', 'encounter', 'evaluation', 'evaluation_detail',
            'alert_type', 'alert_type_display', 'message',
            'is_dismissed', 'dismissed_at', 'dismissed_by', 'dismissed_by_name',
            'created_at'
        ]
        read_only_fields = [
            'created_at', 'created_by', 'dismissed_at', 'dismissed_by'
        ]
    
    def update(self, instance, validated_data):
        """
        به‌روزرسانی هشدار
        """
        # اگر هشدار رد شد، اطلاعات آن را ثبت کن
        if 'is_dismissed' in validated_data:
            if validated_data['is_dismissed'] and not instance.is_dismissed:
                instance.dismissed_at = timezone.now()
                instance.dismissed_by = self.context['request'].user
        
        return super().update(instance, validated_data)


class ChecklistSummarySerializer(serializers.Serializer):
    """
    سریالایزر برای خلاصه وضعیت چک‌لیست یک ویزیت
    """
    total_items = serializers.IntegerField()
    covered_items = serializers.IntegerField()
    missing_items = serializers.IntegerField()
    partial_items = serializers.IntegerField()
    unclear_items = serializers.IntegerField()
    coverage_percentage = serializers.FloatField()
    needs_attention = serializers.IntegerField()
    active_alerts = serializers.IntegerField()


class BulkEvaluationSerializer(serializers.Serializer):
    """
    سریالایزر برای ارزیابی دسته‌ای چک‌لیست
    """
    encounter_id = serializers.IntegerField()
    template_id = serializers.IntegerField(required=False)
    
    def validate_encounter_id(self, value):
        """
        اعتبارسنجی شناسه ویزیت
        """
        # این بررسی در سرویس انجام می‌شود
        return value