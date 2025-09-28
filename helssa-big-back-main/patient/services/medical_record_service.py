"""
سرویس مدیریت سوابق پزشکی
Medical Records Management Service
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from django.db import transaction
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from datetime import datetime, timedelta

from ..models import PatientProfile, MedicalRecord
from ..serializers import MedicalRecordSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


class MedicalRecordService:
    """
    سرویس جامع مدیریت سوابق پزشکی
    Comprehensive medical records management service
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache_timeout = 600  # 10 minutes
    
    async def create_medical_record(
        self,
        record_data: Dict[str, Any],
        created_by: Optional[User] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        ایجاد سابقه پزشکی جدید
        Create new medical record
        
        Args:
            record_data: اطلاعات سابقه پزشکی
            created_by: کاربر ایجادکننده
            
        Returns:
            Tuple[bool, Dict]: (موفقیت، داده‌های نتیجه)
        """
        try:
            # اعتبارسنجی داده‌ها
            serializer = MedicalRecordSerializer(data=record_data)
            if not serializer.is_valid():
                return False, {
                    'error': 'validation_failed',
                    'errors': serializer.errors,
                    'message': 'اطلاعات ورودی معتبر نیست'
                }
            
            # بررسی وجود بیمار
            patient_id = record_data.get('patient')
            if not await self._validate_patient_exists(patient_id):
                return False, {
                    'error': 'patient_not_found',
                    'message': 'بیمار یافت نشد'
                }
            
            # ایجاد سابقه پزشکی
            with transaction.atomic():
                if created_by:
                    record_data['created_by'] = created_by.id
                
                medical_record = serializer.save()
                
                # ثبت لاگ
                self.logger.info(
                    f"Medical record created: {medical_record.id}",
                    extra={
                        'medical_record_id': str(medical_record.id),
                        'patient_id': str(medical_record.patient.id),
                        'record_type': medical_record.record_type,
                        'created_by': created_by.id if created_by else None
                    }
                )
                
                # پاک کردن کش مرتبط
                await self._clear_patient_records_cache(patient_id)
                
                return True, {
                    'medical_record_id': str(medical_record.id),
                    'message': 'سابقه پزشکی با موفقیت ایجاد شد',
                    'record_data': MedicalRecordSerializer(medical_record).data
                }
                
        except Exception as e:
            self.logger.error(
                f"Error creating medical record: {str(e)}",
                extra={'record_data': record_data},
                exc_info=True
            )
            return False, {
                'error': 'creation_failed',
                'message': 'خطا در ایجاد سابقه پزشکی'
            }
    
    async def get_patient_medical_records(
        self,
        patient_id: str,
        record_type: Optional[str] = None,
        include_inactive: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        دریافت سوابق پزشکی بیمار
        Get patient medical records
        """
        try:
            # بررسی وجود بیمار
            if not await self._validate_patient_exists(patient_id):
                return False, {
                    'error': 'patient_not_found',
                    'message': 'بیمار یافت نشد'
                }
            
            # ساخت کلید کش
            cache_key = f"medical_records:{patient_id}:{record_type or 'all'}:{include_inactive}"
            cached_data = cache.get(cache_key)
            
            if cached_data:
                return True, cached_data
            
            # ساخت فیلتر
            filters = Q(patient_id=patient_id)
            
            if record_type:
                filters &= Q(record_type=record_type)
            
            # دریافت از دیتابیس
            records = MedicalRecord.objects.filter(filters).order_by('-start_date', '-created_at')
            
            # سریالایز داده‌ها
            records_data = MedicalRecordSerializer(records, many=True).data
            
            # تجمیع آمار
            statistics = await self._calculate_records_statistics(records)
            
            result_data = {
                'records': records_data,
                'count': len(records_data),
                'statistics': statistics,
                'patient_id': patient_id
            }
            
            # ذخیره در کش
            cache.set(cache_key, result_data, timeout=self.cache_timeout)
            
            return True, result_data
            
        except Exception as e:
            self.logger.error(f"Error getting patient medical records: {str(e)}")
            return False, {
                'error': 'retrieval_failed',
                'message': 'خطا در دریافت سوابق پزشکی'
            }
    
    async def get_medical_record(
        self,
        record_id: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        دریافت یک سابقه پزشکی خاص
        Get specific medical record
        """
        try:
            # جستجو در کش
            cache_key = f"medical_record:{record_id}"
            cached_data = cache.get(cache_key)
            
            if cached_data:
                return True, cached_data
            
            # دریافت از دیتابیس
            try:
                record = MedicalRecord.objects.select_related(
                    'patient', 'created_by'
                ).get(id=record_id)
            except MedicalRecord.DoesNotExist:
                return False, {
                    'error': 'record_not_found',
                    'message': 'سابقه پزشکی یافت نشد'
                }
            
            # سریالایز داده‌ها
            record_data = MedicalRecordSerializer(record).data
            
            result_data = {'record_data': record_data}
            
            # ذخیره در کش
            cache.set(cache_key, result_data, timeout=self.cache_timeout)
            
            return True, result_data
            
        except Exception as e:
            self.logger.error(f"Error getting medical record: {str(e)}")
            return False, {
                'error': 'retrieval_failed',
                'message': 'خطا در دریافت سابقه پزشکی'
            }
    
    async def update_medical_record(
        self,
        record_id: str,
        update_data: Dict[str, Any],
        updated_by: Optional[User] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        بروزرسانی سابقه پزشکی
        Update medical record
        """
        try:
            # دریافت سابقه پزشکی
            try:
                record = MedicalRecord.objects.get(id=record_id)
            except MedicalRecord.DoesNotExist:
                return False, {
                    'error': 'record_not_found',
                    'message': 'سابقه پزشکی یافت نشد'
                }
            
            # اعتبارسنجی داده‌ها
            serializer = MedicalRecordSerializer(
                record,
                data=update_data,
                partial=True
            )
            
            if not serializer.is_valid():
                return False, {
                    'error': 'validation_failed',
                    'errors': serializer.errors,
                    'message': 'اطلاعات ورودی معتبر نیست'
                }
            
            # بروزرسانی
            with transaction.atomic():
                updated_record = serializer.save()
                
                # ثبت لاگ
                self.logger.info(
                    f"Medical record updated: {updated_record.id}",
                    extra={
                        'medical_record_id': str(updated_record.id),
                        'patient_id': str(updated_record.patient.id),
                        'updated_fields': list(update_data.keys()),
                        'updated_by': updated_by.id if updated_by else None
                    }
                )
                
                # پاک کردن کش
                cache.delete(f"medical_record:{record_id}")
                await self._clear_patient_records_cache(str(updated_record.patient.id))
                
                return True, {
                    'message': 'سابقه پزشکی بروزرسانی شد',
                    'record_data': MedicalRecordSerializer(updated_record).data
                }
                
        except Exception as e:
            self.logger.error(f"Error updating medical record: {str(e)}")
            return False, {
                'error': 'update_failed',
                'message': 'خطا در بروزرسانی سابقه پزشکی'
            }
    
    async def delete_medical_record(
        self,
        record_id: str,
        deleted_by: Optional[User] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        حذف سابقه پزشکی
        Delete medical record
        """
        try:
            # دریافت سابقه پزشکی
            try:
                record = MedicalRecord.objects.get(id=record_id)
            except MedicalRecord.DoesNotExist:
                return False, {
                    'error': 'record_not_found',
                    'message': 'سابقه پزشکی یافت نشد'
                }
            
            # حذف
            with transaction.atomic():
                patient_id = str(record.patient.id)
                record_info = {
                    'id': str(record.id),
                    'title': record.title,
                    'type': record.record_type
                }
                
                record.delete()
                
                # ثبت لاگ
                self.logger.info(
                    f"Medical record deleted: {record_info['id']}",
                    extra={
                        'medical_record_id': record_info['id'],
                        'patient_id': patient_id,
                        'record_type': record_info['type'],
                        'deleted_by': deleted_by.id if deleted_by else None
                    }
                )
                
                # پاک کردن کش
                cache.delete(f"medical_record:{record_id}")
                await self._clear_patient_records_cache(patient_id)
                
                return True, {
                    'message': 'سابقه پزشکی حذف شد',
                    'deleted_record': record_info
                }
                
        except Exception as e:
            self.logger.error(f"Error deleting medical record: {str(e)}")
            return False, {
                'error': 'deletion_failed',
                'message': 'خطا در حذف سابقه پزشکی'
            }
    
    async def search_medical_records(
        self,
        search_params: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        جستجوی سوابق پزشکی
        Search medical records
        """
        try:
            # ساخت فیلتر جستجو
            filters = Q()
            
            # جستجو در متن
            if search_params.get('query'):
                query = search_params['query']
                filters &= (
                    Q(title__icontains=query) |
                    Q(description__icontains=query) |
                    Q(notes__icontains=query)
                )
            
            # فیلتر بر اساس نوع
            if search_params.get('record_type'):
                filters &= Q(record_type=search_params['record_type'])
            
            # فیلتر بر اساس شدت
            if search_params.get('severity'):
                filters &= Q(severity=search_params['severity'])
            
            # فیلتر تاریخی
            if search_params.get('date_from'):
                filters &= Q(start_date__gte=search_params['date_from'])
            
            if search_params.get('date_to'):
                filters &= Q(start_date__lte=search_params['date_to'])
            
            # فیلتر بیمار خاص
            if search_params.get('patient_id'):
                filters &= Q(patient_id=search_params['patient_id'])
            
            # فیلتر موارد در حال ادامه
            if search_params.get('is_ongoing') is not None:
                filters &= Q(is_ongoing=search_params['is_ongoing'])
            
            # اجرای جستجو
            limit = search_params.get('limit', 100)
            records = MedicalRecord.objects.filter(filters).select_related(
                'patient', 'created_by'
            ).order_by('-start_date', '-created_at')[:limit]
            
            # سریالایز نتایج
            results = MedicalRecordSerializer(records, many=True).data
            
            # آمار نتایج
            stats = await self._calculate_search_statistics(records)
            
            return True, {
                'results': results,
                'count': len(results),
                'search_params': search_params,
                'statistics': stats,
                'message': f'{len(results)} سابقه پزشکی یافت شد'
            }
            
        except Exception as e:
            self.logger.error(f"Error searching medical records: {str(e)}")
            return False, {
                'error': 'search_failed',
                'message': 'خطا در جستجوی سوابق پزشکی'
            }
    
    async def get_patient_medical_summary(
        self,
        patient_id: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        دریافت خلاصه پزشکی بیمار
        Get patient medical summary
        """
        try:
            # بررسی وجود بیمار
            if not await self._validate_patient_exists(patient_id):
                return False, {
                    'error': 'patient_not_found',
                    'message': 'بیمار یافت نشد'
                }
            
            # جستجو در کش
            cache_key = f"medical_summary:{patient_id}"
            cached_data = cache.get(cache_key)
            
            if cached_data:
                return True, cached_data
            
            # دریافت سوابق پزشکی
            records = MedicalRecord.objects.filter(
                patient_id=patient_id
            ).order_by('-start_date')
            
            # تجمیع اطلاعات
            summary = {
                'patient_id': patient_id,
                'total_records': records.count(),
                'by_type': {},
                'by_severity': {},
                'ongoing_conditions': [],
                'allergies': [],
                'surgeries': [],
                'family_history': [],
                'recent_records': []
            }
            
            # تجمیع بر اساس نوع
            type_counts = records.values('record_type').annotate(count=Count('id'))
            for item in type_counts:
                summary['by_type'][item['record_type']] = item['count']
            
            # تجمیع بر اساس شدت
            severity_counts = records.values('severity').annotate(count=Count('id'))
            for item in severity_counts:
                summary['by_severity'][item['severity']] = item['count']
            
            # موارد در حال ادامه
            ongoing = records.filter(is_ongoing=True)
            summary['ongoing_conditions'] = [
                {
                    'id': str(r.id),
                    'title': r.title,
                    'type': r.record_type,
                    'severity': r.severity,
                    'start_date': r.start_date.isoformat() if r.start_date else None
                }
                for r in ongoing[:10]
            ]
            
            # آلرژی‌ها
            allergies = records.filter(record_type='allergy')
            summary['allergies'] = [
                {
                    'id': str(r.id),
                    'title': r.title,
                    'severity': r.severity,
                    'description': r.description[:200] if r.description else None
                }
                for r in allergies[:10]
            ]
            
            # جراحی‌ها
            surgeries = records.filter(record_type='surgery')
            summary['surgeries'] = [
                {
                    'id': str(r.id),
                    'title': r.title,
                    'date': r.start_date.isoformat() if r.start_date else None,
                    'doctor': r.doctor_name
                }
                for r in surgeries[:10]
            ]
            
            # سابقه خانوادگی
            family_history = records.filter(record_type='family_history')
            summary['family_history'] = [
                {
                    'id': str(r.id),
                    'title': r.title,
                    'description': r.description[:200] if r.description else None
                }
                for r in family_history[:10]
            ]
            
            # آخرین سوابق
            recent = records[:10]
            summary['recent_records'] = MedicalRecordSerializer(recent, many=True).data
            
            result_data = {'summary': summary}
            
            # ذخیره در کش
            cache.set(cache_key, result_data, timeout=self.cache_timeout)
            
            return True, result_data
            
        except Exception as e:
            self.logger.error(f"Error getting patient medical summary: {str(e)}")
            return False, {
                'error': 'summary_failed',
                'message': 'خطا در دریافت خلاصه پزشکی'
            }
    
    async def bulk_create_medical_records(
        self,
        records_data: List[Dict[str, Any]],
        created_by: Optional[User] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        ایجاد انبوه سوابق پزشکی
        Bulk create medical records
        """
        try:
            created_records = []
            errors = []
            
            with transaction.atomic():
                for i, record_data in enumerate(records_data):
                    try:
                        if created_by:
                            record_data['created_by'] = created_by.id
                        
                        serializer = MedicalRecordSerializer(data=record_data)
                        if serializer.is_valid():
                            record = serializer.save()
                            created_records.append({
                                'index': i,
                                'id': str(record.id),
                                'title': record.title
                            })
                        else:
                            errors.append({
                                'index': i,
                                'errors': serializer.errors,
                                'data': record_data
                            })
                    except Exception as e:
                        errors.append({
                            'index': i,
                            'error': str(e),
                            'data': record_data
                        })
                
                # اگر خطاهای زیادی وجود دارد، transaction را rollback کن
                if len(errors) > len(records_data) * 0.5:  # بیش از 50% خطا
                    raise Exception("Too many errors in bulk creation")
            
            # پاک کردن کش
            patient_ids = set()
            for record_data in records_data:
                if 'patient' in record_data:
                    patient_ids.add(str(record_data['patient']))
            
            for patient_id in patient_ids:
                await self._clear_patient_records_cache(patient_id)
            
            # ثبت لاگ
            self.logger.info(
                f"Bulk medical records creation: {len(created_records)} created, {len(errors)} errors",
                extra={
                    'created_count': len(created_records),
                    'error_count': len(errors),
                    'created_by': created_by.id if created_by else None
                }
            )
            
            return True, {
                'created_records': created_records,
                'errors': errors,
                'total_processed': len(records_data),
                'created_count': len(created_records),
                'error_count': len(errors),
                'message': f'{len(created_records)} سابقه پزشکی ایجاد شد'
            }
            
        except Exception as e:
            self.logger.error(f"Error in bulk medical records creation: {str(e)}")
            return False, {
                'error': 'bulk_creation_failed',
                'message': 'خطا در ایجاد انبوه سوابق پزشکی'
            }
    
    # Helper methods
    
    async def _validate_patient_exists(self, patient_id: str) -> bool:
        """بررسی وجود بیمار"""
        try:
            return PatientProfile.objects.filter(
                id=patient_id,
                is_active=True
            ).exists()
        except Exception:
            return False
    
    async def _calculate_records_statistics(self, records) -> Dict[str, Any]:
        """محاسبه آمار سوابق پزشکی"""
        try:
            total_count = records.count()
            
            # آمار بر اساس نوع
            type_stats = {}
            type_counts = records.values('record_type').annotate(count=Count('id'))
            for item in type_counts:
                type_stats[item['record_type']] = item['count']
            
            # آمار بر اساس شدت
            severity_stats = {}
            severity_counts = records.values('severity').annotate(count=Count('id'))
            for item in severity_counts:
                severity_stats[item['severity']] = item['count']
            
            # موارد در حال ادامه
            ongoing_count = records.filter(is_ongoing=True).count()
            
            return {
                'total': total_count,
                'by_type': type_stats,
                'by_severity': severity_stats,
                'ongoing': ongoing_count,
                'completed': total_count - ongoing_count
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating records statistics: {str(e)}")
            return {}
    
    async def _calculate_search_statistics(self, records) -> Dict[str, Any]:
        """محاسبه آمار نتایج جستجو"""
        try:
            return {
                'total': len(records),
                'types': list(set(r.record_type for r in records)),
                'severities': list(set(r.severity for r in records)),
                'date_range': {
                    'earliest': min(r.start_date for r in records if r.start_date).isoformat() if records else None,
                    'latest': max(r.start_date for r in records if r.start_date).isoformat() if records else None
                }
            }
        except Exception as e:
            self.logger.error(f"Error calculating search statistics: {str(e)}")
            return {}
    
    async def _clear_patient_records_cache(self, patient_id: str):
        """پاک کردن کش سوابق پزشکی بیمار"""
        try:
            # پاک کردن کش‌های مرتبط با این بیمار
            patterns = [
                f"medical_records:{patient_id}:*",
                f"medical_summary:{patient_id}"
            ]
            
            # در Django cache framework نمی‌توان pattern matching کرد
            # بنابراین کلیدهای مشخص را پاک می‌کنیم
            keys_to_delete = [
                f"medical_records:{patient_id}:all:False",
                f"medical_records:{patient_id}:all:True",
                f"medical_summary:{patient_id}"
            ]
            
            # همچنین کلیدهای نوع‌های مختلف
            record_types = ['allergy', 'medication', 'surgery', 'illness', 'family_history', 'vaccination', 'other']
            for record_type in record_types:
                keys_to_delete.extend([
                    f"medical_records:{patient_id}:{record_type}:False",
                    f"medical_records:{patient_id}:{record_type}:True"
                ])
            
            cache.delete_many(keys_to_delete)
            
        except Exception as e:
            self.logger.error(f"Error clearing patient records cache: {str(e)}")