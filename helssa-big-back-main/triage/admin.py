"""
تنظیمات پنل مدیریت برای اپلیکیشن تریاژ
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    SymptomCategory,
    Symptom,
    DifferentialDiagnosis,
    DiagnosisSymptom,
    TriageSession,
    SessionSymptom,
    SessionDiagnosis,
    TriageRule
)


@admin.register(SymptomCategory)
class SymptomCategoryAdmin(admin.ModelAdmin):
    """
    مدیریت دسته‌بندی علائم در پنل ادمین
    """
    list_display = ['name', 'name_en', 'priority_level', 'is_active', 'created_at']
    list_filter = ['priority_level', 'is_active', 'created_at']
    search_fields = ['name', 'name_en', 'description']
    list_editable = ['priority_level', 'is_active']
    ordering = ['priority_level', 'name']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'name_en', 'description')
        }),
        ('تنظیمات', {
            'fields': ('priority_level', 'is_active')
        }),
    )


class DiagnosisSymptomInline(admin.TabularInline):
    """
    Inline برای مدیریت علائم در تشخیص
    """
    model = DiagnosisSymptom
    extra = 1
    fields = ['symptom', 'weight', 'is_mandatory']
    autocomplete_fields = ['symptom']


@admin.register(Symptom)
class SymptomAdmin(admin.ModelAdmin):
    """
    مدیریت علائم در پنل ادمین
    """
    list_display = ['name', 'name_en', 'category', 'urgency_score', 'is_active']
    list_filter = ['category', 'urgency_score', 'is_active', 'created_at']
    search_fields = ['name', 'name_en', 'description']
    list_editable = ['urgency_score', 'is_active']
    autocomplete_fields = ['category', 'related_symptoms']
    ordering = ['-urgency_score', 'name']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'name_en', 'category', 'description')
        }),
        ('تنظیمات کلینیکی', {
            'fields': ('severity_levels', 'common_locations', 'urgency_score')
        }),
        ('روابط', {
            'fields': ('related_symptoms',)
        }),
        ('وضعیت', {
            'fields': ('is_active',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')


@admin.register(DifferentialDiagnosis)
class DifferentialDiagnosisAdmin(admin.ModelAdmin):
    """
    مدیریت تشخیص‌های افتراقی در پنل ادمین
    """
    list_display = ['name', 'name_en', 'icd_10_code', 'urgency_level', 'is_active']
    list_filter = ['urgency_level', 'is_active', 'created_at']
    search_fields = ['name', 'name_en', 'icd_10_code', 'description']
    list_editable = ['urgency_level', 'is_active']
    ordering = ['-urgency_level', 'name']
    inlines = [DiagnosisSymptomInline]
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'name_en', 'icd_10_code', 'description')
        }),
        ('تنظیمات کلینیکی', {
            'fields': ('urgency_level', 'recommended_actions', 'red_flags')
        }),
        ('وضعیت', {
            'fields': ('is_active',)
        }),
    )


class SessionSymptomInline(admin.TabularInline):
    """
    Inline برای علائم جلسه
    """
    model = SessionSymptom
    extra = 0
    fields = ['symptom', 'severity', 'duration_hours', 'location']
    autocomplete_fields = ['symptom']
    readonly_fields = ['reported_at']


class SessionDiagnosisInline(admin.TabularInline):
    """
    Inline برای تشخیص‌های جلسه
    """
    model = SessionDiagnosis
    extra = 0
    fields = ['diagnosis', 'probability_score', 'confidence_level', 'reasoning']
    autocomplete_fields = ['diagnosis']
    readonly_fields = ['suggested_at']


@admin.register(TriageSession)
class TriageSessionAdmin(admin.ModelAdmin):
    """
    مدیریت جلسات تریاژ در پنل ادمین
    """
    list_display = [
        'patient', 'chief_complaint_short', 'status', 'urgency_level',
        'requires_immediate_attention', 'started_at', 'duration_display'
    ]
    list_filter = [
        'status', 'urgency_level', 'requires_immediate_attention',
        'started_at', 'completed_at'
    ]
    search_fields = ['patient__username', 'patient__email', 'chief_complaint', 'triage_notes']
    readonly_fields = [
        'started_at', 'duration_display', 'ai_confidence_score',
        'red_flags_detected', 'metadata'
    ]
    autocomplete_fields = ['patient', 'completed_by']
    ordering = ['-started_at']
    inlines = [SessionSymptomInline, SessionDiagnosisInline]
    
    fieldsets = (
        ('اطلاعات بیمار', {
            'fields': ('patient', 'chief_complaint')
        }),
        ('وضعیت جلسه', {
            'fields': ('status', 'urgency_level', 'requires_immediate_attention')
        }),
        ('علائم گزارش شده', {
            'fields': ('reported_symptoms',)
        }),
        ('نتایج تحلیل', {
            'fields': (
                'recommended_actions', 'red_flags_detected',
                'ai_confidence_score', 'estimated_wait_time'
            )
        }),
        ('یادداشت‌ها', {
            'fields': ('triage_notes',)
        }),
        ('زمان‌بندی', {
            'fields': ('started_at', 'completed_at', 'completed_by', 'duration_display')
        }),
        ('متادیتا', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    def chief_complaint_short(self, obj):
        """نمایش خلاصه شکایت اصلی"""
        return obj.chief_complaint[:50] + '...' if len(obj.chief_complaint) > 50 else obj.chief_complaint
    chief_complaint_short.short_description = 'شکایت اصلی'
    
    def duration_display(self, obj):
        """نمایش مدت زمان جلسه"""
        duration = obj.duration
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        return f"{hours}:{minutes:02d}"
    duration_display.short_description = 'مدت زمان'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('patient', 'completed_by')


@admin.register(TriageRule)
class TriageRuleAdmin(admin.ModelAdmin):
    """
    مدیریت قوانین تریاژ در پنل ادمین
    """
    list_display = ['name', 'priority', 'is_active', 'created_by', 'created_at']
    list_filter = ['priority', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['priority', 'is_active']
    autocomplete_fields = ['created_by']
    ordering = ['-priority', 'name']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'description', 'priority')
        }),
        ('قوانین', {
            'fields': ('conditions', 'actions')
        }),
        ('وضعیت', {
            'fields': ('is_active',)
        }),
        ('ایجادکننده', {
            'fields': ('created_by',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # فقط برای ایجاد جدید
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# تنظیمات عمومی پنل ادمین
admin.site.site_header = 'مدیریت سیستم تریاژ هلسا'
admin.site.site_title = 'تریاژ هلسا'
admin.site.index_title = 'پنل مدیریت تریاژ پزشکی'