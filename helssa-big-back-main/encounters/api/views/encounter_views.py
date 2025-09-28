from rest_framework import viewsets, views, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q

from ...models import Encounter
from ...services import VisitSchedulingService
from ..serializers import (
    EncounterSerializer,
    EncounterCreateSerializer,
    EncounterStatusUpdateSerializer,
    RecordingConsentSerializer,
    VisitStartSerializer
)
from ..permissions import (
    IsPatientOrDoctor,
    IsDoctorOfEncounter,
    CanStartEncounter
)


class EncounterViewSet(viewsets.ModelViewSet):
    """ViewSet برای مدیریت ملاقات‌ها"""
    
    serializer_class = EncounterSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """فیلتر ملاقات‌ها بر اساس کاربر"""
        user = self.request.user
        
        # ملاقات‌های کاربر (به عنوان بیمار یا پزشک)
        queryset = Encounter.objects.filter(
            Q(patient_id=user.id) | Q(doctor_id=user.id)
        ).select_related('patient', 'doctor')
        
        # فیلترهای اضافی
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(scheduled_at__gte=date_from)
            
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(scheduled_at__lte=date_to)
            
        return queryset.order_by('-scheduled_at')
        
    def get_serializer_class(self):
        """انتخاب serializer بر اساس action"""
        if self.action == 'create':
            return EncounterCreateSerializer
        elif self.action == 'update_status':
            return EncounterStatusUpdateSerializer
        elif self.action == 'set_recording_consent':
            return RecordingConsentSerializer
        return EncounterSerializer
        
    def get_permissions(self):
        """تنظیم دسترسی‌ها بر اساس action"""
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsDoctorOfEncounter]
        elif self.action in ['retrieve', 'list']:
            permission_classes = [IsAuthenticated, IsPatientOrDoctor]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
        
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """ملاقات‌های آینده"""
        queryset = self.get_queryset().filter(
            scheduled_at__gt=timezone.now(),
            status__in=['scheduled', 'confirmed']
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
        
    @action(detail=False, methods=['get'])
    def today(self, request):
        """ملاقات‌های امروز"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            scheduled_at__date=today
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
        
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """تغییر وضعیت ملاقات"""
        encounter = self.get_object()
        serializer = EncounterStatusUpdateSerializer(
            encounter, data=request.data, partial=True
        )
        
        if serializer.is_valid():
            new_status = serializer.validated_data['status']
            reason = serializer.validated_data.get('reason', '')
            
            # به‌روزرسانی وضعیت
            encounter.status = new_status
            if reason and new_status == 'cancelled':
                encounter.metadata['cancellation_reason'] = reason
            encounter.save()
            
            return Response({
                'status': 'success',
                'new_status': new_status
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=True, methods=['post'])
    def set_recording_consent(self, request, pk=None):
        """ثبت رضایت ضبط"""
        encounter = self.get_object()
        serializer = RecordingConsentSerializer(data=request.data)
        
        if serializer.is_valid():
            encounter.recording_consent = serializer.validated_data['recording_consent']
            encounter.metadata['recording_consent_date'] = timezone.now().isoformat()
            encounter.metadata['recording_consent_by'] = str(request.user.id)
            encounter.save()
            
            return Response({
                'status': 'success',
                'recording_consent': encounter.recording_consent
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EncounterScheduleView(views.APIView):
    """زمان‌بندی ملاقات جدید"""
    
    permission_classes = [IsAuthenticated]
    
    async def post(self, request):
        """ایجاد ملاقات جدید"""
        serializer = EncounterCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            scheduling_service = VisitSchedulingService()
            
            try:
                encounter = await scheduling_service.schedule_visit(
                    patient_id=str(serializer.validated_data['patient'].id),
                    doctor_id=str(serializer.validated_data['doctor'].id),
                    visit_type=serializer.validated_data['type'],
                    scheduled_at=serializer.validated_data['scheduled_at'],
                    duration_minutes=serializer.validated_data.get('duration_minutes', 30),
                    chief_complaint=serializer.validated_data['chief_complaint'],
                    notes=serializer.validated_data.get('patient_notes')
                )
                
                # سریالایز نتیجه
                result_serializer = EncounterSerializer(encounter)
                return Response(
                    result_serializer.data,
                    status=status.HTTP_201_CREATED
                )
                
            except Exception as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EncounterStatusView(views.APIView):
    """مدیریت وضعیت ملاقات"""
    
    permission_classes = [IsAuthenticated, IsPatientOrDoctor]
    
    def post(self, request, encounter_id):
        """تغییر وضعیت"""
        try:
            encounter = Encounter.objects.get(id=encounter_id)
            self.check_object_permissions(request, encounter)
            
            action = request.data.get('action')
            
            if action == 'confirm':
                return self._confirm_encounter(encounter, request.user.id)
            elif action == 'cancel':
                reason = request.data.get('reason', '')
                return self._cancel_encounter(encounter, request.user.id, reason)
                
            return Response({
                'error': 'عملیات نامعتبر'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Encounter.DoesNotExist:
            return Response({
                'error': 'ملاقات یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
            
    async def _confirm_encounter(self, encounter, user_id):
        """تایید ملاقات"""
        scheduling_service = VisitSchedulingService()
        
        try:
            confirmed_encounter = await scheduling_service.confirm_visit(
                str(encounter.id),
                str(user_id)
            )
            
            serializer = EncounterSerializer(confirmed_encounter)
            return Response({
                'status': 'confirmed',
                'encounter': serializer.data
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
    async def _cancel_encounter(self, encounter, user_id, reason):
        """لغو ملاقات"""
        scheduling_service = VisitSchedulingService()
        
        try:
            cancelled_encounter = await scheduling_service.cancel_visit(
                str(encounter.id),
                str(user_id),
                reason
            )
            
            serializer = EncounterSerializer(cancelled_encounter)
            return Response({
                'status': 'cancelled',
                'encounter': serializer.data
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class VisitStartView(views.APIView):
    """شروع ویزیت"""
    
    permission_classes = [IsAuthenticated, CanStartEncounter]
    
    async def post(self, request, encounter_id):
        """شروع ملاقات"""
        try:
            encounter = await Encounter.objects.aget(id=encounter_id)
            self.check_object_permissions(request, encounter)
            
            scheduling_service = VisitSchedulingService()
            
            visit_info = await scheduling_service.start_visit(
                str(encounter.id),
                str(request.user.id)
            )
            
            return Response({
                'status': 'started',
                'visit_info': visit_info
            })
            
        except Encounter.DoesNotExist:
            return Response({
                'error': 'ملاقات یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class VisitEndView(views.APIView):
    """پایان ویزیت"""
    
    permission_classes = [IsAuthenticated, IsPatientOrDoctor]
    
    async def post(self, request, encounter_id):
        """پایان ملاقات"""
        try:
            encounter = await Encounter.objects.aget(id=encounter_id)
            self.check_object_permissions(request, encounter)
            
            scheduling_service = VisitSchedulingService()
            
            ended_encounter = await scheduling_service.end_visit(
                str(encounter.id),
                str(request.user.id)
            )
            
            serializer = EncounterSerializer(ended_encounter)
            return Response({
                'status': 'ended',
                'encounter': serializer.data
            })
            
        except Encounter.DoesNotExist:
            return Response({
                'error': 'ملاقات یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)