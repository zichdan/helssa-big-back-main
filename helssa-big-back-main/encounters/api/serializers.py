from rest_framework import serializers
from django.utils import timezone

from ..models import (
    Encounter, AudioChunk, Transcript, 
    SOAPReport, Prescription, EncounterFile
)
from ..utils.validators import (
    validate_phone_number, validate_visit_duration,
    validate_chief_complaint, validate_prescription_data
)


class EncounterSerializer(serializers.ModelSerializer):
    """سریالایزر ملاقات"""
    
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    actual_duration = serializers.SerializerMethodField()
    can_start = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = Encounter
        fields = [
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name',
            'type', 'status', 'chief_complaint', 'scheduled_at',
            'duration_minutes', 'started_at', 'ended_at', 'actual_duration',
            'video_room_id', 'patient_join_url', 'doctor_join_url',
            'is_recording_enabled', 'recording_consent', 'fee_amount',
            'is_paid', 'patient_notes', 'doctor_notes', 'can_start',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'video_room_id', 'patient_join_url', 'doctor_join_url',
            'started_at', 'ended_at', 'encryption_key', 'created_at', 'updated_at'
        ]
        
    def get_patient_name(self, obj):
        """نام کامل بیمار"""
        # TODO: دریافت از UnifiedUser
        return "بیمار"
        
    def get_doctor_name(self, obj):
        """نام کامل پزشک"""
        # TODO: دریافت از UnifiedUser
        return "دکتر"
        
    def get_actual_duration(self, obj):
        """مدت زمان واقعی به دقیقه"""
        if obj.actual_duration:
            return obj.actual_duration.total_seconds() / 60
        return None
        
    def validate_duration_minutes(self, value):
        """اعتبارسنجی مدت زمان"""
        if not validate_visit_duration(value):
            raise serializers.ValidationError(
                "مدت زمان ویزیت باید بین 5 تا 180 دقیقه باشد"
            )
        return value
        
    def validate_chief_complaint(self, value):
        """اعتبارسنجی شکایت اصلی"""
        is_valid, error = validate_chief_complaint(value)
        if not is_valid:
            raise serializers.ValidationError(error)
        return value


class EncounterCreateSerializer(serializers.ModelSerializer):
    """سریالایزر ایجاد ملاقات"""
    
    class Meta:
        model = Encounter
        fields = [
            'patient', 'doctor', 'type', 'chief_complaint',
            'scheduled_at', 'duration_minutes', 'patient_notes',
            'fee_amount', 'is_recording_enabled', 'recording_consent'
        ]
        
    def validate(self, data):
        """اعتبارسنجی کلی"""
        # بررسی زمان در آینده
        if data['scheduled_at'] <= timezone.now():
            raise serializers.ValidationError(
                "زمان ویزیت باید در آینده باشد"
            )
            
        return data


class AudioChunkSerializer(serializers.ModelSerializer):
    """سریالایزر قطعات صوتی"""
    
    has_transcript = serializers.SerializerMethodField()
    
    class Meta:
        model = AudioChunk
        fields = [
            'id', 'encounter', 'chunk_index', 'file_url', 'file_size',
            'duration_seconds', 'format', 'sample_rate', 'bit_rate',
            'is_processed', 'transcription_status', 'has_transcript',
            'recorded_at', 'processed_at'
        ]
        read_only_fields = ['id', 'file_url', 'recorded_at', 'processed_at']
        
    def get_has_transcript(self, obj):
        """آیا رونویسی دارد"""
        return hasattr(obj, 'transcript')


class TranscriptSerializer(serializers.ModelSerializer):
    """سریالایزر رونویسی"""
    
    word_count = serializers.ReadOnlyField()
    has_medical_entities = serializers.ReadOnlyField()
    is_high_confidence = serializers.ReadOnlyField()
    
    class Meta:
        model = Transcript
        fields = [
            'id', 'audio_chunk', 'text', 'language', 'confidence_score',
            'word_timestamps', 'speakers', 'medical_entities', 'corrections',
            'stt_model', 'processing_time', 'word_count', 'has_medical_entities',
            'is_high_confidence', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'audio_chunk', 'stt_model', 'processing_time',
            'created_at', 'updated_at'
        ]


