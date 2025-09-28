"""
سرویس اصلی API Gateway
"""
import logging
from typing import Dict, Tuple, Any, Optional
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.request import Request

from ..cores import APIIngressCore, TextProcessorCore, SpeechProcessorCore, OrchestratorCore
from ..models import APIRequest, Workflow, RateLimitTracker
from .helpers import GatewayHelpers


User = get_user_model()
logger = logging.getLogger(__name__)


class APIGatewayService:
    """
    سرویس اصلی API Gateway
    
    این کلاس هماهنگی بین تمام قسمت‌های مختلف API Gateway را انجام می‌دهد
    """
    
    def __init__(self):
        """مقداردهی اولیه سرویس"""
        self.logger = logging.getLogger(__name__)
        self.ingress_core = APIIngressCore()
        self.text_processor = TextProcessorCore()
        self.speech_processor = SpeechProcessorCore()
        self.orchestrator = OrchestratorCore()
        self.helpers = GatewayHelpers()
        
        # تنظیمات rate limiting
        self.rate_limit_enabled = getattr(settings, 'API_GATEWAY_RATE_LIMIT_ENABLED', True)
        self.default_rate_limit = getattr(settings, 'API_GATEWAY_DEFAULT_RATE_LIMIT', 100)  # per hour
        
    def process_request(self, request: Request) -> Tuple[bool, Dict[str, Any]]:
        """
        پردازش کامل یک درخواست API
        
        Args:
            request: درخواست HTTP ورودی
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (موفقیت، نتیجه/خطا)
        """
        api_request = None
        
        try:
            # ایجاد لاگ درخواست
            api_request = self._create_api_request_log(request)
            
            # مرحله 1: API Ingress - اعتبارسنجی اولیه
            valid, ingress_result = self.ingress_core.validate_request(request)
            if not valid:
                api_request.mark_failed(
                    error_message=ingress_result.get('message', 'Validation failed'),
                    response_status=400
                )
                return False, ingress_result
            
            # مرحله 2: بررسی rate limiting
            if self.rate_limit_enabled:
                rate_check = self._check_rate_limit(request, api_request)
                if not rate_check[0]:
                    api_request.mark_failed(
                        error_message='Rate limit exceeded',
                        response_status=429
                    )
                    return False, rate_check[1]
            
            # مرحله 3: استخراج metadata
            metadata = self.ingress_core.extract_metadata(request)
            
            # مرحله 4: تشخیص نوع پردازش مورد نیاز
            processor_type, routing_config = self.ingress_core.route_request(request, metadata)
            api_request.processor_type = processor_type
            api_request.status = 'processing'
            api_request.save()
            
            # مرحله 5: انجام پردازش اصلی
            processing_result = self._execute_processing(
                request, processor_type, routing_config, metadata
            )
            
            if processing_result[0]:
                # موفق
                api_request.mark_completed(
                    response_status=200,
                    response_body=processing_result[1]
                )
                
                self.logger.info(
                    'Request processed successfully',
                    extra={
                        'request_id': str(api_request.id),
                        'processor_type': processor_type,
                        'processing_time': api_request.processing_time
                    }
                )
                
                return True, processing_result[1]
            else:
                # ناموفق
                api_request.mark_failed(
                    error_message=processing_result[1].get('message', 'Processing failed'),
                    response_status=processing_result[1].get('status_code', 500)
                )
                return False, processing_result[1]
                
        except Exception as e:
            self.logger.error(f"Request processing error: {str(e)}")
            
            if api_request:
                api_request.mark_failed(
                    error_message=str(e),
                    response_status=500
                )
            
            return False, {
                'error': 'Internal server error',
                'message': 'خطای داخلی سرور',
                'details': str(e) if settings.DEBUG else None
            }
    
    def process_text(self, text: str, options: Optional[Dict[str, Any]] = None, user=None) -> Tuple[bool, Dict[str, Any]]:
        """
        پردازش متن
        
        Args:
            text: متن ورودی
            options: تنظیمات پردازش
            user: کاربر درخواست‌کننده
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (موفقیت، نتیجه)
        """
        try:
            self.logger.info(
                'Text processing started',
                extra={
                    'text_length': len(text),
                    'user_id': str(user.id) if user else None
                }
            )
            
            # پردازش متن توسط Text Processor Core
            result = self.text_processor.process_text(text, options)
            
            if result[0]:
                self.logger.info('Text processing completed successfully')
            else:
                self.logger.error('Text processing failed', extra={'error': result[1]})
            
            return result
            
        except Exception as e:
            self.logger.error(f"Text processing service error: {str(e)}")
            return False, {
                'error': 'Text processing failed',
                'message': 'خطا در پردازش متن',
                'details': str(e)
            }
    
    def process_speech(self, audio_data: bytes, options: Optional[Dict[str, Any]] = None, user=None) -> Tuple[bool, Dict[str, Any]]:
        """
        پردازش صدا
        
        Args:
            audio_data: داده‌های صوتی
            options: تنظیمات پردازش
            user: کاربر درخواست‌کننده
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (موفقیت، نتیجه)
        """
        try:
            self.logger.info(
                'Speech processing started',
                extra={
                    'audio_size': len(audio_data),
                    'user_id': str(user.id) if user else None
                }
            )
            
            # پردازش صدا توسط Speech Processor Core
            result = self.speech_processor.process_audio(audio_data, options)
            
            if result[0]:
                self.logger.info('Speech processing completed successfully')
            else:
                self.logger.error('Speech processing failed', extra={'error': result[1]})
            
            return result
            
        except Exception as e:
            self.logger.error(f"Speech processing service error: {str(e)}")
            return False, {
                'error': 'Speech processing failed',
                'message': 'خطا در پردازش صدا',
                'details': str(e)
            }
    
    def speech_to_text(self, audio_data: bytes, language: str = 'fa', user=None) -> Tuple[bool, Dict[str, Any]]:
        """
        تبدیل گفتار به متن
        
        Args:
            audio_data: داده‌های صوتی
            language: زبان گفتار
            user: کاربر درخواست‌کننده
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (موفقیت، نتیجه)
        """
        try:
            result = self.speech_processor.speech_to_text(audio_data, language)
            
            if result[0]:
                self.logger.info(
                    'Speech to text completed',
                    extra={
                        'language': language,
                        'confidence': result[1].get('confidence', 0),
                        'user_id': str(user.id) if user else None
                    }
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Speech to text service error: {str(e)}")
            return False, {
                'error': 'Speech to text failed',
                'message': 'خطا در تبدیل گفتار به متن',
                'details': str(e)
            }
    
    def text_to_speech(self, text: str, language: str = 'fa', voice_options: Optional[Dict] = None, user=None) -> Tuple[bool, Dict[str, Any]]:
        """
        تبدیل متن به گفتار
        
        Args:
            text: متن ورودی
            language: زبان
            voice_options: تنظیمات صدا
            user: کاربر درخواست‌کننده
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (موفقیت، نتیجه)
        """
        try:
            result = self.speech_processor.text_to_speech(text, language, voice_options)
            
            if result[0]:
                self.logger.info(
                    'Text to speech completed',
                    extra={
                        'text_length': len(text),
                        'language': language,
                        'user_id': str(user.id) if user else None
                    }
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Text to speech service error: {str(e)}")
            return False, {
                'error': 'Text to speech failed',
                'message': 'خطا در تبدیل متن به گفتار',
                'details': str(e)
            }
    
    def execute_workflow(self, workflow_config: Dict[str, Any], context: Optional[Dict[str, Any]] = None, user=None) -> Tuple[bool, Dict[str, Any]]:
        """
        اجرای workflow
        
        Args:
            workflow_config: تنظیمات workflow
            context: context اضافی
            user: کاربر درخواست‌کننده
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (موفقیت، نتیجه)
        """
        try:
            # ایجاد رکورد workflow در دیتابیس
            workflow = Workflow.objects.create(
                name=workflow_config.get('name', 'Unnamed Workflow'),
                user=user,
                config=workflow_config,
                context=context or {}
            )
            
            workflow.start()
            
            self.logger.info(
                'Workflow execution started',
                extra={
                    'workflow_id': str(workflow.id),
                    'user_id': str(user.id) if user else None
                }
            )
            
            # اجرای workflow توسط Orchestrator Core
            result = self.orchestrator.execute_workflow(workflow_config, context)
            
            if result[0]:
                workflow.complete(result[1])
                self.logger.info(
                    'Workflow completed successfully',
                    extra={'workflow_id': str(workflow.id)}
                )
            else:
                workflow.fail(result[1].get('message', 'Workflow failed'))
                self.logger.error(
                    'Workflow failed',
                    extra={'workflow_id': str(workflow.id), 'error': result[1]}
                )
            
            # اضافه کردن workflow_id به نتیجه
            if result[0]:
                result[1]['workflow_id'] = str(workflow.id)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Workflow execution service error: {str(e)}")
            return False, {
                'error': 'Workflow execution failed',
                'message': 'خطا در اجرای workflow',
                'details': str(e)
            }
    
    def parallel_execute(self, tasks: list, max_workers: Optional[int] = None, user=None) -> Tuple[bool, Dict[str, Any]]:
        """
        اجرای موازی تسک‌ها
        
        Args:
            tasks: لیست تسک‌ها
            max_workers: حداکثر worker موازی
            user: کاربر درخواست‌کننده
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (موفقیت، نتیجه)
        """
        try:
            self.logger.info(
                'Parallel execution started',
                extra={
                    'tasks_count': len(tasks),
                    'max_workers': max_workers,
                    'user_id': str(user.id) if user else None
                }
            )
            
            result = self.orchestrator.parallel_execute(tasks, max_workers)
            
            if result[0]:
                self.logger.info('Parallel execution completed successfully')
            else:
                self.logger.error('Parallel execution failed', extra={'error': result[1]})
            
            return result
            
        except Exception as e:
            self.logger.error(f"Parallel execution service error: {str(e)}")
            return False, {
                'error': 'Parallel execution failed',
                'message': 'خطا در اجرای موازی',
                'details': str(e)
            }
    
    def get_health_status(self, detailed: bool = False) -> Dict[str, Any]:
        """
        دریافت وضعیت سلامت سیستم
        
        Args:
            detailed: نمایش جزئیات بیشتر
            
        Returns:
            Dict[str, Any]: وضعیت سلامت
        """
        try:
            status = {
                'status': 'healthy',
                'timestamp': timezone.now().isoformat(),
                'version': getattr(settings, 'API_GATEWAY_VERSION', '1.0.0')
            }
            
            if detailed:
                # بررسی دیتابیس
                try:
                    User.objects.first()
                    status['database'] = 'healthy'
                except Exception as e:
                    status['database'] = f'unhealthy: {str(e)}'
                    status['status'] = 'degraded'
                
                # بررسی cores
                status['cores'] = {
                    'api_ingress': 'healthy',
                    'text_processor': 'healthy',
                    'speech_processor': 'healthy',
                    'orchestrator': 'healthy'
                }
                
                # آمار سیستم
                try:
                    status['stats'] = {
                        'active_workflows': len(self.orchestrator.get_active_workflows()),
                        'total_requests_today': self._get_requests_count_today(),
                        'average_response_time': self._get_average_response_time()
                    }
                except Exception as e:
                    status['stats_error'] = str(e)
            
            return status
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
    
    def _create_api_request_log(self, request: Request) -> APIRequest:
        """ایجاد لاگ درخواست API"""
        try:
            # استخراج IP
            ip_address = self.helpers.get_client_ip(request)
            
            # ایجاد رکورد
            api_request = APIRequest.objects.create(
                user=request.user if request.user.is_authenticated else None,
                method=request.method,
                path=request.path,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                request_headers=self._extract_safe_headers(request),
                request_body=self._extract_safe_body(request)
            )
            
            return api_request
            
        except Exception as e:
            self.logger.error(f"Failed to create API request log: {str(e)}")
            # در صورت خطا، یک instance ساختگی برمی‌گردانیم
            return APIRequest(
                method=request.method,
                path=request.path,
                ip_address='unknown'
            )
    
    def _check_rate_limit(self, request: Request, api_request: APIRequest) -> Tuple[bool, Dict[str, Any]]:
        """بررسی محدودیت نرخ درخواست"""
        try:
            user = request.user if request.user.is_authenticated else None
            ip_address = self.helpers.get_client_ip(request)
            endpoint = request.path
            
            return self.helpers.check_rate_limit(
                user=user,
                ip_address=ip_address,
                endpoint=endpoint,
                limit=self.default_rate_limit
            )
            
        except Exception as e:
            self.logger.error(f"Rate limit check error: {str(e)}")
            # در صورت خطا، اجازه ادامه می‌دهیم
            return True, {}
    
    def _execute_processing(self, request: Request, processor_type: str, routing_config: Dict, metadata: Dict) -> Tuple[bool, Dict[str, Any]]:
        """انجام پردازش اصلی درخواست"""
        try:
            if processor_type == 'text_processor':
                # استخراج متن از درخواست
                text = self._extract_text_from_request(request)
                if not text:
                    return False, {
                        'error': 'No text found in request',
                        'message': 'متن در درخواست یافت نشد'
                    }
                
                options = self._extract_processing_options(request)
                return self.text_processor.process_text(text, options)
                
            elif processor_type == 'speech_processor':
                # استخراج داده‌های صوتی از درخواست
                audio_data = self._extract_audio_from_request(request)
                if not audio_data:
                    return False, {
                        'error': 'No audio data found in request',
                        'message': 'داده‌های صوتی در درخواست یافت نشد'
                    }
                
                options = self._extract_processing_options(request)
                return self.speech_processor.process_audio(audio_data, options)
                
            elif processor_type == 'orchestrator':
                # استخراج تنظیمات workflow
                workflow_config = self._extract_workflow_config(request)
                if not workflow_config:
                    return False, {
                        'error': 'No workflow config found in request',
                        'message': 'تنظیمات workflow در درخواست یافت نشد'
                    }
                
                context = metadata.copy()
                return self.orchestrator.execute_workflow(workflow_config, context)
            
            else:
                return False, {
                    'error': 'Unknown processor type',
                    'message': f'نوع پردازش‌کننده {processor_type} شناخته نشده است'
                }
                
        except Exception as e:
            return False, {
                'error': 'Processing execution failed',
                'message': 'خطا در اجرای پردازش',
                'details': str(e)
            }
    
    def _extract_safe_headers(self, request: Request) -> Dict[str, str]:
        """استخراج ایمن headers"""
        safe_headers = {}
        sensitive_headers = ['authorization', 'cookie', 'x-api-key']
        
        for key, value in request.META.items():
            if key.startswith('HTTP_'):
                header_name = key[5:].lower().replace('_', '-')
                if header_name not in sensitive_headers:
                    safe_headers[header_name] = str(value)[:200]  # محدود کردن طول
        
        return safe_headers
    
    def _extract_safe_body(self, request: Request) -> Dict[str, Any]:
        """استخراج ایمن body درخواست"""
        try:
            if hasattr(request, 'data'):
                # محدود کردن اندازه body که لاگ می‌شود
                body_str = str(request.data)
                if len(body_str) > 1000:
                    return {'truncated': True, 'size': len(body_str)}
                return request.data
            return {}
        except Exception:
            return {}
    
    def _extract_text_from_request(self, request: Request) -> Optional[str]:
        """استخراج متن از درخواست"""
        if hasattr(request, 'data'):
            return request.data.get('text')
        return None
    
    def _extract_audio_from_request(self, request: Request) -> Optional[bytes]:
        """استخراج داده‌های صوتی از درخواست"""
        if hasattr(request, 'data'):
            audio_b64 = request.data.get('audio_data')
            if audio_b64:
                import base64
                try:
                    return base64.b64decode(audio_b64)
                except Exception:
                    pass
        return None
    
    def _extract_workflow_config(self, request: Request) -> Optional[Dict[str, Any]]:
        """استخراج تنظیمات workflow از درخواست"""
        if hasattr(request, 'data'):
            return request.data.get('workflow_config')
        return None
    
    def _extract_processing_options(self, request: Request) -> Dict[str, Any]:
        """استخراج تنظیمات پردازش از درخواست"""
        if hasattr(request, 'data'):
            return request.data.get('options', {})
        return {}
    
    def _get_requests_count_today(self) -> int:
        """دریافت تعداد درخواست‌های امروز"""
        from datetime import date
        try:
            return APIRequest.objects.filter(
                created_at__date=date.today()
            ).count()
        except Exception:
            return 0
    
    def _get_average_response_time(self) -> float:
        """دریافت میانگین زمان پاسخ"""
        try:
            from django.db.models import Avg
            result = APIRequest.objects.filter(
                processing_time__isnull=False
            ).aggregate(avg_time=Avg('processing_time'))
            return result['avg_time'] or 0
        except Exception:
            return 0