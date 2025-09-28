from rest_framework import viewsets, views, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q

from ...models import SOAPReport, Prescription, Encounter
from ...services import SOAPGenerationService
from ..serializers import (
    SOAPReportSerializer,
    PrescriptionSerializer
)
from ..permissions import (
    IsDoctorOfEncounter,
    IsPatientOrDoctor,
    CanModifySOAPReport,
    CanViewPrescription
)


class SOAPReportViewSet(viewsets.ModelViewSet):
    """ViewSet برای مدیریت گزارش‌های SOAP"""
    
    serializer_class = SOAPReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """فیلتر گزارش‌ها بر اساس دسترسی کاربر"""
        user = self.request.user
        
        # گزارش‌های ملاقات‌های کاربر
        queryset = SOAPReport.objects.filter(
            Q(encounter__patient_id=user.id) | Q(encounter__doctor_id=user.id)
        ).select_related('encounter')
        
        # فیلتر بر اساس وضعیت
        if self.request.query_params.get('approved_only') == 'true':
            queryset = queryset.filter(doctor_approved=True)
            
        if self.request.query_params.get('draft_only') == 'true':
            queryset = queryset.filter(is_draft=True)
            
        return queryset.order_by('-created_at')
        
    def get_permissions(self):
        """تنظیم دسترسی‌ها بر اساس action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, CanModifySOAPReport]
        else:
            permission_classes = [IsAuthenticated, IsPatientOrDoctor]
        return [permission() for permission in permission_classes]
        
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """تایید گزارش توسط پزشک"""
        report = self.get_object()
        
        # فقط پزشک می‌تواند تایید کند
        if str(request.user.id) != str(report.encounter.doctor_id):
            return Response({
                'error': 'فقط پزشک می‌تواند گزارش را تایید کند'
            }, status=status.HTTP_403_FORBIDDEN)
            
        # بررسی کامل بودن گزارش
        if not report.is_complete:
            return Response({
                'error': 'گزارش کامل نیست'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        report.approve_by_doctor(str(request.user.id))
        
        serializer = SOAPReportSerializer(report)
        return Response({
            'status': 'approved',
            'report': serializer.data
        })
        
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """اشتراک گزارش با بیمار"""
        report = self.get_object()
        
        # فقط پزشک می‌تواند به اشتراک بگذارد
        if str(request.user.id) != str(report.encounter.doctor_id):
            return Response({
                'error': 'فقط پزشک می‌تواند گزارش را به اشتراک بگذارد'
            }, status=status.HTTP_403_FORBIDDEN)
            
        # گزارش باید تایید شده باشد
        if not report.doctor_approved:
            return Response({
                'error': 'گزارش باید ابتدا تایید شود'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        report.share_with_patient()
        
        # TODO: ارسال نوتیفیکیشن به بیمار
        
        serializer = SOAPReportSerializer(report)
        return Response({
            'status': 'shared',
            'report': serializer.data
        })
        
    @action(detail=True, methods=['post'])
    def add_diagnosis(self, request, pk=None):
        """افزودن تشخیص"""
        report = self.get_object()
        
        # فقط پزشک می‌تواند تشخیص اضافه کند
        if str(request.user.id) != str(report.encounter.doctor_id):
            return Response({
                'error': 'فقط پزشک می‌تواند تشخیص اضافه کند'
            }, status=status.HTTP_403_FORBIDDEN)
            
        name = request.data.get('name')
        icd_code = request.data.get('icd_code')
        is_primary = request.data.get('is_primary', False)
        
        if not name or not icd_code:
            return Response({
                'error': 'نام و کد ICD الزامی است'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        report.add_diagnosis(name, icd_code, is_primary)
        
        serializer = SOAPReportSerializer(report)
        return Response({
            'status': 'added',
            'report': serializer.data
        })
        
    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """دانلود PDF گزارش"""
        report = self.get_object()
        
        # بررسی دسترسی
        if str(request.user.id) not in [
            str(report.encounter.patient_id),
            str(report.encounter.doctor_id)
        ]:
            return Response({
                'error': 'شما دسترسی به این گزارش ندارید'
            }, status=status.HTTP_403_FORBIDDEN)
            
        # بیمار فقط گزارش‌های share شده را می‌بیند
        if (str(request.user.id) == str(report.encounter.patient_id) and 
            not report.patient_shared):
            return Response({
                'error': 'این گزارش هنوز با شما به اشتراک گذاشته نشده است'
            }, status=status.HTTP_403_FORBIDDEN)
            
        if not report.pdf_url:
            return Response({
                'error': 'فایل PDF موجود نیست'
            }, status=status.HTTP_404_NOT_FOUND)
            
        # TODO: تولید لینک دانلود موقت
        
        return Response({
            'download_url': report.pdf_url,
            'filename': f'SOAP_Report_{report.encounter.id}.pdf'
        })


class PrescriptionViewSet(viewsets.ModelViewSet):
    """ViewSet برای مدیریت نسخه‌ها"""
    
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated, CanViewPrescription]
    
    def get_queryset(self):
        """فیلتر نسخه‌ها بر اساس دسترسی کاربر"""
        user = self.request.user
        
        # نسخه‌های ملاقات‌های کاربر
        queryset = Prescription.objects.filter(
            Q(encounter__patient_id=user.id) | Q(encounter__doctor_id=user.id)
        ).select_related('encounter')
        
        # فیلتر بر اساس وضعیت
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        return queryset.order_by('-created_at')
        
    def get_permissions(self):
        """تنظیم دسترسی‌ها بر اساس action"""
        if self.action in ['create', 'update', 'partial_update']:
            # فقط پزشک می‌تواند نسخه بنویسد
            permission_classes = [IsAuthenticated, IsDoctorOfEncounter]
        elif self.action == 'destroy':
            # حذف نسخه ممنوع است
            permission_classes = []
        else:
            permission_classes = [IsAuthenticated, CanViewPrescription]
        return [permission() for permission in permission_classes]
        
    def destroy(self, request, *args, **kwargs):
        """حذف نسخه ممنوع است"""
        return Response({
            'error': 'حذف نسخه مجاز نیست'
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        
    @action(detail=True, methods=['post'])
    def add_medication(self, request, pk=None):
        """افزودن دارو به نسخه"""
        prescription = self.get_object()
        
        # فقط پزشک می‌تواند دارو اضافه کند
        if str(request.user.id) != str(prescription.encounter.doctor_id):
            return Response({
                'error': 'فقط پزشک می‌تواند دارو اضافه کند'
            }, status=status.HTTP_403_FORBIDDEN)
            
        # نسخه نباید صادر شده باشد
        if prescription.status != 'draft':
            return Response({
                'error': 'نسخه قبلاً صادر شده است'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        medication_data = request.data
        
        try:
            prescription.add_medication(medication_data)
            serializer = PrescriptionSerializer(prescription)
            return Response({
                'status': 'added',
                'prescription': serializer.data
            })
        except ValueError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
    @action(detail=True, methods=['post'])
    def issue(self, request, pk=None):
        """صدور نسخه"""
        prescription = self.get_object()
        
        # فقط پزشک می‌تواند صادر کند
        if str(request.user.id) != str(prescription.encounter.doctor_id):
            return Response({
                'error': 'فقط پزشک می‌تواند نسخه صادر کند'
            }, status=status.HTTP_403_FORBIDDEN)
            
        # بررسی وجود دارو
        if prescription.medication_count == 0:
            return Response({
                'error': 'نسخه باید حداقل یک دارو داشته باشد'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        prescription.issue()
        
        # TODO: تولید امضای دیجیتال
        # prescription.sign(digital_signature)
        
        serializer = PrescriptionSerializer(prescription)
        return Response({
            'status': 'issued',
            'prescription': serializer.data
        })
        
    @action(detail=True, methods=['post'])
    def dispense(self, request, pk=None):
        """تحویل نسخه توسط داروخانه"""
        prescription = self.get_object()
        
        # TODO: بررسی دسترسی داروخانه
        
        if not prescription.can_dispense:
            return Response({
                'error': 'این نسخه قابل تحویل نیست'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        pharmacy_id = request.data.get('pharmacy_id')
        dispensed_by = request.data.get('dispensed_by')
        
        if not pharmacy_id or not dispensed_by:
            return Response({
                'error': 'اطلاعات داروخانه الزامی است'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        prescription.dispense(pharmacy_id, dispensed_by)
        
        serializer = PrescriptionSerializer(prescription)
        return Response({
            'status': 'dispensed',
            'prescription': serializer.data
        })


class GenerateSOAPView(views.APIView):
    """تولید گزارش SOAP"""
    
    permission_classes = [IsAuthenticated, IsDoctorOfEncounter]
    
    async def post(self, request, encounter_id):
        """تولید گزارش SOAP برای ملاقات"""
        try:
            encounter = await Encounter.objects.aget(id=encounter_id)
            
            # بررسی دسترسی
            if str(request.user.id) != str(encounter.doctor_id):
                return Response({
                    'error': 'فقط پزشک می‌تواند گزارش تولید کند'
                }, status=status.HTTP_403_FORBIDDEN)
                
            # بررسی وضعیت ملاقات
            if encounter.status != 'completed':
                return Response({
                    'error': 'ملاقات باید تکمیل شده باشد'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            # تولید گزارش
            soap_service = SOAPGenerationService()
            regenerate = request.data.get('regenerate', False)
            
            report = await soap_service.generate_soap_report(
                encounter_id=str(encounter.id),
                regenerate=regenerate
            )
            
            serializer = SOAPReportSerializer(report)
            return Response({
                'status': 'generated',
                'report': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Encounter.DoesNotExist:
            return Response({
                'error': 'ملاقات یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ShareReportView(views.APIView):
    """اشتراک‌گذاری گزارش با بیمار"""
    
    permission_classes = [IsAuthenticated, IsDoctorOfEncounter]
    
    def post(self, request, report_id):
        """اشتراک گزارش"""
        try:
            report = SOAPReport.objects.select_related('encounter').get(id=report_id)
            
            # بررسی دسترسی
            if str(request.user.id) != str(report.encounter.doctor_id):
                return Response({
                    'error': 'فقط پزشک می‌تواند گزارش را به اشتراک بگذارد'
                }, status=status.HTTP_403_FORBIDDEN)
                
            # بررسی تایید گزارش
            if not report.doctor_approved:
                return Response({
                    'error': 'گزارش باید ابتدا تایید شود'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            report.share_with_patient()
            
            # TODO: ارسال نوتیفیکیشن به بیمار
            
            return Response({
                'status': 'shared',
                'shared_at': report.patient_shared_at
            })
            
        except SOAPReport.DoesNotExist:
            return Response({
                'error': 'گزارش یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)