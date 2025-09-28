"""
سریالایزرهای مربوط به تبدیل گفتار به متن
"""
from rest_framework import serializers
from django.core.validators import FileExtensionValidator
from django.contrib.auth import get_user_model
from .models import STTTask, STTQualityControl, STTUsageStats
import magic
import os

User = get_user_model()


class AudioFileSerializer(serializers.Serializer):
    """
    سریالایزر برای آپلود فایل صوتی
    """
    
    audio_file = serializers.FileField(
        validators=[
            FileExtensionValidator(
                allowed_extensions=['mp3', 'wav', 'ogg', 'm4a', 'webm', 'mp4', 'mpeg', 'mpga']
            )
        ],
        help_text='فایل صوتی (حداکثر 50MB)'
    )
    
    language = serializers.ChoiceField(
        choices=[
            ('fa', 'فارسی'),
            ('en', 'انگلیسی'),
            ('auto', 'تشخیص خودکار'),
        ],
        default='fa',
        help_text='زبان گفتار'
    )
    
    model = serializers.ChoiceField(
        choices=[
            ('tiny', 'Tiny - سریع‌ترین'),
            ('base', 'Base - متعادل'),
            ('small', 'Small - دقیق'),
            ('medium', 'Medium - دقیق‌تر'),
            ('large', 'Large - دقیق‌ترین'),
        ],
        default='base',
        required=False,
        help_text='مدل Whisper مورد استفاده'
    )
    
    context_type = serializers.ChoiceField(
        choices=[
            ('general', 'عمومی'),
            ('medical', 'پزشکی'),
            ('prescription', 'نسخه'),
            ('symptoms', 'علائم'),
        ],
        default='general',
        required=False,
        help_text='نوع محتوای گفتار برای بهبود دقت'
    )
    
    def validate_audio_file(self, value):
        """اعتبارسنجی فایل صوتی"""
        # بررسی حجم فایل (حداکثر 50MB)
        if value.size > 52428800:
            raise serializers.ValidationError(
                'حجم فایل نباید بیشتر از 50 مگابایت باشد.'
            )
        
        # بررسی نوع MIME فایل
        try:
            file_mime = magic.from_buffer(value.read(1024), mime=True)
            value.seek(0)  # برگشت به ابتدای فایل
            
            allowed_mimes = [
                'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav',
                'audio/ogg', 'audio/webm', 'audio/mp4', 'audio/m4a',
                'video/webm', 'video/mp4'  # برای فایل‌های ویدیویی که فقط صدا دارند
            ]
            
            if file_mime not in allowed_mimes:
                raise serializers.ValidationError(
                    f'نوع فایل {file_mime} پشتیبانی نمی‌شود.'
                )
        except Exception:
            # اگر magic در دسترس نبود، فقط بر اساس پسوند بررسی شود
            pass
        
        return value


class STTTaskSerializer(serializers.ModelSerializer):
    """سریالایزر برای مدل STTTask"""
    
    user_full_name = serializers.SerializerMethodField()
    processing_time = serializers.ReadOnlyField()
    audio_file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = STTTask
        fields = [
            'id', 'task_id', 'user', 'user_full_name', 'user_type',
            'audio_file', 'audio_file_url', 'file_size', 'duration',
            'transcription', 'language', 'status', 'confidence_score',
            'model_used', 'error_message', 'started_at', 'completed_at',
            'processing_time', 'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'task_id', 'user', 'file_size', 'duration',
            'transcription', 'status', 'confidence_score',
            'error_message', 'started_at', 'completed_at',
            'created_at', 'updated_at'
        ]
    
    def get_user_full_name(self, obj):
        """نام کامل کاربر"""
        return obj.user.get_full_name() if hasattr(obj.user, 'get_full_name') else str(obj.user)
    
    def get_audio_file_url(self, obj):
        """لینک دانلود فایل صوتی"""
        if obj.audio_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.audio_file.url)
            return obj.audio_file.url
        return None


