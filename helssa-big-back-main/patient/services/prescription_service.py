"""
سرویس مدیریت نسخه‌ها
Prescription Management Service
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from django.db import transaction
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta

from ..models import PatientProfile, PrescriptionHistory
from ..serializers import PrescriptionHistorySerializer

User = get_user_model()
logger = logging.getLogger(__name__)


class PrescriptionService:
    """
    سرویس جامع مدیریت نسخه‌ها
    Comprehensive prescription management service
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache_timeout = 600  # 10 minutes
    
    async def create_prescription(
        self,
        prescription_data: Dict[str, Any],
        prescribed_by: Optional[User] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        ایجاد نسخه جدید
        Create new prescription
        
        Args:
            prescription_data: اطلاعات نسخه
            prescribed_by: پزشک تجویزکننده
            
        Returns:
            Tuple[bool, Dict]: (موفقیت، داده‌های نتیجه)
        """
        try:
            # اعتبارسنجی داده‌ها
            serializer = PrescriptionHistorySerializer(data=prescription_data)
            if not serializer.is_valid():
                return False, {
                    'error': 'validation_failed',
                    'errors': serializer.errors,
                    'message': 'اطلاعات ورودی معتبر نیست'
                }
            
            # بررسی وجود بیمار
            patient_id = prescription_data.get('patient')
            if not await self._validate_patient_exists(patient_id):
                return False, {
                    'error': 'patient_not_found',
                    'message': 'بیمار یافت نشد'
                }
            
            # بررسی تداخل دارویی
            drug_interaction_check = await self._check_drug_interactions(
                patient_id, prescription_data.get('medication_name')
            )
            
            if drug_interaction_check['has_interaction']:
                return False, {
                    'error': 'drug_interaction',
                    'message': 'تداخل دارویی شناسایی شد',
                    'interactions': drug_interaction_check['interactions']
                }
            
            # ایجاد نسخه
            with transaction.atomic():
                if prescribed_by:
                    prescription_data['prescribed_by'] = prescribed_by.id
                
                prescription = serializer.save()
                
                # ثبت لاگ
                self.logger.info(
                    f"Prescription created: {prescription.prescription_number}",
                    extra={
                        'prescription_id': str(prescription.id),
                        'prescription_number': prescription.prescription_number,
                        'patient_id': str(prescription.patient.id),
                        'medication': prescription.medication_name,
                        'prescribed_by': prescribed_by.id if prescribed_by else None
                    }
                )
                
                # پاک کردن کش مرتبط
                await self._clear_patient_prescriptions_cache(patient_id)
                
                return True, {
                    'prescription_id': str(prescription.id),
                    'prescription_number': prescription.prescription_number,
                    'message': 'نسخه با موفقیت ایجاد شد',
                    'prescription_data': PrescriptionHistorySerializer(prescription).data,
                    'warnings': drug_interaction_check.get('warnings', [])
                }
                
        except Exception as e:
            self.logger.error(
                f"Error creating prescription: {str(e)}",
                extra={'prescription_data': prescription_data},
                exc_info=True
            )
            return False, {
                'error': 'creation_failed',
                'message': 'خطا در ایجاد نسخه'
            }
    
    async def get_patient_prescriptions(
        self,
        patient_id: str,
        status: Optional[str] = None,
        include_expired: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        دریافت نسخه‌های بیمار
        Get patient prescriptions
        """
        try:
            # بررسی وجود بیمار
            if not await self._validate_patient_exists(patient_id):
                return False, {
                    'error': 'patient_not_found',
                    'message': 'بیمار یافت نشد'
                }
            
            # ساخت کلید کش
            cache_key = f"prescriptions:{patient_id}:{status or 'all'}:{include_expired}"
            cached_data = cache.get(cache_key)
            
            if cached_data:
                return True, cached_data
            
            # ساخت فیلتر
            filters = Q(patient_id=patient_id)
            
            if status:
                filters &= Q(status=status)
            
            if not include_expired:
                filters &= Q(end_date__gte=timezone.now().date())
            
            # دریافت از دیتابیس
            prescriptions = PrescriptionHistory.objects.filter(filters).order_by(
                '-prescribed_date', '-created_at'
            )
            
            # سریالایز داده‌ها
            prescriptions_data = PrescriptionHistorySerializer(prescriptions, many=True).data
            
            # تجمیع آمار
            statistics = await self._calculate_prescriptions_statistics(prescriptions)
            
            # بررسی نسخه‌های منقضی شده و به‌روزرسانی وضعیت
            await self._update_expired_prescriptions(prescriptions)
            
            result_data = {
                'prescriptions': prescriptions_data,
                'count': len(prescriptions_data),
                'statistics': statistics,
                'patient_id': patient_id
            }
            
            # ذخیره در کش
            cache.set(cache_key, result_data, timeout=self.cache_timeout)
            
            return True, result_data
            
        except Exception as e:
            self.logger.error(f"Error getting patient prescriptions: {str(e)}")
            return False, {
                'error': 'retrieval_failed',
                'message': 'خطا در دریافت نسخه‌ها'
            }
    
    async def get_prescription(
        self,
        prescription_id: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        دریافت یک نسخه خاص
        Get specific prescription
        """
        try:
            # جستجو در کش
            cache_key = f"prescription:{prescription_id}"
            cached_data = cache.get(cache_key)
            
            if cached_data:
                return True, cached_data
            
            # دریافت از دیتابیس
            try:
                prescription = PrescriptionHistory.objects.select_related(
                    'patient', 'prescribed_by'
                ).get(id=prescription_id)
            except PrescriptionHistory.DoesNotExist:
                return False, {
                    'error': 'prescription_not_found',
                    'message': 'نسخه یافت نشد'
                }
            
            # سریالایز داده‌ها
            prescription_data = PrescriptionHistorySerializer(prescription).data
            
            # اضافه کردن اطلاعات اضافی
            additional_info = {
                'can_repeat': prescription.can_repeat(),
                'days_remaining': prescription.days_remaining,
                'is_expired': prescription.is_expired,
                'adherence_info': await self._get_adherence_info(prescription)
            }
            
            result_data = {
                'prescription_data': prescription_data,
                'additional_info': additional_info
            }
            
            # ذخیره در کش
            cache.set(cache_key, result_data, timeout=self.cache_timeout)
            
            return True, result_data
            
        except Exception as e:
            self.logger.error(f"Error getting prescription: {str(e)}")
            return False, {
                'error': 'retrieval_failed',
                'message': 'خطا در دریافت نسخه'
            }
    
    async def update_prescription(
        self,
        prescription_id: str,
        update_data: Dict[str, Any],
        updated_by: Optional[User] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        بروزرسانی نسخه
        Update prescription
        """
        try:
            # دریافت نسخه
            try:
                prescription = PrescriptionHistory.objects.get(id=prescription_id)
            except PrescriptionHistory.DoesNotExist:
                return False, {
                    'error': 'prescription_not_found',
                    'message': 'نسخه یافت نشد'
                }
            
            # بررسی امکان ویرایش
            if not await self._can_edit_prescription(prescription):
                return False, {
                    'error': 'edit_not_allowed',
                    'message': 'ویرایش این نسخه مجاز نیست'
                }
            
            # اعتبارسنجی داده‌ها
            serializer = PrescriptionHistorySerializer(
                prescription,
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
                updated_prescription = serializer.save()
                
                # ثبت لاگ
                self.logger.info(
                    f"Prescription updated: {updated_prescription.prescription_number}",
                    extra={
                        'prescription_id': str(updated_prescription.id),
                        'patient_id': str(updated_prescription.patient.id),
                        'updated_fields': list(update_data.keys()),
                        'updated_by': updated_by.id if updated_by else None
                    }
                )
                
                # پاک کردن کش
                cache.delete(f"prescription:{prescription_id}")
                await self._clear_patient_prescriptions_cache(str(updated_prescription.patient.id))
                
                return True, {
                    'message': 'نسخه بروزرسانی شد',
                    'prescription_data': PrescriptionHistorySerializer(updated_prescription).data
                }
                
        except Exception as e:
            self.logger.error(f"Error updating prescription: {str(e)}")
            return False, {
                'error': 'update_failed',
                'message': 'خطا در بروزرسانی نسخه'
            }
    
    async def repeat_prescription(
        self,
        prescription_id: str,
        prescribed_by: Optional[User] = None,
        notes: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        تکرار نسخه
        Repeat prescription
        """
        try:
            # دریافت نسخه اصلی
            try:
                original_prescription = PrescriptionHistory.objects.get(id=prescription_id)
            except PrescriptionHistory.DoesNotExist:
                return False, {
                    'error': 'prescription_not_found',
                    'message': 'نسخه یافت نشد'
                }
            
            # بررسی امکان تکرار
            if not original_prescription.can_repeat():
                return False, {
                    'error': 'repeat_not_allowed',
                    'message': 'تکرار این نسخه مجاز نیست'
                }
            
            # ایجاد نسخه جدید
            with transaction.atomic():
                # کپی کردن اطلاعات
                new_prescription_data = {
                    'patient': original_prescription.patient.id,
                    'medication_name': original_prescription.medication_name,
                    'dosage': original_prescription.dosage,
                    'frequency': original_prescription.frequency,
                    'duration': original_prescription.duration,
                    'instructions': original_prescription.instructions,
                    'diagnosis': original_prescription.diagnosis,
                    'start_date': timezone.now().date(),
                    'end_date': timezone.now().date() + timedelta(
                        days=self._parse_duration_days(original_prescription.duration)
                    ),
                    'is_repeat_allowed': original_prescription.is_repeat_allowed,
                    'max_repeats': original_prescription.max_repeats,
                    'prescribed_by': prescribed_by.id if prescribed_by else original_prescription.prescribed_by.id
                }
                
                if notes:
                    new_prescription_data['patient_notes'] = notes
                
                # ایجاد نسخه جدید
                new_prescription = PrescriptionHistory.objects.create(**new_prescription_data)
                
                # بروزرسانی شمارنده تکرار نسخه اصلی
                original_prescription.repeat_count += 1
                original_prescription.save()
                
                # ثبت لاگ
                self.logger.info(
                    f"Prescription repeated: {new_prescription.prescription_number} from {original_prescription.prescription_number}",
                    extra={
                        'new_prescription_id': str(new_prescription.id),
                        'original_prescription_id': str(original_prescription.id),
                        'patient_id': str(new_prescription.patient.id),
                        'prescribed_by': prescribed_by.id if prescribed_by else None
                    }
                )
                
                # پاک کردن کش
                await self._clear_patient_prescriptions_cache(str(new_prescription.patient.id))
                
                return True, {
                    'message': 'نسخه تکرار شد',
                    'new_prescription_id': str(new_prescription.id),
                    'new_prescription_number': new_prescription.prescription_number,
                    'prescription_data': PrescriptionHistorySerializer(new_prescription).data,
                    'remaining_repeats': original_prescription.max_repeats - original_prescription.repeat_count
                }
                
        except Exception as e:
            self.logger.error(f"Error repeating prescription: {str(e)}")
            return False, {
                'error': 'repeat_failed',
                'message': 'خطا در تکرار نسخه'
            }
    
    async def cancel_prescription(
        self,
        prescription_id: str,
        cancelled_by: Optional[User] = None,
        reason: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        لغو نسخه
        Cancel prescription
        """
        try:
            # دریافت نسخه
            try:
                prescription = PrescriptionHistory.objects.get(id=prescription_id)
            except PrescriptionHistory.DoesNotExist:
                return False, {
                    'error': 'prescription_not_found',
                    'message': 'نسخه یافت نشد'
                }
            
            # بررسی امکان لغو
            if prescription.status == 'cancelled':
                return False, {
                    'error': 'already_cancelled',
                    'message': 'نسخه قبلاً لغو شده است'
                }
            
            if prescription.status == 'completed':
                return False, {
                    'error': 'cannot_cancel_completed',
                    'message': 'نسخه تکمیل شده قابل لغو نیست'
                }
            
            # لغو نسخه
            with transaction.atomic():
                prescription.status = 'cancelled'
                if reason:
                    if prescription.patient_notes:
                        prescription.patient_notes += f"\n\nلغو شده: {reason}"
                    else:
                        prescription.patient_notes = f"لغو شده: {reason}"
                
                prescription.save()
                
                # ثبت لاگ
                self.logger.info(
                    f"Prescription cancelled: {prescription.prescription_number}",
                    extra={
                        'prescription_id': str(prescription.id),
                        'patient_id': str(prescription.patient.id),
                        'cancelled_by': cancelled_by.id if cancelled_by else None,
                        'reason': reason
                    }
                )
                
                # پاک کردن کش
                cache.delete(f"prescription:{prescription_id}")
                await self._clear_patient_prescriptions_cache(str(prescription.patient.id))
                
                return True, {
                    'message': 'نسخه لغو شد',
                    'prescription_data': PrescriptionHistorySerializer(prescription).data
                }
                
        except Exception as e:
            self.logger.error(f"Error cancelling prescription: {str(e)}")
            return False, {
                'error': 'cancellation_failed',
                'message': 'خطا در لغو نسخه'
            }
    
    async def search_prescriptions(
        self,
        search_params: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        جستجوی نسخه‌ها
        Search prescriptions
        """
        try:
            # ساخت فیلتر جستجو
            filters = Q()
            
            # جستجو در نام دارو
            if search_params.get('medication_name'):
                filters &= Q(medication_name__icontains=search_params['medication_name'])
            
            # فیلتر بر اساس وضعیت
            if search_params.get('status'):
                filters &= Q(status=search_params['status'])
            
            # فیلتر بیمار خاص
            if search_params.get('patient_id'):
                filters &= Q(patient_id=search_params['patient_id'])
            
            # فیلتر پزشک تجویزکننده
            if search_params.get('prescribed_by'):
                filters &= Q(prescribed_by_id=search_params['prescribed_by'])
            
            # فیلتر تاریخی
            if search_params.get('date_from'):
                filters &= Q(prescribed_date__gte=search_params['date_from'])
            
            if search_params.get('date_to'):
                filters &= Q(prescribed_date__lte=search_params['date_to'])
            
            # فیلتر تشخیص
            if search_params.get('diagnosis'):
                filters &= Q(diagnosis__icontains=search_params['diagnosis'])
            
            # فیلتر نسخه‌های قابل تکرار
            if search_params.get('repeatable_only'):
                filters &= Q(is_repeat_allowed=True)
            
            # اجرای جستجو
            limit = search_params.get('limit', 100)
            prescriptions = PrescriptionHistory.objects.filter(filters).select_related(
                'patient', 'prescribed_by'
            ).order_by('-prescribed_date', '-created_at')[:limit]
            
            # سریالایز نتایج
            results = PrescriptionHistorySerializer(prescriptions, many=True).data
            
            # آمار نتایج
            stats = await self._calculate_search_statistics(prescriptions)
            
            return True, {
                'results': results,
                'count': len(results),
                'search_params': search_params,
                'statistics': stats,
                'message': f'{len(results)} نسخه یافت شد'
            }
            
        except Exception as e:
            self.logger.error(f"Error searching prescriptions: {str(e)}")
            return False, {
                'error': 'search_failed',
                'message': 'خطا در جستجوی نسخه‌ها'
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
    
    async def _check_drug_interactions(
        self,
        patient_id: str,
        medication_name: str
    ) -> Dict[str, Any]:
        """بررسی تداخل دارویی"""
        try:
            # دریافت داروهای فعال بیمار
            active_prescriptions = PrescriptionHistory.objects.filter(
                patient_id=patient_id,
                status='active',
                end_date__gte=timezone.now().date()
            )
            
            interactions = []
            warnings = []
            
            # بررسی ساده تداخل (در پیاده‌سازی واقعی باید از پایگاه داده تداخلات استفاده شود)
            for prescription in active_prescriptions:
                if prescription.medication_name.lower() == medication_name.lower():
                    interactions.append({
                        'type': 'duplicate',
                        'existing_medication': prescription.medication_name,
                        'existing_prescription_id': str(prescription.id),
                        'message': 'دارو تکراری است'
                    })
            
            # بررسی تداخلات شناخته شده (مثال ساده)
            known_interactions = {
                'وارفارین': ['آسپیرین', 'ایبوپروفن'],
                'دیگوکسین': ['آمیودارون', 'وراپامیل']
            }
            
            for prescription in active_prescriptions:
                existing_med = prescription.medication_name.lower()
                new_med = medication_name.lower()
                
                if existing_med in known_interactions:
                    if any(interact.lower() in new_med for interact in known_interactions[existing_med]):
                        interactions.append({
                            'type': 'drug_interaction',
                            'existing_medication': prescription.medication_name,
                            'existing_prescription_id': str(prescription.id),
                            'message': f'تداخل احتمالی بین {prescription.medication_name} و {medication_name}'
                        })
            
            return {
                'has_interaction': len(interactions) > 0,
                'interactions': interactions,
                'warnings': warnings
            }
            
        except Exception as e:
            self.logger.error(f"Error checking drug interactions: {str(e)}")
            return {
                'has_interaction': False,
                'interactions': [],
                'warnings': ['خطا در بررسی تداخل دارویی']
            }
    
    async def _can_edit_prescription(self, prescription: PrescriptionHistory) -> bool:
        """بررسی امکان ویرایش نسخه"""
        # نسخه‌های لغو شده یا تکمیل شده قابل ویرایش نیستند
        if prescription.status in ['cancelled', 'completed']:
            return False
        
        # نسخه‌های منقضی شده قابل ویرایش نیستند
        if prescription.is_expired:
            return False
        
        return True
    
    async def _get_adherence_info(self, prescription: PrescriptionHistory) -> Dict[str, Any]:
        """دریافت اطلاعات پایبندی به دارو"""
        # در پیاده‌سازی واقعی، این اطلاعات از سیستم مانیتورینگ دریافت می‌شود
        return {
            'adherence_rate': None,  # درصد پایبندی
            'missed_doses': 0,       # دوزهای از دست رفته
            'last_taken': None,      # آخرین زمان مصرف
            'reminders_set': False   # یادآوری تنظیم شده
        }
    
    async def _parse_duration_days(self, duration: str) -> int:
        """تبدیل مدت زمان به روز"""
        try:
            duration = duration.lower().strip()
            
            if 'روز' in duration:
                days = int(''.join(filter(str.isdigit, duration)))
                return days
            elif 'هفته' in duration:
                weeks = int(''.join(filter(str.isdigit, duration)))
                return weeks * 7
            elif 'ماه' in duration:
                months = int(''.join(filter(str.isdigit, duration)))
                return months * 30
            else:
                # پیش‌فرض 7 روز
                return 7
                
        except Exception:
            return 7
    
    async def _update_expired_prescriptions(self, prescriptions):
        """به‌روزرسانی وضعیت نسخه‌های منقضی شده"""
        try:
            expired_prescriptions = [
                p for p in prescriptions 
                if p.is_expired and p.status == 'active'
            ]
            
            if expired_prescriptions:
                for prescription in expired_prescriptions:
                    prescription.status = 'expired'
                
                PrescriptionHistory.objects.bulk_update(
                    expired_prescriptions, ['status']
                )
                
        except Exception as e:
            self.logger.error(f"Error updating expired prescriptions: {str(e)}")
    
    async def _calculate_prescriptions_statistics(self, prescriptions) -> Dict[str, Any]:
        """محاسبه آمار نسخه‌ها"""
        try:
            total_count = prescriptions.count()
            
            # آمار بر اساس وضعیت
            status_stats = {}
            status_counts = prescriptions.values('status').annotate(count=Count('id'))
            for item in status_counts:
                status_stats[item['status']] = item['count']
            
            # نسخه‌های قابل تکرار
            repeatable_count = prescriptions.filter(is_repeat_allowed=True).count()
            
            # نسخه‌های منقضی شده
            expired_count = len([p for p in prescriptions if p.is_expired])
            
            return {
                'total': total_count,
                'by_status': status_stats,
                'repeatable': repeatable_count,
                'expired': expired_count,
                'active': status_stats.get('active', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating prescriptions statistics: {str(e)}")
            return {}
    
    async def _calculate_search_statistics(self, prescriptions) -> Dict[str, Any]:
        """محاسبه آمار نتایج جستجو"""
        try:
            return {
                'total': len(prescriptions),
                'statuses': list(set(p.status for p in prescriptions)),
                'medications': list(set(p.medication_name for p in prescriptions)),
                'date_range': {
                    'earliest': min(p.prescribed_date for p in prescriptions if p.prescribed_date).isoformat() if prescriptions else None,
                    'latest': max(p.prescribed_date for p in prescriptions if p.prescribed_date).isoformat() if prescriptions else None
                }
            }
        except Exception as e:
            self.logger.error(f"Error calculating search statistics: {str(e)}")
            return {}
    
    async def _clear_patient_prescriptions_cache(self, patient_id: str):
        """پاک کردن کش نسخه‌های بیمار"""
        try:
            # کلیدهای مرتبط با این بیمار
            keys_to_delete = [
                f"prescriptions:{patient_id}:all:False",
                f"prescriptions:{patient_id}:all:True",
            ]
            
            # همچنین کلیدهای وضعیت‌های مختلف
            statuses = ['active', 'completed', 'cancelled', 'expired']
            for status in statuses:
                keys_to_delete.extend([
                    f"prescriptions:{patient_id}:{status}:False",
                    f"prescriptions:{patient_id}:{status}:True"
                ])
            
            cache.delete_many(keys_to_delete)
            
        except Exception as e:
            self.logger.error(f"Error clearing patient prescriptions cache: {str(e)}")