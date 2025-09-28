"""
ویوهای اپلیکیشن Checklist
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import (
    ChecklistCatalog,
    ChecklistTemplate,
    ChecklistEval,
    ChecklistAlert
)
from .serializers import (
    ChecklistCatalogSerializer,
    ChecklistTemplateSerializer,
    ChecklistEvalSerializer,
    ChecklistEvalCreateSerializer,
    ChecklistAlertSerializer,
    ChecklistSummarySerializer,
    BulkEvaluationSerializer
)
from .services import ChecklistService, ChecklistEvaluationService


class ChecklistCatalogViewSet(viewsets.ModelViewSet):
    """
    ViewSet برای مدیریت آیتم‌های کاتالوگ چک‌لیست
    """
    queryset = ChecklistCatalog.objects.all()
    serializer_class = ChecklistCatalogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        فیلتر کردن آیتم‌ها بر اساس پارامترهای query
        """
        queryset = super().get_queryset()
        
        # فیلتر بر اساس دسته‌بندی
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # فیلتر بر اساس اولویت
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # فیلتر بر اساس تخصص
        specialty = self.request.query_params.get('specialty')
        if specialty:
            queryset = queryset.filter(specialty__icontains=specialty)
        
        # فیلتر بر اساس وضعیت فعال
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # جستجو در عنوان و توضیحات
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(keywords__icontains=search)
            )
        
        return queryset
    
    def perform_create(self, serializer):
        """
        ذخیره کاربر ایجادکننده
        """
        serializer.save(created_by=self.request.user, updated_by=self.request.user)
    
    def perform_update(self, serializer):
        """
        ذخیره کاربر به‌روزرسانی‌کننده
        """
        serializer.save(updated_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """
        دریافت آیتم‌ها گروه‌بندی شده بر اساس دسته‌بندی
        """
        categories = {}
        for cat_value, cat_display in ChecklistCatalog.CATEGORY_CHOICES:
            items = self.get_queryset().filter(category=cat_value)
            if items.exists():
                categories[cat_value] = {
                    'display': cat_display,
                    'count': items.count(),
                    'items': ChecklistCatalogSerializer(items[:5], many=True).data
                }
        
        return Response(categories)


class ChecklistTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet برای مدیریت قالب‌های چک‌لیست
    """
    queryset = ChecklistTemplate.objects.all()
    serializer_class = ChecklistTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        فیلتر کردن قالب‌ها
        """
        queryset = super().get_queryset()
        
        # فیلتر بر اساس تخصص
        specialty = self.request.query_params.get('specialty')
        if specialty:
            queryset = queryset.filter(specialty__icontains=specialty)
        
        # فیلتر بر اساس شکایت اصلی
        chief_complaint = self.request.query_params.get('chief_complaint')
        if chief_complaint:
            queryset = queryset.filter(chief_complaint__icontains=chief_complaint)
        
        # فیلتر بر اساس وضعیت فعال
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # جستجو
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.annotate(items_count=Count('catalog_items'))
    
    def perform_create(self, serializer):
        """
        ذخیره کاربر ایجادکننده
        """
        serializer.save(created_by=self.request.user, updated_by=self.request.user)
    
    def perform_update(self, serializer):
        """
        ذخیره کاربر به‌روزرسانی‌کننده
        """
        serializer.save(updated_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        ایجاد کپی از یک قالب
        """
        template = self.get_object()
        
        # ایجاد قالب جدید
        new_template = ChecklistTemplate.objects.create(
            name=f"{template.name} (کپی)",
            description=template.description,
            specialty=template.specialty,
            chief_complaint=template.chief_complaint,
            is_active=True,
            created_by=request.user,
            updated_by=request.user
        )
        
        # کپی آیتم‌های کاتالوگ
        new_template.catalog_items.set(template.catalog_items.all())
        
        serializer = self.get_serializer(new_template)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChecklistEvalViewSet(viewsets.ModelViewSet):
    """
    ViewSet برای مدیریت ارزیابی‌های چک‌لیست
    """
    queryset = ChecklistEval.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        انتخاب سریالایزر بر اساس action
        """
        if self.action == 'create':
            return ChecklistEvalCreateSerializer
        return ChecklistEvalSerializer
    
    def get_queryset(self):
        """
        فیلتر کردن ارزیابی‌ها
        """
        queryset = super().get_queryset()
        
        # فیلتر بر اساس ویزیت
        encounter_id = self.request.query_params.get('encounter_id')
        if encounter_id:
            queryset = queryset.filter(encounter_id=encounter_id)
        
        # فیلتر بر اساس وضعیت
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # فیلتر بر اساس دسته‌بندی آیتم
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(catalog_item__category=category)
        
        # فیلتر بر اساس اولویت آیتم
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(catalog_item__priority=priority)
        
        # فیلتر بر اساس وضعیت تایید
        is_acknowledged = self.request.query_params.get('is_acknowledged')
        if is_acknowledged is not None:
            queryset = queryset.filter(is_acknowledged=is_acknowledged.lower() == 'true')
        
        # فیلتر آیتم‌های نیازمند توجه
        needs_attention = self.request.query_params.get('needs_attention')
        if needs_attention and needs_attention.lower() == 'true':
            queryset = queryset.filter(
                Q(status__in=['missing', 'unclear']) |
                (Q(status='partial') & Q(confidence_score__lt=0.7))
            )
        
        return queryset.select_related('encounter', 'catalog_item')
    
    def perform_create(self, serializer):
        """
        ذخیره کاربر ایجادکننده
        """
        serializer.save(created_by=self.request.user, updated_by=self.request.user)
    
    def perform_update(self, serializer):
        """
        ذخیره کاربر به‌روزرسانی‌کننده
        """
        serializer.save(updated_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def bulk_evaluate(self, request):
        """
        ارزیابی دسته‌ای چک‌لیست برای یک ویزیت
        """
        serializer = BulkEvaluationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        encounter_id = serializer.validated_data['encounter_id']
        template_id = serializer.validated_data.get('template_id')
        
        service = ChecklistEvaluationService()
        
        try:
            result = service.evaluate_encounter(encounter_id, template_id)
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': 'خطا در ارزیابی چک‌لیست'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        دریافت خلاصه وضعیت چک‌لیست برای یک ویزیت
        """
        encounter_id = request.query_params.get('encounter_id')
        if not encounter_id:
            return Response(
                {'error': 'encounter_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = ChecklistService()
        summary = service.get_evaluation_summary(int(encounter_id))
        
        serializer = ChecklistSummarySerializer(summary)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_questions(self, request):
        """
        دریافت سوالات در انتظار پاسخ
        """
        encounter_id = request.query_params.get('encounter_id')
        if not encounter_id:
            return Response(
                {'error': 'encounter_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = ChecklistService()
        questions = service.get_pending_questions(int(encounter_id))
        
        return Response({'questions': questions})
    
    @action(detail=True, methods=['post'])
    def answer_question(self, request, pk=None):
        """
        پاسخ به سوال چک‌لیست
        """
        evaluation = self.get_object()
        
        doctor_response = request.data.get('doctor_response')
        if not doctor_response:
            return Response(
                {'error': 'doctor_response is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        evaluation.doctor_response = doctor_response
        evaluation.is_acknowledged = True
        evaluation.acknowledged_at = timezone.now()
        evaluation.save()
        
        serializer = self.get_serializer(evaluation)
        return Response(serializer.data)


class ChecklistAlertViewSet(viewsets.ModelViewSet):
    """
    ViewSet برای مدیریت هشدارهای چک‌لیست
    """
    queryset = ChecklistAlert.objects.all()
    serializer_class = ChecklistAlertSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch', 'head', 'options']  # فقط خواندن و به‌روزرسانی
    
    def get_queryset(self):
        """
        فیلتر کردن هشدارها
        """
        queryset = super().get_queryset()
        
        # فیلتر بر اساس ویزیت
        encounter_id = self.request.query_params.get('encounter_id')
        if encounter_id:
            queryset = queryset.filter(encounter_id=encounter_id)
        
        # فیلتر بر اساس نوع هشدار
        alert_type = self.request.query_params.get('alert_type')
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        
        # فیلتر بر اساس وضعیت رد شدن
        is_dismissed = self.request.query_params.get('is_dismissed')
        if is_dismissed is not None:
            queryset = queryset.filter(is_dismissed=is_dismissed.lower() == 'true')
        
        # به صورت پیش‌فرض فقط هشدارهای فعال را نمایش بده
        if 'show_all' not in self.request.query_params:
            queryset = queryset.filter(is_dismissed=False)
        
        return queryset.select_related('encounter', 'evaluation', 'dismissed_by')
    
    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        """
        رد کردن یک هشدار
        """
        alert = self.get_object()
        
        if alert.is_dismissed:
            return Response(
                {'message': 'این هشدار قبلاً رد شده است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        alert.is_dismissed = True
        alert.dismissed_at = timezone.now()
        alert.dismissed_by = request.user
        alert.save()
        
        serializer = self.get_serializer(alert)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def dismiss_bulk(self, request):
        """
        رد کردن دسته‌ای هشدارها
        """
        alert_ids = request.data.get('alert_ids', [])
        if not alert_ids:
            return Response(
                {'error': 'alert_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        alerts = ChecklistAlert.objects.filter(
            id__in=alert_ids,
            is_dismissed=False
        )
        
        updated_count = alerts.update(
            is_dismissed=True,
            dismissed_at=timezone.now(),
            dismissed_by=request.user
        )
        
        return Response({
            'message': f'{updated_count} هشدار رد شد',
            'dismissed_count': updated_count
        })