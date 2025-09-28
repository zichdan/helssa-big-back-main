"""
هسته Orchestrator برای سیستم مدیریت بیماران
Patient Management Orchestrator Core
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Callable
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction
from datetime import datetime, timedelta

from .api_ingress import PatientAPIIngress
from .text_processor import PatientTextProcessor
from .speech_processor import PatientSpeechProcessor

logger = logging.getLogger(__name__)


class PatientOrchestrator:
    """
    هسته هماهنگ‌کننده برای مدیریت جریان کار سیستم بیماران
    Orchestrator core for managing patient system workflows
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_ingress = PatientAPIIngress()
        self.text_processor = PatientTextProcessor()
        self.speech_processor = PatientSpeechProcessor()
        
        # تنظیمات workflow
        self.max_retry_attempts = 3
        self.workflow_timeout = 300  # 5 minutes
        self.cache_ttl = 3600  # 1 hour
        
        # رجیستر workflow handlers
        self.workflow_handlers = {
            'patient_registration': self._handle_patient_registration,
            'medical_record_creation': self._handle_medical_record_creation,
            'prescription_processing': self._handle_prescription_processing,
            'consent_management': self._handle_consent_management,
            'audio_transcription': self._handle_audio_transcription,
            'patient_search': self._handle_patient_search,
            'data_analysis': self._handle_data_analysis,
            'bulk_processing': self._handle_bulk_processing
        }
    
    async def orchestrate_workflow(
        self,
        workflow_type: str,
        workflow_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        هماهنگی اجرای workflow
        Orchestrate workflow execution
        
        Args:
            workflow_type: نوع workflow
            workflow_data: داده‌های ورودی
            context: اطلاعات محیطی (کاربر، درخواست، etc.)
            
        Returns:
            Dict: نتیجه اجرای workflow
        """
        workflow_id = self._generate_workflow_id()
        
        try:
            # ثبت شروع workflow
            await self._log_workflow_start(workflow_id, workflow_type, context)
            
            # اعتبارسنجی ورودی
            validation_result = await self._validate_workflow_input(
                workflow_type, workflow_data
            )
            if not validation_result['valid']:
                return await self._handle_workflow_error(
                    workflow_id, 'validation_failed', validation_result
                )
            
            # بررسی وجود handler
            if workflow_type not in self.workflow_handlers:
                return await self._handle_workflow_error(
                    workflow_id, 'unsupported_workflow', 
                    {'workflow_type': workflow_type}
                )
            
            # اجرای workflow
            workflow_result = await self._execute_workflow_with_retry(
                workflow_id, workflow_type, workflow_data, context
            )
            
            # ثبت نتیجه
            await self._log_workflow_completion(workflow_id, workflow_result)
            
            return {
                'success': True,
                'workflow_id': workflow_id,
                'workflow_type': workflow_type,
                'result': workflow_result,
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(
                f"Workflow orchestration error: {str(e)}",
                extra={
                    'workflow_id': workflow_id,
                    'workflow_type': workflow_type
                },
                exc_info=True
            )
            
            return await self._handle_workflow_error(
                workflow_id, 'execution_failed', {'error': str(e)}
            )
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        دریافت وضعیت workflow
        Get workflow status
        """
        try:
            workflow_data = cache.get(f"workflow:{workflow_id}")
            
            if not workflow_data:
                return {
                    'success': False,
                    'message': 'Workflow یافت نشد'
                }
            
            return {
                'success': True,
                'workflow_data': workflow_data
            }
            
        except Exception as e:
            self.logger.error(f"Error getting workflow status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def cancel_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        لغو workflow
        Cancel workflow
        """
        try:
            workflow_data = cache.get(f"workflow:{workflow_id}")
            
            if not workflow_data:
                return {
                    'success': False,
                    'message': 'Workflow یافت نشد'
                }
            
            # تنظیم وضعیت لغو
            workflow_data['status'] = 'cancelled'
            workflow_data['cancelled_at'] = timezone.now().isoformat()
            
            cache.set(f"workflow:{workflow_id}", workflow_data, timeout=self.cache_ttl)
            
            return {
                'success': True,
                'message': 'Workflow لغو شد'
            }
            
        except Exception as e:
            self.logger.error(f"Error cancelling workflow: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _execute_workflow_with_retry(
        self,
        workflow_id: str,
        workflow_type: str,
        workflow_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        اجرای workflow با قابلیت تلاش مجدد
        Execute workflow with retry capability
        """
        handler = self.workflow_handlers[workflow_type]
        last_error = None
        
        for attempt in range(self.max_retry_attempts):
            try:
                # بروزرسانی وضعیت
                await self._update_workflow_status(
                    workflow_id, 'running', f"تلاش {attempt + 1}"
                )
                
                # اجرای handler با timeout
                result = await asyncio.wait_for(
                    handler(workflow_data, context),
                    timeout=self.workflow_timeout
                )
                
                # در صورت موفقیت، خروج از حلقه
                await self._update_workflow_status(
                    workflow_id, 'completed', 'تکمیل شد'
                )
                
                return result
                
            except asyncio.TimeoutError:
                last_error = f"Timeout در تلاش {attempt + 1}"
                self.logger.warning(
                    f"Workflow timeout: {workflow_id}, attempt {attempt + 1}"
                )
                
            except Exception as e:
                last_error = str(e)
                self.logger.error(
                    f"Workflow error: {workflow_id}, attempt {attempt + 1}: {str(e)}"
                )
                
                # اگر خطای غیرقابل بازیابی است، متوقف شو
                if self._is_non_recoverable_error(e):
                    break
                
            # منتظر ماندن قبل از تلاش مجدد
            if attempt < self.max_retry_attempts - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # تمام تلاش‌ها ناموفق بود
        await self._update_workflow_status(
            workflow_id, 'failed', f"شکست بعد از {self.max_retry_attempts} تلاش"
        )
        
        raise Exception(f"Workflow failed after {self.max_retry_attempts} attempts: {last_error}")
    
    async def _handle_patient_registration(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        مدیریت فرآیند ثبت‌نام بیمار
        Handle patient registration workflow
        """
        try:
            # مرحله 1: اعتبارسنجی داده‌های بیمار
            patient_data = data.get('patient_data', {})
            
            # مرحله 2: پردازش اطلاعات شخصی
            processed_personal_data = await self._process_personal_information(
                patient_data
            )
            
            # مرحله 3: پردازش اطلاعات پزشکی (در صورت وجود)
            medical_history = data.get('medical_history', [])
            processed_medical_data = await self._process_medical_history_bulk(
                medical_history
            )
            
            # مرحله 4: ایجاد پروفایل بیمار
            from ..models import PatientProfile
            from ..serializers import PatientProfileCreateSerializer
            
            with transaction.atomic():
                serializer = PatientProfileCreateSerializer(data=processed_personal_data)
                if serializer.is_valid():
                    patient_profile = serializer.save()
                    
                    # ایجاد سوابق پزشکی
                    medical_records = []
                    if processed_medical_data:
                        medical_records = await self._create_medical_records(
                            patient_profile, processed_medical_data
                        )
                    
                    return {
                        'success': True,
                        'patient_id': str(patient_profile.id),
                        'medical_record_number': patient_profile.medical_record_number,
                        'medical_records_created': len(medical_records),
                        'message': 'بیمار با موفقیت ثبت شد'
                    }
                else:
                    return {
                        'success': False,
                        'errors': serializer.errors,
                        'message': 'خطا در اعتبارسنجی اطلاعات بیمار'
                    }
                    
        except Exception as e:
            self.logger.error(f"Patient registration error: {str(e)}")
            raise
    
    async def _handle_medical_record_creation(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        مدیریت فرآیند ایجاد سابقه پزشکی
        Handle medical record creation workflow
        """
        try:
            # پردازش متن سابقه پزشکی
            text_data = data.get('description', '')
            if text_data:
                text_analysis = await self.text_processor.process_patient_text(
                    text_data, 'medical_record'
                )
                
                # استخراج اطلاعات ساختاریافته
                extracted_info = text_analysis.get('specific_processing', {})
                
                # بروزرسانی داده‌ها با اطلاعات استخراج شده
                if extracted_info.get('record_type') and extracted_info['record_type'] != 'other':
                    data['record_type'] = extracted_info['record_type']
                
                # افزودن اطلاعات تحلیل به metadata
                data['analysis_metadata'] = {
                    'text_analysis': text_analysis,
                    'medical_entities': text_analysis.get('medical_analysis', {}).get('entities', {}),
                    'confidence_score': text_analysis.get('processing_metadata', {}).get('confidence_score', 0)
                }
            
            # ایجاد رکورد
            from ..models import MedicalRecord
            from ..serializers import MedicalRecordSerializer
            
            # اضافه کردن اطلاعات کاربر ایجادکننده
            if context and 'user' in context:
                data['created_by'] = context['user'].id
            
            serializer = MedicalRecordSerializer(data=data)
            if serializer.is_valid():
                medical_record = serializer.save()
                
                return {
                    'success': True,
                    'medical_record_id': str(medical_record.id),
                    'extracted_entities': data.get('analysis_metadata', {}).get('medical_entities', {}),
                    'message': 'سابقه پزشکی با موفقیت ایجاد شد'
                }
            else:
                return {
                    'success': False,
                    'errors': serializer.errors,
                    'message': 'خطا در اعتبارسنجی اطلاعات سابقه پزشکی'
                }
                
        except Exception as e:
            self.logger.error(f"Medical record creation error: {str(e)}")
            raise
    
    async def _handle_prescription_processing(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        مدیریت فرآیند پردازش نسخه
        Handle prescription processing workflow
        """
        try:
            # پردازش متن نسخه
            prescription_text = data.get('prescription_text', '')
            if prescription_text:
                standardized_prescription = await self.text_processor.standardize_prescription_text(
                    prescription_text
                )
                
                # استخراج اطلاعات نسخه
                prescription_data = standardized_prescription.get('prescription_data', {})
                
                # بروزرسانی داده‌های نسخه
                if prescription_data.get('medications'):
                    # اگر چندین دارو شناسایی شد، از اولی استفاده کن
                    first_medication = prescription_data['medications'][0]
                    data.update({
                        'medication_name': first_medication.get('name', data.get('medication_name', '')),
                        'dosage': first_medication.get('dosage', data.get('dosage', '')),
                        'frequency': first_medication.get('frequency', data.get('frequency', '')),
                        'duration': first_medication.get('duration', data.get('duration', ''))
                    })
                
                # افزودن metadata
                data['processing_metadata'] = {
                    'standardized_text': standardized_prescription.get('standardized_text', ''),
                    'confidence_score': standardized_prescription.get('confidence_score', 0),
                    'all_medications': prescription_data.get('medications', [])
                }
            
            # ایجاد نسخه
            from ..models import PrescriptionHistory
            from ..serializers import PrescriptionHistorySerializer
            
            # اضافه کردن اطلاعات پزشک تجویزکننده
            if context and 'user' in context:
                data['prescribed_by'] = context['user'].id
            
            serializer = PrescriptionHistorySerializer(data=data)
            if serializer.is_valid():
                prescription = serializer.save()
                
                return {
                    'success': True,
                    'prescription_id': str(prescription.id),
                    'prescription_number': prescription.prescription_number,
                    'can_repeat': prescription.can_repeat(),
                    'extracted_medications': data.get('processing_metadata', {}).get('all_medications', []),
                    'message': 'نسخه با موفقیت ثبت شد'
                }
            else:
                return {
                    'success': False,
                    'errors': serializer.errors,
                    'message': 'خطا در اعتبارسنجی اطلاعات نسخه'
                }
                
        except Exception as e:
            self.logger.error(f"Prescription processing error: {str(e)}")
            raise
    
    async def _handle_consent_management(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        مدیریت فرآیند رضایت‌نامه
        Handle consent management workflow
        """
        try:
            action = data.get('action', 'create')
            
            if action == 'create':
                return await self._create_consent(data, context)
            elif action == 'grant':
                return await self._grant_consent(data, context)
            elif action == 'revoke':
                return await self._revoke_consent(data, context)
            else:
                return {
                    'success': False,
                    'message': f'عمل {action} پشتیبانی نمی‌شود'
                }
                
        except Exception as e:
            self.logger.error(f"Consent management error: {str(e)}")
            raise
    
    async def _handle_audio_transcription(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        مدیریت فرآیند رونویسی صوت
        Handle audio transcription workflow
        """
        try:
            audio_file = data.get('audio_file')
            audio_format = data.get('audio_format', 'wav')
            processing_options = data.get('processing_options', {})
            
            if not audio_file:
                return {
                    'success': False,
                    'message': 'فایل صوتی ارائه نشده'
                }
            
            # پردازش صوت
            transcription_result = await self.speech_processor.process_patient_audio(
                audio_file, audio_format, processing_options
            )
            
            if transcription_result.get('success'):
                # ذخیره نتیجه در کش برای دسترسی بعدی
                transcription_id = self._generate_workflow_id()
                cache.set(
                    f"transcription:{transcription_id}",
                    transcription_result,
                    timeout=86400  # 24 hours
                )
                
                return {
                    'success': True,
                    'transcription_id': transcription_id,
                    'transcription': transcription_result['transcription'],
                    'medical_analysis': transcription_result['medical_analysis'],
                    'audio_metadata': transcription_result['audio_metadata'],
                    'message': 'رونویسی با موفقیت انجام شد'
                }
            else:
                return transcription_result
                
        except Exception as e:
            self.logger.error(f"Audio transcription error: {str(e)}")
            raise
    
    async def _handle_patient_search(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        مدیریت فرآیند جستجوی بیمار
        Handle patient search workflow
        """
        try:
            from ..models import PatientProfile
            from django.db.models import Q
            
            query = data.get('query', '').strip()
            search_type = data.get('search_type', 'all')
            
            if not query:
                return {
                    'success': False,
                    'message': 'متن جستجو خالی است'
                }
            
            # ساخت query بر اساس نوع جستجو
            if search_type == 'national_code':
                search_filter = Q(national_code__icontains=query)
            elif search_type == 'medical_record':
                search_filter = Q(medical_record_number__icontains=query)
            elif search_type == 'name':
                search_filter = (
                    Q(first_name__icontains=query) |
                    Q(last_name__icontains=query)
                )
            else:  # all
                search_filter = (
                    Q(first_name__icontains=query) |
                    Q(last_name__icontains=query) |
                    Q(national_code__icontains=query) |
                    Q(medical_record_number__icontains=query)
                )
            
            # اجرای جستجو
            patients = PatientProfile.objects.filter(
                search_filter
            ).filter(is_active=True)[:20]  # محدود به 20 نتیجه
            
            # سریالایز نتایج
            from ..serializers import PatientProfileSerializer
            results = PatientProfileSerializer(patients, many=True).data
            
            return {
                'success': True,
                'results': results,
                'count': len(results),
                'query': query,
                'search_type': search_type,
                'message': f'{len(results)} بیمار یافت شد'
            }
            
        except Exception as e:
            self.logger.error(f"Patient search error: {str(e)}")
            raise
    
    async def _handle_data_analysis(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        مدیریت فرآیند تحلیل داده‌ها
        Handle data analysis workflow
        """
        try:
            analysis_type = data.get('analysis_type', 'general')
            patient_ids = data.get('patient_ids', [])
            date_range = data.get('date_range', {})
            
            if analysis_type == 'patient_statistics':
                return await self._analyze_patient_statistics(patient_ids, date_range)
            elif analysis_type == 'medical_trends':
                return await self._analyze_medical_trends(patient_ids, date_range)
            elif analysis_type == 'prescription_analysis':
                return await self._analyze_prescriptions(patient_ids, date_range)
            else:
                return {
                    'success': False,
                    'message': f'نوع تحلیل {analysis_type} پشتیبانی نمی‌شود'
                }
                
        except Exception as e:
            self.logger.error(f"Data analysis error: {str(e)}")
            raise
    
    async def _handle_bulk_processing(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        مدیریت فرآیند پردازش انبوه
        Handle bulk processing workflow
        """
        try:
            operation_type = data.get('operation_type')
            items = data.get('items', [])
            
            if not items:
                return {
                    'success': False,
                    'message': 'هیچ آیتمی برای پردازش ارائه نشده'
                }
            
            results = []
            errors = []
            
            for i, item in enumerate(items):
                try:
                    # پردازش هر آیتم
                    if operation_type == 'medical_records':
                        result = await self._handle_medical_record_creation(item, context)
                    elif operation_type == 'prescriptions':
                        result = await self._handle_prescription_processing(item, context)
                    else:
                        result = {
                            'success': False,
                            'message': f'نوع عملیات {operation_type} پشتیبانی نمی‌شود'
                        }
                    
                    results.append({
                        'index': i,
                        'result': result
                    })
                    
                except Exception as e:
                    errors.append({
                        'index': i,
                        'error': str(e),
                        'item': item
                    })
            
            successful_count = sum(1 for r in results if r['result'].get('success'))
            
            return {
                'success': True,
                'total_items': len(items),
                'successful': successful_count,
                'failed': len(errors),
                'results': results,
                'errors': errors,
                'message': f'{successful_count} از {len(items)} آیتم با موفقیت پردازش شد'
            }
            
        except Exception as e:
            self.logger.error(f"Bulk processing error: {str(e)}")
            raise
    
    # Helper methods
    
    def _generate_workflow_id(self) -> str:
        """تولید شناسه workflow"""
        import uuid
        return f"wf_{uuid.uuid4().hex[:16]}"
    
    async def _validate_workflow_input(
        self,
        workflow_type: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """اعتبارسنجی ورودی workflow"""
        # اعتبارسنجی پایه
        if not isinstance(data, dict):
            return {
                'valid': False,
                'error': 'Invalid data format',
                'message': 'فرمت داده نامعتبر است'
            }
        
        # اعتبارسنجی خاص هر workflow
        required_fields = {
            'patient_registration': ['patient_data'],
            'medical_record_creation': ['patient', 'record_type', 'title'],
            'prescription_processing': ['patient', 'medication_name'],
            'consent_management': ['action'],
            'audio_transcription': ['audio_file'],
            'patient_search': ['query'],
            'data_analysis': ['analysis_type'],
            'bulk_processing': ['operation_type', 'items']
        }
        
        required = required_fields.get(workflow_type, [])
        missing_fields = [field for field in required if field not in data]
        
        if missing_fields:
            return {
                'valid': False,
                'error': 'Missing required fields',
                'message': f'فیلدهای الزامی موجود نیست: {", ".join(missing_fields)}'
            }
        
        return {'valid': True}
    
    async def _log_workflow_start(
        self,
        workflow_id: str,
        workflow_type: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """ثبت شروع workflow"""
        workflow_data = {
            'id': workflow_id,
            'type': workflow_type,
            'status': 'started',
            'started_at': timezone.now().isoformat(),
            'context': context or {},
            'attempts': 0
        }
        
        cache.set(f"workflow:{workflow_id}", workflow_data, timeout=self.cache_ttl)
        
        self.logger.info(
            f"Workflow started: {workflow_type}",
            extra={
                'workflow_id': workflow_id,
                'workflow_type': workflow_type,
                'user_id': context.get('user', {}).get('id') if context else None
            }
        )
    
    async def _update_workflow_status(
        self,
        workflow_id: str,
        status: str,
        message: Optional[str] = None
    ):
        """بروزرسانی وضعیت workflow"""
        workflow_data = cache.get(f"workflow:{workflow_id}")
        if workflow_data:
            workflow_data['status'] = status
            workflow_data['last_update'] = timezone.now().isoformat()
            if message:
                workflow_data['message'] = message
            
            cache.set(f"workflow:{workflow_id}", workflow_data, timeout=self.cache_ttl)
    
    async def _log_workflow_completion(
        self,
        workflow_id: str,
        result: Dict[str, Any]
    ):
        """ثبت تکمیل workflow"""
        workflow_data = cache.get(f"workflow:{workflow_id}")
        if workflow_data:
            workflow_data['status'] = 'completed'
            workflow_data['completed_at'] = timezone.now().isoformat()
            workflow_data['result'] = result
            
            cache.set(f"workflow:{workflow_id}", workflow_data, timeout=self.cache_ttl)
        
        self.logger.info(
            f"Workflow completed: {workflow_id}",
            extra={
                'workflow_id': workflow_id,
                'success': result.get('success', False)
            }
        )
    
    async def _handle_workflow_error(
        self,
        workflow_id: str,
        error_type: str,
        error_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """مدیریت خطای workflow"""
        await self._update_workflow_status(
            workflow_id, 'failed', f"خطا: {error_type}"
        )
        
        return {
            'success': False,
            'workflow_id': workflow_id,
            'error_type': error_type,
            'error_data': error_data,
            'timestamp': timezone.now().isoformat()
        }
    
    def _is_non_recoverable_error(self, exception: Exception) -> bool:
        """بررسی اینکه آیا خطا قابل بازیابی است یا نه"""
        non_recoverable_types = [
            ValueError,
            TypeError,
            AttributeError
        ]
        
        return any(isinstance(exception, error_type) for error_type in non_recoverable_types)
    
    # Additional helper methods for specific workflows
    
    async def _process_personal_information(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """پردازش اطلاعات شخصی"""
        # تمیز کردن و استانداردسازی
        if 'national_code' in data:
            data['national_code'] = ''.join(filter(str.isdigit, data['national_code']))
        
        if 'postal_code' in data:
            data['postal_code'] = ''.join(filter(str.isdigit, data['postal_code']))
        
        return data
    
    async def _process_medical_history_bulk(self, medical_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """پردازش انبوه سوابق پزشکی"""
        processed_records = []
        
        for record in medical_history:
            if 'description' in record:
                # پردازش متن توصیف
                text_analysis = await self.text_processor.process_patient_text(
                    record['description'], 'medical_record'
                )
                
                # بروزرسانی داده‌ها
                extracted_info = text_analysis.get('specific_processing', {})
                if extracted_info.get('record_type'):
                    record['record_type'] = extracted_info['record_type']
                
                record['analysis_metadata'] = text_analysis
            
            processed_records.append(record)
        
        return processed_records
    
    async def _create_medical_records(
        self,
        patient_profile,
        medical_data: List[Dict[str, Any]]
    ) -> List[Any]:
        """ایجاد سوابق پزشکی"""
        from ..models import MedicalRecord
        from ..serializers import MedicalRecordSerializer
        
        created_records = []
        
        for record_data in medical_data:
            record_data['patient'] = patient_profile.id
            
            serializer = MedicalRecordSerializer(data=record_data)
            if serializer.is_valid():
                medical_record = serializer.save()
                created_records.append(medical_record)
        
        return created_records
    
    async def _create_consent(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """ایجاد رضایت‌نامه"""
        from ..models import MedicalConsent
        from ..serializers import MedicalConsentSerializer
        
        if context and 'user' in context:
            data['requested_by'] = context['user'].id
        
        serializer = MedicalConsentSerializer(data=data)
        if serializer.is_valid():
            consent = serializer.save()
            
            return {
                'success': True,
                'consent_id': str(consent.id),
                'message': 'رضایت‌نامه ایجاد شد'
            }
        else:
            return {
                'success': False,
                'errors': serializer.errors
            }
    
    async def _grant_consent(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """ثبت رضایت"""
        from ..models import MedicalConsent
        
        consent_id = data.get('consent_id')
        digital_signature = data.get('digital_signature')
        
        try:
            consent = MedicalConsent.objects.get(id=consent_id)
            
            # دریافت اطلاعات کلاینت
            ip_address = context.get('ip_address', '0.0.0.0') if context else '0.0.0.0'
            user_agent = context.get('user_agent', '') if context else ''
            
            consent.grant_consent(digital_signature, ip_address, user_agent)
            
            return {
                'success': True,
                'message': 'رضایت ثبت شد'
            }
            
        except MedicalConsent.DoesNotExist:
            return {
                'success': False,
                'message': 'رضایت‌نامه یافت نشد'
            }
    
    async def _revoke_consent(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """لغو رضایت"""
        from ..models import MedicalConsent
        
        consent_id = data.get('consent_id')
        
        try:
            consent = MedicalConsent.objects.get(id=consent_id)
            consent.revoke_consent()
            
            return {
                'success': True,
                'message': 'رضایت لغو شد'
            }
            
        except MedicalConsent.DoesNotExist:
            return {
                'success': False,
                'message': 'رضایت‌نامه یافت نشد'
            }
    
    async def _analyze_patient_statistics(
        self,
        patient_ids: List[str],
        date_range: Dict[str, Any]
    ) -> Dict[str, Any]:
        """تحلیل آمار بیماران"""
        # پیاده‌سازی ساده - می‌تواند گسترش یابد
        return {
            'success': True,
            'statistics': {
                'total_patients': len(patient_ids),
                'analysis_period': date_range,
                'generated_at': timezone.now().isoformat()
            }
        }
    
    async def _analyze_medical_trends(
        self,
        patient_ids: List[str],
        date_range: Dict[str, Any]
    ) -> Dict[str, Any]:
        """تحلیل روندهای پزشکی"""
        return {
            'success': True,
            'trends': {
                'patients_analyzed': len(patient_ids),
                'period': date_range,
                'generated_at': timezone.now().isoformat()
            }
        }
    
    async def _analyze_prescriptions(
        self,
        patient_ids: List[str],
        date_range: Dict[str, Any]
    ) -> Dict[str, Any]:
        """تحلیل نسخه‌ها"""
        return {
            'success': True,
            'prescription_analysis': {
                'patients_analyzed': len(patient_ids),
                'period': date_range,
                'generated_at': timezone.now().isoformat()
            }
        }