class SOAPReportSerializer(serializers.ModelSerializer):
    """سریالایزر گزارش SOAP"""
    
    is_complete = serializers.ReadOnlyField()
    has_prescriptions = serializers.ReadOnlyField()
    needs_follow_up = serializers.ReadOnlyField()
    
    class Meta:
        model = SOAPReport
        fields = [
            'id', 'encounter', 'subjective', 'objective', 'assessment', 'plan',
            'diagnoses', 'medications', 'lab_orders', 'follow_up',
            'is_draft', 'doctor_approved', 'doctor_approved_at',
            'patient_shared', 'patient_shared_at', 'pdf_url', 'markdown_content',
            'generation_method', 'ai_confidence', 'is_complete',
            'has_prescriptions', 'needs_follow_up', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'encounter', 'doctor_approved_at', 'patient_shared_at',
            'pdf_url', 'created_at', 'updated_at'
        ]
        
    def validate(self, data):
        """اعتبارسنجی بخش‌های SOAP"""
        from ..utils.validators import validate_soap_sections
        
        # فقط برای گزارش‌های غیر پیش‌نویس
        if not data.get('is_draft', True):
            soap_data = {
                'subjective': data.get('subjective', ''),
                'objective': data.get('objective', ''),
                'assessment': data.get('assessment', ''),
                'plan': data.get('plan', '')
            }
            
            is_valid, errors = validate_soap_sections(soap_data)
            if not is_valid:
                raise serializers.ValidationError({
                    'detail': errors
                })
                
        return data


class PrescriptionSerializer(serializers.ModelSerializer):
    """سریالایزر نسخه"""
    
    medication_count = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    can_dispense = serializers.ReadOnlyField()
    
    class Meta:
        model = Prescription
        fields = [
            'id', 'encounter', 'prescription_number', 'status', 'medications',
            'is_signed', 'signed_at', 'pharmacy_id', 'dispensed_at',
            'dispensed_by', 'doctor_notes', 'pharmacy_notes', 'pdf_url',
            'qr_code', 'insurance_code', 'medication_count', 'is_expired',
            'can_dispense', 'created_at', 'updated_at', 'expires_at'
        ]
        read_only_fields = [
            'id', 'prescription_number', 'signed_at', 'dispensed_at',
            'pdf_url', 'qr_code', 'created_at', 'updated_at'
        ]
        
    def validate_medications(self, value):
        """اعتبارسنجی لیست داروها"""
        is_valid, errors = validate_prescription_data(value)
        if not is_valid:
            raise serializers.ValidationError(errors)
        return value


class EncounterFileSerializer(serializers.ModelSerializer):
    """سریالایزر فایل‌های ملاقات"""
    
    file_size_mb = serializers.ReadOnlyField()
    is_medical_document = serializers.ReadOnlyField()
    uploaded_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = EncounterFile
        fields = [
            'id', 'encounter', 'file_name', 'file_type', 'mime_type',
            'file_url', 'file_size', 'file_size_mb', 'file_hash',
            'uploaded_by', 'uploaded_by_name', 'is_encrypted',
            'description', 'is_medical_document', 'created_at'
        ]
        read_only_fields = [
            'id', 'file_url', 'file_size', 'file_hash',
            'is_encrypted', 'created_at'
        ]
        
    def get_uploaded_by_name(self, obj):
        """نام آپلودکننده"""
        # TODO: دریافت از UnifiedUser
        return "کاربر"


class EncounterStatusUpdateSerializer(serializers.Serializer):
    """سریالایزر تغییر وضعیت ملاقات"""
    
    status = serializers.ChoiceField(choices=[
        'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show'
    ])
    reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """اعتبارسنجی تغییر وضعیت"""
        from ..utils.validators import validate_encounter_status_transition
        
        if self.instance:
            current_status = self.instance.status
            new_status = data['status']
            
            if not validate_encounter_status_transition(current_status, new_status):
                raise serializers.ValidationError(
                    f"انتقال از وضعیت {current_status} به {new_status} مجاز نیست"
                )
                
        return data


class RecordingConsentSerializer(serializers.Serializer):
    """سریالایزر رضایت ضبط"""
    
    recording_consent = serializers.BooleanField()
    consent_date = serializers.DateTimeField(read_only=True)


class VisitStartSerializer(serializers.Serializer):
    """سریالایزر شروع ویزیت"""
    
    access_code = serializers.CharField(
        required=False,
        max_length=6,
        help_text="کد دسترسی برای بیمار"
    )


class FileUploadSerializer(serializers.Serializer):
    """سریالایزر آپلود فایل"""
    
    file = serializers.FileField()
    file_type = serializers.ChoiceField(choices=[
        'audio', 'image', 'document', 'video',
        'lab_result', 'radiology', 'other'
    ])
    description = serializers.CharField(required=False, allow_blank=True)