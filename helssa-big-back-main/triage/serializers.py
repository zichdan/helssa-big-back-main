"""
سریالایزرهای سیستم تریاژ پزشکی
Triage System Serializers
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
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

User = get_user_model()


class SymptomCategorySerializer(serializers.ModelSerializer):
    """
    سریالایزر دسته‌بندی علائم
    """
    
    class Meta:
        model = SymptomCategory
        fields = [
            'id', 'name', 'name_en', 'description', 'priority_level',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_priority_level(self, value: int) -> int:
        """اعتبارسنجی سطح اولویت"""
        if not 1 <= value <= 10:
            raise serializers.ValidationError('سطح اولویت باید بین 1 تا 10 باشد')
        return value


class SymptomListSerializer(serializers.ModelSerializer):
    """
    سریالایزر لیست علائم (خلاصه)
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Symptom
        fields = [
            'id', 'name', 'name_en', 'category_name', 'urgency_score',
            'is_active'
        ]


class SymptomDetailSerializer(serializers.ModelSerializer):
    """
    سریالایزر جزئیات علائم
    """
    category = SymptomCategorySerializer(read_only=True)
    category_id = serializers.UUIDField(write_only=True)
    related_symptoms = SymptomListSerializer(many=True, read_only=True)
    
    class Meta:
        model = Symptom
        fields = [
            'id', 'name', 'name_en', 'category', 'category_id',
            'description', 'severity_levels', 'common_locations',
            'related_symptoms', 'urgency_score', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_urgency_score(self, value: int) -> int:
        """اعتبارسنجی امتیاز اورژانس"""
        if not 1 <= value <= 10:
            raise serializers.ValidationError('امتیاز اورژانس باید بین 1 تا 10 باشد')
        return value
    
    def validate_severity_levels(self, value: list) -> list:
        """اعتبارسنجی سطوح شدت"""
        if not isinstance(value, list):
            raise serializers.ValidationError('سطوح شدت باید لیست باشد')
        
        valid_levels = ['خفیف', 'متوسط', 'شدید', 'بسیار شدید']
        for level in value:
            if level not in valid_levels:
                raise serializers.ValidationError(f'سطح شدت "{level}" معتبر نیست')
        
        return value


class DiagnosisSymptomSerializer(serializers.ModelSerializer):
    """
    سریالایزر رابطه تشخیص-علامت
    """
    symptom_name = serializers.CharField(source='symptom.name', read_only=True)
    
    class Meta:
        model = DiagnosisSymptom
        fields = [
            'id', 'symptom', 'symptom_name', 'weight', 'is_mandatory',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate_weight(self, value: float) -> float:
        """اعتبارسنجی وزن"""
        if not 0.1 <= value <= 10.0:
            raise serializers.ValidationError('وزن باید بین 0.1 تا 10.0 باشد')
        return value


class DifferentialDiagnosisListSerializer(serializers.ModelSerializer):
    """
    سریالایزر لیست تشخیص‌های افتراقی (خلاصه)
    """
    
    class Meta:
        model = DifferentialDiagnosis
        fields = [
            'id', 'name', 'name_en', 'icd_10_code', 'urgency_level',
            'is_active'
        ]


class DifferentialDiagnosisDetailSerializer(serializers.ModelSerializer):
    """
    سریالایزر جزئیات تشخیص‌های افتراقی
    """
    typical_symptoms = DiagnosisSymptomSerializer(
        source='diagnosissymptom_set',
        many=True,
        read_only=True
    )
    
    class Meta:
        model = DifferentialDiagnosis
        fields = [
            'id', 'name', 'name_en', 'icd_10_code', 'description',
            'typical_symptoms', 'urgency_level', 'recommended_actions',
            'red_flags', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_urgency_level(self, value: int) -> int:
        """اعتبارسنجی سطح اورژانس"""
        if not 1 <= value <= 10:
            raise serializers.ValidationError('سطح اورژانس باید بین 1 تا 10 باشد')
        return value
    
    def validate_recommended_actions(self, value: list) -> list:
        """اعتبارسنجی اقدامات توصیه شده"""
        if not isinstance(value, list):
            raise serializers.ValidationError('اقدامات توصیه شده باید لیست باشد')
        return value
    
    def validate_red_flags(self, value: list) -> list:
        """اعتبارسنجی علائم هشدار"""
        if not isinstance(value, list):
            raise serializers.ValidationError('علائم هشدار باید لیست باشد')
        return value


class SessionSymptomSerializer(serializers.ModelSerializer):
    """
    سریالایزر علائم جلسه
    """
    symptom_name = serializers.CharField(source='symptom.name', read_only=True)
    symptom_category = serializers.CharField(source='symptom.category.name', read_only=True)
    
    class Meta:
        model = SessionSymptom
        fields = [
            'id', 'symptom', 'symptom_name', 'symptom_category',
            'severity', 'duration_hours', 'location', 'additional_details',
            'reported_at'
        ]
        read_only_fields = ['id', 'reported_at']
    
    def validate_severity(self, value: int) -> int:
        """اعتبارسنجی شدت"""
        if not 1 <= value <= 10:
            raise serializers.ValidationError('شدت باید بین 1 تا 10 باشد')
        return value
    
    def validate_duration_hours(self, value: int) -> int:
        """اعتبارسنجی مدت زمان"""
        if value is not None and value < 0:
            raise serializers.ValidationError('مدت زمان نمی‌تواند منفی باشد')
        return value


class SessionDiagnosisSerializer(serializers.ModelSerializer):
    """
    سریالایزر تشخیص‌های جلسه
    """
    diagnosis_name = serializers.CharField(source='diagnosis.name', read_only=True)
    diagnosis_urgency = serializers.IntegerField(source='diagnosis.urgency_level', read_only=True)
    
    class Meta:
        model = SessionDiagnosis
        fields = [
            'id', 'diagnosis', 'diagnosis_name', 'diagnosis_urgency',
            'probability_score', 'confidence_level', 'reasoning',
            'suggested_at'
        ]
        read_only_fields = ['id', 'suggested_at']
    
    def validate_probability_score(self, value: float) -> float:
        """اعتبارسنجی امتیاز احتمال"""
        if not 0.0 <= value <= 1.0:
            raise serializers.ValidationError('امتیاز احتمال باید بین 0.0 تا 1.0 باشد')
        return value
    
    def validate_confidence_level(self, value: int) -> int:
        """اعتبارسنجی سطح اطمینان"""
        if not 1 <= value <= 5:
            raise serializers.ValidationError('سطح اطمینان باید بین 1 تا 5 باشد')
        return value


class TriageSessionListSerializer(serializers.ModelSerializer):
    """
    سریالایزر لیست جلسات تریاژ (خلاصه)
    """
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    duration_minutes = serializers.SerializerMethodField()
    
    class Meta:
        model = TriageSession
        fields = [
            'id', 'patient_name', 'chief_complaint', 'status',
            'urgency_level', 'requires_immediate_attention',
            'started_at', 'completed_at', 'duration_minutes'
        ]
    
    def get_duration_minutes(self, obj) -> int:
        """محاسبه مدت زمان به دقیقه"""
        return int(obj.duration.total_seconds() // 60)


class TriageSessionCreateSerializer(serializers.ModelSerializer):
    """
    سریالایزر ایجاد جلسه تریاژ
    """
    
    class Meta:
        model = TriageSession
        fields = [
            'chief_complaint', 'reported_symptoms'
        ]
    
    def validate_chief_complaint(self, value: str) -> str:
        """اعتبارسنجی شکایت اصلی"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError('شکایت اصلی باید حداقل 10 کاراکتر باشد')
        return value.strip()
    
    def validate_reported_symptoms(self, value: list) -> list:
        """اعتبارسنجی علائم گزارش شده"""
        if not isinstance(value, list):
            raise serializers.ValidationError('علائم گزارش شده باید لیست باشد')
        return value
    
    def create(self, validated_data):
        """ایجاد جلسه تریاژ جدید"""
        user = self.context['request'].user
        validated_data['patient'] = user
        return super().create(validated_data)


class TriageSessionDetailSerializer(serializers.ModelSerializer):
    """
    سریالایزر جزئیات جلسه تریاژ
    """
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    identified_symptoms = SessionSymptomSerializer(
        source='sessionsymptom_set',
        many=True,
        read_only=True
    )
    preliminary_diagnoses = SessionDiagnosisSerializer(
        source='sessiondiagnosis_set',
        many=True,
        read_only=True
    )
    completed_by_name = serializers.CharField(
        source='completed_by.get_full_name',
        read_only=True
    )
    duration_minutes = serializers.SerializerMethodField()
    
    class Meta:
        model = TriageSession
        fields = [
            'id', 'patient_name', 'chief_complaint', 'reported_symptoms',
            'identified_symptoms', 'status', 'urgency_level',
            'preliminary_diagnoses', 'recommended_actions',
            'red_flags_detected', 'triage_notes', 'ai_confidence_score',
            'requires_immediate_attention', 'estimated_wait_time',
            'completed_by_name', 'started_at', 'completed_at',
            'duration_minutes', 'metadata'
        ]
        read_only_fields = [
            'id', 'patient_name', 'identified_symptoms',
            'preliminary_diagnoses', 'completed_by_name',
            'started_at', 'duration_minutes'
        ]
    
    def get_duration_minutes(self, obj) -> int:
        """محاسبه مدت زمان به دقیقه"""
        return int(obj.duration.total_seconds() // 60)
    
    def validate_urgency_level(self, value: int) -> int:
        """اعتبارسنجی سطح اورژانس"""
        if value is not None and not 1 <= value <= 5:
            raise serializers.ValidationError('سطح اورژانس باید بین 1 تا 5 باشد')
        return value
    
    def validate_ai_confidence_score(self, value: float) -> float:
        """اعتبارسنجی امتیاز اطمینان هوش مصنوعی"""
        if value is not None and not 0.0 <= value <= 1.0:
            raise serializers.ValidationError('امتیاز اطمینان باید بین 0.0 تا 1.0 باشد')
        return value


class TriageSessionUpdateSerializer(serializers.ModelSerializer):
    """
    سریالایزر به‌روزرسانی جلسه تریاژ
    """
    
    class Meta:
        model = TriageSession
        fields = [
            'status', 'urgency_level', 'recommended_actions',
            'red_flags_detected', 'triage_notes', 'ai_confidence_score',
            'requires_immediate_attention', 'estimated_wait_time'
        ]
    
    def validate_status(self, value: str) -> str:
        """اعتبارسنجی وضعیت"""
        valid_statuses = ['started', 'in_progress', 'completed', 'cancelled', 'escalated']
        if value not in valid_statuses:
            raise serializers.ValidationError(f'وضعیت باید یکی از {valid_statuses} باشد')
        return value


class AddSymptomToSessionSerializer(serializers.Serializer):
    """
    سریالایزر افزودن علامت به جلسه
    """
    symptom_id = serializers.UUIDField()
    severity = serializers.IntegerField(min_value=1, max_value=10)
    duration_hours = serializers.IntegerField(required=False, min_value=0)
    location = serializers.CharField(required=False, max_length=100)
    additional_details = serializers.CharField(required=False)
    
    def validate_symptom_id(self, value):
        """اعتبارسنجی شناسه علامت"""
        try:
            symptom = Symptom.objects.get(id=value, is_active=True)
            return value
        except Symptom.DoesNotExist:
            raise serializers.ValidationError('علامت یافت نشد یا غیرفعال است')


class TriageRuleSerializer(serializers.ModelSerializer):
    """
    سریالایزر قوانین تریاژ
    """
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = TriageRule
        fields = [
            'id', 'name', 'description', 'conditions', 'actions',
            'priority', 'is_active', 'created_at', 'updated_at',
            'created_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by_name']
    
    def validate_priority(self, value: int) -> int:
        """اعتبارسنجی اولویت"""
        if not 1 <= value <= 10:
            raise serializers.ValidationError('اولویت باید بین 1 تا 10 باشد')
        return value
    
    def validate_conditions(self, value: dict) -> dict:
        """اعتبارسنجی شرایط"""
        if not isinstance(value, dict):
            raise serializers.ValidationError('شرایط باید دیکشنری باشد')
        return value
    
    def validate_actions(self, value: dict) -> dict:
        """اعتبارسنجی اقدامات"""
        if not isinstance(value, dict):
            raise serializers.ValidationError('اقدامات باید دیکشنری باشد')
        return value
    
    def create(self, validated_data):
        """ایجاد قانون جدید"""
        user = self.context['request'].user
        validated_data['created_by'] = user
        return super().create(validated_data)


class TriageAnalysisSerializer(serializers.Serializer):
    """
    سریالایزر تحلیل تریاژ
    """
    symptoms = serializers.ListField(
        child=serializers.CharField(),
        help_text='لیست علائم برای تحلیل'
    )
    severity_scores = serializers.DictField(
        child=serializers.IntegerField(min_value=1, max_value=10),
        required=False,
        help_text='امتیاز شدت برای هر علامت'
    )
    patient_age = serializers.IntegerField(required=False, min_value=0, max_value=120)
    patient_gender = serializers.ChoiceField(
        choices=[('male', 'مرد'), ('female', 'زن')],
        required=False
    )
    medical_history = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text='سابقه پزشکی'
    )
    
    def validate_symptoms(self, value: list) -> list:
        """اعتبارسنجی علائم"""
        if not value:
            raise serializers.ValidationError('حداقل یک علامت باید وارد شود')
        return value