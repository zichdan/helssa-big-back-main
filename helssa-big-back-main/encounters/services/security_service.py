from typing import Dict, List, Optional
import hashlib
from datetime import datetime
from asgiref.sync import sync_to_async
from django.utils import timezone

from ..models import Encounter
from ..utils.encryption import generate_encryption_key, encrypt_data, decrypt_data


class EncounterSecurityService:
    """سرویس امنیت ملاقات‌ها"""
    
    def __init__(self):
        pass
        
    async def check_encounter_access(
        self,
        user_id: str,
        encounter_id: str,
        action: str = 'view'
    ) -> bool:
        """بررسی دسترسی به ملاقات"""
        
        try:
            encounter = await sync_to_async(Encounter.objects.get)(id=encounter_id)
        except Encounter.DoesNotExist:
            return False
            
        # دسترسی‌های پایه
        # بیمار و پزشک همیشه دسترسی دارند
        if str(encounter.patient_id) == user_id:
            allowed_actions = ['view', 'download']
            return action in allowed_actions
            
        if str(encounter.doctor_id) == user_id:
            return True  # پزشک دسترسی کامل دارد
            
        # TODO: بررسی دسترسی موقت از unified_access
        
        # TODO: بررسی نقش‌های سیستمی
        
        # ثبت در audit log
        await self._log_access_attempt(
            user_id=user_id,
            resource_type='encounter',
            resource_id=encounter_id,
            action=action,
            granted=False
        )
        
        return False
        
    def generate_encryption_key(self) -> str:
        """تولید کلید رمزنگاری برای ملاقات"""
        return generate_encryption_key()
        
    async def encrypt_sensitive_data(
        self,
        data: str,
        encryption_key: str
    ) -> str:
        """رمزنگاری داده‌های حساس"""
        return await encrypt_data(data.encode(), encryption_key)
        
    async def decrypt_sensitive_data(
        self,
        encrypted_data: str,
        encryption_key: str
    ) -> str:
        """رمزگشایی داده‌های حساس"""
        decrypted = await decrypt_data(encrypted_data, encryption_key)
        return decrypted.decode()
        
    async def anonymize_encounter_data(
        self,
        encounter_id: str
    ) -> Dict:
        """ناشناس‌سازی داده‌های ملاقات برای تحقیقات"""
        
        encounter = await sync_to_async(
            Encounter.objects.select_related('patient', 'soap_report').get
        )(id=encounter_id)
        
        # محاسبه سن بیمار
        # TODO: دریافت تاریخ تولد از UnifiedUser
        patient_age = 30  # مقدار موقت
        
        # داده‌های ناشناس شده
        anonymized = {
            'id': hashlib.sha256(str(encounter.id).encode()).hexdigest()[:16],
            'patient_age': patient_age,
            'patient_gender': 'unknown',  # TODO: دریافت از UnifiedUser
            'visit_type': encounter.type,
            'duration_minutes': encounter.duration_minutes,
            'chief_complaint_category': self._categorize_complaint(
                encounter.chief_complaint
            )
        }
        
        # گزارش SOAP ناشناس
        if hasattr(encounter, 'soap_report'):
            report = encounter.soap_report
            anonymized['diagnoses'] = [
                d.get('icd_code') for d in report.diagnoses
            ]
            anonymized['medication_count'] = len(report.medications)
            anonymized['lab_order_count'] = len(report.lab_orders)
            
        return anonymized
        
    async def audit_encounter_access(
        self,
        encounter_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """گزارش دسترسی‌ها به ملاقات"""
        
        # TODO: دریافت از جدول AuditLog
        # فعلاً لیست خالی
        return []
        
    async def validate_file_access(
        self,
        user_id: str,
        file_id: str
    ) -> bool:
        """اعتبارسنجی دسترسی به فایل"""
        
        # TODO: بررسی از EncounterFile
        return False
        
    async def generate_access_token(
        self,
        user_id: str,
        encounter_id: str,
        expires_in_minutes: int = 60
    ) -> str:
        """تولید توکن دسترسی موقت"""
        
        import jwt
        from django.conf import settings
        
        payload = {
            'user_id': user_id,
            'encounter_id': encounter_id,
            'exp': datetime.utcnow() + timezone.timedelta(minutes=expires_in_minutes)
        }
        
        token = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm='HS256'
        )
        
        return token
        
    async def verify_access_token(
        self,
        token: str
    ) -> Optional[Dict]:
        """اعتبارسنجی توکن دسترسی"""
        
        import jwt
        from django.conf import settings
        
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=['HS256']
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
            
    async def check_data_retention_policy(
        self,
        encounter_id: str
    ) -> Dict:
        """بررسی سیاست نگهداری داده"""
        
        encounter = await sync_to_async(Encounter.objects.get)(id=encounter_id)
        
        # محاسبه مدت زمان از اتمام ویزیت
        if encounter.ended_at:
            days_since_completion = (timezone.now() - encounter.ended_at).days
        else:
            days_since_completion = 0
            
        # سیاست‌های نگهداری (به روز)
        retention_policies = {
            'audio_files': 365,      # 1 سال
            'video_files': 180,      # 6 ماه
            'transcripts': 1825,     # 5 سال
            'soap_reports': 3650,    # 10 سال
            'prescriptions': 3650,   # 10 سال
        }
        
        status = {}
        for data_type, retention_days in retention_policies.items():
            remaining_days = retention_days - days_since_completion
            status[data_type] = {
                'retention_days': retention_days,
                'days_elapsed': days_since_completion,
                'days_remaining': max(0, remaining_days),
                'should_delete': remaining_days <= 0
            }
            
        return status
        
    async def apply_data_masking(
        self,
        data: Dict,
        masking_level: str = 'partial'
    ) -> Dict:
        """اعمال ماسک‌گذاری روی داده‌های حساس"""
        
        if masking_level == 'full':
            # ماسک کامل
            masked_data = {
                'patient_name': '***',
                'patient_phone': '***',
                'patient_id': '***',
                'doctor_name': '***',
                'doctor_id': '***'
            }
        elif masking_level == 'partial':
            # ماسک جزئی
            masked_data = data.copy()
            
            # ماسک شماره تلفن
            if 'patient_phone' in masked_data:
                phone = masked_data['patient_phone']
                masked_data['patient_phone'] = f"{phone[:4]}****{phone[-2:]}"
                
            # ماسک نام
            if 'patient_name' in masked_data:
                name_parts = masked_data['patient_name'].split()
                if len(name_parts) > 1:
                    masked_data['patient_name'] = f"{name_parts[0]} {name_parts[-1][0]}***"
                    
        else:
            # بدون ماسک
            masked_data = data
            
        return masked_data
        
    def _categorize_complaint(self, complaint: str) -> str:
        """دسته‌بندی شکایت اصلی"""
        
        # کلمات کلیدی برای دسته‌بندی
        categories = {
            'respiratory': ['سرفه', 'تنگی نفس', 'خلط', 'گلودرد'],
            'gastrointestinal': ['درد شکم', 'اسهال', 'یبوست', 'تهوع'],
            'cardiovascular': ['درد قفسه سینه', 'تپش قلب', 'فشار خون'],
            'neurological': ['سردرد', 'سرگیجه', 'تشنج', 'بی‌حسی'],
            'musculoskeletal': ['درد مفصل', 'کمردرد', 'درد عضلانی'],
            'dermatological': ['خارش', 'بثورات', 'قرمزی پوست'],
            'general': ['تب', 'ضعف', 'بی‌اشتهایی', 'کاهش وزن']
        }
        
        complaint_lower = complaint.lower()
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in complaint_lower:
                    return category
                    
        return 'other'
        
    async def _log_access_attempt(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        granted: bool
    ):
        """ثبت تلاش دسترسی در audit log"""
        
        # TODO: ذخیره در جدول AuditLog
        log_entry = {
            'user_id': user_id,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'action': action,
            'granted': granted,
            'timestamp': timezone.now().isoformat()
        }
        
        # فعلاً فقط print
        print(f"Access log: {log_entry}")