class STTTaskCreateSerializer(serializers.ModelSerializer):
    """سریالایزر برای ایجاد وظیفه STT"""
    
    audio_file = serializers.FileField(
        validators=[
            FileExtensionValidator(
                allowed_extensions=['mp3', 'wav', 'ogg', 'm4a', 'webm', 'mp4', 'mpeg', 'mpga']
            )
        ]
    )
    
    class Meta:
        model = STTTask
        fields = ['audio_file', 'language', 'model_used', 'metadata']
        
    def validate_audio_file(self, value):
        """اعتبارسنجی فایل صوتی"""
        # بررسی حجم فایل (حداکثر 50MB)
        if value.size > 52428800:
            raise serializers.ValidationError(
                'حجم فایل نباید بیشتر از 50 مگابایت باشد.'
            )
        return value
    
    def create(self, validated_data):
        """ایجاد وظیفه جدید"""
        # افزودن اطلاعات کاربر
        validated_data['user'] = self.context['request'].user
        validated_data['user_type'] = self.context['request'].user.user_type
        validated_data['file_size'] = validated_data['audio_file'].size
        
        return super().create(validated_data)


class STTQualityControlSerializer(serializers.ModelSerializer):
    """سریالایزر برای کنترل کیفیت"""
    
    task_details = STTTaskSerializer(source='task', read_only=True)
    reviewed_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = STTQualityControl
        fields = [
            'id', 'task', 'task_details', 'audio_quality_score',
            'background_noise_level', 'speech_clarity',
            'medical_terms_detected', 'suggested_corrections',
            'corrected_transcription', 'needs_human_review',
            'review_reason', 'reviewed_by', 'reviewed_by_name',
            'reviewed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at'
        ]
    
    def get_reviewed_by_name(self, obj):
        """نام بررسی کننده"""
        if obj.reviewed_by:
            return obj.reviewed_by.get_full_name() if hasattr(obj.reviewed_by, 'get_full_name') else str(obj.reviewed_by)
        return None


class STTUsageStatsSerializer(serializers.ModelSerializer):
    """سریالایزر برای آمار استفاده"""
    
    user_full_name = serializers.SerializerMethodField()
    success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = STTUsageStats
        fields = [
            'id', 'user', 'user_full_name', 'date',
            'total_requests', 'successful_requests', 'failed_requests',
            'success_rate', 'total_audio_duration', 'total_processing_time',
            'average_confidence_score', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_user_full_name(self, obj):
        """نام کامل کاربر"""
        return obj.user.get_full_name() if hasattr(obj.user, 'get_full_name') else str(obj.user)
    
    def get_success_rate(self, obj):
        """نرخ موفقیت"""
        if obj.total_requests > 0:
            return round((obj.successful_requests / obj.total_requests) * 100, 2)
        return 0.0


class TranscriptionResultSerializer(serializers.Serializer):
    """سریالایزر برای نتیجه تبدیل"""
    
    task_id = serializers.UUIDField(read_only=True)
    transcription = serializers.CharField(read_only=True)
    language = serializers.CharField(read_only=True)
    confidence_score = serializers.FloatField(read_only=True)
    duration = serializers.FloatField(read_only=True)
    status = serializers.CharField(read_only=True)
    quality_control = STTQualityControlSerializer(read_only=True, required=False)
    
    
class STTTaskStatusSerializer(serializers.Serializer):
    """سریالایزر برای بررسی وضعیت وظیفه"""
    
    task_id = serializers.UUIDField()
    status = serializers.CharField(read_only=True)
    progress = serializers.IntegerField(read_only=True, min_value=0, max_value=100)
    transcription = serializers.CharField(read_only=True, required=False)
    error_message = serializers.CharField(read_only=True, required=False)
    estimated_time_remaining = serializers.IntegerField(
        read_only=True, 
        required=False,
        help_text='زمان تخمینی باقیمانده (ثانیه)'
    )