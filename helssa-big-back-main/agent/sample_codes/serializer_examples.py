"""
نمونه کدهای Serializer برای ایجنت‌ها
Sample Serializer Code Examples for Agents
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from app_standards.serializers.base_serializers import (
    BaseModelSerializer, PhoneNumberField, NationalCodeField,
    AmountField, PersianDateField, DurationField,
    validate_future_date, validate_persian_text
)
from decimal import Decimal

User = get_user_model()


# ====================================
# نمونه 1: Basic Model Serializer
# ====================================

class PatientProfileSerializer(BaseModelSerializer):
    """
    سریالایزر پروفایل بیمار
    """
    phone_number = PhoneNumberField()
    national_code = NationalCodeField()
    age = serializers.SerializerMethodField()
    full_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    
    class Meta:
        from patient_records.models import PatientProfile
        model = PatientProfile
        fields = [
            'id', 'patient', 'full_name', 'national_code', 
            'date_of_birth', 'age', 'gender', 'phone_number',
            'blood_type', 'allergies', 'chronic_diseases',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'age']
    
    def get_age(self, obj):
        """محاسبه سن"""
        return obj.age
    
    def validate_date_of_birth(self, value):
        """اعتبارسنجی تاریخ تولد"""
        if value > timezone.now().date():
            raise serializers.ValidationError("تاریخ تولد نمی‌تواند در آینده باشد")
        
        # حداقل سن 1 سال
        min_date = timezone.now().date().replace(year=timezone.now().year - 120)
        if value < min_date:
            raise serializers.ValidationError("تاریخ تولد نامعتبر است")
        
        return value


# ====================================
# نمونه 2: Nested Serializer
# ====================================

class DoctorSerializer(serializers.ModelSerializer):
    """سریالایزر ساده برای نمایش اطلاعات پزشک"""
    full_name = serializers.SerializerMethodField()
    speciality = serializers.CharField(source='doctor_profile.speciality', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'speciality']
    
    def get_full_name(self, obj):
        return f"دکتر {obj.first_name} {obj.last_name}".strip()


class MedicalVisitSerializer(BaseModelSerializer):
    """
    سریالایزر ویزیت پزشکی با اطلاعات nested
    """
    patient = serializers.StringRelatedField(read_only=True)
    doctor = DoctorSerializer(read_only=True)
    fee_display = AmountField(source='fee', read_only=True)
    visit_date_persian = PersianDateField(source='visit_date', read_only=True)
    duration_display = DurationField(source='duration_minutes', read_only=True)
    
    class Meta:
        from visit_management.models import MedicalVisit
        model = MedicalVisit
        fields = [
            'id', 'patient', 'doctor', 'visit_date', 'visit_date_persian',
            'visit_type', 'status', 'chief_complaint', 'diagnosis',
            'treatment_plan', 'fee', 'fee_display', 'is_paid',
            'duration_minutes', 'duration_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'patient', 'doctor']
    
    def validate_visit_date(self, value):
        """اعتبارسنجی تاریخ ویزیت"""
        # برای ویزیت‌های جدید، تاریخ باید در آینده باشد
        if self.instance is None:  # Create
            if value <= timezone.now():
                raise serializers.ValidationError("تاریخ ویزیت باید در آینده باشد")
        
        return value


# ====================================
# نمونه 3: Create/Update Serializers
# ====================================

class PrescriptionCreateSerializer(serializers.Serializer):
    """
    سریالایزر برای ایجاد نسخه جدید
    """
    patient_id = serializers.UUIDField()
    visit_id = serializers.UUIDField(required=False)
    items = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        max_length=20
    )
    notes = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
        validators=[validate_persian_text]
    )
    
    def validate_patient_id(self, value):
        """اعتبارسنجی بیمار"""
        try:
            patient = User.objects.get(id=value, user_type='patient', is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("بیمار یافت نشد")
        
        # بررسی دسترسی پزشک به بیمار
        request = self.context.get('request')
        if request and request.user.user_type == 'doctor':
            # در اینجا می‌توان دسترسی را بررسی کرد
            pass
        
        return value
    
    def validate_items(self, value):
        """اعتبارسنجی اقلام نسخه"""
        for item in value:
            # بررسی فیلدهای اجباری
            required_fields = ['drug_name', 'dosage', 'frequency', 'quantity']
            for field in required_fields:
                if field not in item:
                    raise serializers.ValidationError(
                        f"فیلد {field} برای همه اقلام اجباری است"
                    )
            
            # بررسی quantity
            if item['quantity'] <= 0:
                raise serializers.ValidationError("تعداد باید بیشتر از صفر باشد")
        
        return value
    
    def create(self, validated_data):
        """ایجاد نسخه و اقلام آن"""
        from prescription_system.models import Prescription, PrescriptionItem
        from django.db import transaction
        
        with transaction.atomic():
            # ایجاد نسخه
            prescription = Prescription.objects.create(
                patient_id=validated_data['patient_id'],
                doctor=self.context['request'].user,
                visit_id=validated_data.get('visit_id'),
                notes=validated_data.get('notes', ''),
                status='issued'
            )
            
            # ایجاد اقلام
            for item_data in validated_data['items']:
                PrescriptionItem.objects.create(
                    prescription=prescription,
                    **item_data
                )
            
            return prescription


# ====================================
# نمونه 4: List Serializer with Filtering
# ====================================

class AppointmentListSerializer(BaseModelSerializer):
    """
    سریالایزر لیست قرارهای ملاقات
    """
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    time_until = serializers.SerializerMethodField()
    
    class Meta:
        from appointment_scheduler.models import Appointment
        model = Appointment
        fields = [
            'id', 'patient_name', 'doctor_name', 'appointment_date',
            'appointment_time', 'status', 'status_display',
            'reason', 'time_until'
        ]
    
    def get_time_until(self, obj):
        """محاسبه زمان باقیمانده تا قرار"""
        if obj.status in ['completed', 'cancelled']:
            return None
        
        now = timezone.now()
        appointment_datetime = timezone.make_aware(
            timezone.datetime.combine(obj.appointment_date, obj.appointment_time)
        )
        
        if appointment_datetime < now:
            return "گذشته"
        
        delta = appointment_datetime - now
        days = delta.days
        hours = delta.seconds // 3600
        
        if days > 0:
            return f"{days} روز"
        elif hours > 0:
            return f"{hours} ساعت"
        else:
            minutes = delta.seconds // 60
            return f"{minutes} دقیقه"


# ====================================
# نمونه 5: File Upload Serializer
# ====================================

class MedicalDocumentSerializer(BaseModelSerializer):
    """
    سریالایزر آپلود مدارک پزشکی
    """
    file = serializers.FileField(write_only=True)
    file_url = serializers.SerializerMethodField(read_only=True)
    file_size_display = serializers.SerializerMethodField()
    uploaded_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        from patient_records.models import MedicalDocument
        model = MedicalDocument
        fields = [
            'id', 'file', 'file_url', 'file_name', 'file_size',
            'file_size_display', 'file_type', 'document_type',
            'description', 'uploaded_by', 'created_at'
        ]
        read_only_fields = ['id', 'file_name', 'file_size', 'uploaded_by', 'created_at']
    
    def get_file_url(self, obj):
        """دریافت URL فایل"""
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None
    
    def get_file_size_display(self, obj):
        """نمایش حجم فایل به صورت خوانا"""
        size = obj.file_size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"
    
    def validate_file(self, value):
        """اعتبارسنجی فایل آپلودی"""
        # حجم فایل (حداکثر 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("حجم فایل نباید بیشتر از 10 مگابایت باشد")
        
        # نوع فایل
        allowed_types = {
            'image/jpeg': 'jpg',
            'image/png': 'png',
            'application/pdf': 'pdf',
            'application/msword': 'doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx'
        }
        
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("فرمت فایل مجاز نیست")
        
        # بررسی پسوند فایل
        import os
        ext = os.path.splitext(value.name)[1].lower()
        expected_ext = '.' + allowed_types[value.content_type]
        
        if ext != expected_ext:
            raise serializers.ValidationError("پسوند فایل با نوع آن مطابقت ندارد")
        
        return value


# ====================================
# نمونه 6: Validation Examples
# ====================================

class ChatMessageSerializer(serializers.Serializer):
    """
    سریالایزر پیام چت با اعتبارسنجی‌های پیچیده
    """
    message = serializers.CharField(
        min_length=2,
        max_length=1000,
        trim_whitespace=True
    )
    attachments = serializers.ListField(
        child=serializers.FileField(),
        max_length=3,
        required=False
    )
    metadata = serializers.JSONField(required=False)
    
    def validate_message(self, value):
        """اعتبارسنجی پیام"""
        # حذف کاراکترهای کنترلی
        import re
        value = re.sub(r'[\x00-\x1F\x7F]', '', value)
        
        # بررسی محتوای نامناسب (می‌توان پیچیده‌تر کرد)
        inappropriate_words = ['spam', 'abuse']  # لیست واقعی باید کامل‌تر باشد
        
        for word in inappropriate_words:
            if word in value.lower():
                raise serializers.ValidationError("پیام حاوی محتوای نامناسب است")
        
        return value
    
    def validate_attachments(self, value):
        """اعتبارسنجی فایل‌های پیوست"""
        total_size = sum(file.size for file in value)
        
        if total_size > 20 * 1024 * 1024:  # 20MB total
            raise serializers.ValidationError("حجم کل فایل‌ها نباید بیشتر از 20 مگابایت باشد")
        
        return value
    
    def validate(self, attrs):
        """اعتبارسنجی ترکیبی"""
        # اگر پیام خالی است، باید حداقل یک فایل داشته باشد
        message = attrs.get('message', '').strip()
        attachments = attrs.get('attachments', [])
        
        if not message and not attachments:
            raise serializers.ValidationError("پیام یا فایل پیوست الزامی است")
        
        return attrs


# ====================================
# نمونه 7: Dynamic Fields Serializer
# ====================================

class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    سریالایزر با قابلیت انتخاب فیلدها
    """
    def __init__(self, *args, **kwargs):
        # فیلدهای درخواستی
        fields = kwargs.pop('fields', None)
        exclude = kwargs.pop('exclude', None)
        
        super().__init__(*args, **kwargs)
        
        if fields is not None:
            # حذف فیلدهایی که درخواست نشده‌اند
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)
        
        if exclude is not None:
            # حذف فیلدهای exclude شده
            for field_name in exclude:
                self.fields.pop(field_name, None)


