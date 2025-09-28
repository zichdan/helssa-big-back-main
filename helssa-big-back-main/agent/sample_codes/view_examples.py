"""
نمونه کدهای View برای ایجنت‌ها
Sample View Code Examples for Agents
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from app_standards.four_cores import APIIngressCore, CentralOrchestrator, with_api_ingress
from unified_auth.permissions import IsPatient, IsDoctor
import logging

logger = logging.getLogger(__name__)


# ====================================
# نمونه 1: Simple API Endpoint
# ====================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """
    دریافت پروفایل کاربر
    
    Returns:
        200: پروفایل کاربر
        401: عدم احراز هویت
    """
    try:
        user = request.user
        data = {
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'user_type': user.user_type,
            'full_name': f"{user.first_name} {user.last_name}".strip(),
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat()
        }
        return Response(data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Profile fetch error: {str(e)}")
        return Response(
            {'error': 'خطا در دریافت پروفایل'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ====================================
# نمونه 2: Create with Validation
# ====================================

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsPatient])
@with_api_ingress(rate_limit=20, rate_window=3600)
def create_medical_record(request):
    """
    ایجاد سابقه پزشکی جدید
    
    Request Body:
        - title: عنوان
        - description: توضیحات
        - record_date: تاریخ
        
    Returns:
        201: سابقه ایجاد شد
        400: خطای اعتبارسنجی
    """
    ingress = APIIngressCore()
    
    try:
        # اعتبارسنجی
        from patient_records.serializers import MedicalRecordCreateSerializer
        is_valid, data = ingress.validate_request(
            request.data,
            MedicalRecordCreateSerializer
        )
        
        if not is_valid:
            return Response(
                ingress.build_error_response('validation', data),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ایجاد رکورد
        with transaction.atomic():
            from patient_records.models import MedicalRecord
            
            record = MedicalRecord.objects.create(
                patient=request.user,
                title=data['title'],
                description=data['description'],
                record_date=data['record_date'],
                created_by=request.user
            )
            
            # Serialize response
            from patient_records.serializers import MedicalRecordSerializer
            serializer = MedicalRecordSerializer(record)
            
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
            
    except Exception as e:
        logger.exception("Medical record creation error")
        return Response(
            ingress.build_error_response('internal'),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ====================================
# نمونه 3: Complex Workflow
# ====================================

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsDoctor])
def process_patient_encounter(request):
    """
    پردازش ملاقات با بیمار (SOAP generation)
    
    Request Body:
        - patient_id: شناسه بیمار
        - audio_file: فایل صوتی
        - encounter_type: نوع ملاقات
        
    Returns:
        200: SOAP تولید شد
        400: خطای ورودی
        500: خطای سرور
    """
    orchestrator = CentralOrchestrator()
    
    try:
        # اجرای workflow
        result = orchestrator.execute_workflow(
            'soap_generation',
            {
                'patient_id': request.data.get('patient_id'),
                'audio_file': request.FILES.get('audio_file'),
                'encounter_type': request.data.get('encounter_type', 'general'),
                'doctor': request.user
            },
            request.user,
            async_mode=False
        )
        
        if result.status == 'completed':
            return Response(
                {
                    'soap_report': result.data.get('soap_report'),
                    'transcription': result.data.get('transcription'),
                    'processing_time': result.execution_time
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    'error': 'پردازش ناموفق',
                    'details': result.errors
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Encounter processing error: {str(e)}")
        return Response(
            {'error': 'خطای داخلی سرور'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ====================================
# نمونه 4: List with Filtering
# ====================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_appointments(request):
    """
    لیست قرارهای ملاقات
    
    Query Parameters:
        - status: فیلتر بر اساس وضعیت
        - date_from: تاریخ شروع
        - date_to: تاریخ پایان
        - page: شماره صفحه
        - page_size: تعداد در هر صفحه
        
    Returns:
        200: لیست قرارها
    """
    try:
        from appointment_scheduler.models import Appointment
        from appointment_scheduler.serializers import AppointmentListSerializer
        from django.core.paginator import Paginator
        from datetime import datetime
        
        # Base queryset
        user = request.user
        if user.user_type == 'patient':
            queryset = Appointment.objects.filter(patient=user)
        elif user.user_type == 'doctor':
            queryset = Appointment.objects.filter(doctor=user)
        else:
            queryset = Appointment.objects.none()
        
        # Apply filters
        status_filter = request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        date_from = request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(appointment_date__gte=date_from)
        
        date_to = request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(appointment_date__lte=date_to)
        
        # Order by date
        queryset = queryset.order_by('-appointment_date')
        
        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        paginator = Paginator(queryset, page_size)
        
        appointments = paginator.get_page(page)
        
        # Serialize
        serializer = AppointmentListSerializer(appointments, many=True)
        
        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'page': page,
            'pages': paginator.num_pages,
            'has_next': appointments.has_next(),
            'has_previous': appointments.has_previous()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Appointment list error: {str(e)}")
        return Response(
            {'error': 'خطا در دریافت لیست'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ====================================
# نمونه 5: Update with Permissions
# ====================================

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_prescription(request, prescription_id):
    """
    بروزرسانی نسخه
    
    Path Parameters:
        - prescription_id: شناسه نسخه
        
    Returns:
        200: بروزرسانی موفق
        403: عدم دسترسی
        404: نسخه یافت نشد
    """
    try:
        from prescription_system.models import Prescription
        from prescription_system.serializers import PrescriptionUpdateSerializer
        
        # Get prescription
        try:
            prescription = Prescription.objects.get(id=prescription_id)
        except Prescription.DoesNotExist:
            return Response(
                {'error': 'نسخه یافت نشد'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permissions
        if request.user != prescription.doctor:
            return Response(
                {'error': 'شما دسترسی به این نسخه ندارید'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate and update
        serializer = PrescriptionUpdateSerializer(
            prescription,
            data=request.data,
            partial=(request.method == 'PATCH')
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Prescription update error: {str(e)}")
        return Response(
            {'error': 'خطا در بروزرسانی'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ====================================
# نمونه 6: Delete with Confirmation
# ====================================

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_medical_file(request, file_id):
    """
    حذف فایل پزشکی
    
    Path Parameters:
        - file_id: شناسه فایل
        
    Query Parameters:
        - confirm: تأیید حذف (true/false)
        
    Returns:
        204: حذف موفق
        400: نیاز به تأیید
        403: عدم دسترسی
        404: فایل یافت نشد
    """
    try:
        from patient_records.models import MedicalFile
        
        # Get file
        try:
            medical_file = MedicalFile.objects.get(id=file_id)
        except MedicalFile.DoesNotExist:
            return Response(
                {'error': 'فایل یافت نشد'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check ownership
        if request.user != medical_file.patient:
            return Response(
                {'error': 'شما مالک این فایل نیستید'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check confirmation
        confirm = request.GET.get('confirm', '').lower() == 'true'
        if not confirm:
            return Response(
                {
                    'error': 'برای حذف باید تأیید کنید',
                    'message': 'لطفا با افزودن ?confirm=true تأیید کنید'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Soft delete
        medical_file.soft_delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
        
    except Exception as e:
        logger.error(f"File deletion error: {str(e)}")
        return Response(
            {'error': 'خطا در حذف فایل'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ====================================
# نمونه 7: Async Task Creation
# ====================================

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsDoctor])
def generate_report_async(request):
    """
    تولید گزارش به صورت غیرهمزمان
    
    Request Body:
        - report_type: نوع گزارش
        - start_date: تاریخ شروع
        - end_date: تاریخ پایان
        
    Returns:
        202: تسک ایجاد شد
        400: خطای ورودی
    """
    orchestrator = CentralOrchestrator()
    
    try:
        # Validate input
        report_type = request.data.get('report_type')
        if not report_type:
            return Response(
                {'error': 'نوع گزارش الزامی است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Execute async workflow
        result = orchestrator.execute_workflow(
            'generate_report',
            {
                'report_type': report_type,
                'start_date': request.data.get('start_date'),
                'end_date': request.data.get('end_date'),
                'doctor_id': request.user.id
            },
            request.user,
            async_mode=True
        )
        
        return Response(
            {
                'task_id': result.data['task_id'],
                'message': 'گزارش در حال تولید است',
                'check_status_url': f'/api/reports/status/{result.data["task_id"]}/'
            },
            status=status.HTTP_202_ACCEPTED
        )
        
    except Exception as e:
        logger.error(f"Report generation error: {str(e)}")
        return Response(
            {'error': 'خطا در ایجاد گزارش'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ====================================
# نمونه 8: File Upload
# ====================================

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsPatient])
def upload_medical_document(request):
    """
    آپلود مدرک پزشکی
    
    Request Body:
        - file: فایل
        - document_type: نوع مدرک
        - description: توضیحات
        
    Returns:
        201: آپلود موفق
        400: خطای اعتبارسنجی
    """
    try:
        from patient_records.models import MedicalDocument
        from app_standards.serializers.base_serializers import FileUploadSerializer
        
        # Validate file
        file_serializer = FileUploadSerializer(data=request.data)
        if not file_serializer.is_valid():
            return Response(
                file_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create document
        document = MedicalDocument.objects.create(
            patient=request.user,
            file=file_serializer.validated_data['file'],
            document_type=request.data.get('document_type', 'other'),
            description=file_serializer.validated_data.get('description', ''),
            created_by=request.user
        )
        
        return Response(
            {
                'id': str(document.id),
                'file_url': document.file.url,
                'document_type': document.document_type,
                'created_at': document.created_at.isoformat()
            },
            status=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        logger.error(f"Document upload error: {str(e)}")
        return Response(
            {'error': 'خطا در آپلود فایل'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ====================================
# نمونه 9: Bulk Operations
# ====================================

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsDoctor])
def bulk_update_appointments(request):
    """
    بروزرسانی دسته‌ای قرارها
    
    Request Body:
        - ids: لیست شناسه‌ها
        - action: عملیات (cancel, confirm, reschedule)
        - data: داده‌های اضافی
        
    Returns:
        200: عملیات موفق
        400: خطای ورودی
    """
    try:
        from appointment_scheduler.models import Appointment
        from app_standards.serializers.base_serializers import BulkOperationSerializer
        
        # Validate input
        serializer = BulkOperationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ids = serializer.validated_data['ids']
        action = serializer.validated_data['action']
        
        # Get appointments
        appointments = Appointment.objects.filter(
            id__in=ids,
            doctor=request.user
        )
        
        if appointments.count() != len(ids):
            return Response(
                {'error': 'برخی قرارها یافت نشد یا دسترسی ندارید'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Perform action
        results = []
        with transaction.atomic():
            for appointment in appointments:
                if action == 'cancel':
                    appointment.status = 'cancelled'
                    appointment.save()
                    results.append({'id': str(appointment.id), 'status': 'cancelled'})
                elif action == 'confirm':
                    appointment.status = 'confirmed'
                    appointment.save()
                    results.append({'id': str(appointment.id), 'status': 'confirmed'})
                # Add more actions as needed
        
        return Response(
            {
                'updated': len(results),
                'results': results
            },
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Bulk update error: {str(e)}")
        return Response(
            {'error': 'خطا در عملیات دسته‌ای'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )