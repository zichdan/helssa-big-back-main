"""
ویوهای سیستم تریاژ پزشکی
Triage System Views
"""

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.core.cache import cache
from typing import Dict, List, Any
import logging

from .models import (
    SymptomCategory,
    Symptom,
    DifferentialDiagnosis,
    TriageSession,
    SessionSymptom,
    SessionDiagnosis,
    TriageRule
)
from .serializers import (
    SymptomCategorySerializer,
    SymptomListSerializer,
    SymptomDetailSerializer,
    DifferentialDiagnosisListSerializer,
    DifferentialDiagnosisDetailSerializer,
    TriageSessionListSerializer,
    TriageSessionCreateSerializer,
    TriageSessionDetailSerializer,
    TriageSessionUpdateSerializer,
    AddSymptomToSessionSerializer,
    TriageRuleSerializer,
    TriageAnalysisSerializer,
    SessionSymptomSerializer,
    SessionDiagnosisSerializer
)
from .services import TriageAnalysisService

logger = logging.getLogger(__name__)


class SymptomCategoryViewSet(ModelViewSet):
    """
    ViewSet برای مدیریت دسته‌بندی علائم
    """
    queryset = SymptomCategory.objects.filter(is_active=True)
    serializer_class = SymptomCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """فیلتر کردن دسته‌بندی‌ها"""
        queryset = super().get_queryset()
        
        # فیلتر بر اساس اولویت
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority_level=priority)
        
        return queryset.order_by('priority_level', 'name')


class SymptomViewSet(ModelViewSet):
    """
    ViewSet برای مدیریت علائم
    """
    queryset = Symptom.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """انتخاب serializer مناسب"""
        if self.action == 'list':
            return SymptomListSerializer
        return SymptomDetailSerializer
    
    def get_queryset(self):
        """فیلتر کردن علائم"""
        queryset = super().get_queryset()
        
        # جستجو در نام علائم
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(name_en__icontains=search)
            )
        
        # فیلتر بر اساس دسته‌بندی
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # فیلتر بر اساس سطح اورژانس
        urgency_min = self.request.query_params.get('urgency_min')
        if urgency_min:
            queryset = queryset.filter(urgency_score__gte=urgency_min)
        
        urgency_max = self.request.query_params.get('urgency_max')
        if urgency_max:
            queryset = queryset.filter(urgency_score__lte=urgency_max)
        
        return queryset.order_by('-urgency_score', 'name')
    
    @action(detail=True, methods=['get'])
    def related_symptoms(self, request, pk=None):
        """دریافت علائم مرتبط"""
        symptom = self.get_object()
        related = symptom.related_symptoms.filter(is_active=True)
        serializer = SymptomListSerializer(related, many=True)
        return Response(serializer.data)


class DifferentialDiagnosisViewSet(ModelViewSet):
    """
    ViewSet برای مدیریت تشخیص‌های افتراقی
    """
    queryset = DifferentialDiagnosis.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """انتخاب serializer مناسب"""
        if self.action == 'list':
            return DifferentialDiagnosisListSerializer
        return DifferentialDiagnosisDetailSerializer
    
    def get_queryset(self):
        """فیلتر کردن تشخیص‌ها"""
        queryset = super().get_queryset()
        
        # جستجو در نام تشخیص‌ها
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(name_en__icontains=search) |
                Q(icd_10_code__icontains=search)
            )
        
        # فیلتر بر اساس سطح اورژانس
        urgency = self.request.query_params.get('urgency')
        if urgency:
            queryset = queryset.filter(urgency_level=urgency)
        
        return queryset.order_by('-urgency_level', 'name')
    
    @action(detail=True, methods=['get'])
    def symptoms(self, request, pk=None):
        """دریافت علائم مرتبط با تشخیص"""
        diagnosis = self.get_object()
        symptoms = diagnosis.typical_symptoms.filter(is_active=True)
        serializer = SymptomListSerializer(symptoms, many=True)
        return Response(serializer.data)