class PatientRecordSerializer(DynamicFieldsModelSerializer):
    """
    مثال استفاده از DynamicFieldsModelSerializer
    """
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    files_count = serializers.SerializerMethodField()
    
    class Meta:
        from patient_records.models import PatientRecord
        model = PatientRecord
        fields = '__all__'
    
    def get_files_count(self, obj):
        return obj.files.count()


# ====================================
# نمونه 8: Bulk Operations Serializer
# ====================================

class BulkUpdateSerializer(serializers.Serializer):
    """
    سریالایزر برای عملیات دسته‌ای
    """
    ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100,
        help_text="لیست شناسه‌های موارد برای به‌روزرسانی"
    )
    updates = serializers.DictField(
        help_text="فیلدهایی که باید به‌روزرسانی شوند"
    )
    
    def validate_ids(self, value):
        """اعتبارسنجی شناسه‌ها"""
        # حذف تکراری‌ها
        unique_ids = list(set(value))
        
        if len(unique_ids) != len(value):
            raise serializers.ValidationError("شناسه‌های تکراری وجود دارد")
        
        return unique_ids
    
    def validate_updates(self, value):
        """اعتبارسنجی فیلدهای به‌روزرسانی"""
        # فیلدهای مجاز برای به‌روزرسانی دسته‌ای
        allowed_fields = ['status', 'is_active', 'priority']
        
        for field in value.keys():
            if field not in allowed_fields:
                raise serializers.ValidationError(
                    f"فیلد '{field}' برای به‌روزرسانی دسته‌ای مجاز نیست"
                )
        
        return value


