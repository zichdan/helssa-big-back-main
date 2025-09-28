"""
سریالایزرهای سیستم مدیریت بیماران
Patient Management System Serializers
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import date, timedelta
from typing import Dict, Any

from .models import (
    PatientProfile,
    MedicalRecord,
    PrescriptionHistory,
    MedicalConsent
)

User = get_user_model()


class PatientProfileSerializer(serializers.ModelSerializer):
    """
    سریالایزر پروفایل بیمار
    Patient Profile Serializer
    """
    
    # فیلدهای محاسبه شده
    age = serializers.ReadOnlyField()
    bmi = serializers.ReadOnlyField()
    full_name = serializers.SerializerMethodField()
    
    # فیلدهای اضافی برای نمایش
    user_phone = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = PatientProfile
        fields = [
            'id',
            'user',
            'national_code',
            'first_name',
            'last_name',
            'full_name',
            'birth_date',
            'age',
            'gender',
            'emergency_contact_name',
            'emergency_contact_phone',
            'emergency_contact_relation',
            'address',
            'city',
            'province',
            'postal_code',
            'blood_type',
            'height',
            'weight',
            'bmi',
            'marital_status',
            'medical_record_number',
            'is_active',
            'user_phone',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'medical_record_number',
            'age',
            'bmi',
            'full_name',
            'user_phone',
            'created_at',
            'updated_at',
        ]
    
    def get_full_name(self, obj: PatientProfile) -> str:
        """
        دریافت نام کامل بیمار
        Get patient's full name
        """
        return obj.get_full_name()
    
    def validate_national_code(self, value: str) -> str:
        """
        اعتبارسنجی کد ملی
        Validate national code
        """
        if not value.isdigit():
            raise serializers.ValidationError("کد ملی باید فقط شامل عدد باشد")
        
        if len(value) != 10:
            raise serializers.ValidationError("کد ملی باید 10 رقم باشد")
        
        # الگوریتم اعتبارسنجی کد ملی
        if not self._is_valid_national_code(value):
            raise serializers.ValidationError("کد ملی وارد شده معتبر نیست")
        
        # بررسی تکراری نبودن (در صورت ویرایش، کد ملی فعلی را نادیده بگیر)
        queryset = PatientProfile.objects.filter(national_code=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError("این کد ملی قبلاً ثبت شده است")
        
        return value
    
    def validate_birth_date(self, value: date) -> date:
        """
        اعتبارسنجی تاریخ تولد
        Validate birth date
        """
        today = date.today()
        
        if value > today:
            raise serializers.ValidationError("تاریخ تولد نمی‌تواند در آینده باشد")
        
        # محدودیت سنی (حداقل 1 سال، حداکثر 120 سال)
        min_birth_date = today - timedelta(days=120*365)
        max_birth_date = today - timedelta(days=365)
        
        if value < min_birth_date:
            raise serializers.ValidationError("سن وارد شده بیش از حد مجاز است")
        
        if value > max_birth_date:
            raise serializers.ValidationError("سن باید حداقل 1 سال باشد")
        
        return value
    
    def validate_height(self, value: float) -> float:
        """
        اعتبارسنجی قد
        Validate height
        """
        if value is not None:
            if value < 50 or value > 250:
                raise serializers.ValidationError("قد باید بین 50 تا 250 سانتی‌متر باشد")
        return value
    
    def validate_weight(self, value: float) -> float:
        """
        اعتبارسنجی وزن
        Validate weight
        """
        if value is not None:
            if value < 10 or value > 500:
                raise serializers.ValidationError("وزن باید بین 10 تا 500 کیلوگرم باشد")
        return value
    
    def validate_postal_code(self, value: str) -> str:
        """
        اعتبارسنجی کد پستی
        Validate postal code
        """
        if not value.isdigit():
            raise serializers.ValidationError("کد پستی باید فقط شامل عدد باشد")
        
        if len(value) != 10:
            raise serializers.ValidationError("کد پستی باید 10 رقم باشد")
        
        return value
    
    def _is_valid_national_code(self, national_code: str) -> bool:
        """
        بررسی اعتبار کد ملی با الگوریتم checksum
        Validate national code using checksum algorithm
        """
        if len(national_code) != 10:
            return False
        
        # کدهای ملی نامعتبر شناخته شده
        invalid_codes = [
            '0000000000', '1111111111', '2222222222',
            '3333333333', '4444444444', '5555555555',
            '6666666666', '7777777777', '8888888888', '9999999999'
        ]
        
        if national_code in invalid_codes:
            return False
        
        # محاسبه checksum
        check_sum = 0
        for i in range(9):
            check_sum += int(national_code[i]) * (10 - i)
        
        remainder = check_sum % 11
        check_digit = int(national_code[9])
        
        if remainder < 2:
            return check_digit == remainder
        else:
            return check_digit == 11 - remainder


class PatientProfileCreateSerializer(PatientProfileSerializer):
    """
    سریالایزر ایجاد پروفایل بیمار
    Create Patient Profile Serializer
    """
    
    # فیلد شماره تلفن برای ایجاد کاربر
    phone_number = serializers.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                r'^09\d{9}$',
                'شماره موبایل باید با 09 شروع شود و 11 رقم باشد'
            )
        ],
        write_only=True
    )
    
    class Meta(PatientProfileSerializer.Meta):
        fields = PatientProfileSerializer.Meta.fields + ['phone_number']
    
    def create(self, validated_data: Dict[str, Any]) -> PatientProfile:
        """
        ایجاد پروفایل بیمار همراه با کاربر
        Create patient profile with user
        """
        phone_number = validated_data.pop('phone_number')
        
        # ایجاد یا دریافت کاربر
        user, created = User.objects.get_or_create(
            username=phone_number,
            defaults={
                'user_type': 'patient',
                'is_active': True
            }
        )
        
        if not created and hasattr(user, 'patient_profile'):
            raise serializers.ValidationError({
                'phone_number': 'این شماره تلفن قبلاً ثبت شده است'
            })
        
        validated_data['user'] = user
        return super().create(validated_data)


class MedicalRecordSerializer(serializers.ModelSerializer):
    """
    سریالایزر سابقه پزشکی
    Medical Record Serializer
    """
    
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    duration_days = serializers.SerializerMethodField()
    
    class Meta:
        model = MedicalRecord
        fields = [
            'id',
            'patient',
            'patient_name',
            'record_type',
            'title',
            'description',
            'severity',
            'start_date',
            'end_date',
            'is_ongoing',
            'duration_days',
            'doctor_name',
            'notes',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'patient_name',
            'created_by_name',
            'duration_days',
            'created_at',
            'updated_at',
        ]
    
    def get_duration_days(self, obj: MedicalRecord) -> int:
        """
        محاسبه مدت زمان (روز)
        Calculate duration in days
        """
        if obj.end_date:
            return (obj.end_date - obj.start_date).days
        elif obj.is_ongoing:
            return (date.today() - obj.start_date).days
        return 0
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        اعتبارسنجی کلی
        General validation
        """
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        is_ongoing = data.get('is_ongoing', False)
        
        if start_date and start_date > date.today():
            raise serializers.ValidationError({
                'start_date': 'تاریخ شروع نمی‌تواند در آینده باشد'
            })
        
        if end_date:
            if start_date and end_date < start_date:
                raise serializers.ValidationError({
                    'end_date': 'تاریخ پایان نمی‌تواند قبل از تاریخ شروع باشد'
                })
            
            if end_date > date.today():
                raise serializers.ValidationError({
                    'end_date': 'تاریخ پایان نمی‌تواند در آینده باشد'
                })
            
            # اگر تاریخ پایان مشخص شده، نباید ongoing باشد
            if is_ongoing:
                raise serializers.ValidationError({
                    'is_ongoing': 'اگر تاریخ پایان مشخص شده، نمی‌تواند در حال ادامه باشد'
                })
        
        return data


class PrescriptionHistorySerializer(serializers.ModelSerializer):
    """
    سریالایزر تاریخچه نسخه‌ها
    Prescription History Serializer
    """
    
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    prescribed_by_name = serializers.CharField(source='prescribed_by.get_full_name', read_only=True)
    is_expired = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    can_repeat = serializers.SerializerMethodField()
    
    class Meta:
        model = PrescriptionHistory
        fields = [
            'id',
            'patient',
            'patient_name',
            'prescribed_by',
            'prescribed_by_name',
            'prescription_number',
            'medication_name',
            'dosage',
            'frequency',
            'duration',
            'instructions',
            'diagnosis',
            'prescribed_date',
            'start_date',
            'end_date',
            'status',
            'is_repeat_allowed',
            'repeat_count',
            'max_repeats',
            'can_repeat',
            'is_expired',
            'days_remaining',
            'pharmacy_notes',
            'patient_notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'patient_name',
            'prescribed_by_name',
            'prescription_number',
            'is_expired',
            'days_remaining',
            'can_repeat',
            'created_at',
            'updated_at',
        ]
    
    def get_can_repeat(self, obj: PrescriptionHistory) -> bool:
        """
        بررسی امکان تکرار نسخه
        Check if prescription can be repeated
        """
        return obj.can_repeat()
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        اعتبارسنجی کلی نسخه
        General prescription validation
        """
        prescribed_date = data.get('prescribed_date')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if prescribed_date and prescribed_date > date.today():
            raise serializers.ValidationError({
                'prescribed_date': 'تاریخ تجویز نمی‌تواند در آینده باشد'
            })
        
        if start_date and start_date < date.today() - timedelta(days=30):
            raise serializers.ValidationError({
                'start_date': 'تاریخ شروع نمی‌تواند بیش از 30 روز گذشته باشد'
            })
        
        if end_date:
            if start_date and end_date <= start_date:
                raise serializers.ValidationError({
                    'end_date': 'تاریخ پایان باید بعد از تاریخ شروع باشد'
                })
            
            # حداکثر مدت نسخه 90 روز
            if start_date and (end_date - start_date).days > 90:
                raise serializers.ValidationError({
                    'end_date': 'مدت نسخه نمی‌تواند بیش از 90 روز باشد'
                })
        
        # بررسی حداکثر تکرار
        max_repeats = data.get('max_repeats', 1)
        if max_repeats > 10:
            raise serializers.ValidationError({
                'max_repeats': 'حداکثر تکرار نمی‌تواند بیش از 10 بار باشد'
            })
        
        return data


class MedicalConsentSerializer(serializers.ModelSerializer):
    """
    سریالایزر رضایت‌نامه‌های پزشکی
    Medical Consent Serializer
    """
    
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.get_full_name', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)
    is_valid = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = MedicalConsent
        fields = [
            'id',
            'patient',
            'patient_name',
            'consent_type',
            'title',
            'description',
            'consent_text',
            'status',
            'created_date',
            'consent_date',
            'expiry_date',
            'is_valid',
            'is_expired',
            'digital_signature',
            'ip_address',
            'user_agent',
            'witness_name',
            'witness_signature',
            'notes',
            'requested_by',
            'requested_by_name',
            'processed_by',
            'processed_by_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'patient_name',
            'requested_by_name',
            'processed_by_name',
            'is_valid',
            'is_expired',
            'digital_signature',
            'ip_address',
            'user_agent',
            'consent_date',
            'created_at',
            'updated_at',
        ]
    
    def validate_expiry_date(self, value: date) -> date:
        """
        اعتبارسنجی تاریخ انقضا
        Validate expiry date
        """
        if value and value <= date.today():
            raise serializers.ValidationError("تاریخ انقضا باید در آینده باشد")
        return value


class ConsentGrantSerializer(serializers.Serializer):
    """
    سریالایزر ثبت رضایت
    Grant Consent Serializer
    """
    
    digital_signature = serializers.CharField(
        max_length=1000,
        help_text="امضای دیجیتال بیمار"
    )
    
    def validate_digital_signature(self, value: str) -> str:
        """
        اعتبارسنجی امضای دیجیتال
        Validate digital signature
        """
        if len(value.strip()) < 10:
            raise serializers.ValidationError("امضای دیجیتال بسیار کوتاه است")
        return value


class PatientStatisticsSerializer(serializers.Serializer):
    """
    سریالایزر آمار بیمار
    Patient Statistics Serializer
    """
    
    total_visits = serializers.IntegerField(read_only=True)
    total_prescriptions = serializers.IntegerField(read_only=True)
    active_prescriptions = serializers.IntegerField(read_only=True)
    pending_consents = serializers.IntegerField(read_only=True)
    medical_records_count = serializers.IntegerField(read_only=True)
    last_visit_date = serializers.DateField(read_only=True)
    next_appointment = serializers.DateTimeField(read_only=True)


class PatientSearchSerializer(serializers.Serializer):
    """
    سریالایزر جستجوی بیمار
    Patient Search Serializer
    """
    
    query = serializers.CharField(
        max_length=100,
        help_text="متن جستجو (نام، نام خانوادگی، کد ملی، شماره پرونده)"
    )
    
    search_type = serializers.ChoiceField(
        choices=[
            ('all', 'همه'),
            ('name', 'نام'),
            ('national_code', 'کد ملی'),
            ('medical_record', 'شماره پرونده'),
        ],
        default='all'
    )
    
    def validate_query(self, value: str) -> str:
        """
        اعتبارسنجی متن جستجو
        Validate search query
        """
        if len(value.strip()) < 2:
            raise serializers.ValidationError("متن جستجو باید حداقل 2 کاراکتر باشد")
        return value.strip()