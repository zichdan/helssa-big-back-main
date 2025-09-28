"""
ویوهای سیستم مدیریت بیماران
Patient Management System Views
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from .cores.orchestrator import PatientOrchestrator
from .cores.api_ingress import PatientAPIIngress
from .permissions import (
    PatientOnlyPermission,
    DoctorOnlyPermission,
    PatientOrDoctorPermission,
    MedicalRecordPermission,
    PrescriptionPermission,
    ConsentPermission
)
from .services import (
    PatientService,
    MedicalRecordService,
    PrescriptionService,
    ConsentService
)

User = get_user_model()
logger = logging.getLogger(__name__)


# ایجاد نمونه‌ها
orchestrator = PatientOrchestrator()
api_ingress = PatientAPIIngress()
patient_service = PatientService()
medical_record_service = MedicalRecordService()
prescription_service = PrescriptionService()
consent_service = ConsentService()


@api_view(['POST'])
@permission_classes([PatientOnlyPermission])
async def create_patient_profile(request):
    """
    ایجاد پروفایل بیمار جدید
    Create new patient profile
    
    POST /api/patient/profile/create/
    
    Request Body:
        - phone_number: شماره موبایل (required)
        - national_code: کد ملی (required)
        - first_name: نام (required)
        - last_name: نام خانوادگی (required)
        - birth_date: تاریخ تولد (required)
        - gender: جنسیت (required)
        - ... سایر فیلدها
    
    Returns:
        201: پروفایل با موفقیت ایجاد شد
        400: خطای validation
        403: عدم دسترسی
        500: خطای سرور
    """
    try:
        # پردازش درخواست ورودی
        success, processed_data = await api_ingress.process_incoming_request(
            request, 'patient_profile', request.data
        )
        
        if not success:
            return Response(
                await api_ingress.format_response(
                    processed_data, False, processed_data.get('message'),
                    status.HTTP_400_BAD_REQUEST
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # هماهنگی workflow
        workflow_result = await orchestrator.orchestrate_workflow(
            'patient_registration',
            {
                'patient_data': processed_data,
                'medical_history': request.data.get('medical_history', [])
            },
            {'user': request.user, 'request': request}
        )
        
        if workflow_result['success']:
            return Response(
                await api_ingress.format_response(
                    workflow_result['result'], True,
                    'پروفایل بیمار با موفقیت ایجاد شد',
                    status.HTTP_201_CREATED
                ),
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                await api_ingress.format_response(
                    workflow_result, False,
                    'خطا در ایجاد پروفایل بیمار',
                    status.HTTP_400_BAD_REQUEST
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Error in create_patient_profile: {str(e)}")
        return Response(
            await api_ingress.format_response(
                None, False, 'خطای سرور',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([PatientOrDoctorPermission])
async def get_patient_profile(request, patient_id):
    """
    دریافت پروفایل بیمار
    Get patient profile
    
    GET /api/patient/profile/{patient_id}/
    
    Query Parameters:
        - include_statistics: شامل آمار (optional)
    
    Returns:
        200: اطلاعات بیمار
        404: بیمار یافت نشد
        403: عدم دسترسی
    """
    try:
        # بررسی دسترسی
        has_access = await patient_service.validate_patient_access(
            request.user, patient_id, 'view'
        )
        
        if not has_access:
            return Response(
                await api_ingress.format_response(
                    None, False, 'عدم دسترسی',
                    status.HTTP_403_FORBIDDEN
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # دریافت پروفایل
        include_statistics = request.query_params.get('include_statistics', 'false').lower() == 'true'
        success, result = await patient_service.get_patient_profile(
            patient_id, include_statistics
        )
        
        if success:
            return Response(
                await api_ingress.format_response(
                    result, True, 'اطلاعات بیمار',
                    status.HTTP_200_OK
                ),
                status=status.HTTP_200_OK
            )
        else:
            error_status = (
                status.HTTP_404_NOT_FOUND 
                if result.get('error') == 'patient_not_found'
                else status.HTTP_400_BAD_REQUEST
            )
            return Response(
                await api_ingress.format_response(
                    result, False, result.get('message'),
                    error_status
                ),
                status=error_status
            )
            
    except Exception as e:
        logger.error(f"Error in get_patient_profile: {str(e)}")
        return Response(
            await api_ingress.format_response(
                None, False, 'خطای سرور',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT', 'PATCH'])
@permission_classes([PatientOrDoctorPermission])
async def update_patient_profile(request, patient_id):
    """
    بروزرسانی پروفایل بیمار
    Update patient profile
    
    PUT/PATCH /api/patient/profile/{patient_id}/
    """
    try:
        # بررسی دسترسی
        has_access = await patient_service.validate_patient_access(
            request.user, patient_id, 'update'
        )
        
        if not has_access:
            return Response(
                await api_ingress.format_response(
                    None, False, 'عدم دسترسی',
                    status.HTTP_403_FORBIDDEN
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # پردازش درخواست
        success, processed_data = await api_ingress.process_incoming_request(
            request, 'patient_profile', request.data
        )
        
        if not success:
            return Response(
                await api_ingress.format_response(
                    processed_data, False, processed_data.get('message'),
                    status.HTTP_400_BAD_REQUEST
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # بروزرسانی
        success, result = await patient_service.update_patient_profile(
            patient_id, processed_data, request.user
        )
        
        if success:
            return Response(
                await api_ingress.format_response(
                    result, True, 'پروفایل بیمار بروزرسانی شد',
                    status.HTTP_200_OK
                ),
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                await api_ingress.format_response(
                    result, False, result.get('message'),
                    status.HTTP_400_BAD_REQUEST
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Error in update_patient_profile: {str(e)}")
        return Response(
            await api_ingress.format_response(
                None, False, 'خطای سرور',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([DoctorOnlyPermission])
async def search_patients(request):
    """
    جستجوی بیماران
    Search patients
    
    POST /api/patient/search/
    
    Request Body:
        - query: متن جستجو (required)
        - search_type: نوع جستجو (optional)
    """
    try:
        # هماهنگی workflow
        workflow_result = await orchestrator.orchestrate_workflow(
            'patient_search',
            request.data,
            {'user': request.user}
        )
        
        if workflow_result['success']:
            return Response(
                await api_ingress.format_response(
                    workflow_result['result'], True,
                    workflow_result['result'].get('message'),
                    status.HTTP_200_OK
                ),
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                await api_ingress.format_response(
                    workflow_result, False,
                    'خطا در جستجوی بیماران',
                    status.HTTP_400_BAD_REQUEST
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Error in search_patients: {str(e)}")
        return Response(
            await api_ingress.format_response(
                None, False, 'خطای سرور',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Medical Records Views

@api_view(['POST'])
@permission_classes([DoctorOnlyPermission])
async def create_medical_record(request):
    """
    ایجاد سابقه پزشکی جدید
    Create new medical record
    
    POST /api/patient/medical-records/
    """
    try:
        # پردازش درخواست
        success, processed_data = await api_ingress.process_incoming_request(
            request, 'medical_record', request.data
        )
        
        if not success:
            return Response(
                await api_ingress.format_response(
                    processed_data, False, processed_data.get('message'),
                    status.HTTP_400_BAD_REQUEST
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # هماهنگی workflow
        workflow_result = await orchestrator.orchestrate_workflow(
            'medical_record_creation',
            processed_data,
            {'user': request.user}
        )
        
        if workflow_result['success']:
            return Response(
                await api_ingress.format_response(
                    workflow_result['result'], True,
                    'سابقه پزشکی ایجاد شد',
                    status.HTTP_201_CREATED
                ),
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                await api_ingress.format_response(
                    workflow_result, False,
                    'خطا در ایجاد سابقه پزشکی',
                    status.HTTP_400_BAD_REQUEST
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Error in create_medical_record: {str(e)}")
        return Response(
            await api_ingress.format_response(
                None, False, 'خطای سرور',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([MedicalRecordPermission])
async def get_patient_medical_records(request, patient_id):
    """
    دریافت سوابق پزشکی بیمار
    Get patient medical records
    
    GET /api/patient/{patient_id}/medical-records/
    """
    try:
        # بررسی دسترسی
        has_access = await patient_service.validate_patient_access(
            request.user, patient_id, 'view'
        )
        
        if not has_access:
            return Response(
                await api_ingress.format_response(
                    None, False, 'عدم دسترسی',
                    status.HTTP_403_FORBIDDEN
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # دریافت سوابق
        record_type = request.query_params.get('record_type')
        success, result = await medical_record_service.get_patient_medical_records(
            patient_id, record_type
        )
        
        if success:
            return Response(
                await api_ingress.format_response(
                    result, True, 'سوابق پزشکی بیمار',
                    status.HTTP_200_OK
                ),
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                await api_ingress.format_response(
                    result, False, result.get('message'),
                    status.HTTP_400_BAD_REQUEST
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Error in get_patient_medical_records: {str(e)}")
        return Response(
            await api_ingress.format_response(
                None, False, 'خطای سرور',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Prescription Views

@api_view(['POST'])
@permission_classes([DoctorOnlyPermission])
async def create_prescription(request):
    """
    ایجاد نسخه جدید
    Create new prescription
    
    POST /api/patient/prescriptions/
    """
    try:
        # پردازش درخواست
        success, processed_data = await api_ingress.process_incoming_request(
            request, 'prescription', request.data
        )
        
        if not success:
            return Response(
                await api_ingress.format_response(
                    processed_data, False, processed_data.get('message'),
                    status.HTTP_400_BAD_REQUEST
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # هماهنگی workflow
        workflow_result = await orchestrator.orchestrate_workflow(
            'prescription_processing',
            processed_data,
            {'user': request.user}
        )
        
        if workflow_result['success']:
            return Response(
                await api_ingress.format_response(
                    workflow_result['result'], True,
                    'نسخه ایجاد شد',
                    status.HTTP_201_CREATED
                ),
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                await api_ingress.format_response(
                    workflow_result, False,
                    'خطا در ایجاد نسخه',
                    status.HTTP_400_BAD_REQUEST
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Error in create_prescription: {str(e)}")
        return Response(
            await api_ingress.format_response(
                None, False, 'خطای سرور',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([PrescriptionPermission])
async def get_patient_prescriptions(request, patient_id):
    """
    دریافت نسخه‌های بیمار
    Get patient prescriptions
    
    GET /api/patient/{patient_id}/prescriptions/
    """
    try:
        # بررسی دسترسی
        has_access = await patient_service.validate_patient_access(
            request.user, patient_id, 'view'
        )
        
        if not has_access:
            return Response(
                await api_ingress.format_response(
                    None, False, 'عدم دسترسی',
                    status.HTTP_403_FORBIDDEN
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # دریافت نسخه‌ها
        prescription_status = request.query_params.get('status')
        include_expired = request.query_params.get('include_expired', 'false').lower() == 'true'
        
        success, result = await prescription_service.get_patient_prescriptions(
            patient_id, prescription_status, include_expired
        )
        
        if success:
            return Response(
                await api_ingress.format_response(
                    result, True, 'نسخه‌های بیمار',
                    status.HTTP_200_OK
                ),
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                await api_ingress.format_response(
                    result, False, result.get('message'),
                    status.HTTP_400_BAD_REQUEST
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Error in get_patient_prescriptions: {str(e)}")
        return Response(
            await api_ingress.format_response(
                None, False, 'خطای سرور',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([DoctorOnlyPermission])
async def repeat_prescription(request, prescription_id):
    """
    تکرار نسخه
    Repeat prescription
    
    POST /api/patient/prescriptions/{prescription_id}/repeat/
    """
    try:
        success, result = await prescription_service.repeat_prescription(
            prescription_id, request.user, request.data.get('notes')
        )
        
        if success:
            return Response(
                await api_ingress.format_response(
                    result, True, 'نسخه تکرار شد',
                    status.HTTP_200_OK
                ),
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                await api_ingress.format_response(
                    result, False, result.get('message'),
                    status.HTTP_400_BAD_REQUEST
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Error in repeat_prescription: {str(e)}")
        return Response(
            await api_ingress.format_response(
                None, False, 'خطای سرور',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Consent Management Views

@api_view(['POST'])
@permission_classes([DoctorOnlyPermission])
async def create_consent(request):
    """
    ایجاد رضایت‌نامه جدید
    Create new consent form
    
    POST /api/patient/consents/
    """
    try:
        # هماهنگی workflow
        workflow_result = await orchestrator.orchestrate_workflow(
            'consent_management',
            {
                'action': 'create',
                **request.data
            },
            {'user': request.user}
        )
        
        if workflow_result['success']:
            return Response(
                await api_ingress.format_response(
                    workflow_result['result'], True,
                    'رضایت‌نامه ایجاد شد',
                    status.HTTP_201_CREATED
                ),
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                await api_ingress.format_response(
                    workflow_result, False,
                    'خطا در ایجاد رضایت‌نامه',
                    status.HTTP_400_BAD_REQUEST
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Error in create_consent: {str(e)}")
        return Response(
            await api_ingress.format_response(
                None, False, 'خطای سرور',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([PatientOnlyPermission])
async def grant_consent(request, consent_id):
    """
    ثبت رضایت
    Grant consent
    
    POST /api/patient/consents/{consent_id}/grant/
    """
    try:
        # جمع‌آوری اطلاعات کلاینت
        client_info = {
            'ip_address': request.META.get('REMOTE_ADDR', '0.0.0.0'),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')
        }
        
        success, result = await consent_service.grant_consent(
            consent_id, request.data, client_info
        )
        
        if success:
            return Response(
                await api_ingress.format_response(
                    result, True, 'رضایت ثبت شد',
                    status.HTTP_200_OK
                ),
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                await api_ingress.format_response(
                    result, False, result.get('message'),
                    status.HTTP_400_BAD_REQUEST
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Error in grant_consent: {str(e)}")
        return Response(
            await api_ingress.format_response(
                None, False, 'خطای سرور',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Audio Transcription Views

@api_view(['POST'])
@permission_classes([DoctorOnlyPermission])
async def transcribe_audio(request):
    """
    رونویسی فایل صوتی
    Transcribe audio file
    
    POST /api/patient/transcribe/
    """
    try:
        # بررسی وجود فایل صوتی
        if 'audio_file' not in request.FILES:
            return Response(
                await api_ingress.format_response(
                    None, False, 'فایل صوتی ارائه نشده',
                    status.HTTP_400_BAD_REQUEST
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        audio_file = request.FILES['audio_file']
        
        # آماده‌سازی داده‌ها
        workflow_data = {
            'audio_file': audio_file.read(),
            'audio_format': audio_file.name.split('.')[-1].lower(),
            'processing_options': {
                'language': request.data.get('language', 'fa'),
                'model': request.data.get('model', 'whisper-1')
            }
        }
        
        # هماهنگی workflow
        workflow_result = await orchestrator.orchestrate_workflow(
            'audio_transcription',
            workflow_data,
            {'user': request.user}
        )
        
        if workflow_result['success']:
            return Response(
                await api_ingress.format_response(
                    workflow_result['result'], True,
                    'رونویسی انجام شد',
                    status.HTTP_200_OK
                ),
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                await api_ingress.format_response(
                    workflow_result, False,
                    'خطا در رونویسی',
                    status.HTTP_400_BAD_REQUEST
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Error in transcribe_audio: {str(e)}")
        return Response(
            await api_ingress.format_response(
                None, False, 'خطای سرور',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Statistics and Analytics Views

@api_view(['GET'])
@permission_classes([PatientOrDoctorPermission])
async def get_patient_statistics(request, patient_id):
    """
    دریافت آمار بیمار
    Get patient statistics
    
    GET /api/patient/{patient_id}/statistics/
    """
    try:
        # بررسی دسترسی
        has_access = await patient_service.validate_patient_access(
            request.user, patient_id, 'view'
        )
        
        if not has_access:
            return Response(
                await api_ingress.format_response(
                    None, False, 'عدم دسترسی',
                    status.HTTP_403_FORBIDDEN
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # دریافت آمار
        success, result = await patient_service.get_patient_statistics(patient_id)
        
        if success:
            return Response(
                await api_ingress.format_response(
                    result, True, 'آمار بیمار',
                    status.HTTP_200_OK
                ),
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                await api_ingress.format_response(
                    result, False, result.get('message'),
                    status.HTTP_400_BAD_REQUEST
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Error in get_patient_statistics: {str(e)}")
        return Response(
            await api_ingress.format_response(
                None, False, 'خطای سرور',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([DoctorOnlyPermission])
async def analyze_data(request):
    """
    تحلیل داده‌ها
    Analyze data
    
    POST /api/patient/analyze/
    """
    try:
        # هماهنگی workflow
        workflow_result = await orchestrator.orchestrate_workflow(
            'data_analysis',
            request.data,
            {'user': request.user}
        )
        
        if workflow_result['success']:
            return Response(
                await api_ingress.format_response(
                    workflow_result['result'], True,
                    'تحلیل انجام شد',
                    status.HTTP_200_OK
                ),
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                await api_ingress.format_response(
                    workflow_result, False,
                    'خطا در تحلیل',
                    status.HTTP_400_BAD_REQUEST
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Error in analyze_data: {str(e)}")
        return Response(
            await api_ingress.format_response(
                None, False, 'خطای سرور',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )