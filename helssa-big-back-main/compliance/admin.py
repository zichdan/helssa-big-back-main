from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    SecurityLayer, SecurityLog, MFAConfig, Role, TemporaryAccess,
    AuditLog, HIPAAComplianceReport, SecurityIncident, MedicalFile
)


@admin.register(SecurityLayer)
class SecurityLayerAdmin(admin.ModelAdmin):
    """مدیریت لایه‌های امنیتی"""
    list_display = ['name', 'layer_type', 'priority', 'is_active', 'created_at']
    list_filter = ['layer_type', 'is_active', 'created_at']
    search_fields = ['name']
    ordering = ['priority', 'name']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'layer_type', 'priority', 'is_active')
        }),
        ('تنظیمات', {
            'fields': ('config',),
            'classes': ('wide',)
        }),
        ('زمان‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    """مدیریت لاگ‌های امنیتی"""
    list_display = ['event_type', 'user', 'ip_address', 'risk_score', 'created_at']
    list_filter = ['event_type', 'risk_score', 'created_at']
    search_fields = ['reason', 'ip_address', 'user__username']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def has_add_permission(self, request):
        return False  # لاگ‌ها فقط توسط سیستم ایجاد می‌شوند


@admin.register(MFAConfig)
class MFAConfigAdmin(admin.ModelAdmin):
    """مدیریت تنظیمات MFA"""
    list_display = ['user', 'is_active', 'last_used', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['secret', 'backup_codes', 'last_used', 'created_at', 'updated_at']
    
    fieldsets = (
        ('کاربر', {
            'fields': ('user', 'is_active')
        }),
        ('اطلاعات امنیتی', {
            'fields': ('secret', 'backup_codes', 'last_used'),
            'classes': ('collapse',)
        }),
        ('زمان‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """مدیریت نقش‌ها"""
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('اطلاعات نقش', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('مجوزها', {
            'fields': ('permissions',),
            'classes': ('wide',)
        }),
    )


@admin.register(TemporaryAccess)
class TemporaryAccessAdmin(admin.ModelAdmin):
    """مدیریت دسترسی‌های موقت"""
    list_display = ['doctor', 'patient_id', 'is_active', 'granted_at', 'expires_at', 'is_valid_display']
    list_filter = ['is_active', 'granted_at', 'expires_at']
    search_fields = ['doctor__username', 'patient_id', 'reason']
    date_hierarchy = 'granted_at'
    
    def is_valid_display(self, obj):
        """نمایش وضعیت اعتبار"""
        if obj.is_valid():
            return format_html('<span style="color: green;">✓ معتبر</span>')
        return format_html('<span style="color: red;">✗ نامعتبر</span>')
    is_valid_display.short_description = 'وضعیت'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('doctor', 'granted_by')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """مدیریت لاگ‌های ممیزی"""
    list_display = ['event_type', 'user_id', 'resource', 'action', 'result', 'timestamp']
    list_filter = ['event_type', 'result', 'timestamp']
    search_fields = ['event_type', 'resource', 'action']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False  # لاگ‌های audit نباید حذف شوند


@admin.register(HIPAAComplianceReport)
class HIPAAComplianceReportAdmin(admin.ModelAdmin):
    """مدیریت گزارش‌های HIPAA"""
    list_display = ['report_date', 'compliant', 'score', 'generated_by', 'created_at']
    list_filter = ['compliant', 'report_date', 'created_at']
    date_hierarchy = 'report_date'
    readonly_fields = ['generated_by', 'created_at']
    
    fieldsets = (
        ('اطلاعات گزارش', {
            'fields': ('report_date', 'compliant', 'score')
        }),
        ('امتیازات', {
            'fields': ('administrative_score', 'physical_score', 'technical_score')
        }),
        ('یافته‌ها و پیشنهادات', {
            'fields': ('findings', 'recommendations'),
            'classes': ('wide',)
        }),
        ('اطلاعات تولید', {
            'fields': ('generated_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # فقط برای ایجاد
            obj.generated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SecurityIncident)
class SecurityIncidentAdmin(admin.ModelAdmin):
    """مدیریت حوادث امنیتی"""
    list_display = ['incident_type', 'severity', 'status', 'detected_at', 'assigned_to']
    list_filter = ['incident_type', 'severity', 'status', 'detected_at']
    search_fields = ['details']
    date_hierarchy = 'detected_at'
    
    fieldsets = (
        ('اطلاعات حادثه', {
            'fields': ('incident_type', 'severity', 'status', 'detected_at')
        }),
        ('جزئیات', {
            'fields': ('details', 'affected_systems'),
            'classes': ('wide',)
        }),
        ('مدیریت', {
            'fields': ('assigned_to', 'response_plan'),
        }),
        ('زمان‌بندی', {
            'fields': ('contained_at', 'resolved_at'),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('assigned_to')


@admin.register(MedicalFile)
class MedicalFileAdmin(admin.ModelAdmin):
    """مدیریت فایل‌های پزشکی"""
    list_display = ['file_id', 'patient_id', 'file_type', 'file_size', 'uploaded_by', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['file_id', 'patient_id']
    date_hierarchy = 'uploaded_at'
    readonly_fields = ['file_id', 'encryption_key_id', 'uploaded_at', 'last_accessed', 'access_count']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('uploaded_by')
    
    def has_delete_permission(self, request, obj=None):
        # فقط superuser می‌تواند فایل‌های پزشکی را حذف کند
        return request.user.is_superuser