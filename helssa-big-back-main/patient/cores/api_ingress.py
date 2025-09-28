"""
هسته API Ingress برای سیستم مدیریت بیماران
Patient Management API Ingress Core
"""

import logging
from typing import Dict, Any, Optional, Tuple
from django.core.cache import cache
from django.utils import timezone
from rest_framework import status
from rest_framework.request import Request

logger = logging.getLogger(__name__)


class PatientAPIIngress:
    """
    هسته API Ingress برای مدیریت ورود و خروج داده‌ها
    API Ingress core for managing data input/output
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache_timeout = 300  # 5 minutes
        
    async def process_incoming_request(
        self,
        request: Request,
        endpoint: str,
        data: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        پردازش درخواست ورودی
        Process incoming request
        
        Args:
            request: Django request object
            endpoint: نام endpoint
            data: داده‌های ورودی
            
        Returns:
            Tuple[bool, Dict]: (success, processed_data)
        """
        try:
            # لاگ درخواست
            self.logger.info(
                f"Processing request for endpoint: {endpoint}",
                extra={
                    'user_id': getattr(request.user, 'id', None),
                    'ip_address': self._get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'endpoint': endpoint,
                    'method': request.method
                }
            )
            
            # اعتبارسنجی اولیه
            validation_result = await self._validate_request(request, endpoint, data)
            if not validation_result['is_valid']:
                return False, validation_result
            
            # پردازش داده‌های ورودی
            processed_data = await self._process_input_data(data, endpoint)
            
            # Rate limiting check
            rate_limit_result = await self._check_rate_limit(request, endpoint)
            if not rate_limit_result['allowed']:
                return False, {
                    'error': 'Rate limit exceeded',
                    'message': 'تعداد درخواست‌ها بیش از حد مجاز است',
                    'retry_after': rate_limit_result.get('retry_after', 60)
                }
            
            # اضافه کردن metadata
            processed_data['_metadata'] = {
                'timestamp': timezone.now().isoformat(),
                'user_id': getattr(request.user, 'id', None),
                'ip_address': self._get_client_ip(request),
                'endpoint': endpoint,
                'request_id': self._generate_request_id()
            }
            
            return True, processed_data
            
        except Exception as e:
            self.logger.error(
                f"Error in API ingress: {str(e)}",
                extra={
                    'endpoint': endpoint,
                    'user_id': getattr(request.user, 'id', None),
                    'error': str(e)
                },
                exc_info=True
            )
            
            return False, {
                'error': 'Internal processing error',
                'message': 'خطا در پردازش درخواست'
            }
    
    async def format_response(
        self,
        data: Any,
        success: bool = True,
        message: Optional[str] = None,
        status_code: int = status.HTTP_200_OK
    ) -> Dict[str, Any]:
        """
        فرمت کردن پاسخ خروجی
        Format outgoing response
        
        Args:
            data: داده‌های پاسخ
            success: وضعیت موفقیت
            message: پیام اضافی
            status_code: کد وضعیت HTTP
            
        Returns:
            Dict: فرمت شده پاسخ
        """
        try:
            response = {
                'success': success,
                'status_code': status_code,
                'timestamp': timezone.now().isoformat(),
                'data': data if success else None,
                'message': message
            }
            
            # اضافه کردن جزئیات خطا در صورت ناموفق بودن
            if not success and isinstance(data, dict):
                response['errors'] = data
                response['data'] = None
            
            # فیلتر کردن داده‌های حساس
            if success:
                response['data'] = await self._filter_sensitive_data(data)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error formatting response: {str(e)}")
            return {
                'success': False,
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'message': 'خطا در فرمت کردن پاسخ',
                'data': None,
                'timestamp': timezone.now().isoformat()
            }
    
    async def _validate_request(
        self,
        request: Request,
        endpoint: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        اعتبارسنجی درخواست
        Validate request
        """
        try:
            # بررسی نوع محتوا
            content_type = request.content_type
            if content_type and 'application/json' not in content_type:
                if endpoint not in ['upload', 'file']:  # endpoints که فایل قبول می‌کنند
                    return {
                        'is_valid': False,
                        'error': 'Invalid content type',
                        'message': 'نوع محتوا باید application/json باشد'
                    }
            
            # بررسی حجم داده
            if isinstance(data, dict):
                data_size = len(str(data))
                if data_size > 1024 * 1024:  # 1MB limit
                    return {
                        'is_valid': False,
                        'error': 'Payload too large',
                        'message': 'حجم داده‌ها بیش از حد مجاز است'
                    }
            
            # بررسی فیلدهای مورد نیاز بر اساس endpoint
            required_fields = self._get_required_fields(endpoint)
            missing_fields = []
            
            for field in required_fields:
                if field not in data or data[field] is None:
                    missing_fields.append(field)
            
            if missing_fields:
                return {
                    'is_valid': False,
                    'error': 'Missing required fields',
                    'message': f'فیلدهای الزامی موجود نیست: {", ".join(missing_fields)}'
                }
            
            return {'is_valid': True}
            
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            return {
                'is_valid': False,
                'error': 'Validation error',
                'message': 'خطا در اعتبارسنجی درخواست'
            }
    
    async def _process_input_data(
        self,
        data: Dict[str, Any],
        endpoint: str
    ) -> Dict[str, Any]:
        """
        پردازش داده‌های ورودی
        Process input data
        """
        try:
            processed_data = data.copy()
            
            # تمیز کردن رشته‌ها
            for key, value in processed_data.items():
                if isinstance(value, str):
                    processed_data[key] = value.strip()
            
            # پردازش خاص بر اساس endpoint
            if endpoint == 'patient_profile':
                processed_data = await self._process_patient_data(processed_data)
            elif endpoint == 'medical_record':
                processed_data = await self._process_medical_record_data(processed_data)
            elif endpoint == 'prescription':
                processed_data = await self._process_prescription_data(processed_data)
            
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Data processing error: {str(e)}")
            raise
    
    async def _check_rate_limit(
        self,
        request: Request,
        endpoint: str
    ) -> Dict[str, Any]:
        """
        بررسی محدودیت نرخ درخواست
        Check rate limiting
        """
        try:
            user_id = getattr(request.user, 'id', None)
            ip_address = self._get_client_ip(request)
            
            # کلید کش برای rate limiting
            cache_key = f"rate_limit:{endpoint}:{user_id or ip_address}"
            
            # دریافت تعداد درخواست‌های فعلی
            current_requests = cache.get(cache_key, 0)
            
            # تعیین محدودیت بر اساس endpoint
            limit = self._get_rate_limit(endpoint)
            
            if current_requests >= limit:
                return {
                    'allowed': False,
                    'retry_after': 60
                }
            
            # افزایش شمارنده
            cache.set(cache_key, current_requests + 1, 60)  # 60 seconds window
            
            return {'allowed': True}
            
        except Exception as e:
            self.logger.error(f"Rate limit check error: {str(e)}")
            # در صورت خطا، اجازه دسترسی داده می‌شود
            return {'allowed': True}
    
    async def _filter_sensitive_data(self, data: Any) -> Any:
        """
        فیلتر کردن داده‌های حساس
        Filter sensitive data
        """
        if isinstance(data, dict):
            filtered_data = {}
            sensitive_fields = [
                'password', 'token', 'secret', 'key',
                'national_code', 'digital_signature'
            ]
            
            for key, value in data.items():
                if any(field in key.lower() for field in sensitive_fields):
                    if isinstance(value, str) and len(value) > 4:
                        filtered_data[key] = value[:2] + '*' * (len(value) - 4) + value[-2:]
                    else:
                        filtered_data[key] = '***'
                else:
                    filtered_data[key] = await self._filter_sensitive_data(value)
            
            return filtered_data
        
        elif isinstance(data, list):
            return [await self._filter_sensitive_data(item) for item in data]
        
        return data
    
    def _get_client_ip(self, request: Request) -> str:
        """
        دریافت IP کلاینت
        Get client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip
    
    def _generate_request_id(self) -> str:
        """
        تولید شناسه منحصر به فرد درخواست
        Generate unique request ID
        """
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _get_required_fields(self, endpoint: str) -> list:
        """
        دریافت فیلدهای الزامی بر اساس endpoint
        Get required fields based on endpoint
        """
        required_fields_map = {
            'patient_profile': ['first_name', 'last_name', 'national_code', 'birth_date'],
            'medical_record': ['patient', 'record_type', 'title', 'start_date'],
            'prescription': ['patient', 'medication_name', 'dosage', 'start_date'],
            'consent': ['patient', 'consent_type', 'title', 'consent_text']
        }
        return required_fields_map.get(endpoint, [])
    
    def _get_rate_limit(self, endpoint: str) -> int:
        """
        دریافت محدودیت نرخ بر اساس endpoint
        Get rate limit based on endpoint
        """
        rate_limits = {
            'patient_profile': 10,  # 10 requests per minute
            'medical_record': 20,
            'prescription': 15,
            'consent': 5,
            'search': 30,
            'default': 100
        }
        return rate_limits.get(endpoint, rate_limits['default'])
    
    async def _process_patient_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        پردازش اختصاصی داده‌های بیمار
        Process patient-specific data
        """
        # استانداردسازی کد ملی
        if 'national_code' in data:
            data['national_code'] = data['national_code'].strip().replace('-', '')
        
        # استانداردسازی شماره تلفن
        if 'emergency_contact_phone' in data:
            phone = data['emergency_contact_phone'].strip()
            # حذف کاراکترهای غیر عددی
            phone = ''.join(filter(str.isdigit, phone))
            if phone.startswith('98') and len(phone) == 12:
                phone = '0' + phone[2:]
            data['emergency_contact_phone'] = phone
        
        return data
    
    async def _process_medical_record_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        پردازش اختصاصی داده‌های سابقه پزشکی
        Process medical record specific data
        """
        # استانداردسازی تاریخ‌ها
        from datetime import datetime
        
        for date_field in ['start_date', 'end_date']:
            if date_field in data and isinstance(data[date_field], str):
                try:
                    # تبدیل فرمت‌های مختلف تاریخ
                    data[date_field] = datetime.strptime(
                        data[date_field], '%Y-%m-%d'
                    ).date()
                except ValueError:
                    pass  # اگر فرمت معتبر نبود، همان‌طور بماند
        
        return data
    
    async def _process_prescription_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        پردازش اختصاصی داده‌های نسخه
        Process prescription specific data
        """
        # استانداردسازی نام دارو
        if 'medication_name' in data:
            data['medication_name'] = data['medication_name'].title()
        
        # پردازش دوز
        if 'dosage' in data:
            dosage = data['dosage'].lower()
            # تبدیل اختصارات رایج
            dosage_replacements = {
                'mg': 'میلی‌گرم',
                'gr': 'گرم',
                'ml': 'میلی‌لیتر',
                'tab': 'قرص',
                'cap': 'کپسول'
            }
            for abbr, full in dosage_replacements.items():
                dosage = dosage.replace(abbr, full)
            data['dosage'] = dosage
        
        return data