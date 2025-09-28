"""
سرویس مدیریت رضایت‌های کاربر (Consent Management)
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from ..models import ConsentRecord, DataClassification

User = get_user_model()
logger = logging.getLogger(__name__)


class ConsentManager:
    """
    کلاس مدیریت رضایت‌های کاربر
    """
    
    def __init__(self):
        self.logger = logger
    
    def grant_consent(
        self,
        user_id: str,
        consent_type: str,
        purpose: str,
        data_categories: List[str],
        legal_basis: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        expires_in_days: Optional[int] = None,
        version: str = "1.0"
    ) -> ConsentRecord:
        """
        اعطای رضایت جدید
        
        Args:
            user_id: شناسه کاربر
            consent_type: نوع رضایت
            purpose: هدف استفاده
            data_categories: لیست دسته‌بندی داده‌ها
            legal_basis: مبنای قانونی
            ip_address: آدرس IP
            user_agent: User Agent
            expires_in_days: تعداد روز تا انقضا
            version: نسخه سیاست
            
        Returns:
            ConsentRecord: رکورد رضایت ایجاد شده
        """
        try:
            with transaction.atomic():
                # بررسی وجود کاربر
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    raise ValueError(f"کاربر با شناسه {user_id} یافت نشد")
                
                # بررسی وجود دسته‌بندی‌های داده
                classifications = DataClassification.objects.filter(
                    id__in=data_categories,
                    is_active=True
                )
                
                if len(classifications) != len(data_categories):
                    missing = set(data_categories) - set(classifications.values_list('id', flat=True))
                    raise ValueError(f"دسته‌بندی‌های داده یافت نشد: {missing}")
                
                # محاسبه تاریخ انقضا
                expires_at = None
                if expires_in_days:
                    expires_at = timezone.now() + timedelta(days=expires_in_days)
                
                # پس‌گیری رضایت‌های قبلی از همین نوع
                existing_consents = ConsentRecord.objects.filter(
                    user=user,
                    consent_type=consent_type,
                    status='granted'
                )
                
                for consent in existing_consents:
                    consent.status = 'withdrawn'
                    consent.withdrawn_at = timezone.now()
                    consent.withdrawal_reason = 'جایگزین شده با رضایت جدید'
                    consent.save()
                
                # ایجاد رضایت جدید
                consent = ConsentRecord.objects.create(
                    user=user,
                    consent_type=consent_type,
                    purpose=purpose,
                    legal_basis=legal_basis,
                    ip_address=ip_address,
                    user_agent=user_agent or '',
                    expires_at=expires_at,
                    version=version
                )
                
                # اضافه کردن دسته‌بندی‌های داده
                consent.data_categories.set(classifications)
                
                self.logger.info(
                    f"رضایت جدید اعطا شد",
                    extra={
                        'user_id': user_id,
                        'consent_id': str(consent.id),
                        'consent_type': consent_type,
                        'purpose': purpose
                    }
                )
                
                return consent
                
        except Exception as e:
            self.logger.error(
                f"خطا در اعطای رضایت: {str(e)}",
                extra={'user_id': user_id, 'consent_type': consent_type}
            )
            raise
    
    def withdraw_consent(
        self,
        user_id: str,
        consent_type: str,
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        پس‌گیری رضایت
        
        Args:
            user_id: شناسه کاربر
            consent_type: نوع رضایت
            reason: دلیل پس‌گیری
            ip_address: آدرس IP
            user_agent: User Agent
            
        Returns:
            bool: آیا عملیات موفق بود؟
        """
        try:
            with transaction.atomic():
                # یافتن رضایت‌های فعال
                consents = ConsentRecord.objects.filter(
                    user_id=user_id,
                    consent_type=consent_type,
                    status='granted'
                )
                
                if not consents.exists():
                    self.logger.warning(
                        f"رضایت فعال برای پس‌گیری یافت نشد",
                        extra={'user_id': user_id, 'consent_type': consent_type}
                    )
                    return False
                
                # پس‌گیری تمام رضایت‌های فعال
                updated_count = consents.update(
                    status='withdrawn',
                    withdrawn_at=timezone.now(),
                    withdrawal_reason=reason
                )
                
                self.logger.info(
                    f"رضایت پس‌گرفته شد",
                    extra={
                        'user_id': user_id,
                        'consent_type': consent_type,
                        'reason': reason,
                        'count': updated_count
                    }
                )
                
                return True
                
        except Exception as e:
            self.logger.error(
                f"خطا در پس‌گیری رضایت: {str(e)}",
                extra={'user_id': user_id, 'consent_type': consent_type}
            )
            return False
    
    def check_consent(
        self,
        user_id: str,
        consent_type: str,
        data_category_id: Optional[str] = None
    ) -> bool:
        """
        بررسی وجود رضایت فعال
        
        Args:
            user_id: شناسه کاربر
            consent_type: نوع رضایت
            data_category_id: شناسه دسته‌بندی داده (اختیاری)
            
        Returns:
            bool: آیا رضایت فعال وجود دارد؟
        """
        try:
            query = ConsentRecord.objects.filter(
                user_id=user_id,
                consent_type=consent_type,
                status='granted'
            )
            
            # بررسی انقضا
            now = timezone.now()
            from django.db import models
            query = query.filter(
                models.Q(expires_at__isnull=True) | 
                models.Q(expires_at__gt=now)
            )
            
            # بررسی دسته‌بندی داده خاص
            if data_category_id:
                query = query.filter(
                    data_categories__id=data_category_id
                )
            
            return query.exists()
            
        except Exception as e:
            self.logger.error(
                f"خطا در بررسی رضایت: {str(e)}",
                extra={'user_id': user_id, 'consent_type': consent_type}
            )
            return False
    
    def get_user_consents(self, user_id: str) -> List[Dict[str, Any]]:
        """
        دریافت تمام رضایت‌های کاربر
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            List: لیست رضایت‌های کاربر
        """
        try:
            consents = ConsentRecord.objects.filter(
                user_id=user_id
            ).select_related('user').prefetch_related('data_categories').order_by('-granted_at')
            
            result = []
            for consent in consents:
                result.append({
                    'id': str(consent.id),
                    'consent_type': consent.consent_type,
                    'consent_type_display': consent.get_consent_type_display(),
                    'status': consent.status,
                    'status_display': consent.get_status_display(),
                    'purpose': consent.purpose,
                    'legal_basis': consent.legal_basis,
                    'granted_at': consent.granted_at,
                    'expires_at': consent.expires_at,
                    'withdrawn_at': consent.withdrawn_at,
                    'withdrawal_reason': consent.withdrawal_reason,
                    'version': consent.version,
                    'is_active': consent.is_active,
                    'data_categories': [
                        {
                            'id': str(cat.id),
                            'name': cat.name,
                            'type': cat.classification_type
                        }
                        for cat in consent.data_categories.all()
                    ]
                })
            
            return result
            
        except Exception as e:
            self.logger.error(
                f"خطا در دریافت رضایت‌های کاربر: {str(e)}",
                extra={'user_id': user_id}
            )
            return []
    
    def expire_consents(self) -> int:
        """
        منقضی کردن رضایت‌های انقضا یافته
        
        Returns:
            int: تعداد رضایت‌های منقضی شده
        """
        try:
            now = timezone.now()
            
            expired_consents = ConsentRecord.objects.filter(
                status='granted',
                expires_at__lt=now
            )
            
            count = expired_consents.update(status='expired')
            
            self.logger.info(
                f"رضایت‌های منقضی شده بروزرسانی شدند",
                extra={'count': count}
            )
            
            return count
            
        except Exception as e:
            self.logger.error(f"خطا در منقضی کردن رضایت‌ها: {str(e)}")
            return 0
    
    def get_consent_statistics(self) -> Dict[str, Any]:
        """
        دریافت آمار رضایت‌ها
        
        Returns:
            Dict: آمار رضایت‌ها
        """
        try:
            from django.db.models import Count
            
            # آمار کلی
            total_consents = ConsentRecord.objects.count()
            active_consents = ConsentRecord.objects.filter(status='granted').count()
            withdrawn_consents = ConsentRecord.objects.filter(status='withdrawn').count()
            expired_consents = ConsentRecord.objects.filter(status='expired').count()
            
            # آمار بر اساس نوع رضایت
            consent_type_stats = ConsentRecord.objects.values('consent_type').annotate(
                count=Count('id')
            )
            
            # آمار بر اساس وضعیت
            status_stats = ConsentRecord.objects.values('status').annotate(
                count=Count('id')
            )
            
            return {
                'total_consents': total_consents,
                'active_consents': active_consents,
                'withdrawn_consents': withdrawn_consents,
                'expired_consents': expired_consents,
                'consent_type_breakdown': list(consent_type_stats),
                'status_breakdown': list(status_stats),
                'generated_at': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(f"خطا در تولید آمار رضایت‌ها: {str(e)}")
            return {}
    
    def validate_consent_requirements(
        self,
        user_id: str,
        requested_data_types: List[str],
        purpose: str
    ) -> Dict[str, Any]:
        """
        اعتبارسنجی نیازمندی‌های رضایت
        
        Args:
            user_id: شناسه کاربر
            requested_data_types: انواع داده درخواستی
            purpose: هدف استفاده
            
        Returns:
            Dict: نتیجه اعتبارسنجی
        """
        try:
            # دریافت رضایت‌های فعال کاربر
            active_consents = ConsentRecord.objects.filter(
                user_id=user_id,
                status='granted'
            ).prefetch_related('data_categories')
            
            # بررسی انقضا
            now = timezone.now()
            valid_consents = [
                consent for consent in active_consents
                if consent.expires_at is None or consent.expires_at > now
            ]
            
            # دسته‌بندی‌های داده مجاز
            allowed_categories = set()
            for consent in valid_consents:
                allowed_categories.update(
                    consent.data_categories.values_list('classification_type', flat=True)
                )
            
            # بررسی داده‌های درخواستی
            missing_consents = []
            for data_type in requested_data_types:
                if data_type not in allowed_categories:
                    missing_consents.append(data_type)
            
            is_valid = len(missing_consents) == 0
            
            return {
                'is_valid': is_valid,
                'allowed_categories': list(allowed_categories),
                'requested_categories': requested_data_types,
                'missing_consents': missing_consents,
                'active_consents_count': len(valid_consents),
                'purpose': purpose,
                'checked_at': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(
                f"خطا در اعتبارسنجی نیازمندی‌های رضایت: {str(e)}",
                extra={'user_id': user_id, 'purpose': purpose}
            )
            return {
                'is_valid': False,
                'error': str(e)
            }


# نمونه‌ای از consent manager برای استفاده در سایر بخش‌ها
default_consent_manager = ConsentManager()