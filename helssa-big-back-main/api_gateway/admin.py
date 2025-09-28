"""
Django Admin برای API Gateway
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import UnifiedUser, APIRequest, Workflow, RateLimitTracker


@admin.register(UnifiedUser)
class UnifiedUserAdmin(admin.ModelAdmin):
    """
    مدیریت کاربران در پنل ادمین
    """
    
    list_display = [
        'username', 'get_full_name', 'user_type', 
        'is_phone_verified', 'is_active', 'created_at'
    ]
    list_filter = [
        'user_type', 'is_phone_verified', 'is_active', 
        'is_staff', 'created_at'
    ]
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('id', 'username', 'user_type', 'is_phone_verified')
        }),
        ('اطلاعات شخصی', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('دسترسی‌ها', {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at', 'last_login')
        }),
    )
    
    def get_full_name(self, obj):
        """نمایش نام کامل"""
        return obj.get_full_name()
    get_full_name.short_description = 'نام کامل'


@admin.register(APIRequest)
class APIRequestAdmin(admin.ModelAdmin):
    """
    مدیریت لاگ درخواست‌های API
    """
    
    list_display = [
        'id', 'get_user_display', 'method', 'path', 
        'status', 'response_status', 'get_duration', 'created_at'
    ]
    list_filter = [
        'method', 'status', 'response_status', 
        'processor_type', 'created_at'
    ]
    search_fields = ['user__username', 'path', 'ip_address']
    ordering = ['-created_at']
    readonly_fields = [
        'id', 'processing_time', 'created_at', 'completed_at'
    ]
    
    fieldsets = (
        ('اطلاعات درخواست', {
            'fields': ('id', 'user', 'method', 'path', 'ip_address')
        }),
        ('Headers و Body', {
            'fields': ('user_agent', 'request_headers', 'request_body'),
            'classes': ('collapse',)
        }),
        ('پاسخ', {
            'fields': ('response_status', 'response_body', 'status')
        }),
        ('پردازش', {
            'fields': (
                'processor_type', 'processing_time', 
                'error_message', 'created_at', 'completed_at'
            )
        }),
    )
    
    def get_user_display(self, obj):
        """نمایش کاربر"""
        if obj.user:
            return obj.user.username
        return 'مهمان'
    get_user_display.short_description = 'کاربر'
    
    def get_duration(self, obj):
        """نمایش مدت زمان پردازش"""
        if obj.processing_time:
            if obj.processing_time < 1:
                return f"{obj.processing_time*1000:.0f}ms"
            else:
                return f"{obj.processing_time:.2f}s"
        return "نامشخص"
    get_duration.short_description = 'مدت زمان'
    
    def has_add_permission(self, request):
        """غیرفعال کردن امکان افزودن دستی"""
        return False


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    """
    مدیریت workflow ها
    """
    
    list_display = [
        'name', 'user', 'status', 'current_step',
        'get_steps_count', 'get_duration_display', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'started_at', 'completed_at']
    search_fields = ['name', 'user__username']
    ordering = ['-created_at']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 
        'started_at', 'completed_at', 'get_duration_display'
    ]
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('id', 'name', 'user', 'api_request')
        }),
        ('وضعیت', {
            'fields': ('status', 'current_step', 'error_message')
        }),
        ('تنظیمات', {
            'fields': ('config', 'context'),
            'classes': ('collapse',)
        }),
        ('نتایج', {
            'fields': ('completed_steps', 'results'),
            'classes': ('collapse',)
        }),
        ('زمان‌بندی', {
            'fields': (
                'created_at', 'updated_at', 
                'started_at', 'completed_at', 'get_duration_display'
            )
        }),
    )
    
    def get_steps_count(self, obj):
        """تعداد مراحل"""
        return len(obj.completed_steps)
    get_steps_count.short_description = 'مراحل تکمیل شده'
    
    def get_duration_display(self, obj):
        """نمایش مدت زمان اجرا"""
        duration = obj.get_duration()
        if duration > 0:
            if duration < 60:
                return f"{duration:.1f} ثانیه"
            elif duration < 3600:
                return f"{duration/60:.1f} دقیقه"
            else:
                return f"{duration/3600:.1f} ساعت"
        return "نامشخص"
    get_duration_display.short_description = 'مدت زمان اجرا'
    
    actions = ['cancel_workflows']
    
    def cancel_workflows(self, request, queryset):
        """لغو workflow های انتخاب شده"""
        cancelled_count = 0
        for workflow in queryset.filter(status__in=['pending', 'running']):
            workflow.status = 'cancelled'
            workflow.completed_at = timezone.now()
            workflow.save()
            cancelled_count += 1
        
        self.message_user(
            request,
            f"{cancelled_count} workflow لغو شد."
        )
    cancel_workflows.short_description = "لغو workflow های انتخاب شده"


@admin.register(RateLimitTracker)
class RateLimitTrackerAdmin(admin.ModelAdmin):
    """
    مدیریت ردگیری محدودیت نرخ
    """
    
    list_display = [
        'user', 'ip_address', 'endpoint', 
        'request_count', 'window_start', 'last_request'
    ]
    list_filter = ['endpoint', 'window_start', 'last_request']
    search_fields = ['user__username', 'ip_address', 'endpoint']
    ordering = ['-last_request']
    readonly_fields = ['window_start', 'last_request']
    
    def has_add_permission(self, request):
        """غیرفعال کردن امکان افزودن دستی"""
        return False


# تنظیمات اضافی Admin
admin.site.site_header = 'پنل مدیریت API Gateway'
admin.site.site_title = 'API Gateway'
admin.site.index_title = 'مدیریت دروازه API'