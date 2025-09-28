"""
Django Admin برای feedback app
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import SessionRating, MessageFeedback, Survey, SurveyResponse, FeedbackSettings


@admin.register(SessionRating)
class SessionRatingAdmin(admin.ModelAdmin):
    """مدیریت امتیازدهی جلسات در پنل ادمین"""
    
    list_display = [
        'session_id', 'user', 'overall_rating', 'response_quality',
        'response_speed', 'helpfulness', 'would_recommend', 'created_at'
    ]
    list_filter = [
        'overall_rating', 'would_recommend', 'created_at',
        'response_quality', 'response_speed', 'helpfulness'
    ]
    search_fields = ['session_id', 'user__phone_number', 'comment', 'suggestions']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('session_id', 'user', 'overall_rating')
        }),
        ('امتیازات تفکیکی', {
            'fields': ('response_quality', 'response_speed', 'helpfulness'),
            'classes': ('collapse',)
        }),
        ('نظرات', {
            'fields': ('comment', 'suggestions', 'would_recommend'),
            'classes': ('collapse',)
        }),
        ('اطلاعات سیستم', {
            'fields': ('id', 'created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(MessageFeedback)
class MessageFeedbackAdmin(admin.ModelAdmin):
    """مدیریت بازخورد پیام‌ها در پنل ادمین"""
    
    list_display = [
        'message_id', 'user', 'feedback_type', 'is_helpful', 
        'has_detailed_feedback', 'created_at'
    ]
    list_filter = [
        'feedback_type', 'is_helpful', 'created_at'
    ]
    search_fields = [
        'message_id', 'user__phone_number', 'detailed_feedback', 'expected_response'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('message_id', 'user', 'feedback_type', 'is_helpful')
        }),
        ('بازخورد تفصیلی', {
            'fields': ('detailed_feedback', 'expected_response'),
            'classes': ('collapse',)
        }),
        ('اطلاعات سیستم', {
            'fields': ('id', 'created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    def has_detailed_feedback(self, obj):
        """نمایش وجود بازخورد تفصیلی"""
        return bool(obj.detailed_feedback)
    has_detailed_feedback.boolean = True
    has_detailed_feedback.short_description = 'بازخورد تفصیلی'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    """مدیریت نظرسنجی‌ها در پنل ادمین"""
    
    list_display = [
        'title', 'survey_type', 'target_users', 'is_active',
        'questions_count', 'responses_count', 'created_at'
    ]
    list_filter = [
        'survey_type', 'target_users', 'is_active', 'allow_anonymous', 'created_at'
    ]
    search_fields = ['title', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'responses_count']
    
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('title', 'description', 'survey_type', 'target_users')
        }),
        ('تنظیمات', {
            'fields': ('is_active', 'allow_anonymous', 'max_responses'),
        }),
        ('زمان‌بندی', {
            'fields': ('start_date', 'end_date'),
            'classes': ('collapse',)
        }),
        ('سوالات', {
            'fields': ('questions',),
        }),
        ('اطلاعات سیستم', {
            'fields': ('id', 'responses_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def questions_count(self, obj):
        """تعداد سوالات"""
        return len(obj.questions) if obj.questions else 0
    questions_count.short_description = 'تعداد سوالات'
    
    def responses_count(self, obj):
        """تعداد پاسخ‌ها"""
        return obj.responses.count()
    responses_count.short_description = 'تعداد پاسخ‌ها'


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    """مدیریت پاسخ‌های نظرسنجی در پنل ادمین"""
    
    list_display = [
        'survey', 'user_display', 'overall_score', 'completion_time_display', 'created_at'
    ]
    list_filter = [
        'survey', 'overall_score', 'created_at'
    ]
    search_fields = ['survey__title', 'user__phone_number']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('survey', 'user', 'overall_score')
        }),
        ('پاسخ‌ها', {
            'fields': ('answers',),
        }),
        ('اطلاعات اضافی', {
            'fields': ('completion_time', 'metadata'),
            'classes': ('collapse',)
        }),
        ('اطلاعات سیستم', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_display(self, obj):
        """نمایش کاربر"""
        if obj.user:
            return obj.user.get_full_name() or obj.user.phone_number
        return 'ناشناس'
    user_display.short_description = 'کاربر'
    
    def completion_time_display(self, obj):
        """نمایش زمان تکمیل"""
        if obj.completion_time:
            total_seconds = int(obj.completion_time.total_seconds())
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}:{seconds:02d}"
        return '-'
    completion_time_display.short_description = 'زمان تکمیل'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('survey', 'user')


@admin.register(FeedbackSettings)
class FeedbackSettingsAdmin(admin.ModelAdmin):
    """مدیریت تنظیمات feedback در پنل ادمین"""
    
    list_display = [
        'key', 'setting_type', 'value_preview', 'is_active', 'updated_at'
    ]
    list_filter = ['setting_type', 'is_active']
    search_fields = ['key', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('key', 'setting_type', 'description')
        }),
        ('مقدار', {
            'fields': ('value',),
        }),
        ('اطلاعات سیستم', {
            'fields': ('id', 'is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def value_preview(self, obj):
        """پیش‌نمایش مقدار"""
        if not obj.value:
            return '-'
        
        value_str = str(obj.value)
        if len(value_str) > 50:
            return value_str[:47] + '...'
        return value_str
    value_preview.short_description = 'پیش‌نمایش مقدار'


# تنظیمات کلی Admin
admin.site.site_header = 'مدیریت سیستم بازخورد هلسا'
admin.site.site_title = 'پنل مدیریت'
admin.site.index_title = 'خوش آمدید به پنل مدیریت سیستم بازخورد'
