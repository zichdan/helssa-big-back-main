"""
API Views برای feedback app
"""

import logging
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Avg, Count, Q
from django.utils import timezone

from .models import SessionRating, MessageFeedback, Survey, SurveyResponse, FeedbackSettings
from .serializers import (
    SessionRatingCreateSerializer, SessionRatingSerializer,
    MessageFeedbackCreateSerializer, MessageFeedbackSerializer,
    SurveySerializer, SurveyCreateSerializer, SurveyListSerializer,
    SurveyResponseCreateSerializer, FeedbackSettingsSerializer
)
from .cores import FeedbackOrchestrator

logger = logging.getLogger(__name__)


class SessionRatingViewSet(viewsets.ModelViewSet):
    """ViewSet برای مدیریت امتیازدهی جلسات"""
    
    queryset = SessionRating.objects.all()
    serializer_class = SessionRatingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SessionRatingCreateSerializer
        return SessionRatingSerializer
    
    def get_queryset(self):
        queryset = SessionRating.objects.filter(is_active=True)
        
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        
        session_id = self.request.query_params.get('session_id')
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        
        return queryset.order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """ایجاد امتیازدهی جدید"""
        try:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'error': 'validation_error',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # ایجاد امتیازدهی
            rating = SessionRating.objects.create(
                session_id=serializer.validated_data['session_id'],
                user=request.user,
                overall_rating=serializer.validated_data['overall_rating'],
                response_quality=serializer.validated_data.get('response_quality'),
                response_speed=serializer.validated_data.get('response_speed'),
                helpfulness=serializer.validated_data.get('helpfulness'),
                comment=serializer.validated_data.get('comment', ''),
                suggestions=serializer.validated_data.get('suggestions', ''),
                would_recommend=serializer.validated_data.get('would_recommend')
            )
            
            response_serializer = SessionRatingSerializer(rating)
            
            return Response({
                'success': True,
                'message': 'امتیازدهی با موفقیت ثبت شد',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating session rating: {str(e)}")
            return Response({
                'success': False,
                'error': 'internal_error',
                'message': 'خطای داخلی سرور'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """آمار امتیازدهی‌ها"""
        try:
            queryset = self.get_queryset()
            total_ratings = queryset.count()
            
            if total_ratings == 0:
                return Response({
                    'success': True,
                    'data': {'total_ratings': 0, 'message': 'هنوز امتیازدهی وجود ندارد'}
                })
            
            stats = queryset.aggregate(
                average_overall=Avg('overall_rating'),
                average_quality=Avg('response_quality'),
                average_speed=Avg('response_speed'),
                average_helpfulness=Avg('helpfulness')
            )
            
            rating_distribution = {}
            for i in range(1, 6):
                count = queryset.filter(overall_rating=i).count()
                rating_distribution[str(i)] = count
            
            recommendation_count = queryset.filter(would_recommend=True).count()
            recommendation_rate = (recommendation_count / total_ratings) * 100
            
            recent_comments = list(
                queryset.filter(comment__isnull=False, comment__gt='')
                .values_list('comment', flat=True)[:5]
            )
            
            return Response({
                'success': True,
                'data': {
                    'total_ratings': total_ratings,
                    'average_overall': round(stats['average_overall'] or 0, 2),
                    'average_quality': round(stats['average_quality'] or 0, 2),
                    'average_speed': round(stats['average_speed'] or 0, 2),
                    'average_helpfulness': round(stats['average_helpfulness'] or 0, 2),
                    'recommendation_rate': round(recommendation_rate, 2),
                    'rating_distribution': rating_distribution,
                    'recent_comments': recent_comments
                }
            })
                
        except Exception as e:
            logger.error(f"Error getting rating stats: {str(e)}")
            return Response({
                'success': False,
                'error': 'internal_error',
                'message': 'خطا در دریافت آمار'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MessageFeedbackViewSet(viewsets.ModelViewSet):
    """ViewSet برای مدیریت بازخورد پیام‌ها"""
    
    queryset = MessageFeedback.objects.all()
    serializer_class = MessageFeedbackSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MessageFeedbackCreateSerializer
        return MessageFeedbackSerializer
    
    def get_queryset(self):
        queryset = MessageFeedback.objects.filter(is_active=True)
        
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        
        message_id = self.request.query_params.get('message_id')
        if message_id:
            queryset = queryset.filter(message_id=message_id)
        
        feedback_type = self.request.query_params.get('type')
        if feedback_type:
            queryset = queryset.filter(feedback_type=feedback_type)
        
        return queryset.order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """ایجاد بازخورد جدید"""
        try:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'error': 'validation_error',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # ایجاد بازخورد
            feedback = MessageFeedback.objects.create(
                message_id=serializer.validated_data['message_id'],
                user=request.user,
                feedback_type=serializer.validated_data['feedback_type'],
                is_helpful=serializer.validated_data.get('is_helpful'),
                detailed_feedback=serializer.validated_data.get('detailed_feedback', ''),
                expected_response=serializer.validated_data.get('expected_response', '')
            )
            
            response_serializer = MessageFeedbackSerializer(feedback)
            
            return Response({
                'success': True,
                'message': 'بازخورد شما ثبت شد',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating message feedback: {str(e)}")
            return Response({
                'success': False,
                'error': 'internal_error',
                'message': 'خطای داخلی سرور'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SurveyViewSet(viewsets.ModelViewSet):
    """ViewSet برای مدیریت نظرسنجی‌ها"""
    
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SurveyCreateSerializer
        elif self.action == 'list':
            return SurveyListSerializer
        return SurveySerializer
    
    def get_queryset(self):
        queryset = Survey.objects.filter(is_active=True)
        
        survey_type = self.request.query_params.get('type')
        if survey_type:
            queryset = queryset.filter(survey_type=survey_type)
        
        target_users = self.request.query_params.get('target')
        if target_users:
            queryset = queryset.filter(target_users=target_users)
        
        available_only = self.request.query_params.get('available_only')
        if available_only == 'true':
            now = timezone.now()
            queryset = queryset.filter(
                Q(start_date__isnull=True) | Q(start_date__lte=now),
                Q(end_date__isnull=True) | Q(end_date__gte=now)
            )
        
        return queryset.order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """ایجاد نظرسنجی جدید"""
        try:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'error': 'validation_error',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # ایجاد نظرسنجی
            survey = Survey.objects.create(
                title=serializer.validated_data['title'],
                description=serializer.validated_data['description'],
                survey_type=serializer.validated_data.get('survey_type', 'general'),
                target_users=serializer.validated_data.get('target_users', 'all'),
                questions=serializer.validated_data['questions'],
                start_date=serializer.validated_data.get('start_date'),
                end_date=serializer.validated_data.get('end_date'),
                max_responses=serializer.validated_data.get('max_responses'),
                allow_anonymous=serializer.validated_data.get('allow_anonymous', False),
                created_by=request.user
            )
            
            response_serializer = SurveySerializer(survey)
            
            return Response({
                'success': True,
                'message': 'نظرسنجی با موفقیت ایجاد شد',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating survey: {str(e)}")
            return Response({
                'success': False,
                'error': 'internal_error',
                'message': 'خطای داخلی سرور'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_dashboard(request):
    """داشبورد آنالیتیک feedback"""
    try:
        # آمار کلی
        total_ratings = SessionRating.objects.filter(is_active=True).count()
        total_feedbacks = MessageFeedback.objects.filter(is_active=True).count()
        total_surveys = Survey.objects.filter(is_active=True).count()
        
        # میانگین امتیاز
        avg_rating = SessionRating.objects.filter(is_active=True).aggregate(
            avg=Avg('overall_rating')
        )['avg'] or 0
        
        return Response({
            'success': True,
            'data': {
                'summary': {
                    'total_ratings': total_ratings,
                    'total_feedbacks': total_feedbacks,
                    'total_surveys': total_surveys,
                    'average_rating': round(avg_rating, 2)
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating analytics: {str(e)}")
        return Response({
            'success': False,
            'error': 'internal_error',
            'message': 'خطا در تولید آنالیتیک'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FeedbackSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet برای مدیریت تنظیمات feedback"""
    
    queryset = FeedbackSettings.objects.all()
    serializer_class = FeedbackSettingsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = FeedbackSettings.objects.filter(is_active=True)
        
        setting_type = self.request.query_params.get('type')
        if setting_type:
            queryset = queryset.filter(setting_type=setting_type)
        
        return queryset.order_by('setting_type', 'key')