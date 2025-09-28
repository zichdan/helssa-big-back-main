"""
Helper functions برای API Gateway
"""
import logging
from typing import Dict, Tuple, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from rest_framework.request import Request

from ..models import RateLimitTracker


logger = logging.getLogger(__name__)


class GatewayHelpers:
    """
    کلاس Helper functions برای API Gateway
    
    این کلاس شامل توابع کمکی مختلف برای عملیات رایج است
    """
    
    def __init__(self):
        """مقداردهی اولیه"""
        self.logger = logging.getLogger(__name__)
        
    def get_client_ip(self, request: Request) -> str:
        """
        استخراج IP واقعی کلاینت
        
        Args:
            request: درخواست HTTP
            
        Returns:
            str: آدرس IP کلاینت
        """
        try:
            # بررسی X-Forwarded-For header
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                # اولین IP در لیست IP واقعی کلاینت است
                ip = x_forwarded_for.split(',')[0].strip()
                return ip
            
            # بررسی X-Real-IP header
            x_real_ip = request.META.get('HTTP_X_REAL_IP')
            if x_real_ip:
                return x_real_ip.strip()
            
            # استفاده از REMOTE_ADDR
            remote_addr = request.META.get('REMOTE_ADDR')
            if remote_addr:
                return remote_addr
            
            return 'unknown'
            
        except Exception as e:
            self.logger.error(f"Error extracting client IP: {str(e)}")
            return 'unknown'
    
    def check_rate_limit(self, user, ip_address: str, endpoint: str, limit: int = 100, window_minutes: int = 60) -> Tuple[bool, Dict[str, Any]]:
        """
        بررسی محدودیت نرخ درخواست
        
        Args:
            user: کاربر (می‌تواند None باشد)
            ip_address: آدرس IP
            endpoint: نقطه پایانی
            limit: حد مجاز درخواست در بازه زمانی
            window_minutes: بازه زمانی به دقیقه
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (مجاز بودن، اطلاعات)
        """
        try:
            if not getattr(settings, 'API_GATEWAY_RATE_LIMIT_ENABLED', True):
                return True, {'rate_limit': 'disabled'}
            
            window_start = timezone.now() - timedelta(minutes=window_minutes)
            
            # کلید cache برای سرعت بیشتر
            cache_key = f"rate_limit:{user.id if user else 'anon'}:{ip_address}:{endpoint}"
            
            # بررسی cache
            cached_count = cache.get(cache_key)
            if cached_count is not None:
                if cached_count >= limit:
                    return False, {
                        'error': 'Rate limit exceeded',
                        'message': 'تعداد درخواست‌ها بیش از حد مجاز است',
                        'limit': limit,
                        'window_minutes': window_minutes,
                        'retry_after': window_minutes * 60
                    }
                
                # افزایش شمارنده
                cache.set(cache_key, cached_count + 1, window_minutes * 60)
                
                return True, {
                    'requests_count': cached_count + 1,
                    'limit': limit,
                    'remaining': limit - (cached_count + 1)
                }
            
            # اگر در cache نبود، از دیتابیس بررسی کن
            if user:
                tracker, created = RateLimitTracker.objects.get_or_create(
                    user=user,
                    ip_address=ip_address,
                    endpoint=endpoint,
                    window_start__gte=window_start,
                    defaults={
                        'request_count': 1,
                        'window_start': timezone.now()
                    }
                )
                
                if not created:
                    if tracker.request_count >= limit:
                        return False, {
                            'error': 'Rate limit exceeded',
                            'message': 'تعداد درخواست‌ها بیش از حد مجاز است',
                            'limit': limit,
                            'window_minutes': window_minutes,
                            'retry_after': window_minutes * 60
                        }
                    
                    tracker.request_count += 1
                    tracker.save()
                
                # ذخیره در cache
                cache.set(cache_key, tracker.request_count, window_minutes * 60)
                
                return True, {
                    'requests_count': tracker.request_count,
                    'limit': limit,
                    'remaining': limit - tracker.request_count
                }
            else:
                # برای کاربران ناشناس از cache استفاده کن
                cache.set(cache_key, 1, window_minutes * 60)
                
                return True, {
                    'requests_count': 1,
                    'limit': limit,
                    'remaining': limit - 1
                }
                
        except Exception as e:
            self.logger.error(f"Rate limit check error: {str(e)}")
            # در صورت خطا، اجازه ادامه می‌دهیم
            return True, {'error': 'Rate limit check failed'}
    
    def validate_json_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        اعتبارسنجی JSON بر اساس schema
        
        Args:
            data: داده‌های JSON
            schema: طرح اعتبارسنجی
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (معتبر بودن، خطاها)
        """
        try:
            import jsonschema
            
            jsonschema.validate(instance=data, schema=schema)
            return True, {}
            
        except ImportError:
            # اگر jsonschema نصب نیست، اعتبارسنجی ساده انجام دهیم
            return self._simple_schema_validation(data, schema)
            
        except jsonschema.ValidationError as e:
            return False, {
                'error': 'Schema validation failed',
                'message': 'داده‌ها با طرح مورد نظر مطابقت ندارند',
                'details': str(e)
            }
        except Exception as e:
            return False, {
                'error': 'Validation error',
                'message': 'خطا در اعتبارسنجی',
                'details': str(e)
            }
    
    def _simple_schema_validation(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        اعتبارسنجی ساده JSON
        
        Args:
            data: داده‌های JSON
            schema: طرح اعتبارسنجی
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (معتبر بودن، خطاها)
        """
        try:
            required_fields = schema.get('required', [])
            properties = schema.get('properties', {})
            
            # بررسی فیلدهای الزامی
            for field in required_fields:
                if field not in data:
                    return False, {
                        'error': f'Required field missing: {field}',
                        'message': f'فیلد الزامی {field} موجود نیست'
                    }
            
            # بررسی نوع فیلدها
            for field, field_schema in properties.items():
                if field in data:
                    field_type = field_schema.get('type')
                    if field_type:
                        if not self._check_type(data[field], field_type):
                            return False, {
                                'error': f'Invalid type for field {field}',
                                'message': f'نوع فیلد {field} نامعتبر است'
                            }
            
            return True, {}
            
        except Exception as e:
            return False, {
                'error': 'Simple validation error',
                'details': str(e)
            }
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """بررسی نوع مقدار"""
        if expected_type == 'string':
            return isinstance(value, str)
        elif expected_type == 'integer':
            return isinstance(value, int)
        elif expected_type == 'number':
            return isinstance(value, (int, float))
        elif expected_type == 'boolean':
            return isinstance(value, bool)
        elif expected_type == 'array':
            return isinstance(value, list)
        elif expected_type == 'object':
            return isinstance(value, dict)
        else:
            return True  # نوع ناشناخته را قبول کن
    
    def sanitize_text(self, text: str, max_length: int = 10000) -> str:
        """
        پاکسازی متن از کاراکترهای مخرب
        
        Args:
            text: متن ورودی
            max_length: حداکثر طول مجاز
            
        Returns:
            str: متن پاکسازی شده
        """
        try:
            if not isinstance(text, str):
                return ""
            
            # محدود کردن طول
            if len(text) > max_length:
                text = text[:max_length]
            
            # حذف کاراکترهای کنترلی خطرناک
            import re
            
            # حذف کاراکترهای کنترلی (به جز \n, \r, \t)
            text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
            
            # نرمال‌سازی فاصله‌ها
            text = re.sub(r'\s+', ' ', text)
            
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"Text sanitization error: {str(e)}")
            return ""
    
    def format_file_size(self, size_bytes: int) -> str:
        """
        فرمت کردن اندازه فایل
        
        Args:
            size_bytes: اندازه به بایت
            
        Returns:
            str: اندازه فرمت شده
        """
        try:
            if size_bytes == 0:
                return "0B"
            
            size_names = ["B", "KB", "MB", "GB", "TB"]
            i = 0
            size = float(size_bytes)
            
            while size >= 1024.0 and i < len(size_names) - 1:
                size /= 1024.0
                i += 1
            
            return f"{size:.1f}{size_names[i]}"
            
        except Exception:
            return f"{size_bytes}B"
    
    def generate_trace_id(self) -> str:
        """
        تولید شناسه ردگیری یکتا
        
        Returns:
            str: شناسه ردگیری
        """
        try:
            import uuid
            return f"trace_{uuid.uuid4().hex[:16]}"
        except Exception:
            # اگر uuid کار نکرد، از timestamp استفاده کن
            import time
            return f"trace_{int(time.time()*1000000)}"
    
    def mask_sensitive_data(self, data: Dict[str, Any], sensitive_fields: Optional[list] = None) -> Dict[str, Any]:
        """
        پوشاندن داده‌های حساس
        
        Args:
            data: داده‌های ورودی
            sensitive_fields: لیست فیلدهای حساس
            
        Returns:
            Dict[str, Any]: داده‌های پوشانده شده
        """
        try:
            if sensitive_fields is None:
                sensitive_fields = [
                    'password', 'token', 'api_key', 'secret',
                    'authorization', 'credit_card', 'ssn', 'national_code'
                ]
            
            masked_data = data.copy()
            
            for key, value in masked_data.items():
                if any(sensitive in key.lower() for sensitive in sensitive_fields):
                    if isinstance(value, str) and len(value) > 4:
                        masked_data[key] = value[:2] + '*' * (len(value) - 4) + value[-2:]
                    else:
                        masked_data[key] = '***'
                elif isinstance(value, dict):
                    masked_data[key] = self.mask_sensitive_data(value, sensitive_fields)
            
            return masked_data
            
        except Exception as e:
            self.logger.error(f"Data masking error: {str(e)}")
            return data
    
    def calculate_processing_priority(self, user, request_type: str, request_size: int) -> int:
        """
        محاسبه اولویت پردازش درخواست
        
        Args:
            user: کاربر درخواست‌کننده
            request_type: نوع درخواست
            request_size: اندازه درخواست
            
        Returns:
            int: اولویت (1=بالا، 5=پایین)
        """
        try:
            priority = 3  # اولویت متوسط
            
            # اولویت بر اساس نوع کاربر
            if user and hasattr(user, 'user_type'):
                if user.user_type == 'admin':
                    priority -= 2
                elif user.user_type == 'doctor':
                    priority -= 1
                elif user.user_type == 'staff':
                    priority += 0
                else:  # patient
                    priority += 1
            else:
                # کاربر مهمان
                priority += 2
            
            # اولویت بر اساس نوع درخواست
            high_priority_types = ['emergency', 'critical', 'health_check']
            if request_type in high_priority_types:
                priority -= 1
            
            # اولویت بر اساس اندازه درخواست
            if request_size > 1024 * 1024:  # بزرگتر از 1MB
                priority += 1
            
            # محدود کردن اولویت
            priority = max(1, min(5, priority))
            
            return priority
            
        except Exception as e:
            self.logger.error(f"Priority calculation error: {str(e)}")
            return 3  # اولویت متوسط
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """
        دریافت متریک‌های سیستم
        
        Returns:
            Dict[str, Any]: متریک‌های سیستم
        """
        try:
            import psutil
            import os
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Process info
            process = psutil.Process(os.getpid())
            process_memory = process.memory_info()
            
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count()
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'process_rss': process_memory.rss,
                    'process_vms': process_memory.vms
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                },
                'timestamp': timezone.now().isoformat()
            }
            
        except ImportError:
            # اگر psutil نصب نیست
            return {
                'error': 'psutil not available',
                'timestamp': timezone.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"System metrics error: {str(e)}")
            return {
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
    
    def clean_old_logs(self, days_to_keep: int = 30) -> Dict[str, int]:
        """
        پاکسازی لاگ‌های قدیمی
        
        Args:
            days_to_keep: تعداد روزهایی که لاگ‌ها باید نگهداری شوند
            
        Returns:
            Dict[str, int]: تعداد رکوردهای پاک شده
        """
        try:
            from ..models import APIRequest
            
            cutoff_date = timezone.now() - timedelta(days=days_to_keep)
            
            # پاکسازی درخواست‌های API قدیمی
            deleted_requests = APIRequest.objects.filter(
                created_at__lt=cutoff_date
            ).count()
            
            APIRequest.objects.filter(
                created_at__lt=cutoff_date
            ).delete()
            
            # پاکسازی rate limit trackers قدیمی
            deleted_rate_limits = RateLimitTracker.objects.filter(
                window_start__lt=cutoff_date
            ).count()
            
            RateLimitTracker.objects.filter(
                window_start__lt=cutoff_date
            ).delete()
            
            self.logger.info(
                'Old logs cleaned',
                extra={
                    'deleted_requests': deleted_requests,
                    'deleted_rate_limits': deleted_rate_limits,
                    'days_to_keep': days_to_keep
                }
            )
            
            return {
                'deleted_requests': deleted_requests,
                'deleted_rate_limits': deleted_rate_limits,
                'cutoff_date': cutoff_date.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Log cleanup error: {str(e)}")
            return {
                'error': str(e),
                'deleted_requests': 0,
                'deleted_rate_limits': 0
            }