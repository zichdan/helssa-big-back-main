from rest_framework import viewsets, views, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from django.db.models import Q

from ...models import AudioChunk, Transcript, Encounter
from ...services import AudioProcessingService
from ..serializers import (
    AudioChunkSerializer,
    TranscriptSerializer
)
from ..permissions import IsPatientOrDoctor, IsDoctorOfEncounter


class AudioChunkViewSet(viewsets.ModelViewSet):
    """ViewSet برای مدیریت قطعات صوتی"""
    
    serializer_class = AudioChunkSerializer
    permission_classes = [IsAuthenticated, IsPatientOrDoctor]
    
    def get_queryset(self):
        """فیلتر قطعات صوتی بر اساس دسترسی کاربر"""
        user = self.request.user
        
        # قطعات صوتی ملاقات‌های کاربر
        queryset = AudioChunk.objects.filter(
            Q(encounter__patient_id=user.id) | Q(encounter__doctor_id=user.id)
        ).select_related('encounter')
        
        # فیلتر بر اساس encounter
        encounter_id = self.request.query_params.get('encounter_id')
        if encounter_id:
            queryset = queryset.filter(encounter_id=encounter_id)
            
        # فیلتر بر اساس وضعیت پردازش
        status_filter = self.request.query_params.get('transcription_status')
        if status_filter:
            queryset = queryset.filter(transcription_status=status_filter)
            
        return queryset.order_by('encounter', 'chunk_index')
        
    def create(self, request, *args, **kwargs):
        """ایجاد قطعه صوتی ممنوع است (فقط از طریق سیستم)"""
        return Response({
            'error': 'ایجاد مستقیم قطعه صوتی مجاز نیست'
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        
    def update(self, request, *args, **kwargs):
        """به‌روزرسانی قطعه صوتی ممنوع است"""
        return Response({
            'error': 'به‌روزرسانی قطعه صوتی مجاز نیست'
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        
    def destroy(self, request, *args, **kwargs):
        """حذف قطعه صوتی ممنوع است"""
        return Response({
            'error': 'حذف قطعه صوتی مجاز نیست'
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        
    @action(detail=True, methods=['get'])
    def transcript(self, request, pk=None):
        """دریافت رونویسی قطعه"""
        audio_chunk = self.get_object()
        
        try:
            transcript = audio_chunk.transcript
            serializer = TranscriptSerializer(transcript)
            return Response(serializer.data)
        except Transcript.DoesNotExist:
            return Response({
                'error': 'رونویسی یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
            
    @action(detail=False, methods=['get'])
    def merge_status(self, request):
        """وضعیت ادغام قطعات یک ملاقات"""
        encounter_id = request.query_params.get('encounter_id')
        
        if not encounter_id:
            return Response({
                'error': 'شناسه ملاقات الزامی است'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # بررسی دسترسی
        try:
            encounter = Encounter.objects.get(id=encounter_id)
            if request.user.id not in [encounter.patient_id, encounter.doctor_id]:
                return Response({
                    'error': 'شما دسترسی به این ملاقات ندارید'
                }, status=status.HTTP_403_FORBIDDEN)
        except Encounter.DoesNotExist:
            return Response({
                'error': 'ملاقات یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
            
        # محاسبه وضعیت
        total_chunks = AudioChunk.objects.filter(
            encounter_id=encounter_id
        ).count()
        
        processed_chunks = AudioChunk.objects.filter(
            encounter_id=encounter_id,
            is_processed=True
        ).count()
        
        return Response({
            'encounter_id': encounter_id,
            'total_chunks': total_chunks,
            'processed_chunks': processed_chunks,
            'progress_percent': (processed_chunks / total_chunks * 100) if total_chunks > 0 else 0,
            'is_complete': total_chunks > 0 and processed_chunks == total_chunks
        })


class AudioUploadView(views.APIView):
    """آپلود صوت ملاقات"""
    
    permission_classes = [IsAuthenticated, IsPatientOrDoctor]
    parser_classes = [MultiPartParser]
    
    async def post(self, request, encounter_id):
        """آپلود قطعه صوتی"""
        try:
            encounter = await Encounter.objects.aget(id=encounter_id)
            
            # بررسی دسترسی
            if str(request.user.id) not in [str(encounter.patient_id), str(encounter.doctor_id)]:
                return Response({
                    'error': 'شما دسترسی به این ملاقات ندارید'
                }, status=status.HTTP_403_FORBIDDEN)
                
            # بررسی رضایت ضبط
            if not encounter.recording_consent:
                return Response({
                    'error': 'رضایت ضبط ثبت نشده است'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            # دریافت فایل
            audio_file = request.FILES.get('audio')
            if not audio_file:
                return Response({
                    'error': 'فایل صوتی ارسال نشده است'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            # دریافت chunk_index
            chunk_index = int(request.data.get('chunk_index', 0))
            
            # پردازش صوت
            audio_service = AudioProcessingService()
            audio_chunk = await audio_service.process_visit_audio(
                encounter_id=str(encounter.id),
                audio_stream=audio_file.read(),
                chunk_index=chunk_index
            )
            
            serializer = AudioChunkSerializer(audio_chunk)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
            
        except Encounter.DoesNotExist:
            return Response({
                'error': 'ملاقات یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class TranscriptViewSet(viewsets.ModelViewSet):
    """ViewSet برای مدیریت رونویسی‌ها"""
    
    serializer_class = TranscriptSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """فیلتر رونویسی‌ها بر اساس دسترسی کاربر"""
        user = self.request.user
        
        # رونویسی‌های ملاقات‌های کاربر
        queryset = Transcript.objects.filter(
            Q(audio_chunk__encounter__patient_id=user.id) |
            Q(audio_chunk__encounter__doctor_id=user.id)
        ).select_related('audio_chunk__encounter')
        
        # فیلتر بر اساس encounter
        encounter_id = self.request.query_params.get('encounter_id')
        if encounter_id:
            queryset = queryset.filter(audio_chunk__encounter_id=encounter_id)
            
        # فیلتر بر اساس confidence
        min_confidence = self.request.query_params.get('min_confidence')
        if min_confidence:
            queryset = queryset.filter(confidence_score__gte=float(min_confidence))
            
        return queryset.order_by('audio_chunk__chunk_index')
        
    def get_permissions(self):
        """تنظیم دسترسی‌ها بر اساس action"""
        if self.action in ['create', 'destroy']:
            # فقط سیستم می‌تواند ایجاد یا حذف کند
            permission_classes = [IsAuthenticated, IsDoctorOfEncounter]
        elif self.action in ['update', 'partial_update']:
            # فقط پزشک می‌تواند ویرایش کند
            permission_classes = [IsAuthenticated, IsDoctorOfEncounter]
        else:
            permission_classes = [IsAuthenticated, IsPatientOrDoctor]
        return [permission() for permission in permission_classes]
        
    @action(detail=True, methods=['post'])
    def add_correction(self, request, pk=None):
        """افزودن اصلاح به رونویسی"""
        transcript = self.get_object()
        
        # فقط پزشک می‌تواند اصلاح کند
        if str(request.user.id) != str(transcript.audio_chunk.encounter.doctor_id):
            return Response({
                'error': 'فقط پزشک می‌تواند رونویسی را اصلاح کند'
            }, status=status.HTTP_403_FORBIDDEN)
            
        original_text = request.data.get('original_text')
        corrected_text = request.data.get('corrected_text')
        
        if not original_text or not corrected_text:
            return Response({
                'error': 'متن اصلی و اصلاح شده الزامی است'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # افزودن اصلاح
        transcript.add_correction(
            original_text=original_text,
            corrected_text=corrected_text,
            corrected_by=str(request.user.id)
        )
        
        serializer = TranscriptSerializer(transcript)
        return Response({
            'status': 'success',
            'transcript': serializer.data
        })
        
    @action(detail=False, methods=['get'])
    def full_transcript(self, request):
        """دریافت رونویسی کامل یک ملاقات"""
        encounter_id = request.query_params.get('encounter_id')
        
        if not encounter_id:
            return Response({
                'error': 'شناسه ملاقات الزامی است'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # بررسی دسترسی
        try:
            encounter = Encounter.objects.get(id=encounter_id)
            if str(request.user.id) not in [str(encounter.patient_id), str(encounter.doctor_id)]:
                return Response({
                    'error': 'شما دسترسی به این ملاقات ندارید'
                }, status=status.HTTP_403_FORBIDDEN)
        except Encounter.DoesNotExist:
            return Response({
                'error': 'ملاقات یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
            
        # جمع‌آوری رونویسی‌ها
        transcripts = Transcript.objects.filter(
            audio_chunk__encounter_id=encounter_id
        ).order_by('audio_chunk__chunk_index').values_list('text', flat=True)
        
        full_text = ' '.join(transcripts)
        
        return Response({
            'encounter_id': encounter_id,
            'full_transcript': full_text,
            'word_count': len(full_text.split()),
            'chunk_count': len(transcripts)
        })