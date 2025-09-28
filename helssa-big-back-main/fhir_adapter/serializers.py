from rest_framework import serializers
from typing import Dict, Any, List
import json
from django.core.exceptions import ValidationError
from .models import FHIRResource, FHIRMapping, FHIRBundle, FHIRExportLog


class FHIRResourceSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای منابع FHIR
    
    این سریالایزر برای تبدیل منابع FHIR به/از JSON استفاده می‌شود
    """
    class Meta:
        model = FHIRResource
        fields = [
            'resource_id',
            'resource_type',
            'resource_content',
            'version',
            'last_updated',
            'created',
            'internal_id',
            'internal_model'
        ]
        read_only_fields = ['resource_id', 'last_updated', 'created']
    
    def validate_resource_content(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """
        اعتبارسنجی محتوای منبع FHIR
        
        بررسی می‌کند که محتوا ساختار صحیح FHIR را داشته باشد
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("محتوای منبع باید یک شیء JSON باشد")
        
        # بررسی وجود فیلدهای الزامی FHIR
        if 'resourceType' not in value:
            raise serializers.ValidationError("فیلد resourceType الزامی است")
        
        # بررسی تطابق نوع منبع
        if 'resource_type' in self.initial_data:
            if value['resourceType'] != self.initial_data['resource_type']:
                raise serializers.ValidationError(
                    f"نوع منبع در محتوا ({value['resourceType']}) "
                    f"با نوع تعریف شده ({self.initial_data['resource_type']}) مطابقت ندارد"
                )
        
        return value
    
    def create(self, validated_data: Dict[str, Any]) -> FHIRResource:
        """ایجاد منبع FHIR جدید"""
        # اطمینان از تطابق resourceType در محتوا
        if 'resourceType' not in validated_data['resource_content']:
            validated_data['resource_content']['resourceType'] = validated_data['resource_type']
        
        return super().create(validated_data)


class FHIRMappingSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای نقشه‌برداری FHIR
    """
    class Meta:
        model = FHIRMapping
        fields = [
            'mapping_id',
            'source_model',
            'target_resource_type',
            'field_mappings',
            'transformation_rules',
            'is_active',
            'created',
            'updated'
        ]
        read_only_fields = ['mapping_id', 'created', 'updated']
    
    def validate_field_mappings(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """
        اعتبارسنجی نقشه‌برداری فیلدها
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("نقشه‌برداری فیلدها باید یک شیء JSON باشد")
        
        # بررسی ساختار نقشه‌برداری
        for source_field, target_field in value.items():
            if not isinstance(source_field, str):
                raise serializers.ValidationError("کلیدهای نقشه‌برداری باید رشته باشند")
            
            # target_field می‌تواند رشته یا شیء پیچیده‌تر باشد
            if not (isinstance(target_field, str) or isinstance(target_field, dict)):
                raise serializers.ValidationError(
                    f"مقدار نقشه‌برداری برای '{source_field}' باید رشته یا شیء باشد"
                )
        
        return value


class FHIRBundleSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای Bundle های FHIR
    """
    resources = FHIRResourceSerializer(many=True, read_only=True)
    resource_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        help_text="لیست شناسه‌های منابع برای اضافه کردن به Bundle"
    )
    
    class Meta:
        model = FHIRBundle
        fields = [
            'bundle_id',
            'bundle_type',
            'resources',
            'resource_ids',
            'bundle_content',
            'total',
            'created',
            'updated'
        ]
        read_only_fields = ['bundle_id', 'total', 'created', 'updated']
    
    def validate_bundle_content(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """
        اعتبارسنجی محتوای Bundle
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("محتوای Bundle باید یک شیء JSON باشد")
        
        # بررسی فیلدهای الزامی Bundle
        required_fields = ['resourceType', 'type']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"فیلد '{field}' الزامی است")
        
        if value['resourceType'] != 'Bundle':
            raise serializers.ValidationError("resourceType باید 'Bundle' باشد")
        
        return value
    
    def create(self, validated_data: Dict[str, Any]) -> FHIRBundle:
        """ایجاد Bundle جدید"""
        resource_ids = validated_data.pop('resource_ids', [])
        
        # ایجاد Bundle
        bundle = super().create(validated_data)
        
        # اضافه کردن منابع
        if resource_ids:
            resources = FHIRResource.objects.filter(resource_id__in=resource_ids)
            bundle.resources.set(resources)
            bundle.total = resources.count()
            bundle.save()
        
        return bundle


class FHIRExportLogSerializer(serializers.ModelSerializer):
    """
    سریالایزر برای لاگ‌های صادرات/واردات FHIR
    """
    duration = serializers.ReadOnlyField()
    
    class Meta:
        model = FHIRExportLog
        fields = [
            'log_id',
            'operation_type',
            'status',
            'source_model',
            'target_resource_type',
            'details',
            'error_message',
            'records_processed',
            'records_failed',
            'started_at',
            'completed_at',
            'duration',
            'performed_by'
        ]
        read_only_fields = [
            'log_id',
            'started_at',
            'duration'
        ]


class FHIRTransformSerializer(serializers.Serializer):
    """
    سریالایزر برای درخواست‌های تبدیل داده به FHIR
    """
    source_model = serializers.CharField(
        help_text="نام مدل منبع"
    )
    source_id = serializers.CharField(
        help_text="شناسه رکورد منبع"
    )
    target_resource_type = serializers.CharField(
        help_text="نوع منبع FHIR هدف"
    )
    include_related = serializers.BooleanField(
        default=False,
        help_text="شامل کردن داده‌های مرتبط"
    )
    
    def validate_target_resource_type(self, value: str) -> str:
        """بررسی نوع منبع FHIR"""
        valid_types = [choice[0] for choice in FHIRResource.RESOURCE_TYPES]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"نوع منبع نامعتبر. انواع معتبر: {', '.join(valid_types)}"
            )
        return value


class FHIRImportSerializer(serializers.Serializer):
    """
    سریالایزر برای واردات منابع FHIR
    """
    resource_type = serializers.CharField(
        help_text="نوع منبع FHIR"
    )
    resource_content = serializers.JSONField(
        help_text="محتوای منبع FHIR"
    )
    update_existing = serializers.BooleanField(
        default=False,
        help_text="به‌روزرسانی منبع موجود در صورت وجود"
    )
    
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """اعتبارسنجی کلی داده‌ها"""
        resource_content = attrs['resource_content']
        
        # بررسی تطابق نوع منبع
        if 'resourceType' in resource_content:
            if resource_content['resourceType'] != attrs['resource_type']:
                raise serializers.ValidationError(
                    "نوع منبع در محتوا با نوع تعریف شده مطابقت ندارد"
                )
        
        return attrs


class FHIRSearchSerializer(serializers.Serializer):
    """
    سریالایزر برای جستجوی منابع FHIR
    """
    resource_type = serializers.CharField(
        required=False,
        help_text="فیلتر بر اساس نوع منبع"
    )
    internal_id = serializers.CharField(
        required=False,
        help_text="جستجو بر اساس شناسه داخلی"
    )
    internal_model = serializers.CharField(
        required=False,
        help_text="جستجو بر اساس مدل داخلی"
    )
    date_from = serializers.DateTimeField(
        required=False,
        help_text="تاریخ شروع برای فیلتر"
    )
    date_to = serializers.DateTimeField(
        required=False,
        help_text="تاریخ پایان برای فیلتر"
    )
    page = serializers.IntegerField(
        default=1,
        min_value=1,
        help_text="شماره صفحه"
    )
    page_size = serializers.IntegerField(
        default=20,
        min_value=1,
        max_value=100,
        help_text="تعداد نتایج در هر صفحه"
    )