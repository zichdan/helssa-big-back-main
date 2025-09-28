"""
تنظیمات پنل ادمین برای اپلیکیشن Checklist
"""
from django.contrib import admin
from django.db.models import Count, Avg
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone

from .models import (
    ChecklistCatalog,
    ChecklistTemplate,
    ChecklistEval,
    ChecklistAlert
)


@admin.register(ChecklistCatalog)
class ChecklistCatalogAdmin(admin.ModelAdmin):
    """
    ادمین برای آیتم‌های کاتالوگ چک‌لیست
    """
    list_display = [
        'title', 'category_badge', 'priority_badge', 'specialty',
        'keywords_count', 'is_active', 'created_at'
    ]
    list_filter = [
        'category', 'priority', 'is_active', 'specialty',
        'created_at', 'updated_at'
    ]
    search_fields = [
        'title', 'description', 'keywords', 'question_template', 'specialty'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'created_by', 'updated_by',
        'keywords_display', 'usage_count'
    ]
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('title', 'description', 'category', 'priority', 'is_active')
        }),
        ('جزئیات', {
            'fields': ('keywords', 'keywords_display', 'question_template', 'specialty', 'conditions')
        }),
        ('آمار استفاده', {
            'fields': ('usage_count',),
            'classes': ('collapse',)
        }),
        ('اطلاعات سیستمی', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def category_badge(self, obj):
        """نمایش دسته‌بندی با badge"""
        colors = {
            'history': 'blue',
            'physical_exam': 'green',
            'diagnosis': 'purple',
            'treatment': 'orange',
            'education': 'teal',
            'follow_up': 'yellow',
            'red_flags': 'red',
            'other': 'gray'
        }
        color = colors.get(obj.category, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_category_display()
        )
    category_badge.short_description = 'دسته‌بندی'
    
    def priority_badge(self, obj):
        """نمایش اولویت با badge"""
        colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#fd7e14',
            'critical': '#dc3545'
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_badge.short_description = 'اولویت'
    
    def keywords_count(self, obj):
        """تعداد کلمات کلیدی"""
        return len(obj.keywords) if obj.keywords else 0
    keywords_count.short_description = 'تعداد کلیدواژه'
    
    def keywords_display(self, obj):
        """نمایش کلمات کلیدی"""
        if not obj.keywords:
            return '-'
        return ', '.join(obj.keywords)
    keywords_display.short_description = 'کلمات کلیدی'
    
    def usage_count(self, obj):
        """تعداد استفاده در ارزیابی‌ها"""
        count = obj.evaluations.count()
        return format_html(
            '<strong>{}</strong> بار در ارزیابی‌ها استفاده شده',
            count
        )
    usage_count.short_description = 'آمار استفاده'
    
    def save_model(self, request, obj, form, change):
        """ذخیره کاربر ایجادکننده/به‌روزرسانی‌کننده"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class CatalogItemInline(admin.TabularInline):
    """Inline برای آیتم‌های کاتالوگ در قالب"""
    model = ChecklistTemplate.catalog_items.through
    extra = 1
    raw_id_fields = ['checklistcatalog']


@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    """
    ادمین برای قالب‌های چک‌لیست
    """
    list_display = [
        'name', 'specialty', 'chief_complaint', 'items_count',
        'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'specialty', 'created_at']
    search_fields = ['name', 'description', 'specialty', 'chief_complaint']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'items_summary']
    filter_horizontal = ['catalog_items']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('جزئیات پزشکی', {
            'fields': ('specialty', 'chief_complaint')
        }),
        ('آیتم‌های کاتالوگ', {
            'fields': ('catalog_items', 'items_summary')
        }),
        ('اطلاعات سیستمی', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def items_count(self, obj):
        """تعداد آیتم‌های کاتالوگ"""
        return obj.catalog_items.count()
    items_count.short_description = 'تعداد آیتم'
    
    def items_summary(self, obj):
        """خلاصه آیتم‌های کاتالوگ"""
        if not obj.pk:
            return '-'
        
        items = obj.catalog_items.all()
        if not items:
            return 'هیچ آیتمی انتخاب نشده'
        
        summary = '<ul style="margin: 0; padding-right: 20px;">'
        for item in items[:10]:  # نمایش ۱۰ آیتم اول
            summary += f'<li>{item.title} ({item.get_category_display()})</li>'
        
        if items.count() > 10:
            summary += f'<li>... و {items.count() - 10} آیتم دیگر</li>'
        summary += '</ul>'
        
        return mark_safe(summary)
    items_summary.short_description = 'آیتم‌های انتخاب شده'
    
    def save_model(self, request, obj, form, change):
        """ذخیره کاربر ایجادکننده/به‌روزرسانی‌کننده"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ChecklistEval)
class ChecklistEvalAdmin(admin.ModelAdmin):
    """
    ادمین برای ارزیابی‌های چک‌لیست
    """
    list_display = [
        'encounter_link', 'catalog_item', 'status_badge',
        'confidence_score_display', 'is_acknowledged', 'created_at'
    ]
    list_filter = [
        'status', 'is_acknowledged', 'catalog_item__category',
        'catalog_item__priority', 'created_at'
    ]
    search_fields = [
        'encounter__id', 'catalog_item__title', 'evidence_text',
        'generated_question', 'doctor_response'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'created_by', 'updated_by',
        'acknowledged_at', 'evidence_display', 'anchor_positions_display'
    ]
    raw_id_fields = ['encounter', 'catalog_item']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('encounter', 'catalog_item', 'status', 'confidence_score')
        }),
        ('شواهد و نتایج', {
            'fields': (
                'evidence_text', 'evidence_display', 'anchor_positions',
                'anchor_positions_display', 'notes'
            )
        }),
        ('سوال و پاسخ', {
            'fields': ('generated_question', 'doctor_response', 'is_acknowledged', 'acknowledged_at')
        }),
        ('اطلاعات سیستمی', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def encounter_link(self, obj):
        """لینک به ویزیت"""
        url = reverse('admin:encounters_encounter_change', args=[obj.encounter.id])
        return format_html('<a href="{}">ویزیت #{}</a>', url, obj.encounter.id)
    encounter_link.short_description = 'ویزیت'
    
    def status_badge(self, obj):
        """نمایش وضعیت با badge"""
        colors = {
            'covered': '#28a745',
            'partial': '#ffc107',
            'missing': '#dc3545',
            'unclear': '#6c757d',
            'not_applicable': '#17a2b8'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'وضعیت'
    
    def confidence_score_display(self, obj):
        """نمایش امتیاز اطمینان با نوار پیشرفت"""
        percentage = int(obj.confidence_score * 100)
        color = '#28a745' if percentage >= 70 else '#ffc107' if percentage >= 40 else '#dc3545'
        return format_html(
            '<div style="width: 100px; background-color: #e9ecef; '
            'border-radius: 3px; overflow: hidden;">'
            '<div style="width: {}%; background-color: {}; height: 20px; '
            'text-align: center; color: white; font-size: 12px; line-height: 20px;">'
            '{}%</div></div>',
            percentage, color, percentage
        )
    confidence_score_display.short_description = 'اطمینان'
    
    def evidence_display(self, obj):
        """نمایش خلاصه شواهد"""
        if not obj.evidence_text:
            return '-'
        return obj.evidence_text[:200] + '...' if len(obj.evidence_text) > 200 else obj.evidence_text
    evidence_display.short_description = 'خلاصه شواهد'
    
    def anchor_positions_display(self, obj):
        """نمایش موقعیت‌های متن"""
        if not obj.anchor_positions:
            return '-'
        positions = []
        for pos in obj.anchor_positions[:3]:
            if isinstance(pos, list) and len(pos) >= 2:
                positions.append(f'[{pos[0]}:{pos[1]}]')
        return ', '.join(positions)
    anchor_positions_display.short_description = 'موقعیت‌ها'
    
    def save_model(self, request, obj, form, change):
        """ذخیره کاربر ایجادکننده/به‌روزرسانی‌کننده"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ChecklistAlert)
class ChecklistAlertAdmin(admin.ModelAdmin):
    """
    ادمین برای هشدارهای چک‌لیست
    """
    list_display = [
        'encounter_link', 'alert_type_badge', 'message_preview',
        'is_dismissed', 'dismissed_by', 'created_at'
    ]
    list_filter = [
        'alert_type', 'is_dismissed', 'created_at', 'dismissed_at'
    ]
    search_fields = ['message', 'encounter__id']
    readonly_fields = [
        'created_at', 'created_by', 'dismissed_at', 'evaluation_link'
    ]
    raw_id_fields = ['encounter', 'evaluation', 'dismissed_by']
    
    fieldsets = (
        ('اطلاعات هشدار', {
            'fields': ('encounter', 'evaluation', 'evaluation_link', 'alert_type', 'message')
        }),
        ('وضعیت', {
            'fields': ('is_dismissed', 'dismissed_at', 'dismissed_by')
        }),
        ('اطلاعات سیستمی', {
            'fields': ('created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def encounter_link(self, obj):
        """لینک به ویزیت"""
        url = reverse('admin:encounters_encounter_change', args=[obj.encounter.id])
        return format_html('<a href="{}">ویزیت #{}</a>', url, obj.encounter.id)
    encounter_link.short_description = 'ویزیت'
    
    def evaluation_link(self, obj):
        """لینک به ارزیابی"""
        if not obj.evaluation:
            return '-'
        url = reverse('admin:checklist_checklisteval_change', args=[obj.evaluation.id])
        return format_html('<a href="{}">مشاهده ارزیابی</a>', url)
    evaluation_link.short_description = 'ارزیابی مرتبط'
    
    def alert_type_badge(self, obj):
        """نمایش نوع هشدار با badge"""
        colors = {
            'missing_critical': '#dc3545',
            'low_confidence': '#ffc107',
            'red_flag': '#dc3545',
            'incomplete': '#fd7e14',
            'reminder': '#17a2b8'
        }
        color = colors.get(obj.alert_type, '#6c757d')
        icon = '⚠️' if obj.alert_type in ['missing_critical', 'red_flag'] else 'ℹ️'
        return format_html(
            '{} <span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            icon, color, obj.get_alert_type_display()
        )
    alert_type_badge.short_description = 'نوع هشدار'
    
    def message_preview(self, obj):
        """پیش‌نمایش پیام"""
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_preview.short_description = 'پیام'
    
    def save_model(self, request, obj, form, change):
        """ذخیره کاربر ایجادکننده"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['dismiss_alerts']
    
    def dismiss_alerts(self, request, queryset):
        """اکشن برای رد کردن هشدارها"""
        updated = queryset.filter(is_dismissed=False).update(
            is_dismissed=True,
            dismissed_at=timezone.now(),
            dismissed_by=request.user
        )
        self.message_user(request, f'{updated} هشدار رد شد.')
    dismiss_alerts.short_description = 'رد کردن هشدارهای انتخاب شده'