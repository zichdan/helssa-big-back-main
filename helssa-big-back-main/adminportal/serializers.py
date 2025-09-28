"""
سریالایزرهای پنل ادمین
AdminPortal Serializers
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import (
    AdminUser, SystemOperation, SupportTicket, 
    SystemMetrics, AdminAuditLog, AdminSession
)

User = get_user_model()


class AdminUserSerializer(serializers.ModelSerializer):
    """سریالایزر کاربر ادمین"""
    
    user_info = serializers.SerializerMethodField()
    last_activity_formatted = serializers.SerializerMethodField()
    permissions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AdminUser
        fields = [
            'id', 'user', 'user_info', 'role', 'department', 
            'permissions', 'permissions_count', 'last_activity', 
            'last_activity_formatted', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_activity']
    
    def get_user_info(self, obj):
        """اطلاعات کاربر"""
        user = obj.user
        return {
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name(),
            'email': getattr(user, 'email', ''),
            'is_active': user.is_active
        }
    
    def get_last_activity_formatted(self, obj):
        """فرمت زمان آخرین فعالیت"""
        if not obj.last_activity:
            return None
        
        now = timezone.now()
        diff = now - obj.last_activity
        
        if diff.days == 0:
            return 'امروز'
        elif diff.days == 1:
            return 'دیروز'
        else:
            return f'{diff.days} روز پیش'
    
    def get_permissions_count(self, obj):
        """تعداد دسترسی‌های اضافی"""
        return len(obj.permissions) if obj.permissions else 0


class AdminUserCreateUpdateSerializer(serializers.ModelSerializer):
    """سریالایزر ایجاد/بروزرسانی کاربر ادمین"""
    
    class Meta:
        model = AdminUser
        fields = ['user', 'role', 'department', 'permissions', 'is_active']
    
    def validate_user(self, value):
        """اعتبارسنجی کاربر"""
        if self.instance is None:  # در حالت ایجاد
            if hasattr(value, 'admin_profile'):
                raise serializers.ValidationError('این کاربر قبلاً پروفایل ادمین دارد')
        return value


class SystemOperationSerializer(serializers.ModelSerializer):
    """سریالایزر عملیات سیستمی"""
    
    operator_info = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    operation_type_display = serializers.CharField(source='get_operation_type_display', read_only=True)
    
    class Meta:
        model = SystemOperation
        fields = [
            'id', 'title', 'operation_type', 'operation_type_display',
            'status', 'status_display', 'description', 'started_at', 
            'completed_at', 'duration', 'result', 'operator', 'operator_info',
            'priority', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_operator_info(self, obj):
        """اطلاعات اپراتور"""
        if obj.operator:
            return {
                'id': obj.operator.id,
                'name': obj.operator.user.get_full_name() or obj.operator.user.username,
                'role': obj.operator.get_role_display()
            }
        return None
    
    def get_duration(self, obj):
        """محاسبه مدت زمان"""
        if obj.started_at and obj.completed_at:
            duration = obj.completed_at - obj.started_at
            return str(duration)
        elif obj.started_at:
            duration = timezone.now() - obj.started_at
            return f'{str(duration)} (در حال اجرا)'
        return None


class SystemOperationCreateSerializer(serializers.ModelSerializer):
    """سریالایزر ایجاد عملیات سیستمی"""
    
    class Meta:
        model = SystemOperation
        fields = ['title', 'operation_type', 'description', 'priority']


class SupportTicketSerializer(serializers.ModelSerializer):
    """سریالایزر تیکت پشتیبانی"""
    
    user_info = serializers.SerializerMethodField()
    assigned_to_info = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    days_since_created = serializers.SerializerMethodField()
    
    class Meta:
        model = SupportTicket
        fields = [
            'id', 'ticket_number', 'user', 'user_info', 'subject', 
            'description', 'category', 'category_display', 'priority', 
            'priority_display', 'status', 'status_display', 'assigned_to', 
            'assigned_to_info', 'resolution', 'resolved_at', 'days_since_created',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'ticket_number', 'created_at', 'updated_at']
    
    def get_user_info(self, obj):
        """اطلاعات کاربر"""
        user = obj.user
        return {
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name(),
            'email': getattr(user, 'email', '')
        }
    
    def get_assigned_to_info(self, obj):
        """اطلاعات تخصیص یافته"""
        if obj.assigned_to:
            return {
                'id': obj.assigned_to.id,
                'name': obj.assigned_to.user.get_full_name() or obj.assigned_to.user.username,
                'role': obj.assigned_to.get_role_display()
            }
        return None
    
    def get_days_since_created(self, obj):
        """روزهای گذشته از ایجاد"""
        now = timezone.now()
        diff = now - obj.created_at
        return diff.days


class SupportTicketUpdateSerializer(serializers.ModelSerializer):
    """سریالایزر بروزرسانی تیکت"""
    
    class Meta:
        model = SupportTicket
        fields = ['category', 'priority', 'status', 'assigned_to', 'resolution']


class SystemMetricsSerializer(serializers.ModelSerializer):
    """سریالایزر متریک‌های سیستم"""
    
    metric_type_display = serializers.CharField(source='get_metric_type_display', read_only=True)
    value_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemMetrics
        fields = [
            'id', 'metric_name', 'metric_type', 'metric_type_display',
            'value', 'value_formatted', 'unit', 'metadata', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']
    
    def get_value_formatted(self, obj):
        """فرمت مقدار"""
        return f'{obj.value:,.2f} {obj.unit}'.strip()


class AdminAuditLogSerializer(serializers.ModelSerializer):
    """سریالایزر لاگ حسابرسی"""
    
    admin_user_info = serializers.SerializerMethodField()
    changes_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = AdminAuditLog
        fields = [
            'id', 'admin_user', 'admin_user_info', 'resource_type', 
            'resource_id', 'action_performed', 'old_values', 'new_values',
            'changes_summary', 'reason', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_admin_user_info(self, obj):
        """اطلاعات کاربر ادمین"""
        if obj.admin_user:
            return {
                'id': obj.admin_user.id,
                'name': obj.admin_user.user.get_full_name() or obj.admin_user.user.username,
                'role': obj.admin_user.get_role_display()
            }
        return None
    
    def get_changes_summary(self, obj):
        """خلاصه تغییرات"""
        old_count = len(obj.old_values) if obj.old_values else 0
        new_count = len(obj.new_values) if obj.new_values else 0
        return f'{old_count} فیلد قبلی، {new_count} فیلد جدید'


class AdminSessionSerializer(serializers.ModelSerializer):
    """سریالایزر نشست ادمین"""
    
    admin_user_info = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = AdminSession
        fields = [
            'id', 'admin_user', 'admin_user_info', 'session_key', 
            'ip_address', 'user_agent', 'location', 'started_at', 
            'last_activity', 'ended_at', 'duration', 'status', 'is_active'
        ]
        read_only_fields = ['id', 'started_at', 'last_activity', 'ended_at']
    
    def get_admin_user_info(self, obj):
        """اطلاعات کاربر ادمین"""
        return {
            'id': obj.admin_user.id,
            'name': obj.admin_user.user.get_full_name() or obj.admin_user.user.username,
            'role': obj.admin_user.get_role_display()
        }
    
    def get_duration(self, obj):
        """مدت زمان نشست"""
        if hasattr(obj, 'duration'):
            return str(obj.duration)
        return None
    
    def get_status(self, obj):
        """وضعیت نشست"""
        if obj.is_active:
            return 'فعال'
        return 'پایان یافته'


# سریالایزرهای عمومی
class SearchQuerySerializer(serializers.Serializer):
    """سریالایزر جستجو"""
    
    query = serializers.CharField(max_length=200)
    search_type = serializers.ChoiceField(
        choices=[
            ('general', 'عمومی'),
            ('user', 'کاربر'),
            ('ticket', 'تیکت'),
            ('operation', 'عملیات')
        ],
        default='general'
    )
    filters = serializers.JSONField(required=False, default=dict)


class BulkOperationSerializer(serializers.Serializer):
    """سریالایزر عملیات دسته‌ای"""
    
    operation_type = serializers.ChoiceField(choices=[
        ('activate', 'فعال‌سازی'),
        ('deactivate', 'غیرفعال‌سازی'),
        ('delete', 'حذف'),
        ('update', 'بروزرسانی'),
        ('export', 'صادرات')
    ])
    item_ids = serializers.ListField(
        child=serializers.CharField(),
        min_length=1
    )
    options = serializers.JSONField(required=False, default=dict)


class SystemMonitoringSerializer(serializers.Serializer):
    """سریالایزر مانیتورینگ سیستم"""
    
    scope = serializers.ChoiceField(
        choices=[
            ('basic', 'پایه'),
            ('full', 'کامل'),
            ('performance', 'عملکرد'),
            ('security', 'امنیت')
        ],
        default='basic'
    )
    include_metrics = serializers.BooleanField(default=True)
    time_range = serializers.ChoiceField(
        choices=[
            ('1h', '1 ساعت'),
            ('24h', '24 ساعت'),
            ('7d', '7 روز'),
            ('30d', '30 روز')
        ],
        default='24h'
    )


class ReportGenerationSerializer(serializers.Serializer):
    """سریالایزر تولید گزارش"""
    
    report_type = serializers.ChoiceField(choices=[
        ('users', 'کاربران'),
        ('tickets', 'تیکت‌ها'),
        ('operations', 'عملیات'),
        ('metrics', 'متریک‌ها'),
        ('audit', 'حسابرسی')
    ])
    date_range = serializers.JSONField(required=False, default=dict)
    filters = serializers.JSONField(required=False, default=dict)
    format = serializers.ChoiceField(
        choices=[('json', 'JSON'), ('csv', 'CSV'), ('pdf', 'PDF')],
        default='json'
    )
    include_details = serializers.BooleanField(default=True)


class VoiceProcessingSerializer(serializers.Serializer):
    """سریالایزر پردازش صوت"""
    
    audio_data = serializers.CharField(
        help_text='داده‌های صوتی به فرمت base64'
    )
    processing_type = serializers.ChoiceField(
        choices=[
            ('command', 'دستور'),
            ('note', 'یادداشت'),
            ('call_analysis', 'تحلیل تماس')
        ],
        default='command'
    )
    context = serializers.CharField(required=False, max_length=100)
    language = serializers.CharField(default='fa-IR', max_length=10)


class ContentAnalysisSerializer(serializers.Serializer):
    """سریالایزر تحلیل محتوا"""
    
    content = serializers.CharField()
    content_type = serializers.ChoiceField(
        choices=[
            ('general', 'عمومی'),
            ('ticket', 'تیکت'),
            ('operation', 'عملیات'),
            ('log', 'لاگ'),
            ('comment', 'نظر')
        ],
        default='general'
    )
    analysis_depth = serializers.ChoiceField(
        choices=[
            ('basic', 'پایه'),
            ('detailed', 'تفصیلی'),
            ('full', 'کامل')
        ],
        default='basic'
    )
    filter_sensitive = serializers.BooleanField(default=True)