"""
ویوهای اپلیکیشن Doctor
Doctor Application Views
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
import logging

from .serializers import (
    DoctorProfileSerializer,
    DoctorProfileCreateSerializer,
    DoctorScheduleSerializer,
    DoctorCertificateSerializer,
    DoctorRatingSerializer,
    DoctorRatingListSerializer,
    DoctorSearchSerializer,
    DoctorListSerializer
)
from .services.doctor_service import (
    DoctorProfileService,
    DoctorScheduleService,
    DoctorCertificateService,
    DoctorRatingService,
    DoctorAnalyticsService
)
from .cores.api_ingress import doctor_required, doctor_rate_limit, DoctorAPIIngressCore

User = get_user_model()
logger = logging.getLogger(__name__)

# سرویس‌ها
profile_service = DoctorProfileService()
schedule_service = DoctorScheduleService()
certificate_service = DoctorCertificateService()
rating_service = DoctorRatingService()
analytics_service = DoctorAnalyticsService()

# هسته‌ها
api_ingress = DoctorAPIIngressCore()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@doctor_rate_limit('create_profile', limit=5, window=3600)
def create_doctor_profile(request):
    """ایجاد پروفایل پزشک"""
    try:
        serializer = DoctorProfileCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(
                api_ingress.build_doctor_error_response(
                    'validation',
                    details=serializer.errors
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        success, result = profile_service.create_doctor_profile(
            request.user,
            serializer.validated_data
        )
        
        if success:
            return Response(
                api_ingress.build_success_response(
                    result,
                    "پروفایل پزشک با موفقیت ایجاد شد"
                ),
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                api_ingress.build_doctor_error_response(
                    'validation',
                    details=result
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.exception("Error in create_doctor_profile")
        return Response(
            api_ingress.build_doctor_error_response('internal'),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@doctor_required(verified_required=False)
def get_doctor_profile(request):
    """دریافت پروفایل پزشک"""
    try:
        success, result = profile_service.get_doctor_profile(request.user)
        
        if success:
            serializer = DoctorProfileSerializer(result['profile'])
            return Response(
                api_ingress.build_success_response(
                    {
                        'profile': serializer.data,
                        'verification_status': result['verification_status'],
                        'rating_info': result['rating_info']
                    }
                ),
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                api_ingress.build_doctor_error_response(
                    'profile_not_found',
                    details=result
                ),
                status=status.HTTP_404_NOT_FOUND
            )
            
    except Exception as e:
        logger.exception("Error in get_doctor_profile")
        return Response(
            api_ingress.build_doctor_error_response('internal'),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@doctor_required(verified_required=False)
@doctor_rate_limit('update_profile', limit=10, window=3600)
def update_doctor_profile(request):
    """بروزرسانی پروفایل پزشک"""
    try:
        serializer = DoctorProfileSerializer(
            request.user.doctor_profile,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(
                api_ingress.build_doctor_error_response(
                    'validation',
                    details=serializer.errors
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        success, result = profile_service.update_doctor_profile(
            request.user,
            serializer.validated_data
        )
        
        if success:
            return Response(
                api_ingress.build_success_response(
                    result,
                    "پروفایل با موفقیت بروزرسانی شد"
                ),
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                api_ingress.build_doctor_error_response(
                    'validation',
                    details=result
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.exception("Error in update_doctor_profile")
        return Response(
            api_ingress.build_doctor_error_response('internal'),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@doctor_required(verified_required=True)
@doctor_rate_limit('create_schedule', limit=20, window=3600)
def create_doctor_schedule(request):
    """ایجاد برنامه کاری پزشک"""
    try:
        serializer = DoctorScheduleSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(
                api_ingress.build_doctor_error_response(
                    'validation',
                    details=serializer.errors
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        success, result = schedule_service.create_schedule(
            request.user,
            serializer.validated_data
        )
        
        if success:
            status_code = status.HTTP_201_CREATED
            if result.get('warnings'):
                status_code = status.HTTP_200_OK
                
            return Response(
                api_ingress.build_success_response(
                    result,
                    "برنامه کاری با موفقیت ایجاد شد"
                ),
                status=status_code
            )
        else:
            return Response(
                api_ingress.build_doctor_error_response(
                    'schedule_conflict',
                    details=result
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.exception("Error in create_doctor_schedule")
        return Response(
            api_ingress.build_doctor_error_response('internal'),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@doctor_required(verified_required=False)
def get_doctor_schedule(request):
    """دریافت برنامه کاری پزشک"""
    try:
        weekday = request.query_params.get('weekday')
        if weekday is not None:
            try:
                weekday = int(weekday)
            except ValueError:
                return Response(
                    api_ingress.build_doctor_error_response(
                        'validation',
                        persian_message='روز هفته باید عدد باشد'
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        success, result = schedule_service.get_doctor_schedule(request.user, weekday)
        
        if success:
            serializer = DoctorScheduleSerializer(result['schedules'], many=True)
            return Response(
                api_ingress.build_success_response({
                    'schedules': serializer.data,
                    'count': result['count']
                }),
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                api_ingress.build_doctor_error_response(
                    'internal',
                    details=result
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.exception("Error in get_doctor_schedule")
        return Response(
            api_ingress.build_doctor_error_response('internal'),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def search_doctors(request):
    """جستجوی پزشکان"""
    try:
        search_serializer = DoctorSearchSerializer(data=request.query_params)
        if not search_serializer.is_valid():
            return Response(
                api_ingress.build_doctor_error_response(
                    'validation',
                    details=search_serializer.errors
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        search_params = search_serializer.validated_data.copy()
        search_params.update({
            'page': int(request.query_params.get('page', 1)),
            'page_size': int(request.query_params.get('page_size', 20)),
            'order_by': request.query_params.get('order_by', '-rating')
        })
        
        success, result = profile_service.search_doctors(search_params)
        
        if success:
            serializer = DoctorListSerializer(result['doctors'], many=True)
            return Response(
                api_ingress.build_success_response({
                    'doctors': serializer.data,
                    'pagination': {
                        'total_count': result['total_count'],
                        'page': result['page'],
                        'page_size': result['page_size'],
                        'has_next': result['has_next']
                    }
                }),
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                api_ingress.build_doctor_error_response(
                    'internal',
                    details=result
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.exception("Error in search_doctors")
        return Response(
            api_ingress.build_doctor_error_response('internal'),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )