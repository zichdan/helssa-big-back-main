"""
سرویس مدیریت بیماران
Patient Management Service
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from django.db import transaction
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Avg
from datetime import datetime, timedelta

from ..models import PatientProfile, MedicalRecord, PrescriptionHistory, MedicalConsent
from ..serializers import (
    PatientProfileSerializer,
    PatientProfileCreateSerializer,
    PatientStatisticsSerializer,
    PatientSearchSerializer
)

User = get_user_model()
logger = logging.getLogger(__name__)


class PatientService:
    """
    سرویس جامع مدیریت بیماران
    Comprehensive patient management service
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache_timeout = 300  # 5 minutes
    
    async def create_patient_profile(
        self,
        patient_data: Dict[str, Any],
        created_by: Optional[User] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        ایجاد پروفایل بیمار جدید
        Create new patient profile
        
        Args:
            patient_data: اطلاعات بیمار
            created_by: کاربر ایجادکننده
            
        Returns:
            Tuple[bool, Dict]: (موفقیت، داده‌های نتیجه)
        """
        try:
            # اعتبارسنجی داده‌ها
            serializer = PatientProfileCreateSerializer(data=patient_data)
            if not serializer.is_valid():
                return False, {
                    'error': 'validation_failed',
                    'errors': serializer.errors,
                    'message': 'اطلاعات ورودی معتبر نیست'
                }
            
            # بررسی تکراری نبودن
            national_code = patient_data.get('national_code')
            if await self._check_duplicate_patient(national_code):
                return False, {
                    'error': 'duplicate_patient',
                    'message': 'بیمار با این کد ملی قبلاً ثبت شده است'
                }
            
            # ایجاد پروفایل
            with transaction.atomic():
                patient_profile = serializer.save()
                
                # ثبت لاگ
                self.logger.info(
                    f"Patient profile created: {patient_profile.medical_record_number}",
                    extra={
                        'patient_id': str(patient_profile.id),
                        'national_code': patient_profile.national_code,
                        'created_by': created_by.id if created_by else None
                    }
                )
                
                # پاک کردن کش مرتبط
                await self._clear_patient_cache()
                
                return True, {
                    'patient_id': str(patient_profile.id),
                    'medical_record_number': patient_profile.medical_record_number,
                    'message': 'پروفایل بیمار با موفقیت ایجاد شد',
                    'patient_data': PatientProfileSerializer(patient_profile).data
                }
                
        except Exception as e:
            self.logger.error(
                f"Error creating patient profile: {str(e)}",
                extra={'patient_data': patient_data},
                exc_info=True
            )
            return False, {
                'error': 'creation_failed',
                'message': 'خطا در ایجاد پروفایل بیمار'
            }
    
    async def get_patient_profile(
        self,
        patient_id: str,
        include_statistics: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        دریافت پروفایل بیمار
        Get patient profile
        """
        try:
            # جستجو در کش
            cache_key = f"patient_profile:{patient_id}"
            cached_data = cache.get(cache_key)
            
            if cached_data and not include_statistics:
                return True, cached_data
            
            # دریافت از دیتابیس
            try:
                patient = PatientProfile.objects.select_related('user').get(
                    id=patient_id,
                    is_active=True
                )
            except PatientProfile.DoesNotExist:
                return False, {
                    'error': 'patient_not_found',
                    'message': 'بیمار یافت نشد'
                }
            
            # سریالایز داده‌ها
            patient_data = PatientProfileSerializer(patient).data
            
            # اضافه کردن آمار در صورت درخواست
            if include_statistics:
                statistics = await self._get_patient_statistics(patient)
                patient_data['statistics'] = statistics
            
            # ذخیره در کش
            if not include_statistics:
                cache.set(cache_key, {'patient_data': patient_data}, timeout=self.cache_timeout)
            
            return True, {'patient_data': patient_data}
            
        except Exception as e:
            self.logger.error(f"Error getting patient profile: {str(e)}")
            return False, {
                'error': 'retrieval_failed',
                'message': 'خطا در دریافت اطلاعات بیمار'
            }
    
    async def update_patient_profile(
        self,
        patient_id: str,
        update_data: Dict[str, Any],
        updated_by: Optional[User] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        بروزرسانی پروفایل بیمار
        Update patient profile
        """
        try:
            # دریافت بیمار
            try:
                patient = PatientProfile.objects.get(id=patient_id, is_active=True)
            except PatientProfile.DoesNotExist:
                return False, {
                    'error': 'patient_not_found',
                    'message': 'بیمار یافت نشد'
                }
            
            # اعتبارسنجی داده‌ها
            serializer = PatientProfileSerializer(
                patient,
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
                updated_patient = serializer.save()
                
                # ثبت لاگ
                self.logger.info(
                    f"Patient profile updated: {updated_patient.medical_record_number}",
                    extra={
                        'patient_id': str(updated_patient.id),
                        'updated_fields': list(update_data.keys()),
                        'updated_by': updated_by.id if updated_by else None
                    }
                )
                
                # پاک کردن کش
                cache.delete(f"patient_profile:{patient_id}")
                await self._clear_patient_cache()
                
                return True, {
                    'message': 'پروفایل بیمار بروزرسانی شد',
                    'patient_data': PatientProfileSerializer(updated_patient).data
                }
                
        except Exception as e:
            self.logger.error(f"Error updating patient profile: {str(e)}")
            return False, {
                'error': 'update_failed',
                'message': 'خطا در بروزرسانی پروفایل بیمار'
            }
    
    async def search_patients(
        self,
        search_params: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        جستجوی بیماران
        Search patients
        """
        try:
            # اعتبارسنجی پارامترهای جستجو
            search_serializer = PatientSearchSerializer(data=search_params)
            if not search_serializer.is_valid():
                return False, {
                    'error': 'invalid_search_params',
                    'errors': search_serializer.errors,
                    'message': 'پارامترهای جستجو معتبر نیست'
                }
            
            query = search_serializer.validated_data['query']
            search_type = search_serializer.validated_data['search_type']
            
            # ساخت فیلتر جستجو
            search_filter = self._build_search_filter(query, search_type)
            
            # اجرای جستجو
            patients = PatientProfile.objects.filter(
                search_filter
            ).filter(is_active=True).order_by('-created_at')[:50]  # محدود به 50 نتیجه
            
            # سریالایز نتایج
            results = PatientProfileSerializer(patients, many=True).data
            
            return True, {
                'results': results,
                'count': len(results),
                'query': query,
                'search_type': search_type,
                'message': f'{len(results)} بیمار یافت شد'
            }
            
        except Exception as e:
            self.logger.error(f"Error searching patients: {str(e)}")
            return False, {
                'error': 'search_failed',
                'message': 'خطا در جستجوی بیماران'
            }
    
    async def get_patient_statistics(
        self,
        patient_id: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        دریافت آمار بیمار
        Get patient statistics
        """
        try:
            # بررسی وجود بیمار
            try:
                patient = PatientProfile.objects.get(id=patient_id, is_active=True)
            except PatientProfile.DoesNotExist:
                return False, {
                    'error': 'patient_not_found',
                    'message': 'بیمار یافت نشد'
                }
            
            # محاسبه آمار
            statistics = await self._get_patient_statistics(patient)
            
            return True, {
                'patient_id': patient_id,
                'statistics': statistics,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting patient statistics: {str(e)}")
            return False, {
                'error': 'statistics_failed',
                'message': 'خطا در دریافت آمار بیمار'
            }
    
    async def deactivate_patient(
        self,
        patient_id: str,
        deactivated_by: Optional[User] = None,
        reason: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        غیرفعال کردن بیمار
        Deactivate patient
        """
        try:
            # دریافت بیمار
            try:
                patient = PatientProfile.objects.get(id=patient_id)
            except PatientProfile.DoesNotExist:
                return False, {
                    'error': 'patient_not_found',
                    'message': 'بیمار یافت نشد'
                }
            
            if not patient.is_active:
                return False, {
                    'error': 'already_inactive',
                    'message': 'بیمار قبلاً غیرفعال شده است'
                }
            
            # غیرفعال کردن
            with transaction.atomic():
                patient.is_active = False
                patient.save()
                
                # ثبت لاگ
                self.logger.info(
                    f"Patient deactivated: {patient.medical_record_number}",
                    extra={
                        'patient_id': str(patient.id),
                        'deactivated_by': deactivated_by.id if deactivated_by else None,
                        'reason': reason
                    }
                )
                
                # پاک کردن کش
                cache.delete(f"patient_profile:{patient_id}")
                await self._clear_patient_cache()
                
                return True, {
                    'message': 'بیمار غیرفعال شد'
                }
                
        except Exception as e:
            self.logger.error(f"Error deactivating patient: {str(e)}")
            return False, {
                'error': 'deactivation_failed',
                'message': 'خطا در غیرفعال کردن بیمار'
            }
    
    async def get_patients_by_criteria(
        self,
        criteria: Dict[str, Any],
        limit: int = 100
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        دریافت بیماران بر اساس معیارهای خاص
        Get patients by specific criteria
        """
        try:
            # ساخت فیلتر
            filters = Q(is_active=True)
            
            # معیارهای مختلف
            if criteria.get('age_range'):
                age_min = criteria['age_range'].get('min')
                age_max = criteria['age_range'].get('max')
                if age_min or age_max:
                    # محاسبه تاریخ تولد بر اساس سن
                    today = datetime.now().date()
                    if age_max:
                        birth_date_min = today - timedelta(days=age_max * 365)
                        filters &= Q(birth_date__gte=birth_date_min)
                    if age_min:
                        birth_date_max = today - timedelta(days=age_min * 365)
                        filters &= Q(birth_date__lte=birth_date_max)
            
            if criteria.get('gender'):
                filters &= Q(gender=criteria['gender'])
            
            if criteria.get('city'):
                filters &= Q(city__icontains=criteria['city'])
            
            if criteria.get('blood_type'):
                filters &= Q(blood_type=criteria['blood_type'])
            
            if criteria.get('created_after'):
                filters &= Q(created_at__gte=criteria['created_after'])
            
            if criteria.get('created_before'):
                filters &= Q(created_at__lte=criteria['created_before'])
            
            # اجرای کوئری
            patients = PatientProfile.objects.filter(filters).order_by('-created_at')[:limit]
            
            # سریالایز
            results = PatientProfileSerializer(patients, many=True).data
            
            return True, {
                'results': results,
                'count': len(results),
                'criteria': criteria,
                'message': f'{len(results)} بیمار یافت شد'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting patients by criteria: {str(e)}")
            return False, {
                'error': 'query_failed',
                'message': 'خطا در جستجوی بیماران'
            }
    
    async def validate_patient_access(
        self,
        user: User,
        patient_id: str,
        action: str = 'view'
    ) -> bool:
        """
        اعتبارسنجی دسترسی کاربر به بیمار
        Validate user access to patient
        """
        try:
            # اگر کاربر خود بیمار است
            if hasattr(user, 'patient_profile') and str(user.patient_profile.id) == patient_id:
                return action in ['view', 'update']
            
            # اگر کاربر پزشک است
            if user.user_type == 'doctor':
                # پزشکان می‌توانند به همه بیماران دسترسی داشته باشند
                return True
            
            # اگر کاربر ادمین است
            if user.user_type == 'admin':
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error validating patient access: {str(e)}")
            return False
    
    # Helper methods
    
    async def _check_duplicate_patient(self, national_code: str) -> bool:
        """بررسی تکراری بودن بیمار"""
        return PatientProfile.objects.filter(
            national_code=national_code,
            is_active=True
        ).exists()
    
    def _build_search_filter(self, query: str, search_type: str) -> Q:
        """ساخت فیلتر جستجو"""
        if search_type == 'national_code':
            return Q(national_code__icontains=query)
        elif search_type == 'medical_record':
            return Q(medical_record_number__icontains=query)
        elif search_type == 'name':
            return Q(first_name__icontains=query) | Q(last_name__icontains=query)
        else:  # all
            return (
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(national_code__icontains=query) |
                Q(medical_record_number__icontains=query)
            )
    
    async def _get_patient_statistics(self, patient: PatientProfile) -> Dict[str, Any]:
        """محاسبه آمار بیمار"""
        try:
            # تعداد ویزیت‌ها (فرضی - باید از اپ encounters دریافت شود)
            total_visits = 0
            last_visit_date = None
            next_appointment = None
            
            # سوابق پزشکی
            medical_records_count = MedicalRecord.objects.filter(
                patient=patient
            ).count()
            
            # نسخه‌ها
            total_prescriptions = PrescriptionHistory.objects.filter(
                patient=patient
            ).count()
            
            active_prescriptions = PrescriptionHistory.objects.filter(
                patient=patient,
                status='active'
            ).count()
            
            # رضایت‌نامه‌های در انتظار
            pending_consents = MedicalConsent.objects.filter(
                patient=patient,
                status='pending'
            ).count()
            
            return {
                'total_visits': total_visits,
                'total_prescriptions': total_prescriptions,
                'active_prescriptions': active_prescriptions,
                'pending_consents': pending_consents,
                'medical_records_count': medical_records_count,
                'last_visit_date': last_visit_date,
                'next_appointment': next_appointment
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating patient statistics: {str(e)}")
            return {}
    
    async def _clear_patient_cache(self):
        """پاک کردن کش مرتبط با بیماران"""
        try:
            # پاک کردن کش‌های عمومی
            cache.delete_many([
                'patients_count',
                'recent_patients',
                'patients_summary'
            ])
        except Exception as e:
            self.logger.error(f"Error clearing patient cache: {str(e)}")