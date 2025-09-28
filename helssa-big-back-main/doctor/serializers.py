"""
سریالایزرهای اپلیکیشن Doctor
Doctor Application Serializers
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from .models import (
    DoctorProfile, 
    DoctorSchedule, 
    DoctorShift, 
    DoctorCertificate,
    DoctorRating,
    DoctorSettings
)

User = get_user_model()


class DoctorProfileSerializer(serializers.ModelSerializer):
    """
    سریالایزر پروفایل پزشک
    """
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    specialty_display = serializers.CharField(source='get_specialty_display', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = DoctorProfile
        fields = [
            'id', 'user', 'user_username', 'first_name', 'last_name', 'full_name',
            'national_code', 'medical_system_code', 'specialty', 'specialty_display',
            'sub_specialty', 'phone_number', 'clinic_address', 'clinic_phone',
            'biography', 'years_of_experience', 'profile_picture',
            'visit_duration', 'visit_price', 'is_verified', 'verification_date',
            'rating', 'total_reviews', 'auto_accept_appointments', 'allow_online_visits',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = [
            'id', 'user_username', 'full_name', 'specialty_display',
            'rating', 'total_reviews', 'is_verified', 'verification_date',
            'created_at', 'updated_at'
        ]
    
    def validate_national_code(self, value):
        """اعتبارسنجی کد ملی"""
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError("کد ملی باید 10 رقم باشد")
        
        # بررسی تکراری نبودن (در صورت ویرایش)
        if self.instance:
            if DoctorProfile.objects.exclude(id=self.instance.id).filter(national_code=value).exists():
                raise serializers.ValidationError("این کد ملی قبلاً ثبت شده است")
        else:
            if DoctorProfile.objects.filter(national_code=value).exists():
                raise serializers.ValidationError("این کد ملی قبلاً ثبت شده است")
        
        return value
    
    def validate_medical_system_code(self, value):
        """اعتبارسنجی کد نظام پزشکی"""
        # بررسی تکراری نبودن
        if self.instance:
            if DoctorProfile.objects.exclude(id=self.instance.id).filter(medical_system_code=value).exists():
                raise serializers.ValidationError("این کد نظام پزشکی قبلاً ثبت شده است")
        else:
            if DoctorProfile.objects.filter(medical_system_code=value).exists():
                raise serializers.ValidationError("این کد نظام پزشکی قبلاً ثبت شده است")
        
        return value
    
    def validate_phone_number(self, value):
        """اعتبارسنجی شماره موبایل"""
        phone_regex = RegexValidator(r'^09\d{9}$', 'شماره موبایل باید با 09 شروع شود و 11 رقم باشد')
        phone_regex(value)
        return value
    
    def validate_years_of_experience(self, value):
        """اعتبارسنجی سال‌های تجربه"""
        if value < 0 or value > 50:
            raise serializers.ValidationError("سال‌های تجربه باید بین 0 تا 50 باشد")
        return value
    
    def validate_visit_duration(self, value):
        """اعتبارسنجی مدت ویزیت"""
        if value < 15 or value > 120:
            raise serializers.ValidationError("مدت ویزیت باید بین 15 تا 120 دقیقه باشد")
        return value


class DoctorProfileCreateSerializer(serializers.ModelSerializer):
    """
    سریالایزر ایجاد پروفایل پزشک
    """
    
    class Meta:
        model = DoctorProfile
        fields = [
            'first_name', 'last_name', 'national_code', 'medical_system_code',
            'specialty', 'sub_specialty', 'phone_number', 'clinic_address',
            'clinic_phone', 'biography', 'years_of_experience', 'profile_picture',
            'visit_duration', 'visit_price', 'auto_accept_appointments', 'allow_online_visits'
        ]
    
    def create(self, validated_data):
        """ایجاد پروفایل پزشک با user فعلی"""
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class DoctorScheduleSerializer(serializers.ModelSerializer):
    """
    سریالایزر برنامه کاری پزشک
    """
    
    weekday_display = serializers.CharField(source='get_weekday_display', read_only=True)
    visit_type_display = serializers.CharField(source='get_visit_type_display', read_only=True)
    doctor_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DoctorSchedule
        fields = [
            'id', 'doctor', 'doctor_name', 'weekday', 'weekday_display',
            'start_time', 'end_time', 'visit_type', 'visit_type_display',
            'max_patients', 'break_start', 'break_end',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'doctor_name', 'created_at', 'updated_at']
    
    def get_doctor_name(self, obj):
        """نام پزشک"""
        try:
            return obj.doctor.doctor_profile.get_full_name()
        except:
            return obj.doctor.username
    
    def validate(self, data):
        """اعتبارسنجی زمان‌ها"""
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        break_start = data.get('break_start')
        break_end = data.get('break_end')
        
        # بررسی زمان شروع و پایان
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError({
                'end_time': 'ساعت پایان باید بعد از ساعت شروع باشد'
            })
        
        # بررسی زمان استراحت
        if break_start and break_end:
            if break_start >= break_end:
                raise serializers.ValidationError({
                    'break_end': 'ساعت پایان استراحت باید بعد از ساعت شروع باشد'
                })
            
            if start_time and end_time:
                if not (start_time <= break_start < break_end <= end_time):
                    raise serializers.ValidationError({
                        'break_start': 'زمان استراحت باید در بازه کاری باشد'
                    })
        
        return data
    
    def create(self, validated_data):
        """ایجاد برنامه کاری با doctor فعلی"""
        user = self.context['request'].user
        validated_data['doctor'] = user
        return super().create(validated_data)


class DoctorShiftSerializer(serializers.ModelSerializer):
    """
    سریالایزر شیفت پزشک
    """
    
    shift_type_display = serializers.CharField(source='get_shift_type_display', read_only=True)
    visit_type_display = serializers.CharField(source='get_visit_type_display', read_only=True)
    doctor_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DoctorShift
        fields = [
            'id', 'doctor', 'doctor_name', 'date', 'start_time', 'end_time',
            'shift_type', 'shift_type_display', 'visit_type', 'visit_type_display',
            'max_patients', 'notes', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'doctor_name', 'created_at', 'updated_at']
    
    def get_doctor_name(self, obj):
        """نام پزشک"""
        try:
            return obj.doctor.doctor_profile.get_full_name()
        except:
            return obj.doctor.username
    
    def validate(self, data):
        """اعتبارسنجی زمان‌ها"""
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError({
                'end_time': 'ساعت پایان باید بعد از ساعت شروع باشد'
            })
        
        return data
    
    def create(self, validated_data):
        """ایجاد شیفت با doctor فعلی"""
        user = self.context['request'].user
        validated_data['doctor'] = user
        return super().create(validated_data)


class DoctorCertificateSerializer(serializers.ModelSerializer):
    """
    سریالایزر مدارک پزشک
    """
    
    certificate_type_display = serializers.CharField(source='get_certificate_type_display', read_only=True)
    doctor_name = serializers.SerializerMethodField()
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = DoctorCertificate
        fields = [
            'id', 'doctor', 'doctor_name', 'certificate_type', 'certificate_type_display',
            'title', 'issuer', 'issue_date', 'expiry_date', 'certificate_number',
            'is_verified', 'verification_date', 'verification_notes', 'file',
            'is_expired', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = [
            'id', 'doctor_name', 'is_verified', 'verification_date', 
            'verification_notes', 'is_expired', 'created_at', 'updated_at'
        ]
    
    def get_doctor_name(self, obj):
        """نام پزشک"""
        try:
            return obj.doctor.doctor_profile.get_full_name()
        except:
            return obj.doctor.username
    
    def validate(self, data):
        """اعتبارسنجی تاریخ‌ها"""
        issue_date = data.get('issue_date')
        expiry_date = data.get('expiry_date')
        
        if issue_date and expiry_date and issue_date >= expiry_date:
            raise serializers.ValidationError({
                'expiry_date': 'تاریخ انقضا باید بعد از تاریخ صدور باشد'
            })
        
        return data
    
    def create(self, validated_data):
        """ایجاد مدرک با doctor فعلی"""
        user = self.context['request'].user
        validated_data['doctor'] = user
        return super().create(validated_data)


class DoctorRatingSerializer(serializers.ModelSerializer):
    """
    سریالایزر امتیازدهی پزشک
    """
    
    doctor_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DoctorRating
        fields = [
            'id', 'doctor', 'doctor_name', 'patient', 'patient_name',
            'rating', 'comment', 'visit_date', 'is_approved',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = [
            'id', 'doctor_name', 'patient_name', 'is_approved',
            'created_at', 'updated_at'
        ]
    
    def get_doctor_name(self, obj):
        """نام پزشک"""
        try:
            return obj.doctor.doctor_profile.get_full_name()
        except:
            return obj.doctor.username
    
    def get_patient_name(self, obj):
        """نام بیمار"""
        return obj.patient.username
    
    def validate_rating(self, value):
        """اعتبارسنجی امتیاز"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("امتیاز باید بین 1 تا 5 باشد")
        return value
    
    def create(self, validated_data):
        """ایجاد امتیاز با patient فعلی"""
        user = self.context['request'].user
        validated_data['patient'] = user
        return super().create(validated_data)


