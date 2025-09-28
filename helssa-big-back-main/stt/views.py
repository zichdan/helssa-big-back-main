"""
ویوهای API برای تبدیل گفتار به متن
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
import time

from .services import STTService
from .serializers import (
    AudioFileSerializer,
    STTTaskSerializer,
    TranscriptionResultSerializer,
    STTTaskStatusSerializer,
)

logger = logging.getLogger(__name__)
stt_service = STTService()


# ======================== API های مشترک ========================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def create_transcription(request):
    """
    ایجاد وظیفه تبدیل گفتار به متن
    
    این API برای هر دو نوع کاربر (دکتر و بیمار) قابل استفاده است
    
    Request:
        - audio_file: فایل صوتی (حداکثر 50MB)
        - language: زبان گفتار (fa/en/auto)
        - model: مدل Whisper (tiny/base/small/medium/large)
        - context_type: نوع محتوا (general/medical/prescription/symptoms)
    
    Response:
        200: وظیفه ایجاد شد
        400: خطای validation
        429: محدودیت نرخ
        500: خطای سرور
    """
    start_time = time.time()
    
    try:
        # Validation
        serializer = AudioFileSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'validation_error',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # استخراج داده‌ها
        validated_data = serializer.validated_data
        audio_file = validated_data['audio_file']
        language = validated_data.get('language', 'fa')
        model_size = validated_data.get('model', 'base')
        context_type = validated_data.get('context_type', 'general')
        
        # اضافه کردن metadata
        metadata = {
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': request.META.get('REMOTE_ADDR', ''),
            'context_type': context_type,
        }
        
        # ایجاد وظیفه
        success, result = stt_service.create_transcription_task(
            user=request.user,
            audio_file=audio_file,
            language=language,
            model_size=model_size,
            context_type=context_type,
            metadata=metadata
        )
        
        if success:
            # لاگ موفقیت
            response_time = time.time() - start_time
            logger.info(
                f"Transcription task created - User: {request.user.id}, "
                f"Task: {result.get('task_id')}, Response time: {response_time:.2f}s"
            )
            
            return Response({
                'success': True,
                'data': result
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': result.get('error', 'unknown_error'),
                'message': result.get('message', 'خطای ناشناخته')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error in create_transcription: {str(e)}")
        return Response({
            'success': False,
            'error': 'internal_error',
            'message': 'خطای داخلی سرور'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_task_status(request, task_id):
    """
    دریافت وضعیت وظیفه تبدیل
    
    Path Parameters:
        - task_id: شناسه وظیفه (UUID)
    
    Response:
        200: وضعیت وظیفه
        403: عدم دسترسی
        404: وظیفه یافت نشد
        500: خطای سرور
    """
    try:
        success, result = stt_service.get_task_status(task_id, request.user)
        
        if success:
            return Response({
                'success': True,
                'data': result
            }, status=status.HTTP_200_OK)
        else:
            status_code = status.HTTP_404_NOT_FOUND
            if result.get('error') == 'permission_denied':
                status_code = status.HTTP_403_FORBIDDEN
                
            return Response({
                'success': False,
                'error': result.get('error'),
                'message': result.get('message')
            }, status=status_code)
            
    except Exception as e:
        logger.error(f"Error in get_task_status: {str(e)}")
        return Response({
            'success': False,
            'error': 'internal_error',
            'message': 'خطای داخلی سرور'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_task(request, task_id):
    """
    لغو وظیفه در حال پردازش
    
    Path Parameters:
        - task_id: شناسه وظیفه (UUID)
    
    Response:
        200: وظیفه لغو شد
        400: وظیفه قابل لغو نیست
        403: عدم دسترسی
        404: وظیفه یافت نشد
        500: خطای سرور
    """
    try:
        success, result = stt_service.cancel_task(task_id, request.user)
        
        if success:
            return Response({
                'success': True,
                'message': result.get('message')
            }, status=status.HTTP_200_OK)
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            if result.get('error') == 'not_found':
                status_code = status.HTTP_404_NOT_FOUND
            elif result.get('error') == 'permission_denied':
                status_code = status.HTTP_403_FORBIDDEN
                
            return Response({
                'success': False,
                'error': result.get('error'),
                'message': result.get('message')
            }, status=status_code)
            
    except Exception as e:
        logger.error(f"Error in cancel_task: {str(e)}")
        return Response({
            'success': False,
            'error': 'internal_error',
            'message': 'خطای داخلی سرور'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_tasks(request):
    """
    دریافت لیست وظایف کاربر
    
    Query Parameters:
        - status: فیلتر وضعیت (pending/processing/completed/failed/cancelled)
        - limit: تعداد نتایج (پیش‌فرض: 10)
        - offset: شروع از (پیش‌فرض: 0)
    
    Response:
        200: لیست وظایف
        500: خطای سرور
    """
    try:
        # پارامترها
        status_filter = request.GET.get('status')
        limit = int(request.GET.get('limit', 10))
        offset = int(request.GET.get('offset', 0))
        
        # محدودیت limit
        limit = min(limit, 100)
        
        success, result = stt_service.get_user_tasks(
            user=request.user,
            status=status_filter,
            limit=limit,
            offset=offset
        )
        
        if success:
            return Response({
                'success': True,
                'data': result
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': result.get('error'),
                'message': result.get('message')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error in get_user_tasks: {str(e)}")
        return Response({
            'success': False,
            'error': 'internal_error',
            'message': 'خطای داخلی سرور'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_statistics(request):
    """
    دریافت آمار استفاده کاربر
    
    Query Parameters:
        - days: تعداد روزهای گذشته (پیش‌فرض: 30)
    
    Response:
        200: آمار استفاده
        500: خطای سرور
    """
    try:
        days = int(request.GET.get('days', 30))
        days = min(days, 365)  # حداکثر یک سال
        
        success, result = stt_service.get_user_statistics(
            user=request.user,
            days=days
        )
        
        if success:
            return Response({
                'success': True,
                'data': result
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': result.get('error'),
                'message': result.get('message')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error in get_user_statistics: {str(e)}")
        return Response({
            'success': False,
            'error': 'internal_error',
            'message': 'خطای داخلی سرور'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ======================== API های ویژه بیمار ========================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def patient_voice_to_text(request):
    """
    API ویژه بیمار برای تبدیل صدای علائم به متن
    
    این API مخصوص بیماران است و برای ثبت علائم صوتی بهینه شده است
    
    Request:
        - audio_file: فایل صوتی علائم
        - language: زبان (پیش‌فرض: fa)
    
    Response:
        200: متن علائم
        400: خطای validation
        403: فقط بیماران دسترسی دارند
        500: خطای سرور
    """
    try:
        # بررسی نوع کاربر
        if request.user.user_type != 'patient':
            return Response({
                'success': False,
                'error': 'permission_denied',
                'message': 'این سرویس فقط برای بیماران است'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Validation
        serializer = AudioFileSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'validation_error',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ایجاد وظیفه با context مخصوص علائم
        validated_data = serializer.validated_data
        
        metadata = {
            'api_type': 'patient_symptoms',
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        
        success, result = stt_service.create_transcription_task(
            user=request.user,
            audio_file=validated_data['audio_file'],
            language=validated_data.get('language', 'fa'),
            model_size='base',  # مدل متعادل برای بیماران
            context_type='symptoms',  # context مخصوص علائم
            metadata=metadata
        )
        
        if success:
            return Response({
                'success': True,
                'data': {
                    'task_id': result.get('task_id'),
                    'status': result.get('status'),
                    'message': 'صدای شما در حال پردازش است. لطفاً چند لحظه صبر کنید.',
                    'estimated_time': result.get('estimated_time', 30)
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': result.get('error'),
                'message': result.get('message')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error in patient_voice_to_text: {str(e)}")
        return Response({
            'success': False,
            'error': 'internal_error',
            'message': 'خطای داخلی سرور'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ======================== API های ویژه دکتر ========================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def doctor_dictation(request):
    """
    API ویژه دکتر برای دیکته کردن نسخه و یادداشت‌های پزشکی
    
    این API مخصوص پزشکان است و برای دیکته نسخه و SOAP notes بهینه شده است
    
    Request:
        - audio_file: فایل صوتی دیکته
        - dictation_type: نوع دیکته (prescription/soap_note/medical_report)
        - language: زبان (پیش‌فرض: fa)
        - model: مدل دقت (پیش‌فرض: small برای دقت بیشتر)
    
    Response:
        200: متن دیکته شده
        400: خطای validation
        403: فقط پزشکان دسترسی دارند
        500: خطای سرور
    """
    try:
        # بررسی نوع کاربر
        if request.user.user_type != 'doctor':
            return Response({
                'success': False,
                'error': 'permission_denied',
                'message': 'این سرویس فقط برای پزشکان است'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Validation
        serializer = AudioFileSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'validation_error',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # استخراج داده‌ها
        validated_data = serializer.validated_data
        dictation_type = request.data.get('dictation_type', 'medical_report')
        
        # تعیین context_type بر اساس نوع دیکته
        context_map = {
            'prescription': 'prescription',
            'soap_note': 'medical',
            'medical_report': 'medical',
        }
        context_type = context_map.get(dictation_type, 'medical')
        
        # metadata مخصوص دکتر
        metadata = {
            'api_type': 'doctor_dictation',
            'dictation_type': dictation_type,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        
        # مدل دقیق‌تر برای دکترها
        model_size = validated_data.get('model', 'small')
        
        success, result = stt_service.create_transcription_task(
            user=request.user,
            audio_file=validated_data['audio_file'],
            language=validated_data.get('language', 'fa'),
            model_size=model_size,
            context_type=context_type,
            metadata=metadata
        )
        
        if success:
            return Response({
                'success': True,
                'data': {
                    'task_id': result.get('task_id'),
                    'status': result.get('status'),
                    'dictation_type': dictation_type,
                    'message': 'دیکته شما در حال پردازش است.',
                    'estimated_time': result.get('estimated_time', 45),
                    'quality_features': {
                        'medical_term_detection': True,
                        'prescription_formatting': dictation_type == 'prescription',
                        'soap_structure': dictation_type == 'soap_note',
                    }
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': result.get('error'),
                'message': result.get('message')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error in doctor_dictation: {str(e)}")
        return Response({
            'success': False,
            'error': 'internal_error',
            'message': 'خطای داخلی سرور'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_get_patient_voice_history(request, patient_id):
    """
    API ویژه دکتر برای دریافت تاریخچه صوت‌های بیمار
    
    این API به پزشکان اجازه می‌دهد تاریخچه تبدیل‌های صوتی بیمار خاص را ببینند
    
    Path Parameters:
        - patient_id: شناسه بیمار
    
    Query Parameters:
        - limit: تعداد نتایج (پیش‌فرض: 10)
        - offset: شروع از (پیش‌فرض: 0)
    
    Response:
        200: تاریخچه صوت‌های بیمار
        403: عدم دسترسی
        404: بیمار یافت نشد
        500: خطای سرور
    """
    try:
        # بررسی نوع کاربر
        if request.user.user_type != 'doctor':
            return Response({
                'success': False,
                'error': 'permission_denied',
                'message': 'این سرویس فقط برای پزشکان است'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # TODO: بررسی دسترسی دکتر به بیمار
        # این بخش باید با unified_access یکپارچه شود
        
        # پارامترها
        limit = int(request.GET.get('limit', 10))
        offset = int(request.GET.get('offset', 0))
        limit = min(limit, 50)
        
        # دریافت وظایف بیمار
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            patient = User.objects.get(id=patient_id, user_type='patient')
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'not_found',
                'message': 'بیمار یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        
        success, result = stt_service.get_user_tasks(
            user=patient,
            status='completed',
            limit=limit,
            offset=offset
        )
        
        if success:
            # اضافه کردن اطلاعات بیمار
            result['patient'] = {
                'id': patient.id,
                'name': patient.get_full_name() if hasattr(patient, 'get_full_name') else str(patient),
            }
            
            return Response({
                'success': True,
                'data': result
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': result.get('error'),
                'message': result.get('message')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error in doctor_get_patient_voice_history: {str(e)}")
        return Response({
            'success': False,
            'error': 'internal_error',
            'message': 'خطای داخلی سرور'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ======================== API های ادمین ========================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_get_pending_reviews(request):
    """
    دریافت لیست وظایف نیازمند بررسی (فقط staff)
    
    Query Parameters:
        - limit: تعداد نتایج (پیش‌فرض: 10)
        - offset: شروع از (پیش‌فرض: 0)
    
    Response:
        200: لیست وظایف نیازمند بررسی
        403: فقط staff دسترسی دارد
        500: خطای سرور
    """
    try:
        # بررسی دسترسی
        if not request.user.is_staff:
            return Response({
                'success': False,
                'error': 'permission_denied',
                'message': 'فقط کارکنان دسترسی دارند'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # پارامترها
        limit = int(request.GET.get('limit', 10))
        offset = int(request.GET.get('offset', 0))
        limit = min(limit, 100)
        
        success, result = stt_service.get_pending_reviews(
            limit=limit,
            offset=offset
        )
        
        if success:
            return Response({
                'success': True,
                'data': result
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': result.get('error'),
                'message': result.get('message')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error in admin_get_pending_reviews: {str(e)}")
        return Response({
            'success': False,
            'error': 'internal_error',
            'message': 'خطای داخلی سرور'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_review_transcription(request, task_id):
    """
    بررسی و اصلاح نتیجه تبدیل (فقط staff)
    
    Path Parameters:
        - task_id: شناسه وظیفه
    
    Request Body:
        - corrected_text: متن اصلاح شده
        - review_notes: یادداشت‌های بررسی (اختیاری)
    
    Response:
        200: بررسی انجام شد
        400: خطای validation
        403: فقط staff دسترسی دارد
        404: وظیفه یافت نشد
        500: خطای سرور
    """
    try:
        # بررسی دسترسی
        if not request.user.is_staff:
            return Response({
                'success': False,
                'error': 'permission_denied',
                'message': 'فقط کارکنان دسترسی دارند'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Validation
        corrected_text = request.data.get('corrected_text')
        if not corrected_text:
            return Response({
                'success': False,
                'error': 'validation_error',
                'message': 'متن اصلاح شده الزامی است'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        review_notes = request.data.get('review_notes')
        
        success, result = stt_service.review_transcription(
            task_id=task_id,
            reviewer=request.user,
            corrected_text=corrected_text,
            review_notes=review_notes
        )
        
        if success:
            return Response({
                'success': True,
                'message': result.get('message')
            }, status=status.HTTP_200_OK)
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            if result.get('error') == 'not_found':
                status_code = status.HTTP_404_NOT_FOUND
                
            return Response({
                'success': False,
                'error': result.get('error'),
                'message': result.get('message')
            }, status=status_code)
            
    except Exception as e:
        logger.error(f"Error in admin_review_transcription: {str(e)}")
        return Response({
            'success': False,
            'error': 'internal_error',
            'message': 'خطای داخلی سرور'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)