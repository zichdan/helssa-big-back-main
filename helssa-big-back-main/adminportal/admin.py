"""
رابط ادمین سفارشی پنل ادمین
AdminPortal Custom Django Admin Interface
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.admin import SimpleListFilter
from django.utils.safestring import mark_safe
import json

from .models import (
    AdminUser, SystemOperation, SupportTicket, 
    SystemMetrics, AdminAuditLog, AdminSession
)


class AdminUserRoleFilter(SimpleListFilter):
    """فیلتر نقش کاربران ادمین"""
    title = 'نقش'
    parameter_name = 'role'
    
    def lookups(self, request, model_admin):
        return AdminUser.ROLE_CHOICES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(role=self.value())
        return queryset


class LastActivityFilter(SimpleListFilter):
    """فیلتر آخرین فعالیت"""
    title = 'آخرین فعالیت'
    parameter_name = 'last_activity'
    
    def lookups(self, request, model_admin):
        return [
            ('today', 'امروز'),
            ('week', 'هفته گذشته'),
            ('month', 'ماه گذشته'),
            ('inactive', 'غیرفعال'),
        ]
    
    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'today':
            return queryset.filter(last_activity__date=now.date())
        elif self.value() == 'week':
            return queryset.filter(last_activity__gte=now - timezone.timedelta(days=7))
        elif self.value() == 'month':
            return queryset.filter(last_activity__gte=now - timezone.timedelta(days=30))
        elif self.value() == 'inactive':
            return queryset.filter(
                Q(last_activity__isnull=True) | 
                Q(last_activity__lt=now - timezone.timedelta(days=30))
            )
        return queryset


@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    """ادمین کاربران ادمین"""
    
    list_display = [
        'user_display', 'role_display', 'department', 
        'last_activity_display', 'is_active_display', 'permissions_count'
    ]
    list_filter = [AdminUserRoleFilter, LastActivityFilter, 'is_active', 'department']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'last_activity', 'permissions_display']
    
    fieldsets = [
        ('اطلاعات اصلی', {
            'fields': ['user', 'role', 'department', 'is_active']
        }),
        ('دسترسی‌ها', {
            'fields': ['permissions', 'permissions_display'],
            'classes': ['collapse']
        }),
        ('اطلاعات سیستم', {
            'fields': ['last_activity', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    actions = ['activate_users', 'deactivate_users', 'update_last_activity']
    
    def user_display(self, obj):
        """نمایش کاربر"""
        user = obj.user
        full_name = user.get_full_name()
        if full_name:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                full_name,
                user.username
            )
        return user.username
    user_display.short_description = 'کاربر'
    
    def role_display(self, obj):
        """نمایش نقش با رنگ"""
        colors = {
            'super_admin': '#dc3545',  # قرمز
            'support_admin': '#007bff',  # آبی
            'content_admin': '#28a745',  # سبز
            'financial_admin': '#ffc107',  # زرد
            'technical_admin': '#6c757d',  # خاکستری
        }
        color = colors.get(obj.role, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_role_display()
        )
    role_display.short_description = 'نقش'
    
    def last_activity_display(self, obj):
        """نمایش آخرین فعالیت"""
        if not obj.last_activity:
            return format_html('<span style="color: #dc3545;">هرگز</span>')
        
        now = timezone.now()
        diff = now - obj.last_activity
        
        if diff.days == 0:
            return format_html('<span style="color: #28a745;">امروز</span>')
        elif diff.days <= 7:
            return format_html('<span style="color: #ffc107;">{} روز پیش</span>', diff.days)
        else:
            return format_html('<span style="color: #dc3545;">{} روز پیش</span>', diff.days)
    last_activity_display.short_description = 'آخرین فعالیت'
    
    def is_active_display(self, obj):
        """نمایش وضعیت فعال بودن"""
        if obj.is_active:
            return format_html('<span style="color: #28a745;">✓ فعال</span>')
        return format_html('<span style="color: #dc3545;">✗ غیرفعال</span>')
    is_active_display.short_description = 'وضعیت'
    
    def permissions_count(self, obj):
        """تعداد دسترسی‌های اضافی"""
        return len(obj.permissions) if obj.permissions else 0
    permissions_count.short_description = 'تعداد دسترسی‌ها'
    
    def permissions_display(self, obj):
        """نمایش دسترسی‌ها"""
        if not obj.permissions:
            return 'بدون دسترسی اضافی'
        
        permissions_html = '<ul>'
        for perm in obj.permissions:
            permissions_html += f'<li>{perm}</li>'
        permissions_html += '</ul>'
        return mark_safe(permissions_html)
    permissions_display.short_description = 'دسترسی‌های اضافی'
    
    def activate_users(self, request, queryset):
        """فعال‌سازی کاربران"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} کاربر فعال شد.')
    activate_users.short_description = 'فعال‌سازی کاربران انتخاب شده'
    
    def deactivate_users(self, request, queryset):
        """غیرفعال‌سازی کاربران"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} کاربر غیرفعال شد.')
    deactivate_users.short_description = 'غیرفعال‌سازی کاربران انتخاب شده'
    
    def update_last_activity(self, request, queryset):
        """بروزرسانی آخرین فعالیت"""
        for admin_user in queryset:
            admin_user.update_last_activity()
        self.message_user(request, f'آخرین فعالیت {queryset.count()} کاربر بروزرسانی شد.')
    update_last_activity.short_description = 'بروزرسانی آخرین فعالیت'


class OperationStatusFilter(SimpleListFilter):
    """فیلتر وضعیت عملیات"""
    title = 'وضعیت'
    parameter_name = 'status'
    
    def lookups(self, request, model_admin):
        return SystemOperation.STATUS_CHOICES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


@admin.register(SystemOperation)
class SystemOperationAdmin(admin.ModelAdmin):
    """ادمین عملیات سیستمی"""
    
    list_display = [
        'title', 'operation_type_display', 'status_display', 
        'priority_display', 'operator_display', 'duration_display', 'created_at'
    ]
    list_filter = [OperationStatusFilter, 'operation_type', 'priority', 'operator']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at', 'result_display', 'duration_display']
    date_hierarchy = 'created_at'
    
    fieldsets = [
        ('اطلاعات عملیات', {
            'fields': ['title', 'operation_type', 'description', 'priority']
        }),
        ('وضعیت و زمان‌بندی', {
            'fields': ['status', 'operator', 'started_at', 'completed_at', 'duration_display']
        }),
        ('نتیجه', {
            'fields': ['result', 'result_display'],
            'classes': ['collapse']
        }),
        ('اطلاعات سیستم', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    actions = ['start_operations', 'cancel_operations']
    
    def operation_type_display(self, obj):
        """نمایش نوع عملیات"""
        return obj.get_operation_type_display()
    operation_type_display.short_description = 'نوع عملیات'
    
    def status_display(self, obj):
        """نمایش وضعیت با رنگ"""
        colors = {
            'pending': '#ffc107',
            'in_progress': '#007bff',
            'completed': '#28a745',
            'failed': '#dc3545',
            'cancelled': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'وضعیت'
    
    def priority_display(self, obj):
        """نمایش اولویت"""
        if obj.priority >= 4:
            color = '#dc3545'  # بحرانی
        elif obj.priority >= 3:
            color = '#ffc107'  # بالا
        else:
            color = '#28a745'  # عادی
        
        return format_html(
            '<span style="color: {};">● {}</span>',
            color,
            obj.priority
        )
    priority_display.short_description = 'اولویت'
    
    def operator_display(self, obj):
        """نمایش اپراتور"""
        if obj.operator:
            return obj.operator.user.get_full_name() or obj.operator.user.username
        return '-'
    operator_display.short_description = 'اپراتور'
    
    def duration_display(self, obj):
        """نمایش مدت زمان"""
        if obj.started_at and obj.completed_at:
            duration = obj.completed_at - obj.started_at
            return str(duration)
        elif obj.started_at:
            duration = timezone.now() - obj.started_at
            return f'{str(duration)} (در حال اجرا)'
        return '-'
    duration_display.short_description = 'مدت زمان'
    
    def result_display(self, obj):
        """نمایش نتیجه"""
        if not obj.result:
            return 'بدون نتیجه'
        
        try:
            formatted_result = json.dumps(obj.result, indent=2, ensure_ascii=False)
            return format_html('<pre>{}</pre>', formatted_result)
        except:
            return str(obj.result)
    result_display.short_description = 'نتیجه تفصیلی'
    
    def start_operations(self, request, queryset):
        """شروع عملیات‌ها"""
        pending_ops = queryset.filter(status='pending')
        for op in pending_ops:
            op.start_operation()
        self.message_user(request, f'{pending_ops.count()} عملیات شروع شد.')
    start_operations.short_description = 'شروع عملیات‌های انتخاب شده'
    
    def cancel_operations(self, request, queryset):
        """لغو عملیات‌ها"""
        active_ops = queryset.filter(status__in=['pending', 'in_progress'])
        updated = active_ops.update(status='cancelled', completed_at=timezone.now())
        self.message_user(request, f'{updated} عملیات لغو شد.')
    cancel_operations.short_description = 'لغو عملیات‌های انتخاب شده'


class TicketStatusFilter(SimpleListFilter):
    """فیلتر وضعیت تیکت"""
    title = 'وضعیت'
    parameter_name = 'status'
    
    def lookups(self, request, model_admin):
        return SupportTicket.STATUS_CHOICES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class TicketPriorityFilter(SimpleListFilter):
    """فیلتر اولویت تیکت"""
    title = 'اولویت'
    parameter_name = 'priority'
    
    def lookups(self, request, model_admin):
        return SupportTicket.PRIORITY_CHOICES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(priority=self.value())
        return queryset


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    """ادمین تیکت‌های پشتیبانی"""
    
    list_display = [
        'ticket_number', 'subject_short', 'user_display', 'category_display',
        'priority_display', 'status_display', 'assigned_to_display', 'created_at'
    ]
    list_filter = [TicketStatusFilter, TicketPriorityFilter, 'category', 'assigned_to']
    search_fields = ['ticket_number', 'subject', 'description', 'user__username']
    readonly_fields = ['ticket_number', 'created_at', 'updated_at', 'resolved_at']
    date_hierarchy = 'created_at'
    
    fieldsets = [
        ('اطلاعات تیکت', {
            'fields': ['ticket_number', 'user', 'subject', 'description']
        }),
        ('دسته‌بندی و اولویت', {
            'fields': ['category', 'priority', 'status']
        }),
        ('تخصیص و حل', {
            'fields': ['assigned_to', 'resolution', 'resolved_at']
        }),
        ('اطلاعات سیستم', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    actions = ['assign_to_me', 'mark_as_resolved', 'escalate_priority']
    
    def subject_short(self, obj):
        """موضوع کوتاه"""
        return obj.subject[:50] + '...' if len(obj.subject) > 50 else obj.subject
    subject_short.short_description = 'موضوع'
    
    def user_display(self, obj):
        """نمایش کاربر"""
        user = obj.user
        return user.get_full_name() or user.username
    user_display.short_description = 'کاربر'
    
    def category_display(self, obj):
        """نمایش دسته‌بندی"""
        return obj.get_category_display()
    category_display.short_description = 'دسته‌بندی'
    
    def priority_display(self, obj):
        """نمایش اولویت با رنگ"""
        colors = {
            'low': '#28a745',
            'normal': '#007bff',
            'high': '#ffc107',
            'urgent': '#dc3545'
        }
        color = colors.get(obj.priority, '#007bff')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_display.short_description = 'اولویت'
    
    def status_display(self, obj):
        """نمایش وضعیت با رنگ"""
        colors = {
            'open': '#007bff',
            'in_progress': '#ffc107',
            'waiting_user': '#6c757d',
            'resolved': '#28a745',
            'closed': '#343a40'
        }
        color = colors.get(obj.status, '#007bff')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'وضعیت'
    
    def assigned_to_display(self, obj):
        """نمایش تخصیص یافته"""
        if obj.assigned_to:
            return obj.assigned_to.user.get_full_name() or obj.assigned_to.user.username
        return format_html('<span style="color: #dc3545;">تخصیص نیافته</span>')
    assigned_to_display.short_description = 'تخصیص یافته به'
    
    def assign_to_me(self, request, queryset):
        """تخصیص به خودم"""
        if hasattr(request.user, 'admin_profile'):
            updated = 0
            for ticket in queryset.filter(assigned_to__isnull=True):
                ticket.assign_to_admin(request.user.admin_profile)
                updated += 1
            self.message_user(request, f'{updated} تیکت به شما تخصیص یافت.')
        else:
            self.message_user(request, 'شما پروفایل ادمین ندارید.', level='ERROR')
    assign_to_me.short_description = 'تخصیص به من'
    
    def mark_as_resolved(self, request, queryset):
        """علامت‌گذاری به عنوان حل شده"""
        open_tickets = queryset.exclude(status='resolved')
        updated = 0
        for ticket in open_tickets:
            ticket.resolve_ticket('حل شده توسط ادمین', request.user.admin_profile)
            updated += 1
        self.message_user(request, f'{updated} تیکت حل شد.')
    mark_as_resolved.short_description = 'علامت‌گذاری به عنوان حل شده'
    
    def escalate_priority(self, request, queryset):
        """افزایش اولویت"""
        priority_map = {'low': 'normal', 'normal': 'high', 'high': 'urgent'}
        updated = 0
        for ticket in queryset:
            if ticket.priority in priority_map:
                ticket.priority = priority_map[ticket.priority]
                ticket.save()
                updated += 1
        self.message_user(request, f'اولویت {updated} تیکت افزایش یافت.')
    escalate_priority.short_description = 'افزایش اولویت'


@admin.register(SystemMetrics)
class SystemMetricsAdmin(admin.ModelAdmin):
    """ادمین متریک‌های سیستم"""
    
    list_display = ['metric_name', 'metric_type', 'value_display', 'unit', 'timestamp']
    list_filter = ['metric_type', 'metric_name']
    search_fields = ['metric_name']
    readonly_fields = ['timestamp', 'metadata_display']
    date_hierarchy = 'timestamp'
    
    fieldsets = [
        ('اطلاعات متریک', {
            'fields': ['metric_name', 'metric_type', 'value', 'unit']
        }),
        ('متادیتا', {
            'fields': ['metadata', 'metadata_display'],
            'classes': ['collapse']
        }),
        ('زمان', {
            'fields': ['timestamp']
        })
    ]
    
    def value_display(self, obj):
        """نمایش مقدار با فرمت"""
        return f'{obj.value:,.2f}'
    value_display.short_description = 'مقدار'
    
    def metadata_display(self, obj):
        """نمایش متادیتا"""
        if not obj.metadata:
            return 'بدون متادیتا'
        
        try:
            formatted_metadata = json.dumps(obj.metadata, indent=2, ensure_ascii=False)
            return format_html('<pre>{}</pre>', formatted_metadata)
        except:
            return str(obj.metadata)
    metadata_display.short_description = 'متادیتای تفصیلی'


@admin.register(AdminAuditLog)
class AdminAuditLogAdmin(admin.ModelAdmin):
    """ادمین لاگ‌های حسابرسی"""
    
    list_display = [
        'admin_user_display', 'action_performed', 'resource_type', 
        'resource_id', 'created_at'
    ]
    list_filter = ['action_performed', 'resource_type', 'admin_user']
    search_fields = ['action_performed', 'resource_type', 'resource_id', 'reason']
    readonly_fields = ['created_at', 'changes_display']
    date_hierarchy = 'created_at'
    
    fieldsets = [
        ('اطلاعات عملیات', {
            'fields': ['admin_user', 'action_performed', 'resource_type', 'resource_id']
        }),
        ('تغییرات', {
            'fields': ['old_values', 'new_values', 'changes_display'],
            'classes': ['collapse']
        }),
        ('دلیل و زمان', {
            'fields': ['reason', 'created_at']
        })
    ]
    
    def admin_user_display(self, obj):
        """نمایش کاربر ادمین"""
        if obj.admin_user:
            return obj.admin_user.user.get_full_name() or obj.admin_user.user.username
        return 'نامشخص'
    admin_user_display.short_description = 'کاربر ادمین'
    
    def changes_display(self, obj):
        """نمایش تغییرات"""
        changes_html = '<h4>مقادیر قبلی:</h4>'
        if obj.old_values:
            changes_html += f'<pre>{json.dumps(obj.old_values, indent=2, ensure_ascii=False)}</pre>'
        else:
            changes_html += '<p>بدون مقدار قبلی</p>'
        
        changes_html += '<h4>مقادیر جدید:</h4>'
        if obj.new_values:
            changes_html += f'<pre>{json.dumps(obj.new_values, indent=2, ensure_ascii=False)}</pre>'
        else:
            changes_html += '<p>بدون مقدار جدید</p>'
        
        return mark_safe(changes_html)
    changes_display.short_description = 'تغییرات تفصیلی'


@admin.register(AdminSession)
class AdminSessionAdmin(admin.ModelAdmin):
    """ادمین نشست‌های ادمین"""
    
    list_display = [
        'admin_user_display', 'ip_address', 'location', 
        'started_at', 'last_activity', 'is_active_display', 'duration_display'
    ]
    list_filter = ['is_active', 'admin_user']
    search_fields = ['admin_user__user__username', 'ip_address', 'location']
    readonly_fields = ['session_key', 'started_at', 'last_activity', 'duration_display']
    date_hierarchy = 'started_at'
    
    fieldsets = [
        ('اطلاعات نشست', {
            'fields': ['admin_user', 'session_key', 'ip_address', 'location']
        }),
        ('زمان‌بندی', {
            'fields': ['started_at', 'last_activity', 'ended_at', 'duration_display']
        }),
        ('جزئیات', {
            'fields': ['user_agent', 'is_active'],
            'classes': ['collapse']
        })
    ]
    
    actions = ['end_sessions']
    
    def admin_user_display(self, obj):
        """نمایش کاربر ادمین"""
        return obj.admin_user.user.get_full_name() or obj.admin_user.user.username
    admin_user_display.short_description = 'کاربر ادمین'
    
    def is_active_display(self, obj):
        """نمایش وضعیت فعال بودن"""
        if obj.is_active:
            return format_html('<span style="color: #28a745;">● فعال</span>')
        return format_html('<span style="color: #dc3545;">● غیرفعال</span>')
    is_active_display.short_description = 'وضعیت'
    
    def duration_display(self, obj):
        """نمایش مدت زمان نشست"""
        if hasattr(obj, 'duration'):
            return str(obj.duration)
        return '-'
    duration_display.short_description = 'مدت زمان'
    
    def end_sessions(self, request, queryset):
        """پایان نشست‌ها"""
        active_sessions = queryset.filter(is_active=True)
        for session in active_sessions:
            session.end_session()
        self.message_user(request, f'{active_sessions.count()} نشست پایان یافت.')
    end_sessions.short_description = 'پایان نشست‌های انتخاب شده'


# تنظیمات کلی ادمین
admin.site.site_header = 'پنل ادمین هلسا'
admin.site.site_title = 'ادمین هلسا'
admin.site.index_title = 'پنل مدیریت سیستم'