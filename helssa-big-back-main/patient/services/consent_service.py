"""
سرویس مدیریت رضایت‌نامه‌ها
Consent Management Service
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from django.db import transaction
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
import hashlib
import uuid

from ..models import PatientProfile, MedicalConsent
from ..serializers import MedicalConsentSerializer, ConsentGrantSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


class ConsentService:
    """
    سرویس جامع مدیریت رضایت‌نامه‌ها
    Comprehensive consent management service
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache_timeout = 1800  # 30 minutes
        self.signature_salt = "helssa_consent_signature"
    
    async def create_consent(
        self,
        consent_data: Dict[str, Any],
        requested_by: Optional[User] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        ایجاد رضایت‌نامه جدید
        Create new consent form
        
        Args:
            consent_data: اطلاعات رضایت‌نامه
            requested_by: کاربر درخواست‌کننده
            
        Returns:
            Tuple[bool, Dict]: (موفقیت، داده‌های نتیجه)
        """
        try:
            # اعتبارسنجی داده‌ها
            serializer = MedicalConsentSerializer(data=consent_data)
            if not serializer.is_valid():
                return False, {
                    'error': 'validation_failed',
                    'errors': serializer.errors,
                    'message': 'اطلاعات ورودی معتبر نیست'
                }
            
            # بررسی وجود بیمار
            patient_id = consent_data.get('patient')
            if not await self._validate_patient_exists(patient_id):
                return False, {
                    'error': 'patient_not_found',
                    'message': 'بیمار یافت نشد'
                }
            
            # بررسی وجود رضایت‌نامه مشابه
            duplicate_check = await self._check_duplicate_consent(
                patient_id, consent_data.get('consent_type'), consent_data.get('title')
            )
            
            if duplicate_check['has_duplicate']:
                return False, {
                    'error': 'duplicate_consent',
                    'message': 'رضایت‌نامه مشابه وجود دارد',
                    'existing_consent_id': duplicate_check['existing_id']
                }
            
            # ایجاد رضایت‌نامه
            with transaction.atomic():
                if requested_by:
                    consent_data['requested_by'] = requested_by.id
                
                consent = serializer.save()
                
                # ثبت لاگ
                self.logger.info(
                    f"Consent created: {consent.id}",
                    extra={
                        'consent_id': str(consent.id),
                        'patient_id': str(consent.patient.id),
                        'consent_type': consent.consent_type,
                        'requested_by': requested_by.id if requested_by else None
                    }
                )
                
                # پاک کردن کش مرتبط
                await self._clear_patient_consents_cache(patient_id)
                
                return True, {
                    'consent_id': str(consent.id),
                    'message': 'رضایت‌نامه با موفقیت ایجاد شد',
                    'consent_data': MedicalConsentSerializer(consent).data
                }
                
        except Exception as e:
            self.logger.error(
                f"Error creating consent: {str(e)}",
                extra={'consent_data': consent_data},
                exc_info=True
            )
            return False, {
                'error': 'creation_failed',
                'message': 'خطا در ایجاد رضایت‌نامه'
            }
    
    async def get_patient_consents(
        self,
        patient_id: str,
        consent_type: Optional[str] = None,
        status: Optional[str] = None,
        include_expired: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        دریافت رضایت‌نامه‌های بیمار
        Get patient consent forms
        """
        try:
            # بررسی وجود بیمار
            if not await self._validate_patient_exists(patient_id):
                return False, {
                    'error': 'patient_not_found',
                    'message': 'بیمار یافت نشد'
                }
            
            # ساخت کلید کش
            cache_key = f"consents:{patient_id}:{consent_type or 'all'}:{status or 'all'}:{include_expired}"
            cached_data = cache.get(cache_key)
            
            if cached_data:
                return True, cached_data
            
            # ساخت فیلتر
            filters = Q(patient_id=patient_id)
            
            if consent_type:
                filters &= Q(consent_type=consent_type)
            
            if status:
                filters &= Q(status=status)
            
            if not include_expired:
                # حذف موارد منقضی شده
                filters &= (
                    Q(expiry_date__isnull=True) |
                    Q(expiry_date__gte=timezone.now().date())
                )
            
            # دریافت از دیتابیس
            consents = MedicalConsent.objects.filter(filters).order_by(
                '-created_at'
            )
            
            # به‌روزرسانی وضعیت منقضی‌ها
            await self._update_expired_consents(consents)
            
            # سریالایز داده‌ها
            consents_data = MedicalConsentSerializer(consents, many=True).data
            
            # تجمیع آمار
            statistics = await self._calculate_consents_statistics(consents)
            
            result_data = {
                'consents': consents_data,
                'count': len(consents_data),
                'statistics': statistics,
                'patient_id': patient_id
            }
            
            # ذخیره در کش
            cache.set(cache_key, result_data, timeout=self.cache_timeout)
            
            return True, result_data
            
        except Exception as e:
            self.logger.error(f"Error getting patient consents: {str(e)}")
            return False, {
                'error': 'retrieval_failed',
                'message': 'خطا در دریافت رضایت‌نامه‌ها'
            }
    
    async def get_consent(
        self,
        consent_id: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        دریافت یک رضایت‌نامه خاص
        Get specific consent form
        """
        try:
            # جستجو در کش
            cache_key = f"consent:{consent_id}"
            cached_data = cache.get(cache_key)
            
            if cached_data:
                return True, cached_data
            
            # دریافت از دیتابیس
            try:
                consent = MedicalConsent.objects.select_related(
                    'patient', 'requested_by', 'processed_by'
                ).get(id=consent_id)
            except MedicalConsent.DoesNotExist:
                return False, {
                    'error': 'consent_not_found',
                    'message': 'رضایت‌نامه یافت نشد'
                }
            
            # سریالایز داده‌ها
            consent_data = MedicalConsentSerializer(consent).data
            
            # اضافه کردن اطلاعات اضافی
            additional_info = {
                'is_valid': consent.is_valid,
                'is_expired': consent.is_expired,
                'can_be_processed': await self._can_process_consent(consent),
                'signature_verification': await self._verify_consent_signature(consent)
            }
            
            result_data = {
                'consent_data': consent_data,
                'additional_info': additional_info
            }
            
            # ذخیره در کش
            cache.set(cache_key, result_data, timeout=self.cache_timeout)
            
            return True, result_data
            
        except Exception as e:
            self.logger.error(f"Error getting consent: {str(e)}")
            return False, {
                'error': 'retrieval_failed',
                'message': 'خطا در دریافت رضایت‌نامه'
            }
    
    async def grant_consent(
        self,
        consent_id: str,
        signature_data: Dict[str, Any],
        client_info: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        ثبت رضایت
        Grant consent
        """
        try:
            # اعتبارسنجی داده‌های امضا
            signature_serializer = ConsentGrantSerializer(data=signature_data)
            if not signature_serializer.is_valid():
                return False, {
                    'error': 'invalid_signature_data',
                    'errors': signature_serializer.errors,
                    'message': 'داده‌های امضا معتبر نیست'
                }
            
            # دریافت رضایت‌نامه
            try:
                consent = MedicalConsent.objects.get(id=consent_id)
            except MedicalConsent.DoesNotExist:
                return False, {
                    'error': 'consent_not_found',
                    'message': 'رضایت‌نامه یافت نشد'
                }
            
            # بررسی امکان ثبت رضایت
            if not await self._can_process_consent(consent):
                return False, {
                    'error': 'cannot_grant_consent',
                    'message': 'امکان ثبت رضایت وجود ندارد'
                }
            
            # پردازش امضای دیجیتال
            digital_signature = await self._process_digital_signature(
                signature_data['digital_signature'],
                consent_id,
                client_info
            )
            
            # ثبت رضایت
            with transaction.atomic():
                ip_address = client_info.get('ip_address', '0.0.0.0') if client_info else '0.0.0.0'
                user_agent = client_info.get('user_agent', '') if client_info else ''
                
                consent.grant_consent(
                    digital_signature=digital_signature,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                # ثبت لاگ
                self.logger.info(
                    f"Consent granted: {consent.id}",
                    extra={
                        'consent_id': str(consent.id),
                        'patient_id': str(consent.patient.id),
                        'consent_type': consent.consent_type,
                        'ip_address': ip_address,
                        'signature_hash': hashlib.sha256(digital_signature.encode()).hexdigest()[:16]
                    }
                )
                
                # پاک کردن کش
                cache.delete(f"consent:{consent_id}")
                await self._clear_patient_consents_cache(str(consent.patient.id))
                
                return True, {
                    'message': 'رضایت با موفقیت ثبت شد',
                    'consent_data': MedicalConsentSerializer(consent).data,
                    'granted_at': consent.consent_date.isoformat() if consent.consent_date else None
                }
                
        except Exception as e:
            self.logger.error(f"Error granting consent: {str(e)}")
            return False, {
                'error': 'grant_failed',
                'message': 'خطا در ثبت رضایت'
            }
    
    async def revoke_consent(
        self,
        consent_id: str,
        revoked_by: Optional[User] = None,
        reason: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        لغو رضایت
        Revoke consent
        """
        try:
            # دریافت رضایت‌نامه
            try:
                consent = MedicalConsent.objects.get(id=consent_id)
            except MedicalConsent.DoesNotExist:
                return False, {
                    'error': 'consent_not_found',
                    'message': 'رضایت‌نامه یافت نشد'
                }
            
            # بررسی امکان لغو
            if consent.status != 'granted':
                return False, {
                    'error': 'cannot_revoke',
                    'message': 'فقط رضایت‌نامه‌های تایید شده قابل لغو هستند'
                }
            
            # لغو رضایت
            with transaction.atomic():
                consent.revoke_consent()
                
                # اضافه کردن دلیل لغو
                if reason:
                    if consent.notes:
                        consent.notes += f"\n\nلغو شده: {reason}"
                    else:
                        consent.notes = f"لغو شده: {reason}"
                    consent.save()
                
                # ثبت لاگ
                self.logger.info(
                    f"Consent revoked: {consent.id}",
                    extra={
                        'consent_id': str(consent.id),
                        'patient_id': str(consent.patient.id),
                        'consent_type': consent.consent_type,
                        'revoked_by': revoked_by.id if revoked_by else None,
                        'reason': reason
                    }
                )
                
                # پاک کردن کش
                cache.delete(f"consent:{consent_id}")
                await self._clear_patient_consents_cache(str(consent.patient.id))
                
                return True, {
                    'message': 'رضایت لغو شد',
                    'consent_data': MedicalConsentSerializer(consent).data
                }
                
        except Exception as e:
            self.logger.error(f"Error revoking consent: {str(e)}")
            return False, {
                'error': 'revoke_failed',
                'message': 'خطا در لغو رضایت'
            }
    
    async def search_consents(
        self,
        search_params: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        جستجوی رضایت‌نامه‌ها
        Search consent forms
        """
        try:
            # ساخت فیلتر جستجو
            filters = Q()
            
            # جستجو در عنوان و توضیحات
            if search_params.get('query'):
                query = search_params['query']
                filters &= (
                    Q(title__icontains=query) |
                    Q(description__icontains=query) |
                    Q(consent_text__icontains=query)
                )
            
            # فیلتر بر اساس نوع
            if search_params.get('consent_type'):
                filters &= Q(consent_type=search_params['consent_type'])
            
            # فیلتر بر اساس وضعیت
            if search_params.get('status'):
                filters &= Q(status=search_params['status'])
            
            # فیلتر بیمار خاص
            if search_params.get('patient_id'):
                filters &= Q(patient_id=search_params['patient_id'])
            
            # فیلتر درخواست‌کننده
            if search_params.get('requested_by'):
                filters &= Q(requested_by_id=search_params['requested_by'])
            
            # فیلتر تاریخی
            if search_params.get('date_from'):
                filters &= Q(created_date__gte=search_params['date_from'])
            
            if search_params.get('date_to'):
                filters &= Q(created_date__lte=search_params['date_to'])
            
            # فیلتر منقضی‌ها
            if search_params.get('exclude_expired'):
                filters &= (
                    Q(expiry_date__isnull=True) |
                    Q(expiry_date__gte=timezone.now().date())
                )
            
            # اجرای جستجو
            limit = search_params.get('limit', 100)
            consents = MedicalConsent.objects.filter(filters).select_related(
                'patient', 'requested_by', 'processed_by'
            ).order_by('-created_at')[:limit]
            
            # سریالایز نتایج
            results = MedicalConsentSerializer(consents, many=True).data
            
            # آمار نتایج
            stats = await self._calculate_search_statistics(consents)
            
            return True, {
                'results': results,
                'count': len(results),
                'search_params': search_params,
                'statistics': stats,
                'message': f'{len(results)} رضایت‌نامه یافت شد'
            }
            
        except Exception as e:
            self.logger.error(f"Error searching consents: {str(e)}")
            return False, {
                'error': 'search_failed',
                'message': 'خطا در جستجوی رضایت‌نامه‌ها'
            }
    
    async def get_consent_audit_log(
        self,
        consent_id: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        دریافت لاگ حسابرسی رضایت‌نامه
        Get consent audit log
        """
        try:
            # دریافت رضایت‌نامه
            try:
                consent = MedicalConsent.objects.get(id=consent_id)
            except MedicalConsent.DoesNotExist:
                return False, {
                    'error': 'consent_not_found',
                    'message': 'رضایت‌نامه یافت نشد'
                }
            
            # تجمیع اطلاعات audit
            audit_log = {
                'consent_id': str(consent.id),
                'created_at': consent.created_at.isoformat(),
                'created_by': consent.requested_by.get_full_name() if consent.requested_by else None,
                'status_history': [
                    {
                        'status': 'pending',
                        'timestamp': consent.created_at.isoformat(),
                        'actor': consent.requested_by.get_full_name() if consent.requested_by else None
                    }
                ],
                'signature_info': None,
                'revocation_info': None
            }
            
            # اطلاعات رضایت
            if consent.status == 'granted' and consent.consent_date:
                signature_verification = await self._verify_consent_signature(consent)
                audit_log['signature_info'] = {
                    'granted_at': consent.consent_date.isoformat(),
                    'ip_address': consent.ip_address,
                    'user_agent': consent.user_agent[:100] if consent.user_agent else None,
                    'signature_valid': signature_verification['is_valid'],
                    'signature_hash': hashlib.sha256(
                        consent.digital_signature.encode()
                    ).hexdigest()[:16] if consent.digital_signature else None
                }
                
                audit_log['status_history'].append({
                    'status': 'granted',
                    'timestamp': consent.consent_date.isoformat(),
                    'actor': 'Patient',
                    'ip_address': consent.ip_address
                })
            
            # اطلاعات لغو
            if consent.status == 'revoked':
                audit_log['revocation_info'] = {
                    'revoked_at': consent.updated_at.isoformat(),
                    'reason': consent.notes
                }
                
                audit_log['status_history'].append({
                    'status': 'revoked',
                    'timestamp': consent.updated_at.isoformat(),
                    'actor': 'System'
                })
            
            return True, {
                'audit_log': audit_log
            }
            
        except Exception as e:
            self.logger.error(f"Error getting consent audit log: {str(e)}")
            return False, {
                'error': 'audit_failed',
                'message': 'خطا در دریافت لاگ حسابرسی'
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
    
    async def _check_duplicate_consent(
        self,
        patient_id: str,
        consent_type: str,
        title: str
    ) -> Dict[str, Any]:
        """بررسی تکراری بودن رضایت‌نامه"""
        try:
            existing_consent = MedicalConsent.objects.filter(
                patient_id=patient_id,
                consent_type=consent_type,
                title=title,
                status__in=['pending', 'granted']
            ).first()
            
            return {
                'has_duplicate': existing_consent is not None,
                'existing_id': str(existing_consent.id) if existing_consent else None
            }
            
        except Exception as e:
            self.logger.error(f"Error checking duplicate consent: {str(e)}")
            return {'has_duplicate': False}
    
    async def _can_process_consent(self, consent: MedicalConsent) -> bool:
        """بررسی امکان پردازش رضایت‌نامه"""
        # فقط رضایت‌نامه‌های در انتظار قابل پردازش هستند
        if consent.status != 'pending':
            return False
        
        # بررسی انقضا
        if consent.is_expired:
            return False
        
        return True
    
    async def _process_digital_signature(
        self,
        signature: str,
        consent_id: str,
        client_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """پردازش امضای دیجیتال"""
        try:
            # ایجاد امضای ایمن
            timestamp = timezone.now().isoformat()
            ip_address = client_info.get('ip_address', '0.0.0.0') if client_info else '0.0.0.0'
            
            # ترکیب اطلاعات برای ایجاد hash
            signature_data = f"{signature}:{consent_id}:{timestamp}:{ip_address}:{self.signature_salt}"
            signature_hash = hashlib.sha256(signature_data.encode()).hexdigest()
            
            # ایجاد امضای نهایی
            final_signature = f"{signature}:{timestamp}:{signature_hash[:32]}"
            
            return final_signature
            
        except Exception as e:
            self.logger.error(f"Error processing digital signature: {str(e)}")
            return signature  # بازگشت امضای اصلی در صورت خطا
    
    async def _verify_consent_signature(self, consent: MedicalConsent) -> Dict[str, Any]:
        """تایید امضای رضایت‌نامه"""
        try:
            if not consent.digital_signature:
                return {'is_valid': False, 'reason': 'no_signature'}
            
            # تجزیه امضا
            parts = consent.digital_signature.split(':')
            if len(parts) < 3:
                return {'is_valid': False, 'reason': 'invalid_format'}
            
            original_signature = parts[0]
            timestamp = parts[1]
            signature_hash = parts[2]
            
            # بازسازی hash
            signature_data = f"{original_signature}:{str(consent.id)}:{timestamp}:{consent.ip_address}:{self.signature_salt}"
            expected_hash = hashlib.sha256(signature_data.encode()).hexdigest()[:32]
            
            is_valid = signature_hash == expected_hash
            
            return {
                'is_valid': is_valid,
                'signed_at': timestamp,
                'reason': 'valid' if is_valid else 'hash_mismatch'
            }
            
        except Exception as e:
            self.logger.error(f"Error verifying consent signature: {str(e)}")
            return {'is_valid': False, 'reason': 'verification_error'}
    
    async def _update_expired_consents(self, consents):
        """به‌روزرسانی وضعیت رضایت‌نامه‌های منقضی شده"""
        try:
            expired_consents = [
                c for c in consents 
                if c.is_expired and c.status == 'pending'
            ]
            
            if expired_consents:
                for consent in expired_consents:
                    consent.status = 'expired'
                
                MedicalConsent.objects.bulk_update(
                    expired_consents, ['status']
                )
                
        except Exception as e:
            self.logger.error(f"Error updating expired consents: {str(e)}")
    
    async def _calculate_consents_statistics(self, consents) -> Dict[str, Any]:
        """محاسبه آمار رضایت‌نامه‌ها"""
        try:
            total_count = consents.count()
            
            # آمار بر اساس وضعیت
            status_stats = {}
            status_counts = consents.values('status').annotate(count=Count('id'))
            for item in status_counts:
                status_stats[item['status']] = item['count']
            
            # آمار بر اساس نوع
            type_stats = {}
            type_counts = consents.values('consent_type').annotate(count=Count('id'))
            for item in type_counts:
                type_stats[item['consent_type']] = item['count']
            
            # رضایت‌نامه‌های منقضی شده
            expired_count = len([c for c in consents if c.is_expired])
            
            return {
                'total': total_count,
                'by_status': status_stats,
                'by_type': type_stats,
                'expired': expired_count,
                'valid': total_count - expired_count
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating consents statistics: {str(e)}")
            return {}
    
    async def _calculate_search_statistics(self, consents) -> Dict[str, Any]:
        """محاسبه آمار نتایج جستجو"""
        try:
            return {
                'total': len(consents),
                'statuses': list(set(c.status for c in consents)),
                'types': list(set(c.consent_type for c in consents)),
                'date_range': {
                    'earliest': min(c.created_date for c in consents if c.created_date).isoformat() if consents else None,
                    'latest': max(c.created_date for c in consents if c.created_date).isoformat() if consents else None
                }
            }
        except Exception as e:
            self.logger.error(f"Error calculating search statistics: {str(e)}")
            return {}
    
    async def _clear_patient_consents_cache(self, patient_id: str):
        """پاک کردن کش رضایت‌نامه‌های بیمار"""
        try:
            # کلیدهای مرتبط با این بیمار
            keys_to_delete = []
            
            # کلیدهای عمومی
            for include_expired in [True, False]:
                keys_to_delete.append(f"consents:{patient_id}:all:all:{include_expired}")
            
            # کلیدهای نوع‌های مختلف
            consent_types = ['treatment', 'surgery', 'data_sharing', 'research', 'telemedicine', 'recording', 'emergency']
            statuses = ['pending', 'granted', 'denied', 'expired', 'revoked']
            
            for consent_type in consent_types:
                for status in statuses:
                    for include_expired in [True, False]:
                        keys_to_delete.append(f"consents:{patient_id}:{consent_type}:{status}:{include_expired}")
            
            cache.delete_many(keys_to_delete)
            
        except Exception as e:
            self.logger.error(f"Error clearing patient consents cache: {str(e)}")