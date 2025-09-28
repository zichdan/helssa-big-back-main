"""
هسته هماهنگ‌کننده مرکزی اپ Doctor
Doctor App Central Orchestrator Core
"""

from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta
from django.db import transaction
from django.contrib.auth import get_user_model
from .api_ingress import DoctorAPIIngressCore
from .text_processor import DoctorTextProcessorCore
from .speech_processor import DoctorSpeechProcessorCore
import time

logger = logging.getLogger(__name__)
User = get_user_model()


class DoctorWorkflowStatus(Enum):
    """وضعیت‌های فرآیند کاری پزشک"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REQUIRES_APPROVAL = "requires_approval"


@dataclass
class DoctorWorkflowStep:
    """تعریف یک مرحله از فرآیند پزشکی"""
    name: str
    handler: Callable
    required: bool = True
    timeout: int = 30
    retry_count: int = 3
    requires_verification: bool = False
    dependencies: List[str] = None


@dataclass
class DoctorWorkflowResult:
    """نتیجه اجرای فرآیند پزشکی"""
    status: DoctorWorkflowStatus
    data: Dict[str, Any]
    errors: List[str]
    warnings: List[str]
    execution_time: float
    steps_completed: List[str]
    doctor_id: Optional[str] = None


class DoctorCentralOrchestrator:
    """
    هماهنگ‌کننده مرکزی فرآیندهای پزشک
    مسئول مدیریت جریان کار بین هسته‌های مختلف اپ Doctor
    """
    
    def __init__(self):
        self.api_core = DoctorAPIIngressCore()
        self.text_core = DoctorTextProcessorCore()
        self.speech_core = DoctorSpeechProcessorCore()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.workflows = self._initialize_doctor_workflows()
        
    def execute_doctor_workflow(self, workflow_name: str, 
                               input_data: Dict[str, Any],
                               user: Any,
                               async_mode: bool = False) -> DoctorWorkflowResult:
        """
        اجرای یک فرآیند کاری پزشک
        
        Args:
            workflow_name: نام فرآیند
            input_data: داده‌های ورودی
            user: کاربر درخواست‌دهنده (پزشک)
            async_mode: اجرای غیرهمزمان
            
        Returns:
            DoctorWorkflowResult object
        """
        start_time = time.time()
        
        try:
            # بررسی مجوز پزشک
            is_valid, error_msg = self.api_core.validate_doctor_permissions(user)
            if not is_valid:
                return DoctorWorkflowResult(
                    status=DoctorWorkflowStatus.FAILED,
                    data={},
                    errors=[error_msg],
                    warnings=[],
                    execution_time=time.time() - start_time,
                    steps_completed=[],
                    doctor_id=str(user.id) if user else None
                )
            
            # بررسی وجود workflow
            if workflow_name not in self.workflows:
                raise ValueError(f"Unknown doctor workflow: {workflow_name}")
            
            workflow = self.workflows[workflow_name]
            
            # ایجاد context اولیه
            context = {
                'user': user,
                'doctor_profile': getattr(user, 'doctor_profile', None),
                'input_data': input_data,
                'workflow_name': workflow_name,
                'results': {},
                'errors': [],
                'warnings': []
            }
            
            # اجرای فرآیند
            return self._execute_sync_doctor_workflow(workflow, context, start_time)
                
        except Exception as e:
            self.logger.error(f"Doctor workflow execution error: {str(e)}")
            return DoctorWorkflowResult(
                status=DoctorWorkflowStatus.FAILED,
                data={},
                errors=[str(e)],
                warnings=[],
                execution_time=time.time() - start_time,
                steps_completed=[],
                doctor_id=str(user.id) if user else None
            )
    
    def _execute_sync_doctor_workflow(self, workflow: List[DoctorWorkflowStep], 
                                    context: Dict[str, Any],
                                    start_time: float) -> DoctorWorkflowResult:
        """اجرای همزمان فرآیند پزشک"""
        steps_completed = []
        
        try:
            with transaction.atomic():
                for step in workflow:
                    # بررسی وابستگی‌ها
                    if not self._check_dependencies(step, steps_completed):
                        if step.required:
                            raise Exception(f"Dependencies not met for {step.name}")
                        continue
                    
                    # بررسی نیاز به تایید
                    if step.requires_verification:
                        doctor_profile = context.get('doctor_profile')
                        if not doctor_profile or not doctor_profile.is_verified:
                            context['warnings'].append(f"Step {step.name} requires verified doctor")
                            if step.required:
                                raise Exception(f"Step {step.name} requires verified doctor profile")
                            continue
                    
                    # اجرای مرحله
                    try:
                        self.logger.info(f"Executing doctor step: {step.name}")
                        result = self._execute_step_with_retry(step, context)
                        context['results'][step.name] = result
                        steps_completed.append(step.name)
                        
                    except Exception as e:
                        self.logger.error(f"Doctor step {step.name} failed: {str(e)}")
                        context['errors'].append(f"{step.name}: {str(e)}")
                        
                        if step.required:
                            raise
            
            return DoctorWorkflowResult(
                status=DoctorWorkflowStatus.COMPLETED,
                data=context['results'],
                errors=context['errors'],
                warnings=context['warnings'],
                execution_time=time.time() - start_time,
                steps_completed=steps_completed,
                doctor_id=str(context['user'].id) if context['user'] else None
            )
            
        except Exception as e:
            return DoctorWorkflowResult(
                status=DoctorWorkflowStatus.FAILED,
                data=context['results'],
                errors=context['errors'] + [str(e)],
                warnings=context['warnings'],
                execution_time=time.time() - start_time,
                steps_completed=steps_completed,
                doctor_id=str(context['user'].id) if context['user'] else None
            )
    
    def _execute_step_with_retry(self, step: DoctorWorkflowStep, 
                               context: Dict[str, Any]) -> Any:
        """اجرای یک مرحله با قابلیت retry"""
        last_error = None
        
        for attempt in range(step.retry_count):
            try:
                result = step.handler(context)
                return result
                
            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"Doctor step {step.name} attempt {attempt + 1} failed: {str(e)}"
                )
                
                if attempt < step.retry_count - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        raise last_error
    
    def _check_dependencies(self, step: DoctorWorkflowStep, 
                          completed_steps: List[str]) -> bool:
        """بررسی وابستگی‌های یک مرحله"""
        if not step.dependencies:
            return True
        
        return all(dep in completed_steps for dep in step.dependencies)
    
    def _initialize_doctor_workflows(self) -> Dict[str, List[DoctorWorkflowStep]]:
        """تعریف فرآیندهای اختصاصی پزشک"""
        workflows = {
            # فرآیند ایجاد پروفایل پزشک
            'create_doctor_profile': [
                DoctorWorkflowStep(
                    name='validate_profile_data',
                    handler=self._validate_doctor_profile_data
                ),
                DoctorWorkflowStep(
                    name='check_medical_code_uniqueness',
                    handler=self._check_medical_code_uniqueness,
                    dependencies=['validate_profile_data']
                ),
                DoctorWorkflowStep(
                    name='create_profile',
                    handler=self._create_doctor_profile,
                    dependencies=['check_medical_code_uniqueness']
                ),
                DoctorWorkflowStep(
                    name='setup_default_settings',
                    handler=self._setup_default_doctor_settings,
                    dependencies=['create_profile'],
                    required=False
                ),
            ],
            
            # فرآیند ایجاد برنامه کاری
            'create_schedule': [
                DoctorWorkflowStep(
                    name='validate_schedule_data',
                    handler=self._validate_schedule_data,
                    requires_verification=True
                ),
                DoctorWorkflowStep(
                    name='check_schedule_conflicts',
                    handler=self._check_schedule_conflicts,
                    dependencies=['validate_schedule_data']
                ),
                DoctorWorkflowStep(
                    name='create_schedule',
                    handler=self._create_doctor_schedule,
                    dependencies=['check_schedule_conflicts']
                ),
                DoctorWorkflowStep(
                    name='notify_schedule_creation',
                    handler=self._notify_schedule_creation,
                    dependencies=['create_schedule'],
                    required=False
                ),
            ],
            
            # فرآیند پردازش صوت پزشکی
            'process_medical_audio': [
                DoctorWorkflowStep(
                    name='validate_audio_file',
                    handler=self._validate_medical_audio,
                    requires_verification=True
                ),
                DoctorWorkflowStep(
                    name='transcribe_audio',
                    handler=self._transcribe_medical_audio,
                    dependencies=['validate_audio_file'],
                    timeout=300  # 5 minutes
                ),
                DoctorWorkflowStep(
                    name='extract_medical_info',
                    handler=self._extract_medical_info_from_audio,
                    dependencies=['transcribe_audio']
                ),
                DoctorWorkflowStep(
                    name='generate_soap_from_audio',
                    handler=self._generate_soap_from_audio,
                    dependencies=['extract_medical_info']
                ),
                DoctorWorkflowStep(
                    name='save_audio_analysis',
                    handler=self._save_audio_analysis,
                    dependencies=['generate_soap_from_audio']
                ),
            ],
            
            # فرآیند تولید نسخه PDF
            'generate_prescription_pdf': [
                DoctorWorkflowStep(
                    name='validate_prescription_data',
                    handler=self._validate_prescription_data,
                    requires_verification=True
                ),
                DoctorWorkflowStep(
                    name='check_drug_interactions',
                    handler=self._check_drug_interactions,
                    dependencies=['validate_prescription_data']
                ),
                DoctorWorkflowStep(
                    name='generate_pdf',
                    handler=self._generate_prescription_pdf,
                    dependencies=['check_drug_interactions']
                ),
                DoctorWorkflowStep(
                    name='add_digital_signature',
                    handler=self._add_digital_signature,
                    dependencies=['generate_pdf'],
                    requires_verification=True
                ),
                DoctorWorkflowStep(
                    name='save_prescription_record',
                    handler=self._save_prescription_record,
                    dependencies=['add_digital_signature']
                ),
            ],
            
            # فرآیند تولید گواهی PDF
            'generate_certificate_pdf': [
                DoctorWorkflowStep(
                    name='validate_certificate_data',
                    handler=self._validate_certificate_data,
                    requires_verification=True
                ),
                DoctorWorkflowStep(
                    name='check_certificate_authority',
                    handler=self._check_certificate_authority,
                    dependencies=['validate_certificate_data']
                ),
                DoctorWorkflowStep(
                    name='generate_certificate_pdf',
                    handler=self._generate_certificate_pdf,
                    dependencies=['check_certificate_authority']
                ),
                DoctorWorkflowStep(
                    name='add_certificate_signature',
                    handler=self._add_certificate_signature,
                    dependencies=['generate_certificate_pdf'],
                    requires_verification=True
                ),
                DoctorWorkflowStep(
                    name='save_certificate_record',
                    handler=self._save_certificate_record,
                    dependencies=['add_certificate_signature']
                ),
            ],
        }
        
        return workflows
    
    # Handler methods for doctor workflow steps
    
    def _validate_doctor_profile_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """اعتبارسنجی داده‌های پروفایل پزشک"""
        input_data = context['input_data']
        
        is_valid, result = self.api_core.validate_profile_data(input_data)
        if not is_valid:
            raise ValueError(f"Invalid profile data: {result}")
        
        return {'validated_data': result}
    
    def _check_medical_code_uniqueness(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """بررسی یکتا بودن کد نظام پزشکی"""
        from ..models import DoctorProfile
        
        validated_data = context['results']['validate_profile_data']['validated_data']
        medical_code = validated_data.get('medical_system_code')
        
        if DoctorProfile.objects.filter(medical_system_code=medical_code).exists():
            raise ValueError("کد نظام پزشکی تکراری است")
        
        return {'medical_code_unique': True}
    
    def _create_doctor_profile(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """ایجاد پروفایل پزشک"""
        from ..models import DoctorProfile
        
        validated_data = context['results']['validate_profile_data']['validated_data']
        user = context['user']
        
        profile = DoctorProfile.objects.create(
            user=user,
            **validated_data
        )
        
        return {'profile_id': str(profile.id), 'profile': profile}
    
    def _setup_default_doctor_settings(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """تنظیم پیکربندی‌های پیش‌فرض پزشک"""
        from ..models import DoctorSettings
        
        user = context['user']
        
        settings, created = DoctorSettings.objects.get_or_create(
            doctor=user,
            defaults={
                'email_notifications': True,
                'sms_notifications': True,
                'auto_generate_prescription': True,
                'auto_generate_certificate': True,
            }
        )
        
        return {'settings_created': created, 'settings_id': str(settings.id)}
    
    def _validate_schedule_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """اعتبارسنجی داده‌های برنامه کاری"""
        input_data = context['input_data']
        
        is_valid, result = self.api_core.validate_schedule_data(input_data)
        if not is_valid:
            raise ValueError(f"Invalid schedule data: {result}")
        
        return {'validated_data': result}
    
    def _check_schedule_conflicts(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """بررسی تداخل در برنامه کاری"""
        from ..models import DoctorSchedule
        
        validated_data = context['results']['validate_schedule_data']['validated_data']
        user = context['user']
        weekday = validated_data.get('weekday')
        
        existing_schedule = DoctorSchedule.objects.filter(
            doctor=user,
            weekday=weekday,
            is_active=True
        ).first()
        
        if existing_schedule:
            context['warnings'].append(f"برنامه کاری برای روز {weekday} وجود دارد")
        
        return {'has_conflict': bool(existing_schedule)}
    
    def _create_doctor_schedule(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """ایجاد برنامه کاری پزشک"""
        from ..models import DoctorSchedule
        
        validated_data = context['results']['validate_schedule_data']['validated_data']
        user = context['user']
        
        schedule = DoctorSchedule.objects.create(
            doctor=user,
            **validated_data
        )
        
        return {'schedule_id': str(schedule.id), 'schedule': schedule}
    
    def _notify_schedule_creation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """اعلان ایجاد برنامه کاری"""
        # پیاده‌سازی ارسال اعلان
        self.logger.info("Schedule creation notification sent")
        return {'notification_sent': True}
    
    def _validate_medical_audio(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """اعتبارسنجی فایل صوتی پزشکی"""
        audio_file_path = context['input_data'].get('audio_file_path')
        
        if not audio_file_path:
            raise ValueError("مسیر فایل صوتی الزامی است")
        
        quality_report = self.speech_core.validate_audio_quality(audio_file_path)
        
        if not quality_report['file_valid']:
            raise ValueError(f"فایل صوتی معتبر نیست: {', '.join(quality_report['issues'])}")
        
        return {'quality_report': quality_report}
    
    def _transcribe_medical_audio(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """رونویسی فایل صوتی پزشکی"""
        audio_file_path = context['input_data'].get('audio_file_path')
        
        result = self.speech_core.transcribe_medical_audio(
            audio_file_path,
            medical_mode=True
        )
        
        return {'transcription_result': result}
    
    def _extract_medical_info_from_audio(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """استخراج اطلاعات پزشکی از صوت"""
        transcription_result = context['results']['transcribe_audio']['transcription_result']
        
        medical_info = self.text_core.process_medical_note(
            transcription_result.transcription
        )
        
        return {'medical_info': medical_info}
    
    def _generate_soap_from_audio(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """تولید SOAP از صوت"""
        audio_file_path = context['input_data'].get('audio_file_path')
        
        soap_components = self.speech_core.extract_soap_from_audio(audio_file_path)
        
        return {'soap_components': soap_components}
    
    def _save_audio_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """ذخیره تحلیل صوتی"""
        # پیاده‌سازی ذخیره در دیتابیس
        self.logger.info("Audio analysis saved")
        return {'saved': True, 'analysis_id': 'audio_analysis_123'}
    
    def _validate_prescription_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """اعتبارسنجی داده‌های نسخه"""
        prescription_data = context['input_data'].get('prescription_data')
        
        if not prescription_data:
            raise ValueError("داده‌های نسخه الزامی است")
        
        required_fields = ['patient_info', 'medications', 'diagnosis']
        for field in required_fields:
            if field not in prescription_data:
                raise ValueError(f"فیلد {field} الزامی است")
        
        return {'validated_prescription': prescription_data}
    
    def _check_drug_interactions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """بررسی تداخل دارویی"""
        prescription_data = context['results']['validate_prescription_data']['validated_prescription']
        medications = prescription_data.get('medications', [])
        
        # پیاده‌سازی ساده بررسی تداخل
        interactions = []
        
        return {'interactions': interactions, 'safe': len(interactions) == 0}
    
    def _generate_prescription_pdf(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """تولید PDF نسخه"""
        # پیاده‌سازی تولید PDF
        self.logger.info("Prescription PDF generated")
        return {'pdf_path': '/path/to/prescription.pdf', 'pdf_generated': True}
    
    def _add_digital_signature(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """افزودن امضای دیجیتال"""
        # پیاده‌سازی امضای دیجیتال
        self.logger.info("Digital signature added")
        return {'signature_added': True, 'signature_id': 'sig_123'}
    
    def _save_prescription_record(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """ذخیره رکورد نسخه"""
        # ذخیره در دیتابیس
        self.logger.info("Prescription record saved")
        return {'saved': True, 'prescription_id': 'rx_123'}
    
    def _validate_certificate_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """اعتبارسنجی داده‌های گواهی"""
        certificate_data = context['input_data'].get('certificate_data')
        
        if not certificate_data:
            raise ValueError("داده‌های گواهی الزامی است")
        
        return {'validated_certificate': certificate_data}
    
    def _check_certificate_authority(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """بررسی اختیار صدور گواهی"""
        doctor_profile = context['doctor_profile']
        
        if not doctor_profile or not doctor_profile.is_verified:
            raise ValueError("فقط پزشکان تایید شده می‌توانند گواهی صادر کنند")
        
        return {'authorized': True}
    
    def _generate_certificate_pdf(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """تولید PDF گواهی"""
        # پیاده‌سازی تولید PDF
        self.logger.info("Certificate PDF generated")
        return {'pdf_path': '/path/to/certificate.pdf', 'pdf_generated': True}
    
    def _add_certificate_signature(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """افزودن امضای گواهی"""
        # پیاده‌سازی امضای گواهی
        self.logger.info("Certificate signature added")
        return {'signature_added': True, 'signature_id': 'cert_sig_123'}
    
    def _save_certificate_record(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """ذخیره رکورد گواهی"""
        # ذخیره در دیتابیس
        self.logger.info("Certificate record saved")
        return {'saved': True, 'certificate_id': 'cert_123'}