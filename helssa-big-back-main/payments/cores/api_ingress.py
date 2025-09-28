"""
هسته مدیریت ورودی و خروجی API برای پرداخت‌ها
"""
import logging
from typing import Dict, Any, Optional, Tuple
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class APIIngressCore:
    """
    مدیریت ورودی و خروجی API برای سیستم پرداخت
    
    این کلاس مسئول:
    - دریافت و اعتبارسنجی درخواست‌های API
    - فرمت‌دهی پاسخ‌های API
    - مدیریت خطاها و لاگ‌گیری
    """
    
    def __init__(self):
        self.logger = logger
        
    def process_request(self, request: Request) -> Tuple[bool, Dict[str, Any]]:
        """
        پردازش درخواست ورودی
        
        Args:
            request: درخواست REST framework
            
        Returns:
            Tuple[bool, Dict]: (موفقیت، داده‌های پردازش شده)
        """
        try:
            # بررسی وجود داده‌های ضروری
            if not request.data:
                return False, {
                    'error': 'empty_request',
                    'message': 'داده‌ای ارسال نشده است'
                }
            
            # لاگ درخواست ورودی
            self.logger.info(
                f"Payment API request received",
                extra={
                    'user_id': request.user.id if request.user.is_authenticated else None,
                    'method': request.method,
                    'path': request.path
                }
            )
            
            return True, {'data': request.data}
            
        except Exception as e:
            self.logger.error(f"Error processing request: {str(e)}")
            return False, {
                'error': 'request_processing_failed',
                'message': 'خطا در پردازش درخواست'
            }
    
    def format_response(
        self, 
        success: bool, 
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        message: Optional[str] = None,
        status_code: int = status.HTTP_200_OK
    ) -> Response:
        """
        فرمت‌دهی پاسخ API
        
        Args:
            success: وضعیت موفقیت عملیات
            data: داده‌های پاسخ
            error: کد خطا
            message: پیام کاربری
            status_code: کد وضعیت HTTP
            
        Returns:
            Response: پاسخ فرمت شده
        """
        response_data = {
            'success': success
        }
        
        if success and data:
            response_data['data'] = data
        elif not success:
            response_data['error'] = error or 'unknown_error'
            response_data['message'] = message or 'خطای ناشناخته'
            
        # لاگ پاسخ
        self.logger.info(
            f"Payment API response",
            extra={
                'success': success,
                'status_code': status_code,
                'error': error
            }
        )
        
        return Response(response_data, status=status_code)
    
    def handle_error(self, exception: Exception, context: str = "") -> Response:
        """
        مدیریت خطاها
        
        Args:
            exception: خطای رخ داده
            context: زمینه رخداد خطا
            
        Returns:
            Response: پاسخ خطا
        """
        error_id = f"payment_error_{id(exception)}"
        
        self.logger.error(
            f"Payment error in {context}: {str(exception)}",
            extra={
                'error_id': error_id,
                'error_type': type(exception).__name__,
                'context': context
            },
            exc_info=True
        )
        
        return self.format_response(
            success=False,
            error='internal_error',
            message='خطای داخلی سرور. لطفاً بعداً تلاش کنید.',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )