from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    Encounter, AudioChunk, Transcript,
    SOAPReport, Prescription, EncounterFile
)


@admin.register(Encounter)
class EncounterAdmin(admin.ModelAdmin):
    """ادمین ملاقات‌ها"""
    
    list_display = [
        'id', 'patient_link', 'doctor_link', 'type', 'status',
        'scheduled_at', 'duration_minutes', 'is_paid', 'created_at'
    ]
    list_filter = [
        'type', 'status', 'is_paid', 'is_recording_enabled',
        'scheduled_at', 'created_at'
    ]
    search_fields = [
        'id', 'patient__username', 'doctor__username',
        'chief_complaint', 'video_room_id'
    ]
    readonly_fields = [
        'id', 'encryption_key', 'access_code', 'video_room_id',
        'patient_join_url', 'doctor_join_url', 'recording_url',
        'created_at', 'updated_at', 'actual_duration_display'
    ]
    date_hierarchy = 'scheduled_at'
    ordering = ['-scheduled_at']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': (
                'id', 'patient', 'doctor', 'type', 'status',
                'chief_complaint', 'scheduled_at', 'duration_minutes'
            )
        }),
        ('اطلاعات ویدیو', {
            'fields': (
                'video_room_id', 'patient_join_url', 'doctor_join_url',
                'is_recording_enabled', 'recording_consent', 'recording_url'
            ),
            'classes': ('collapse',)
        }),
        ('اطلاعات مالی', {
            'fields': (
                'fee_amount', 'is_paid', 'payment_transaction'
            )
        }),
        ('یادداشت‌ها', {
            'fields': (
                'patient_notes', 'doctor_notes'
            ),
            'classes': ('collapse',)
        }),
        ('امنیت', {
            'fields': (
                'access_code', 'encryption_key'
            ),
            'classes': ('collapse',)
        }),
        ('زمان‌ها', {
            'fields': (
                'started_at', 'ended_at', 'actual_duration_display',
                'created_at', 'updated_at'
            )
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        })
    )
    
    def patient_link(self, obj):
        """لینک به پروفایل بیمار"""
        # TODO: URL برای UnifiedUser
        return format_html(
            '<a href="#">{}</a>',
            obj.patient_id
        )
    patient_link.short_description = 'بیمار'
    
    def doctor_link(self, obj):
        """لینک به پروفایل پزشک"""
        # TODO: URL برای UnifiedUser
        return format_html(
            '<a href="#">{}</a>',
            obj.doctor_id
        )
    doctor_link.short_description = 'پزشک'
    
    def actual_duration_display(self, obj):
        """نمایش مدت زمان واقعی"""
        if obj.actual_duration:
            return f"{obj.actual_duration.total_seconds() / 60:.0f} دقیقه"
        return "-"
    actual_duration_display.short_description = 'مدت واقعی'
    
    def has_delete_permission(self, request, obj=None):
        """غیرفعال کردن حذف ملاقات‌ها"""
        return False


@admin.register(AudioChunk)
class AudioChunkAdmin(admin.ModelAdmin):
    """ادمین قطعات صوتی"""
    
    list_display = [
        'id', 'encounter', 'chunk_index', 'duration_seconds',
        'format', 'is_processed', 'transcription_status', 'recorded_at'
    ]
    list_filter = [
        'format', 'is_processed', 'transcription_status',
        'is_encrypted', 'recorded_at'
    ]
    search_fields = ['encounter__id', 'file_url']
    readonly_fields = [
        'id', 'file_url', 'file_size', 'recorded_at', 'processed_at'
    ]
    ordering = ['encounter', 'chunk_index']
    
    def has_add_permission(self, request):
        """غیرفعال کردن افزودن دستی"""
        return False
        
    def has_delete_permission(self, request, obj=None):
        """غیرفعال کردن حذف"""
        return False


@admin.register(Transcript)
class TranscriptAdmin(admin.ModelAdmin):
    """ادمین رونویسی‌ها"""
    
    list_display = [
        'id', 'audio_chunk', 'language', 'confidence_score',
        'word_count', 'stt_model', 'created_at'
    ]
    list_filter = [
        'language', 'stt_model', 'created_at'
    ]
    search_fields = ['text', 'audio_chunk__encounter__id']
    readonly_fields = [
        'id', 'audio_chunk', 'word_count', 'has_medical_entities',
        'is_high_confidence', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': (
                'id', 'audio_chunk', 'text', 'language'
            )
        }),
        ('کیفیت و دقت', {
            'fields': (
                'confidence_score', 'word_count', 'is_high_confidence'
            )
        }),
        ('داده‌های تخصصی', {
            'fields': (
                'word_timestamps', 'speakers', 'medical_entities',
                'corrections'
            ),
            'classes': ('collapse',)
        }),
        ('اطلاعات پردازش', {
            'fields': (
                'stt_model', 'processing_time', 'created_at', 'updated_at'
            )
        })
    )


@admin.register(SOAPReport)
class SOAPReportAdmin(admin.ModelAdmin):
    """ادمین گزارش‌های SOAP"""
    
    list_display = [
        'id', 'encounter', 'is_draft', 'doctor_approved',
        'patient_shared', 'generation_method', 'created_at'
    ]
    list_filter = [
        'is_draft', 'doctor_approved', 'patient_shared',
        'generation_method', 'created_at'
    ]
    search_fields = [
        'encounter__id', 'subjective', 'objective',
        'assessment', 'plan'
    ]
    readonly_fields = [
        'id', 'encounter', 'doctor_approved_at', 'patient_shared_at',
        'is_complete', 'has_prescriptions', 'needs_follow_up',
        'created_at', 'updated_at'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('اطلاعات ملاقات', {
            'fields': ('id', 'encounter')
        }),
        ('بخش‌های SOAP', {
            'fields': (
                'subjective', 'objective', 'assessment', 'plan'
            )
        }),
        ('داده‌های ساختاریافته', {
            'fields': (
                'diagnoses', 'medications', 'lab_orders', 'follow_up'
            ),
            'classes': ('collapse',)
        }),
        ('وضعیت و تاییدیه', {
            'fields': (
                'is_draft', 'doctor_approved', 'doctor_approved_at',
                'patient_shared', 'patient_shared_at'
            )
        }),
        ('امضا و خروجی', {
            'fields': (
                'doctor_signature', 'signature_timestamp',
                'pdf_url', 'markdown_content'
            ),
            'classes': ('collapse',)
        }),
        ('اطلاعات تولید', {
            'fields': (
                'generation_method', 'ai_confidence',
                'created_at', 'updated_at'
            )
        })
    )


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    """ادمین نسخه‌ها"""
    
    list_display = [
        'prescription_number', 'encounter', 'status', 'medication_count',
        'is_signed', 'is_expired', 'created_at', 'expires_at'
    ]
    list_filter = [
        'status', 'is_signed', 'is_electronic', 'created_at', 'expires_at'
    ]
    search_fields = [
        'prescription_number', 'encounter__id', 'pharmacy_id'
    ]
    readonly_fields = [
        'id', 'prescription_number', 'medication_count',
        'is_expired', 'can_dispense', 'signed_at', 'dispensed_at',
        'created_at', 'updated_at'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': (
                'id', 'encounter', 'prescription_number', 'status'
            )
        }),
        ('داروها', {
            'fields': ('medications', 'medication_count')
        }),
        ('امضا و صدور', {
            'fields': (
                'is_signed', 'signed_at', 'digital_signature'
            )
        }),
        ('اطلاعات داروخانه', {
            'fields': (
                'pharmacy_id', 'dispensed_at', 'dispensed_by'
            ),
            'classes': ('collapse',)
        }),
        ('یادداشت‌ها', {
            'fields': ('doctor_notes', 'pharmacy_notes'),
            'classes': ('collapse',)
        }),
        ('خروجی و کدها', {
            'fields': ('pdf_url', 'qr_code', 'insurance_code'),
            'classes': ('collapse',)
        }),
        ('زمان‌ها', {
            'fields': (
                'created_at', 'updated_at', 'expires_at',
                'is_expired', 'can_dispense'
            )
        })
    )
    
    def has_delete_permission(self, request, obj=None):
        """غیرفعال کردن حذف نسخه‌ها"""
        return False


@admin.register(EncounterFile)
class EncounterFileAdmin(admin.ModelAdmin):
    """ادمین فایل‌های ملاقات"""
    
    list_display = [
        'file_name', 'encounter', 'file_type', 'mime_type',
        'file_size_mb', 'uploaded_by', 'created_at'
    ]
    list_filter = ['file_type', 'mime_type', 'is_encrypted', 'created_at']
    search_fields = ['file_name', 'encounter__id', 'description']
    readonly_fields = [
        'id', 'file_url', 'file_size', 'file_size_mb',
        'file_hash', 'is_medical_document', 'created_at'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('اطلاعات فایل', {
            'fields': (
                'id', 'encounter', 'file_name', 'file_type',
                'mime_type', 'file_size', 'file_size_mb'
            )
        }),
        ('محتوا و امنیت', {
            'fields': (
                'file_url', 'file_hash', 'is_encrypted',
                'uploaded_by', 'description'
            )
        }),
        ('Metadata', {
            'fields': ('metadata', 'created_at'),
            'classes': ('collapse',)
        })
    )