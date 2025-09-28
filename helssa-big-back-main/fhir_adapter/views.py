from rest_framework import viewsets, views, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.core.paginator import Paginator
from typing import Dict, Any, Optional
import logging

from .models import FHIRResource, FHIRMapping, FHIRBundle, FHIRExportLog
from .serializers import (
    FHIRResourceSerializer,
    FHIRMappingSerializer,
    FHIRBundleSerializer,
    FHIRExportLogSerializer,
    FHIRTransformSerializer,
    FHIRImportSerializer,
    FHIRSearchSerializer
)
from .utils import FHIRTransformer, FHIRValidator

logger = logging.getLogger(__name__)


class FHIRResourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet برای مدیریت منابع FHIR
    
    عملیات CRUD کامل برای منابع FHIR
    """
    queryset = FHIRResource.objects.all()
    serializer_class = FHIRResourceSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'resource_id'
    
    def get_queryset(self):
        """فیلتر کردن بر اساس پارامترهای query"""
        queryset = super().get_queryset()
        
        # فیلتر بر اساس نوع منبع
        resource_type = self.request.query_params.get('type')
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        
        # فیلتر بر اساس مدل داخلی
        internal_model = self.request.query_params.get('internal_model')
        if internal_model:
            queryset = queryset.filter(internal_model=internal_model)
        
        # فیلتر بر اساس شناسه داخلی
        internal_id = self.request.query_params.get('internal_id')
        if internal_id:
            queryset = queryset.filter(internal_id=internal_id)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def history(self, request, resource_id=None):
        """
        دریافت تاریخچه تغییرات یک منبع
        """
        resource = self.get_object()
        
        # در اینجا می‌توان تاریخچه را از سیستم audit trail دریافت کرد
        # فعلاً یک پاسخ ساده برمی‌گردانیم
        history_data = {
            'resource_id': str(resource.resource_id),
            'resource_type': resource.resource_type,
            'current_version': resource.version,
            'last_updated': resource.last_updated,
            'created': resource.created,
            'versions': []  # لیست نسخه‌های قبلی
        }
        
        return Response(history_data)
    
    @action(detail=False, methods=['post'])
    def validate(self, request):
        """
        اعتبارسنجی یک منبع FHIR بدون ذخیره آن
        """
        serializer = FHIRResourceSerializer(data=request.data)
        
        if serializer.is_valid():
            # اعتبارسنجی محتوای FHIR
            validator = FHIRValidator()
            validation_result = validator.validate(
                serializer.validated_data['resource_type'],
                serializer.validated_data['resource_content']
            )
            
            return Response({
                'valid': validation_result['valid'],
                'errors': validation_result.get('errors', []),
                'warnings': validation_result.get('warnings', [])
            })
        
        return Response(
            {'valid': False, 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )


class FHIRMappingViewSet(viewsets.ModelViewSet):
    """
    ViewSet برای مدیریت نقشه‌برداری‌های FHIR
    """
    queryset = FHIRMapping.objects.filter(is_active=True)
    serializer_class = FHIRMappingSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'mapping_id'
    
    @action(detail=False, methods=['get'])
    def by_model(self, request):
        """
        دریافت نقشه‌برداری بر اساس مدل منبع
        """
        source_model = request.query_params.get('model')
        if not source_model:
            return Response(
                {'error': 'پارامتر model الزامی است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        mappings = self.get_queryset().filter(source_model=source_model)
        serializer = self.get_serializer(mappings, many=True)
        return Response(serializer.data)


class FHIRBundleViewSet(viewsets.ModelViewSet):
    """
    ViewSet برای مدیریت Bundle های FHIR
    """
    queryset = FHIRBundle.objects.all()
    serializer_class = FHIRBundleSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'bundle_id'
    
    @action(detail=True, methods=['post'])
    def add_resource(self, request, bundle_id=None):
        """
        اضافه کردن منبع به Bundle
        """
        bundle = self.get_object()
        resource_id = request.data.get('resource_id')
        
        if not resource_id:
            return Response(
                {'error': 'resource_id الزامی است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            resource = FHIRResource.objects.get(resource_id=resource_id)
            bundle.resources.add(resource)
            bundle.total = bundle.resources.count()
            bundle.save()
            
            return Response({
                'message': 'منبع با موفقیت اضافه شد',
                'total': bundle.total
            })
        except FHIRResource.DoesNotExist:
            return Response(
                {'error': 'منبع یافت نشد'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remove_resource(self, request, bundle_id=None):
        """
        حذف منبع از Bundle
        """
        bundle = self.get_object()
        resource_id = request.data.get('resource_id')
        
        if not resource_id:
            return Response(
                {'error': 'resource_id الزامی است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            resource = FHIRResource.objects.get(resource_id=resource_id)
            bundle.resources.remove(resource)
            bundle.total = bundle.resources.count()
            bundle.save()
            
            return Response({
                'message': 'منبع با موفقیت حذف شد',
                'total': bundle.total
            })
        except FHIRResource.DoesNotExist:
            return Response(
                {'error': 'منبع یافت نشد'},
                status=status.HTTP_404_NOT_FOUND
            )


class FHIRTransformView(views.APIView):
    """
    View برای تبدیل داده‌های داخلی به FHIR
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        تبدیل یک رکورد داخلی به منبع FHIR
        """
        serializer = FHIRTransformSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        
        # ایجاد لاگ عملیات
        export_log = FHIRExportLog.objects.create(
            operation_type='transform',
            source_model=validated_data['source_model'],
            target_resource_type=validated_data['target_resource_type'],
            performed_by=request.user.username if request.user else None
        )
        
        try:
            # دریافت نقشه‌برداری
            mapping = FHIRMapping.objects.get(
                source_model=validated_data['source_model'],
                target_resource_type=validated_data['target_resource_type'],
                is_active=True
            )
            
            # انجام تبدیل
            transformer = FHIRTransformer()
            result = transformer.transform(
                source_model=validated_data['source_model'],
                source_id=validated_data['source_id'],
                mapping=mapping,
                include_related=validated_data.get('include_related', False)
            )
            
            # ذخیره منبع FHIR
            fhir_resource = FHIRResource.objects.create(
                resource_type=validated_data['target_resource_type'],
                resource_content=result['resource'],
                internal_model=validated_data['source_model'],
                internal_id=validated_data['source_id']
            )
            
            # به‌روزرسانی لاگ
            export_log.status = 'success'
            export_log.records_processed = 1
            export_log.completed_at = timezone.now()
            export_log.save()
            
            return Response({
                'resource_id': str(fhir_resource.resource_id),
                'resource_type': fhir_resource.resource_type,
                'resource': result['resource']
            }, status=status.HTTP_201_CREATED)
            
        except FHIRMapping.DoesNotExist:
            export_log.status = 'failed'
            export_log.error_message = 'نقشه‌برداری یافت نشد'
            export_log.completed_at = timezone.now()
            export_log.save()
            
            return Response(
                {'error': 'نقشه‌برداری برای این تبدیل یافت نشد'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"خطا در تبدیل FHIR: {str(e)}")
            export_log.status = 'failed'
            export_log.error_message = str(e)
            export_log.completed_at = timezone.now()
            export_log.save()
            
            return Response(
                {'error': f'خطا در تبدیل: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FHIRImportView(views.APIView):
    """
    View برای واردات منابع FHIR
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        واردات یک منبع FHIR
        """
        serializer = FHIRImportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        
        # ایجاد لاگ عملیات
        import_log = FHIRExportLog.objects.create(
            operation_type='import',
            target_resource_type=validated_data['resource_type'],
            performed_by=request.user.username if request.user else None
        )
        
        try:
            with transaction.atomic():
                # بررسی وجود منبع
                existing_resource = None
                if validated_data.get('update_existing'):
                    # جستجو بر اساس id در محتوا
                    resource_id = validated_data['resource_content'].get('id')
                    if resource_id:
                        existing_resource = FHIRResource.objects.filter(
                            resource_content__id=resource_id,
                            resource_type=validated_data['resource_type']
                        ).first()
                
                if existing_resource:
                    # به‌روزرسانی منبع موجود
                    existing_resource.resource_content = validated_data['resource_content']
                    existing_resource.version += 1
                    existing_resource.save()
                    
                    import_log.status = 'success'
                    import_log.records_processed = 1
                    import_log.details = {'action': 'updated', 'resource_id': str(existing_resource.resource_id)}
                    
                    resource = existing_resource
                else:
                    # ایجاد منبع جدید
                    resource = FHIRResource.objects.create(
                        resource_type=validated_data['resource_type'],
                        resource_content=validated_data['resource_content']
                    )
                    
                    import_log.status = 'success'
                    import_log.records_processed = 1
                    import_log.details = {'action': 'created', 'resource_id': str(resource.resource_id)}
                
                import_log.completed_at = timezone.now()
                import_log.save()
                
                return Response({
                    'resource_id': str(resource.resource_id),
                    'resource_type': resource.resource_type,
                    'action': import_log.details['action'],
                    'version': resource.version
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"خطا در واردات FHIR: {str(e)}")
            import_log.status = 'failed'
            import_log.error_message = str(e)
            import_log.completed_at = timezone.now()
            import_log.save()
            
            return Response(
                {'error': f'خطا در واردات: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FHIRSearchView(views.APIView):
    """
    View برای جستجوی پیشرفته منابع FHIR
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        جستجوی منابع FHIR
        """
        serializer = FHIRSearchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        
        # ساخت query
        queryset = FHIRResource.objects.all()
        
        if validated_data.get('resource_type'):
            queryset = queryset.filter(resource_type=validated_data['resource_type'])
        
        if validated_data.get('internal_id'):
            queryset = queryset.filter(internal_id=validated_data['internal_id'])
        
        if validated_data.get('internal_model'):
            queryset = queryset.filter(internal_model=validated_data['internal_model'])
        
        if validated_data.get('date_from'):
            queryset = queryset.filter(last_updated__gte=validated_data['date_from'])
        
        if validated_data.get('date_to'):
            queryset = queryset.filter(last_updated__lte=validated_data['date_to'])
        
        # صفحه‌بندی
        paginator = Paginator(queryset, validated_data['page_size'])
        page = paginator.get_page(validated_data['page'])
        
        # سریالایز نتایج
        resource_serializer = FHIRResourceSerializer(page.object_list, many=True)
        
        return Response({
            'total': paginator.count,
            'page': validated_data['page'],
            'page_size': validated_data['page_size'],
            'total_pages': paginator.num_pages,
            'results': resource_serializer.data
        })


class FHIRExportLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet برای مشاهده لاگ‌های صادرات/واردات
    """
    queryset = FHIRExportLog.objects.all()
    serializer_class = FHIRExportLogSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'log_id'
    
    def get_queryset(self):
        """فیلتر کردن بر اساس پارامترها"""
        queryset = super().get_queryset()
        
        # فیلتر بر اساس نوع عملیات
        operation_type = self.request.query_params.get('operation_type')
        if operation_type:
            queryset = queryset.filter(operation_type=operation_type)
        
        # فیلتر بر اساس وضعیت
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # فیلتر بر اساس کاربر
        user = self.request.query_params.get('user')
        if user:
            queryset = queryset.filter(performed_by=user)
        
        return queryset