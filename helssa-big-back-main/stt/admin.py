"""
تنظیمات پنل ادمین برای اپ STT
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from .models import STTTask, STTQualityControl, STTUsageStats


@admin.register(STTTask)
class STTTaskAdmin(admin.ModelAdmin):
    """ادمین برای وظایف تبدیل گفتار به متن"""
    
    list_display = [
        'task_id_display', 'user_display', 'user_type', 'status_display',
        'language', 'model_used', 'confidence_score_display',
        'duration_display', 'created_at_display'
    ]
    
    list_filter = [
        'status', 'user_type', 'language', 'model_used',
        'created_at', 'quality_control__needs_human_review'
    ]
    
    search_fields = [
        'task_id', 'user__username', 'user__first_name',
        'user__last_name', 'transcription', 'error_message'
    ]
    
    readonly_fields = [
        'task_id', 'file_size_display', 'duration', 'confidence_score',
        'processing_time_display', 'started_at', 'completed_at',
        'created_at', 'updated_at', 'audio_file_link'
    ]
    
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('task_id', 'user', 'user_type', 'status')
        }),
        ('فایل صوتی', {
            'fields': ('audio_file', 'audio_file_link', 'file_size_display', 'duration')
        }),
        ('تنظیمات تبدیل', {
            'fields': ('language', 'model_used')
        }),
        ('نتیجه', {
            'fields': ('transcription', 'confidence_score', 'error_message')
        }),
        ('زمان‌بندی', {
            'fields': ('started_at', 'completed_at', 'processing_time_display',
                      'created_at', 'updated_at')
        }),
        ('اطلاعات اضافی', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_for_review', 'export_transcriptions']
    
    def task_id_display(self, obj):
        """نمایش شناسه وظیفه با لینک"""
        url = reverse('admin:stt_stttask_change', args=[obj.pk])
        return format_html('<a href="{}">{}</a>', url, str(obj.task_id)[:8])
    task_id_display.short_description = 'شناسه'
    
    def user_display(self, obj):
        """نمایش نام کاربر"""
        if hasattr(obj.user, 'get_full_name'):
            name = obj.user.get_full_name()
            if name:
                return name
        return obj.user.username
    user_display.short_description = 'کاربر'
    user_display.admin_order_field = 'user__username'
    
    def status_display(self, obj):
        """نمایش وضعیت با رنگ"""
        colors = {
            'pending': '#FFA500',
            'processing': '#1E90FF',
            'completed': '#32CD32',
            'failed': '#DC143C',
            'cancelled': '#808080',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#000000'),
            obj.get_status_display()
        )
    status_display.short_description = 'وضعیت'
    
    def confidence_score_display(self, obj):
        """نمایش امتیاز اطمینان"""
        if obj.confidence_score is None:
            return '-'
        
        score = obj.confidence_score * 100
        color = '#32CD32' if score >= 80 else '#FFA500' if score >= 50 else '#DC143C'
        
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, score
        )
    confidence_score_display.short_description = 'اطمینان'
    confidence_score_display.admin_order_field = 'confidence_score'
    
    def duration_display(self, obj):
        """نمایش مدت زمان صوت"""
        if obj.duration:
            minutes = int(obj.duration // 60)
            seconds = int(obj.duration % 60)
            return f"{minutes}:{seconds:02d}"
        return '-'
    duration_display.short_description = 'مدت'
    duration_display.admin_order_field = 'duration'
    
    def file_size_display(self, obj):
        """نمایش حجم فایل"""
        if obj.file_size:
            mb = obj.file_size / (1024 * 1024)
            return f"{mb:.2f} MB"
        return '-'
    file_size_display.short_description = 'حجم فایل'
    
    def processing_time_display(self, obj):
        """نمایش زمان پردازش"""
        if obj.processing_time:
            return f"{obj.processing_time:.1f} ثانیه"
        return '-'
    processing_time_display.short_description = 'زمان پردازش'
    
    def created_at_display(self, obj):
        """نمایش تاریخ ایجاد"""
        return timezone.localtime(obj.created_at).strftime('%Y/%m/%d %H:%M')
    created_at_display.short_description = 'تاریخ ایجاد'
    created_at_display.admin_order_field = 'created_at'
    
    def audio_file_link(self, obj):
        """لینک دانلود فایل صوتی"""
        if obj.audio_file:
            return format_html(
                '<a href="{}" target="_blank">دانلود فایل صوتی</a>',
                obj.audio_file.url
            )
        return '-'
    audio_file_link.short_description = 'لینک فایل'
    
    def mark_for_review(self, request, queryset):
        """علامت‌گذاری برای بررسی انسانی"""
        count = 0
        for task in queryset:
            if hasattr(task, 'quality_control'):
                task.quality_control.needs_human_review = True
                task.quality_control.review_reason = 'علامت‌گذاری توسط ادمین'
                task.quality_control.save()
                count += 1
        
        self.message_user(
            request,
            f'{count} وظیفه برای بررسی علامت‌گذاری شد.'
        )
    mark_for_review.short_description = 'علامت‌گذاری برای بررسی'
    
    def export_transcriptions(self, request, queryset):
        """خروجی گرفتن از متن‌های تبدیل شده"""
        # TODO: پیاده‌سازی export به CSV/Excel
        self.message_user(request, 'این قابلیت در حال توسعه است.')
    export_transcriptions.short_description = 'خروجی متن‌ها'
    
    def get_queryset(self, request):
        """بهینه‌سازی query"""
        qs = super().get_queryset(request)
        return qs.select_related('user').prefetch_related('quality_control')


@admin.register(STTQualityControl)
class STTQualityControlAdmin(admin.ModelAdmin):
    """ادمین برای کنترل کیفیت"""
    
    list_display = [
        'task_display', 'audio_quality_score_display',
        'background_noise_level_display', 'speech_clarity_display',
        'needs_review_display', 'reviewed_by_display', 'created_at'
    ]
    
    list_filter = [
        'needs_human_review', 'background_noise_level',
        'speech_clarity', 'reviewed_at'
    ]
    
    search_fields = [
        'task__task_id', 'task__user__username',
        'review_reason', 'corrected_transcription'
    ]
    
    readonly_fields = [
        'task_link', 'audio_quality_score', 'medical_terms_detected',
        'suggested_corrections', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('وظیفه مرتبط', {
            'fields': ('task', 'task_link')
        }),
        ('کیفیت صوت', {
            'fields': ('audio_quality_score', 'background_noise_level', 'speech_clarity')
        }),
        ('تحلیل متن', {
            'fields': ('medical_terms_detected', 'suggested_corrections', 'corrected_transcription')
        }),
        ('بررسی انسانی', {
            'fields': ('needs_human_review', 'review_reason', 'reviewed_by', 'reviewed_at')
        }),
        ('زمان‌ها', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['mark_as_reviewed', 'mark_needs_review']
    
    def task_display(self, obj):
        """نمایش اطلاعات وظیفه"""
        return format_html(
            '{} - {}',
            str(obj.task.task_id)[:8],
            obj.task.user.username
        )
    task_display.short_description = 'وظیفه'
    
    def task_link(self, obj):
        """لینک به وظیفه"""
        url = reverse('admin:stt_stttask_change', args=[obj.task.pk])
        return format_html(
            '<a href="{}" target="_blank">مشاهده وظیفه</a>',
            url
        )
    task_link.short_description = 'لینک وظیفه'
    
    def audio_quality_score_display(self, obj):
        """نمایش امتیاز کیفیت صوت"""
        score = obj.audio_quality_score * 100
        color = '#32CD32' if score >= 70 else '#FFA500' if score >= 40 else '#DC143C'
        
        return format_html(
            '<span style="color: {};">{:.0f}%</span>',
            color, score
        )
    audio_quality_score_display.short_description = 'کیفیت صوت'
    audio_quality_score_display.admin_order_field = 'audio_quality_score'
    
    def background_noise_level_display(self, obj):
        """نمایش سطح نویز"""
        colors = {
            'low': '#32CD32',
            'medium': '#FFA500',
            'high': '#DC143C',
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.background_noise_level, '#000000'),
            obj.get_background_noise_level_display()
        )
    background_noise_level_display.short_description = 'نویز'
    
    def speech_clarity_display(self, obj):
        """نمایش وضوح گفتار"""
        colors = {
            'clear': '#32CD32',
            'moderate': '#FFA500',
            'unclear': '#DC143C',
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.speech_clarity, '#000000'),
            obj.get_speech_clarity_display()
        )
    speech_clarity_display.short_description = 'وضوح'
    
    def needs_review_display(self, obj):
        """نمایش نیاز به بررسی"""
        if obj.needs_human_review:
            return format_html(
                '<span style="color: #DC143C; font-weight: bold;">✓</span>'
            )
        return format_html(
            '<span style="color: #32CD32;">✗</span>'
        )
    needs_review_display.short_description = 'نیاز به بررسی'
    needs_review_display.admin_order_field = 'needs_human_review'
    
    def reviewed_by_display(self, obj):
        """نمایش بررسی کننده"""
        if obj.reviewed_by:
            return obj.reviewed_by.get_full_name() or obj.reviewed_by.username
        return '-'
    reviewed_by_display.short_description = 'بررسی کننده'
    
    def mark_as_reviewed(self, request, queryset):
        """علامت‌گذاری به عنوان بررسی شده"""
        count = queryset.filter(
            needs_human_review=True
        ).update(
            needs_human_review=False,
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        
        self.message_user(request, f'{count} مورد بررسی شد.')
    mark_as_reviewed.short_description = 'علامت‌گذاری بررسی شده'
    
    def mark_needs_review(self, request, queryset):
        """علامت‌گذاری نیاز به بررسی"""
        count = queryset.update(
            needs_human_review=True,
            review_reason='نیاز به بررسی مجدد'
        )
        
        self.message_user(request, f'{count} مورد نیاز به بررسی دارد.')
    mark_needs_review.short_description = 'علامت‌گذاری نیاز به بررسی'
    
    def get_queryset(self, request):
        """بهینه‌سازی query"""
        qs = super().get_queryset(request)
        return qs.select_related('task', 'task__user', 'reviewed_by')


@admin.register(STTUsageStats)
class STTUsageStatsAdmin(admin.ModelAdmin):
    """ادمین برای آمار استفاده"""
    
    list_display = [
        'user_display', 'date', 'total_requests',
        'success_rate_display', 'total_duration_display',
        'avg_confidence_display'
    ]
    
    list_filter = ['date', 'user__user_type']
    
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    
    date_hierarchy = 'date'
    
    readonly_fields = [
        'user', 'date', 'total_requests', 'successful_requests',
        'failed_requests', 'success_rate_display', 'total_audio_duration',
        'total_processing_time', 'average_confidence_score'
    ]
    
    fieldsets = (
        ('کاربر و تاریخ', {
            'fields': ('user', 'date')
        }),
        ('آمار درخواست‌ها', {
            'fields': ('total_requests', 'successful_requests', 'failed_requests',
                      'success_rate_display')
        }),
        ('آمار زمان', {
            'fields': ('total_audio_duration', 'total_processing_time')
        }),
        ('کیفیت', {
            'fields': ('average_confidence_score',)
        }),
    )
    
    def user_display(self, obj):
        """نمایش نام کاربر"""
        if hasattr(obj.user, 'get_full_name'):
            name = obj.user.get_full_name()
            if name:
                return name
        return obj.user.username
    user_display.short_description = 'کاربر'
    user_display.admin_order_field = 'user__username'
    
    def success_rate_display(self, obj):
        """نمایش نرخ موفقیت"""
        if obj.total_requests > 0:
            rate = (obj.successful_requests / obj.total_requests) * 100
            color = '#32CD32' if rate >= 90 else '#FFA500' if rate >= 70 else '#DC143C'
            return format_html(
                '<span style="color: {};">{:.1f}%</span>',
                color, rate
            )
        return '-'
    success_rate_display.short_description = 'نرخ موفقیت'
    
    def total_duration_display(self, obj):
        """نمایش مجموع مدت صوت"""
        if obj.total_audio_duration:
            hours = int(obj.total_audio_duration // 3600)
            minutes = int((obj.total_audio_duration % 3600) // 60)
            seconds = int(obj.total_audio_duration % 60)
            
            if hours > 0:
                return f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes}:{seconds:02d}"
        return '-'
    total_duration_display.short_description = 'مجموع صوت'
    total_duration_display.admin_order_field = 'total_audio_duration'
    
    def avg_confidence_display(self, obj):
        """نمایش میانگین اطمینان"""
        if obj.average_confidence_score:
            score = obj.average_confidence_score * 100
            color = '#32CD32' if score >= 80 else '#FFA500' if score >= 50 else '#DC143C'
            return format_html(
                '<span style="color: {};">{:.1f}%</span>',
                color, score
            )
        return '-'
    avg_confidence_display.short_description = 'میانگین اطمینان'
    avg_confidence_display.admin_order_field = 'average_confidence_score'
    
    def get_queryset(self, request):
        """بهینه‌سازی query"""
        qs = super().get_queryset(request)
        return qs.select_related('user')
    
    def has_add_permission(self, request):
        """غیرفعال کردن افزودن دستی"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """فقط superuser می‌تواند حذف کند"""
        return request.user.is_superuser