class DoctorRatingListSerializer(serializers.ModelSerializer):
    """
    سریالایزر لیست امتیازات (فقط خواندنی)
    """
    
    patient_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DoctorRating
        fields = [
            'id', 'patient_name', 'rating', 'comment', 'visit_date', 'created_at'
        ]
    
    def get_patient_name(self, obj):
        """نام بیمار (مخفی)"""
        return f"بیمار {obj.patient.username[:3]}***"


class DoctorSettingsSerializer(serializers.ModelSerializer):
    """
    سریالایزر تنظیمات پزشک
    """
    
    doctor_name = serializers.SerializerMethodField()
    preferred_language_display = serializers.CharField(source='get_preferred_language_display', read_only=True)
    
    class Meta:
        model = DoctorSettings
        fields = [
            'id', 'doctor', 'doctor_name', 'email_notifications', 'sms_notifications',
            'push_notifications', 'allow_same_day_booking', 'booking_lead_time',
            'max_daily_appointments', 'auto_generate_prescription', 'auto_generate_certificate',
            'preferred_language', 'preferred_language_display',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = [
            'id', 'doctor_name', 'preferred_language_display',
            'created_at', 'updated_at'
        ]
    
    def get_doctor_name(self, obj):
        """نام پزشک"""
        try:
            return obj.doctor.doctor_profile.get_full_name()
        except:
            return obj.doctor.username
    
    def validate_booking_lead_time(self, value):
        """اعتبارسنجی زمان قبل از ویزیت"""
        if value < 30 or value > 1440:
            raise serializers.ValidationError("زمان قبل از ویزیت باید بین 30 تا 1440 دقیقه باشد")
        return value
    
    def validate_max_daily_appointments(self, value):
        """اعتبارسنجی حداکثر نوبت روزانه"""
        if value < 5 or value > 100:
            raise serializers.ValidationError("حداکثر نوبت روزانه باید بین 5 تا 100 باشد")
        return value
    
    def create(self, validated_data):
        """ایجاد تنظیمات با doctor فعلی"""
        user = self.context['request'].user
        validated_data['doctor'] = user
        return super().create(validated_data)


class DoctorSearchSerializer(serializers.Serializer):
    """
    سریالایزر جستجوی پزشک
    """
    
    specialty = serializers.ChoiceField(
        choices=DoctorProfile.SPECIALTY_CHOICES,
        required=False,
        allow_blank=True
    )
    
    location = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True
    )
    
    name = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True
    )
    
    min_rating = serializers.FloatField(
        min_value=0.0,
        max_value=5.0,
        required=False
    )
    
    verified_only = serializers.BooleanField(
        default=False,
        required=False
    )
    
    online_visit = serializers.BooleanField(
        default=False,
        required=False
    )


class DoctorListSerializer(serializers.ModelSerializer):
    """
    سریالایزر لیست پزشکان (خلاصه)
    """
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    specialty_display = serializers.CharField(source='get_specialty_display', read_only=True)
    
    class Meta:
        model = DoctorProfile
        fields = [
            'id', 'full_name', 'specialty', 'specialty_display',
            'years_of_experience', 'rating', 'total_reviews',
            'visit_price', 'is_verified', 'allow_online_visits',
            'profile_picture'
        ]