class TriageSessionViewSet(ModelViewSet):
    """
    ViewSet برای مدیریت جلسات تریاژ
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """دریافت جلسات کاربر"""
        user = self.request.user
        queryset = TriageSession.objects.filter(patient=user)
        
        # فیلتر بر اساس وضعیت
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # فیلتر بر اساس سطح اورژانس
        urgency = self.request.query_params.get('urgency')
        if urgency:
            queryset = queryset.filter(urgency_level=urgency)
        
        return queryset.order_by('-started_at')
    
    def get_serializer_class(self):
        """انتخاب serializer مناسب"""
        if self.action == 'list':
            return TriageSessionListSerializer
        elif self.action == 'create':
            return TriageSessionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TriageSessionUpdateSerializer
        return TriageSessionDetailSerializer
    
    def perform_create(self, serializer):
        """ایجاد جلسه تریاژ جدید"""
        session = serializer.save(patient=self.request.user)
        
        # شروع تحلیل اولیه
        try:
            analysis_service = TriageAnalysisService()
            analysis_service.analyze_initial_symptoms(session)
        except Exception as e:
            logger.error(f"خطا در تحلیل اولیه تریاژ: {e}")
        
        return session
    
    @action(detail=True, methods=['post'])
    def add_symptom(self, request, pk=None):
        """افزودن علامت به جلسه"""
        session = self.get_object()
        
        if session.status not in ['started', 'in_progress']:
            return Response(
                {'error': 'نمی‌توان علامت به جلسه تکمیل شده اضافه کرد'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = AddSymptomToSessionSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # دریافت علامت
                symptom = Symptom.objects.get(
                    id=serializer.validated_data['symptom_id'],
                    is_active=True
                )
                
                # ایجاد یا به‌روزرسانی علامت جلسه
                session_symptom, created = SessionSymptom.objects.update_or_create(
                    session=session,
                    symptom=symptom,
                    defaults={
                        'severity': serializer.validated_data['severity'],
                        'duration_hours': serializer.validated_data.get('duration_hours'),
                        'location': serializer.validated_data.get('location', ''),
                        'additional_details': serializer.validated_data.get('additional_details', '')
                    }
                )
                
                # به‌روزرسانی وضعیت جلسه
                if session.status == 'started':
                    session.status = 'in_progress'
                    session.save()
                
                # اجرای تحلیل مجدد
                try:
                    analysis_service = TriageAnalysisService()
                    analysis_service.analyze_session_symptoms(session)
                except Exception as e:
                    logger.error(f"خطا در تحلیل علائم: {e}")
                
                response_serializer = SessionSymptomSerializer(session_symptom)
                return Response(
                    {
                        'message': 'علامت با موفقیت اضافه شد' if created else 'علامت به‌روزرسانی شد',
                        'symptom': response_serializer.data
                    },
                    status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
                )
                
            except Symptom.DoesNotExist:
                return Response(
                    {'error': 'علامت یافت نشد'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def complete_triage(self, request, pk=None):
        """تکمیل جلسه تریاژ"""
        session = self.get_object()
        
        if session.status in ['completed', 'cancelled']:
            return Response(
                {'error': 'جلسه قبلاً تکمیل شده است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # اجرای تحلیل نهایی
        try:
            analysis_service = TriageAnalysisService()
            final_analysis = analysis_service.complete_triage_analysis(session)
            
            # به‌روزرسانی جلسه
            session.status = 'completed'
            session.completed_at = timezone.now()
            session.completed_by = request.user
            session.save()
            
            return Response({
                'message': 'تریاژ با موفقیت تکمیل شد',
                'analysis': final_analysis,
                'session': TriageSessionDetailSerializer(session).data
            })
            
        except Exception as e:
            logger.error(f"خطا در تکمیل تریاژ: {e}")
            return Response(
                {'error': 'خطا در تکمیل تریاژ'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def analysis(self, request, pk=None):
        """دریافت تحلیل جلسه تریاژ"""
        session = self.get_object()
        
        try:
            analysis_service = TriageAnalysisService()
            analysis = analysis_service.get_session_analysis(session)
            return Response(analysis)
        except Exception as e:
            logger.error(f"خطا در دریافت تحلیل: {e}")
            return Response(
                {'error': 'خطا در دریافت تحلیل'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TriageRuleViewSet(ModelViewSet):
    """
    ViewSet برای مدیریت قوانین تریاژ
    """
    queryset = TriageRule.objects.filter(is_active=True)
    serializer_class = TriageRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """فیلتر کردن قوانین"""
        queryset = super().get_queryset()
        
        # فیلتر بر اساس اولویت
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        return queryset.order_by('-priority', 'name')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def analyze_symptoms(request):
    """
    تحلیل علائم بدون ایجاد جلسه
    """
    serializer = TriageAnalysisSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            analysis_service = TriageAnalysisService()
            analysis = analysis_service.analyze_symptoms_standalone(
                symptoms=serializer.validated_data['symptoms'],
                severity_scores=serializer.validated_data.get('severity_scores', {}),
                patient_age=serializer.validated_data.get('patient_age'),
                patient_gender=serializer.validated_data.get('patient_gender'),
                medical_history=serializer.validated_data.get('medical_history', [])
            )
            
            return Response(analysis)
            
        except Exception as e:
            logger.error(f"خطا در تحلیل علائم: {e}")
            return Response(
                {'error': 'خطا در تحلیل علائم'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def search_symptoms(request):
    """
    جستجوی علائم
    """
    query = request.query_params.get('q', '').strip()
    
    if len(query) < 2:
        return Response(
            {'error': 'حداقل 2 کاراکتر وارد کنید'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # جستجو در کش
    cache_key = f"symptom_search:{query}"
    cached_result = cache.get(cache_key)
    
    if cached_result:
        return Response(cached_result)
    
    # جستجو در دیتابیس
    symptoms = Symptom.objects.filter(
        Q(name__icontains=query) | Q(name_en__icontains=query),
        is_active=True
    ).order_by('-urgency_score', 'name')[:20]
    
    serializer = SymptomListSerializer(symptoms, many=True)
    result = {
        'query': query,
        'results': serializer.data,
        'count': len(serializer.data)
    }
    
    # ذخیره در کش برای 15 دقیقه
    cache.set(cache_key, result, 900)
    
    return Response(result)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_triage_statistics(request):
    """
    دریافت آمار تریاژ
    """
    user = request.user
    
    # آمار کلی کاربر
    total_sessions = TriageSession.objects.filter(patient=user).count()
    completed_sessions = TriageSession.objects.filter(
        patient=user,
        status='completed'
    ).count()
    
    # آمار اورژانس
    urgency_stats = TriageSession.objects.filter(patient=user).values(
        'urgency_level'
    ).annotate(count=Count('id'))
    
    # آمار زمانی
    avg_duration = TriageSession.objects.filter(
        patient=user,
        status='completed'
    ).aggregate(
        avg_duration=Avg('completed_at') - Avg('started_at')
    )
    
    return Response({
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'completion_rate': (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0,
        'urgency_distribution': list(urgency_stats),
        'average_duration_minutes': int(avg_duration['avg_duration'].total_seconds() // 60) if avg_duration['avg_duration'] else 0
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_emergency_symptoms(request):
    """
    دریافت علائم اورژانسی
    """
    emergency_symptoms = Symptom.objects.filter(
        urgency_score__gte=8,
        is_active=True
    ).order_by('-urgency_score', 'name')
    
    serializer = SymptomListSerializer(emergency_symptoms, many=True)
    return Response({
        'emergency_symptoms': serializer.data,
        'warning_message': 'در صورت وجود هر یک از این علائم، فوراً به مراکز درمانی مراجعه کنید'
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_common_diagnoses(request):
    """
    دریافت تشخیص‌های رایج
    """
    # تشخیص‌های پرتکرار در سیستم
    common_diagnoses = DifferentialDiagnosis.objects.filter(
        is_active=True
    ).annotate(
        usage_count=Count('sessiondiagnosis')
    ).order_by('-usage_count', 'name')[:10]
    
    serializer = DifferentialDiagnosisListSerializer(common_diagnoses, many=True)
    return Response({
        'common_diagnoses': serializer.data
    })