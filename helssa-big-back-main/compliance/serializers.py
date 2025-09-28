from rest_framework import serializers
from django.contrib.auth import get_user_model
from typing import Dict, List
import pyotp
from .models import (
    SecurityLayer, SecurityLog, MFAConfig, Role, TemporaryAccess,
    AuditLog, HIPAAComplianceReport, SecurityIncident, MedicalFile
)

User = get_user_model()


class SecurityLayerSerializer(serializers.ModelSerializer):
    """سریالایزر لایه‌های امنیتی"""
    
    class Meta:
        model = SecurityLayer
        fields = [
            'id', 'name', 'layer_type', 'is_active', 
            'priority', 'config', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
        
    def validate_config(self, value: Dict) -> Dict:
        """اعتبارسنجی تنظیمات لایه امنیتی"""
        layer_type = self.initial_data.get('layer_type')
        
        if layer_type == 'network':
            required_keys = ['firewall_rules', 'rate_limit_config']
        elif layer_type == 'application':
            required_keys = ['auth_config', 'session_config']
        elif layer_type == 'data':
            required_keys = ['encryption_config', 'backup_config']
        elif layer_type == 'audit':
            required_keys = ['log_retention', 'alert_config']
        else:
            return value
            
        missing_keys = set(required_keys) - set(value.keys())
        if missing_keys:
            raise serializers.ValidationError(
                f"تنظیمات لایه {layer_type} باید شامل این کلیدها باشد: {', '.join(missing_keys)}"
            )
            
        return value


class SecurityLogSerializer(serializers.ModelSerializer):
    """سریالایزر لاگ‌های امنیتی"""
    
    user_info = serializers.SerializerMethodField()
    
    class Meta:
        model = SecurityLog
        fields = [
            'id', 'event_type', 'layer', 'reason', 'ip_address',
            'user_agent', 'user', 'user_info', 'risk_score', 
            'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
        
    def get_user_info(self, obj) -> Dict:
        """اطلاعات کاربر"""
        if obj.user:
            return {
                'id': str(obj.user.id),
                'username': obj.user.username,
                'full_name': obj.user.get_full_name() if hasattr(obj.user, 'get_full_name') else ''
            }
        return None


class MFAEnableSerializer(serializers.Serializer):
    """سریالایزر فعال‌سازی MFA"""
    
    def create(self, validated_data):
        """فعال‌سازی MFA برای کاربر"""
        user = self.context['request'].user
        
        # بررسی وجود تنظیمات قبلی
        if hasattr(user, 'mfa_config'):
            raise serializers.ValidationError("MFA قبلاً برای این کاربر فعال شده است")
            
        # تولید secret
        secret = pyotp.random_base32()
        
        # ایجاد تنظیمات MFA
        mfa_config = MFAConfig.objects.create(
            user=user,
            secret=secret,  # در عمل باید رمزنگاری شود
            is_active=False
        )
        
        # تولید QR Code URI
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.username,
            issuer_name='HELSSA Medical Platform'
        )
        
        return {
            'secret': secret,
            'provisioning_uri': provisioning_uri,
            'backup_codes': mfa_config.backup_codes
        }


class MFAVerifySerializer(serializers.Serializer):
    """سریالایزر تایید توکن MFA"""
    
    token = serializers.CharField(max_length=6, min_length=6)
    
    def validate_token(self, value):
        """اعتبارسنجی توکن"""
        user = self.context['request'].user
        
        if not hasattr(user, 'mfa_config'):
            raise serializers.ValidationError("MFA برای این کاربر فعال نیست")
            
        mfa_config = user.mfa_config
        totp = pyotp.TOTP(mfa_config.secret)
        
        if not totp.verify(value, valid_window=1):
            raise serializers.ValidationError("توکن نامعتبر یا منقضی شده است")
            
        return value
        
    def save(self):
        """فعال‌سازی MFA پس از تایید اولیه"""
        user = self.context['request'].user
        mfa_config = user.mfa_config
        
        if not mfa_config.is_active:
            mfa_config.is_active = True
            mfa_config.save()
            
        return mfa_config


class RoleSerializer(serializers.ModelSerializer):
    """سریالایزر نقش‌ها"""
    
    class Meta:
        model = Role
        fields = [
            'id', 'name', 'permissions', 'description',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class TemporaryAccessSerializer(serializers.ModelSerializer):
    """سریالایزر دسترسی موقت"""
    
    doctor_info = serializers.SerializerMethodField()
    granted_by_info = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = TemporaryAccess
        fields = [
            'id', 'doctor', 'doctor_info', 'patient_id', 
            'granted_by', 'granted_by_info', 'reason',
            'is_active', 'granted_at', 'expires_at', 
            'revoked_at', 'is_valid'
        ]
        read_only_fields = ['granted_at', 'granted_by']
        
    def get_doctor_info(self, obj) -> Dict:
        """اطلاعات پزشک"""
        return {
            'id': str(obj.doctor.id),
            'name': obj.doctor.get_full_name() if hasattr(obj.doctor, 'get_full_name') else obj.doctor.username
        }
        
    def get_granted_by_info(self, obj) -> Dict:
        """اطلاعات اعطاکننده"""
        if obj.granted_by:
            return {
                'id': str(obj.granted_by.id),
                'name': obj.granted_by.get_full_name() if hasattr(obj.granted_by, 'get_full_name') else obj.granted_by.username
            }
        return None
        
    def get_is_valid(self, obj) -> bool:
        """وضعیت اعتبار"""
        return obj.is_valid()
        
    def create(self, validated_data):
        """ایجاد دسترسی موقت"""
        validated_data['granted_by'] = self.context['request'].user
        return super().create(validated_data)


class AuditLogSerializer(serializers.ModelSerializer):
    """سریالایزر لاگ‌های ممیزی"""
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'timestamp', 'event_type', 'user_id',
            'resource', 'action', 'result', 'ip_address',
            'user_agent', 'session_id', 'metadata'
        ]
        read_only_fields = ['id', 'timestamp']


class HIPAAComplianceReportSerializer(serializers.ModelSerializer):
    """سریالایزر گزارش‌های HIPAA"""
    
    generated_by_info = serializers.SerializerMethodField()
    
    class Meta:
        model = HIPAAComplianceReport
        fields = [
            'id', 'report_date', 'compliant', 'score',
            'findings', 'recommendations', 'administrative_score',
            'physical_score', 'technical_score', 'generated_by',
            'generated_by_info', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'generated_by']
        
    def get_generated_by_info(self, obj) -> Dict:
        """اطلاعات تولیدکننده گزارش"""
        if obj.generated_by:
            return {
                'id': str(obj.generated_by.id),
                'name': obj.generated_by.get_full_name() if hasattr(obj.generated_by, 'get_full_name') else obj.generated_by.username
            }
        return None


class SecurityIncidentSerializer(serializers.ModelSerializer):
    """سریالایزر حوادث امنیتی"""
    
    assigned_to_info = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = SecurityIncident
        fields = [
            'id', 'incident_type', 'severity', 'status',
            'details', 'detected_at', 'contained_at',
            'resolved_at', 'response_plan', 'affected_systems',
            'assigned_to', 'assigned_to_info', 'duration',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def get_assigned_to_info(self, obj) -> Dict:
        """اطلاعات مسئول رسیدگی"""
        if obj.assigned_to:
            return {
                'id': str(obj.assigned_to.id),
                'name': obj.assigned_to.get_full_name() if hasattr(obj.assigned_to, 'get_full_name') else obj.assigned_to.username
            }
        return None
        
    def get_duration(self, obj) -> Dict:
        """مدت زمان‌های مختلف حادثه"""
        from django.utils import timezone
        
        duration = {}
        
        if obj.contained_at and obj.detected_at:
            duration['time_to_contain'] = str(obj.contained_at - obj.detected_at)
            
        if obj.resolved_at and obj.detected_at:
            duration['time_to_resolve'] = str(obj.resolved_at - obj.detected_at)
            
        if obj.status not in ['resolved', 'closed'] and obj.detected_at:
            duration['ongoing_duration'] = str(timezone.now() - obj.detected_at)
            
        return duration


class SecurityIncidentUpdateSerializer(serializers.ModelSerializer):
    """سریالایزر به‌روزرسانی حوادث امنیتی"""
    
    class Meta:
        model = SecurityIncident
        fields = ['status', 'response_plan', 'affected_systems', 'assigned_to']
        
    def update(self, instance, validated_data):
        """به‌روزرسانی با ثبت زمان‌های خاص"""
        from django.utils import timezone
        
        new_status = validated_data.get('status')
        
        if new_status == 'contained' and not instance.contained_at:
            instance.contained_at = timezone.now()
            
        if new_status == 'resolved' and not instance.resolved_at:
            instance.resolved_at = timezone.now()
            
        return super().update(instance, validated_data)


class MedicalFileSerializer(serializers.ModelSerializer):
    """سریالایزر فایل‌های پزشکی"""
    
    uploaded_by_info = serializers.SerializerMethodField()
    
    class Meta:
        model = MedicalFile
        fields = [
            'file_id', 'patient_id', 'storage_path', 'file_type',
            'file_size', 'encryption_key_id', 'upload_metadata',
            'uploaded_by', 'uploaded_by_info', 'uploaded_at',
            'last_accessed', 'access_count'
        ]
        read_only_fields = [
            'file_id', 'storage_path', 'encryption_key_id',
            'uploaded_at', 'last_accessed', 'access_count'
        ]
        
    def get_uploaded_by_info(self, obj) -> Dict:
        """اطلاعات آپلودکننده"""
        if obj.uploaded_by:
            return {
                'id': str(obj.uploaded_by.id),
                'name': obj.uploaded_by.get_full_name() if hasattr(obj.uploaded_by, 'get_full_name') else obj.uploaded_by.username
            }
        return None


# سریالایزرهای گزارش و آمار
class SecurityDashboardSerializer(serializers.Serializer):
    """سریالایزر داشبورد امنیت"""
    
    period = serializers.DictField()
    security_score = serializers.IntegerField()
    active_incidents = serializers.IntegerField()
    failed_auth_attempts = serializers.IntegerField()
    suspicious_activities = serializers.IntegerField()
    compliance_status = serializers.DictField()
    recent_incidents = SecurityIncidentSerializer(many=True)
    top_threats = serializers.ListField()
    recommendations = serializers.ListField()


class AuditReportSerializer(serializers.Serializer):
    """سریالایزر گزارش ممیزی"""
    
    period = serializers.DictField()
    summary = serializers.DictField()
    security_events = serializers.ListField()
    anomalies = serializers.ListField()
    recommendations = serializers.ListField()