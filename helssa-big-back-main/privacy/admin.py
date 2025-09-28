"""
Django Admin Configuration برای ماژول Privacy
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    DataClassification,
    DataField,
    DataAccessLog,
    ConsentRecord,
    DataRetentionPolicy
)


@admin.register(DataClassification)
class DataClassificationAdmin(admin.ModelAdmin):
    """
    ادمین برای طبقه‌بندی داده‌ها
    """
    list_display = [
        'name', 'classification_type', 'retention_period_days',
        'is_active', 'created_at'
    ]
    list_filter = ['classification_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'classification_type', 'description')
        }),
        ('تنظیمات نگهداری', {
            'fields': ('retention_period_days', 'is_active')
        }),
        ('اطلاعات سیستمی', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            fields_count=admin.Count('fields')
        )


@admin.register(DataField)
class DataFieldAdmin(admin.ModelAdmin):
    """
    ادمین برای فیلدهای داده
    """
    list_display = [
        'field_name', 'model_name', 'app_name', 'classification',
        'is_encrypted', 'is_active', 'created_at'
    ]
    list_filter = [
        'app_name', 'classification__classification_type',
        'is_encrypted', 'is_active', 'created_at'
    ]
    search_fields = ['field_name', 'model_name', 'app_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['classification']
    
    fieldsets = (
        ('شناسایی فیلد', {
            'fields': ('field_name', 'model_name', 'app_name')
        }),
        ('طبقه‌بندی و امنیت', {
            'fields': ('classification', 'is_encrypted', 'encryption_algorithm')
        }),
        ('تنظیمات پنهان‌سازی', {
            'fields': ('redaction_pattern', 'replacement_text')
        }),
        ('وضعیت', {
            'fields': ('is_active',)
        }),
        ('اطلاعات سیستمی', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('classification')


@admin.register(DataAccessLog)
class DataAccessLogAdmin(admin.ModelAdmin):
    """
    ادمین برای لاگ‌های دسترسی
    """
    list_display = [
        'user', 'data_field', 'action_type', 'was_redacted',
        'ip_address', 'timestamp'
    ]
    list_filter = [
        'action_type', 'was_redacted', 'timestamp',
        'data_field__classification__classification_type'
    ]
    search_fields = [
        'user__username', 'data_field__field_name',
        'purpose', 'ip_address'
    ]
    readonly_fields = [
        'id', 'user', 'data_field', 'action_type', 'record_id',
        'ip_address', 'user_agent', 'purpose', 'was_redacted',
        'original_value_hash', 'context_data', 'timestamp'
    ]
    
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        """غیرفعال کردن امکان اضافه کردن دستی"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """غیرفعال کردن امکان ویرایش"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """غیرفعال کردن امکان حذف (فقط برای superuser)"""
        return request.user.is_superuser
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'data_field', 'data_field__classification'
        )


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    """
    ادمین برای رکوردهای رضایت
    """
    list_display = [
        'user', 'consent_type', 'status', 'granted_at',
        'expires_at', 'is_active_status'
    ]
    list_filter = [
        'consent_type', 'status', 'granted_at', 'expires_at'
    ]
    search_fields = ['user__username', 'purpose', 'legal_basis']
    readonly_fields = [
        'id', 'granted_at', 'is_active'
    ]
    filter_horizontal = ['data_categories']
    
    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('user',)
        }),
        ('جزئیات رضایت', {
            'fields': ('consent_type', 'status', 'purpose', 'legal_basis')
        }),
        ('دسته‌بندی داده‌ها', {
            'fields': ('data_categories',)
        }),
        ('زمان‌بندی', {
            'fields': ('granted_at', 'expires_at', 'withdrawn_at')
        }),
        ('جزئیات پس‌گیری', {
            'fields': ('withdrawal_reason',),
            'classes': ('collapse',)
        }),
        ('اطلاعات فنی', {
            'fields': ('ip_address', 'user_agent', 'version'),
            'classes': ('collapse',)
        }),
        ('وضعیت', {
            'fields': ('is_active',)
        })
    )
    
    def is_active_status(self, obj):
        """نمایش وضعیت فعال/غیرفعال با رنگ"""
        if obj.is_active:
            return format_html(
                '<span style="color: green;">●</span> فعال'
            )
        else:
            return format_html(
                '<span style="color: red;">●</span> غیرفعال'
            )
    is_active_status.short_description = 'وضعیت'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('data_categories')


@admin.register(DataRetentionPolicy)
class DataRetentionPolicyAdmin(admin.ModelAdmin):
    """
    ادمین برای سیاست‌های نگهداری داده
    """
    list_display = [
        'name', 'classification', 'retention_period_days',
        'auto_delete', 'is_active', 'created_at'
    ]
    list_filter = [
        'classification__classification_type', 'auto_delete',
        'archive_before_delete', 'is_active', 'created_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['classification']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'classification', 'description')
        }),
        ('تنظیمات نگهداری', {
            'fields': (
                'retention_period_days', 'auto_delete',
                'archive_before_delete', 'notification_days_before'
            )
        }),
        ('وضعیت', {
            'fields': ('is_active',)
        }),
        ('اطلاعات سیستمی', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('classification')


# تنظیمات اضافی برای Admin Site
admin.site.site_header = "مدیریت سیستم حریم خصوصی هلسا"
admin.site.site_title = "Privacy Admin"
admin.site.index_title = "مدیریت حریم خصوصی"