# ====================================
# نمونه 9: Report Serializer
# ====================================

class SOAPReportSerializer(serializers.Serializer):
    """
    سریالایزر گزارش SOAP
    """
    encounter_id = serializers.UUIDField(read_only=True)
    patient_info = serializers.SerializerMethodField()
    doctor_info = serializers.SerializerMethodField()
    
    # بخش‌های SOAP
    subjective = serializers.CharField()
    objective = serializers.CharField()
    assessment = serializers.CharField()
    plan = serializers.CharField()
    
    # متادیتا
    transcription_text = serializers.CharField(read_only=True)
    audio_duration = DurationField(read_only=True)
    generated_at = serializers.DateTimeField(read_only=True)
    confidence_score = serializers.FloatField(read_only=True)
    
    def get_patient_info(self, obj):
        """اطلاعات بیمار"""
        return {
            'name': obj.patient.get_full_name(),
            'age': obj.patient.profile.age,
            'gender': obj.patient.profile.get_gender_display()
        }
    
    def get_doctor_info(self, obj):
        """اطلاعات پزشک"""
        return {
            'name': f"دکتر {obj.doctor.get_full_name()}",
            'speciality': obj.doctor.doctor_profile.speciality,
            'license_number': obj.doctor.doctor_profile.license_number
        }


# ====================================
# نمونه 10: Custom Field Example
# ====================================

class TimeSlotField(serializers.Field):
    """
    فیلد سفارشی برای بازه‌های زمانی
    """
    def to_representation(self, value):
        """تبدیل به فرمت نمایش"""
        if not value:
            return None
        
        start_time = value.get('start_time')
        end_time = value.get('end_time')
        
        if start_time and end_time:
            return f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
        
        return None
    
    def to_internal_value(self, data):
        """تبدیل از ورودی کاربر"""
        if not data:
            return None
        
        try:
            # فرمت ورودی: "14:00 - 14:30"
            parts = data.split(' - ')
            if len(parts) != 2:
                raise ValueError
            
            from datetime import datetime
            start_time = datetime.strptime(parts[0].strip(), '%H:%M').time()
            end_time = datetime.strptime(parts[1].strip(), '%H:%M').time()
            
            if start_time >= end_time:
                raise serializers.ValidationError("زمان پایان باید بعد از زمان شروع باشد")
            
            return {
                'start_time': start_time,
                'end_time': end_time
            }
            
        except ValueError:
            raise serializers.ValidationError("فرمت بازه زمانی نامعتبر است. فرمت صحیح: HH:MM - HH:MM")


class DoctorScheduleSerializer(serializers.Serializer):
    """
    مثال استفاده از TimeSlotField
    """
    day_of_week = serializers.ChoiceField(
        choices=[
            (0, 'شنبه'), (1, 'یکشنبه'), (2, 'دوشنبه'),
            (3, 'سه‌شنبه'), (4, 'چهارشنبه'), (5, 'پنج‌شنبه'),
            (6, 'جمعه')
        ]
    )
    time_slots = serializers.ListField(
        child=TimeSlotField(),
        min_length=1,
        max_length=10
    )
    is_available = serializers.BooleanField(default=True)