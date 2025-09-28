"""
Serializer های API Gateway برای validation و serialization
"""
from rest_framework import serializers
from django.core.validators import RegexValidator
from django.contrib.auth.password_validation import validate_password
from typing import Dict, Any
from .models import UnifiedUser, APIRequest, Workflow, RateLimitTracker


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer ثبت‌نام کاربران جدید
    """
    
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text='رمز عبور باید حداقل 8 کاراکتر باشد'
    )
    
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='تکرار رمز عبور'
    )
    
    class Meta:
        model = UnifiedUser
        fields = [
            'username', 'password', 'password_confirm',
            'first_name', 'last_name', 'email', 'user_type'
        ]
        extra_kwargs = {
            'username': {'help_text': 'شماره موبایل به فرمت 09123456789'},
            'first_name': {'help_text': 'نام'},
            'last_name': {'help_text': 'نام خانوادگی'},
            'email': {'help_text': 'آدرس ایمیل (اختیاری)'},
            'user_type': {'help_text': 'نوع کاربر'}
        }
    
    def validate_username(self, value: str) -> str:
        """
        اعتبارسنجی شماره موبایل
        
        Args:
            value: شماره موبایل ورودی
            
        Returns:
            str: شماره موبایل معتبر
            
        Raises:
            serializers.ValidationError: در صورت نامعتبر بودن
        """
        if not value.startswith('09') or len(value) != 11:
            raise serializers.ValidationError(
                'شماره موبایل باید به فرمت 09123456789 باشد'
            )
        
        if not value.isdigit():
            raise serializers.ValidationError(
                'شماره موبایل باید فقط شامل عدد باشد'
            )
        
        # بررسی تکراری نبودن
        if UnifiedUser.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                'این شماره موبایل قبلاً ثبت شده است'
            )
        
        return value
    
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        اعتبارسنجی کلی فیلدها
        
        Args:
            attrs: مقادیر ورودی
            
        Returns:
            Dict[str, Any]: مقادیر معتبر
        """
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        if password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': 'رمزهای عبور یکسان نیستند'
            })
        
        # حذف password_confirm از attrs
        attrs.pop('password_confirm', None)
        
        return attrs
    
    def create(self, validated_data: Dict[str, Any]) -> UnifiedUser:
        """
        ایجاد کاربر جدید
        
        Args:
            validated_data: داده‌های معتبر
            
        Returns:
            UnifiedUser: کاربر ایجاد شده
        """
        password = validated_data.pop('password')
        user = UnifiedUser.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class TextProcessingSerializer(serializers.Serializer):
    """
    Serializer پردازش متن
    """
    
    text = serializers.CharField(
        max_length=50000,
        help_text='متن برای پردازش (حداکثر 50000 کاراکتر)'
    )
    
    language = serializers.ChoiceField(
        choices=[('fa', 'فارسی'), ('en', 'انگلیسی'), ('ar', 'عربی')],
        default='fa',
        help_text='زبان متن'
    )
    
    options = serializers.JSONField(
        default=dict,
        required=False,
        help_text='تنظیمات اضافی پردازش'
    )
    
    include_stats = serializers.BooleanField(
        default=False,
        help_text='آیا آمار متن محاسبه شود؟'
    )
    
    normalize = serializers.BooleanField(
        default=False,
        help_text='آیا متن نرمال‌سازی شود؟'
    )
    
    summary_length = serializers.IntegerField(
        default=100,
        min_value=10,
        max_value=500,
        help_text='طول خلاصه (کاراکتر)'
    )
    
    def validate_text(self, value: str) -> str:
        """اعتبارسنجی متن ورودی"""
        if not value or not value.strip():
            raise serializers.ValidationError('متن نمی‌تواند خالی باشد')
        
        return value.strip()
    
    def validate_options(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """اعتبارسنجی options"""
        if not isinstance(value, dict):
            raise serializers.ValidationError('options باید dictionary باشد')
        
        return value


class SpeechProcessingSerializer(serializers.Serializer):
    """
    Serializer پردازش صدا
    """
    
    audio_data = serializers.CharField(
        help_text='داده‌های صوتی به صورت base64'
    )
    
    format = serializers.ChoiceField(
        choices=[('wav', 'WAV'), ('mp3', 'MP3'), ('ogg', 'OGG'), ('flac', 'FLAC')],
        default='wav',
        help_text='فرمت فایل صوتی'
    )
    
    language = serializers.ChoiceField(
        choices=[('fa', 'فارسی'), ('en', 'انگلیسی'), ('ar', 'عربی')],
        default='fa',
        help_text='زبان گفتار'
    )
    
    speech_to_text = serializers.BooleanField(
        default=True,
        help_text='آیا گفتار به متن تبدیل شود؟'
    )
    
    audio_analysis = serializers.BooleanField(
        default=False,
        help_text='آیا تحلیل صوتی انجام شود؟'
    )
    
    noise_reduction = serializers.BooleanField(
        default=False,
        help_text='آیا نویز کاهش یابد؟'
    )
    
    def validate_audio_data(self, value: str) -> str:
        """اعتبارسنجی داده‌های صوتی"""
        import base64
        
        try:
            audio_bytes = base64.b64decode(value)
            if len(audio_bytes) == 0:
                raise serializers.ValidationError('فایل صوتی خالی است')
                
            # بررسی حداکثر اندازه (50MB)
            max_size = 50 * 1024 * 1024
            if len(audio_bytes) > max_size:
                raise serializers.ValidationError(
                    f'فایل صوتی بیش از حد مجاز بزرگ است (حداکثر: {max_size/1024/1024}MB)'
                )
                
        except Exception as e:
            raise serializers.ValidationError('داده‌های صوتی نامعتبر است')
        
        return value


class TextToSpeechSerializer(serializers.Serializer):
    """
    Serializer تبدیل متن به گفتار
    """
    
    text = serializers.CharField(
        max_length=10000,
        help_text='متن برای تبدیل به گفتار'
    )
    
    language = serializers.ChoiceField(
        choices=[('fa', 'فارسی'), ('en', 'انگلیسی'), ('ar', 'عربی')],
        default='fa',
        help_text='زبان تولید گفتار'
    )
    
    voice_speed = serializers.FloatField(
        default=1.0,
        min_value=0.5,
        max_value=2.0,
        help_text='سرعت گفتار (0.5 تا 2.0)'
    )
    
    voice_pitch = serializers.FloatField(
        default=1.0,
        min_value=0.5,
        max_value=2.0,
        help_text='زیر و بمی صدا (0.5 تا 2.0)'
    )
    
    output_format = serializers.ChoiceField(
        choices=[('wav', 'WAV'), ('mp3', 'MP3')],
        default='wav',
        help_text='فرمت خروجی'
    )


class WorkflowSerializer(serializers.ModelSerializer):
    """
    Serializer مدیریت workflow
    """
    
    class Meta:
        model = Workflow
        fields = [
            'id', 'name', 'config', 'context', 'status',
            'current_step', 'completed_steps', 'results',
            'error_message', 'started_at', 'completed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'current_step', 'completed_steps',
            'results', 'error_message', 'started_at', 'completed_at',
            'created_at', 'updated_at'
        ]
    
    def validate_config(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """
        اعتبارسنجی تنظیمات workflow
        
        Args:
            value: تنظیمات workflow
            
        Returns:
            Dict[str, Any]: تنظیمات معتبر
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError('config باید dictionary باشد')
        
        if 'steps' not in value:
            raise serializers.ValidationError('steps الزامی است')
        
        steps = value['steps']
        if not isinstance(steps, list) or len(steps) == 0:
            raise serializers.ValidationError('steps باید لیست غیرخالی باشد')
        
        # اعتبارسنجی هر مرحله
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                raise serializers.ValidationError(f'مرحله {i} باید dictionary باشد')
            
            if 'name' not in step:
                raise serializers.ValidationError(f'مرحله {i} باید name داشته باشد')
            
            if 'type' not in step:
                raise serializers.ValidationError(f'مرحله {i} باید type داشته باشد')
            
            # بررسی نوع‌های مجاز
            allowed_types = [
                'text_processing', 'speech_processing', 'api_call',
                'data_validation', 'delay'
            ]
            if step['type'] not in allowed_types:
                raise serializers.ValidationError(
                    f'نوع مرحله {step["type"]} پشتیبانی نمی‌شود'
                )
        
        return value


class ParallelTaskSerializer(serializers.Serializer):
    """
    Serializer اجرای موازی تسک‌ها
    """
    
    tasks = serializers.ListField(
        child=serializers.JSONField(),
        min_length=1,
        max_length=50,
        help_text='لیست تسک‌ها برای اجرای موازی (حداکثر 50)'
    )
    
    max_workers = serializers.IntegerField(
        default=5,
        min_value=1,
        max_value=20,
        help_text='حداکثر تعداد worker موازی'
    )
    
    timeout = serializers.IntegerField(
        default=300,
        min_value=10,
        max_value=3600,
        help_text='حداکثر زمان انتظار (ثانیه)'
    )
    
    def validate_tasks(self, value: list) -> list:
        """اعتبارسنجی لیست تسک‌ها"""
        for i, task in enumerate(value):
            if not isinstance(task, dict):
                raise serializers.ValidationError(f'تسک {i} باید dictionary باشد')
            
            if 'type' not in task:
                raise serializers.ValidationError(f'تسک {i} باید type داشته باشد')
        
        return value


class APIRequestSerializer(serializers.ModelSerializer):
    """
    Serializer نمایش لاگ درخواست‌های API
    """
    
    duration = serializers.SerializerMethodField()
    user_display = serializers.SerializerMethodField()
    
    class Meta:
        model = APIRequest
        fields = [
            'id', 'user', 'user_display', 'method', 'path',
            'ip_address', 'response_status', 'status',
            'processing_time', 'duration', 'processor_type',
            'error_message', 'created_at', 'completed_at'
        ]
        read_only_fields = fields
    
    def get_duration(self, obj: APIRequest) -> str:
        """دریافت مدت زمان پردازش به صورت خوانا"""
        if obj.processing_time:
            if obj.processing_time < 1:
                return f"{obj.processing_time*1000:.0f}ms"
            else:
                return f"{obj.processing_time:.2f}s"
        return "نامشخص"
    
    def get_user_display(self, obj: APIRequest) -> str:
        """دریافت نمایش کاربر"""
        if obj.user:
            return str(obj.user)
        return "کاربر مهمان"


class RateLimitSerializer(serializers.ModelSerializer):
    """
    Serializer محدودیت نرخ درخواست
    """
    
    class Meta:
        model = RateLimitTracker
        fields = [
            'user', 'ip_address', 'endpoint', 'request_count',
            'window_start', 'last_request'
        ]
        read_only_fields = fields


class HealthCheckSerializer(serializers.Serializer):
    """
    Serializer بررسی سلامت سیستم
    """
    
    check_database = serializers.BooleanField(
        default=True,
        help_text='بررسی اتصال پایگاه داده'
    )
    
    check_cache = serializers.BooleanField(
        default=True,
        help_text='بررسی cache'
    )
    
    check_external_services = serializers.BooleanField(
        default=False,
        help_text='بررسی سرویس‌های خارجی'
    )
    
    detailed = serializers.BooleanField(
        default=False,
        help_text='نمایش جزئیات بیشتر'
    )