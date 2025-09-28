"""
درگاه پرداخت پایه
Base Payment Gateway
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
import logging


class BasePaymentGateway(ABC):
    """کلاس پایه برای تمام درگاه‌های پرداخت"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.name = self.__class__.__name__
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
        
    @abstractmethod
    def create_payment(
        self,
        amount: int,
        order_id: str,
        callback_url: str,
        description: str = "",
        mobile: Optional[str] = None,
        email: Optional[str] = None
    ) -> Dict:
        """
        ایجاد پرداخت جدید
        
        Args:
            amount: مبلغ به ریال
            order_id: شناسه سفارش
            callback_url: آدرس برگشت
            description: توضیحات
            mobile: شماره موبایل
            email: ایمیل
            
        Returns:
            Dict: نتیجه ایجاد پرداخت
        """
        pass
        
    @abstractmethod
    def verify_payment(
        self,
        reference: str,
        amount: Optional[int] = None
    ) -> Dict:
        """
        تایید پرداخت
        
        Args:
            reference: شماره مرجع
            amount: مبلغ (اختیاری)
            
        Returns:
            Dict: نتیجه تایید
        """
        pass
        
    @abstractmethod
    def refund_payment(
        self,
        reference: str,
        amount: Optional[int] = None
    ) -> Dict:
        """
        بازگشت وجه
        
        Args:
            reference: شماره مرجع
            amount: مبلغ بازگشت (اختیاری)
            
        Returns:
            Dict: نتیجه بازگشت
        """
        pass
        
    def validate_amount(self, amount: int):
        """اعتبارسنجی مبلغ"""
        if amount < 1000:
            raise ValueError("حداقل مبلغ پرداخت 1000 ریال است")
        if amount > 500000000:
            raise ValueError("حداکثر مبلغ پرداخت 500 میلیون ریال است")
            
    def log_request(self, method: str, data: Dict, response: Dict = None):
        """ثبت لاگ درخواست"""
        log_data = {
            'gateway': self.name,
            'method': method,
            'request_data': self._sanitize_data(data),
        }
        
        if response:
            log_data['response'] = self._sanitize_data(response)
            
        self.logger.info(f"Gateway request: {method}", extra=log_data)
        
    def _sanitize_data(self, data: Dict) -> Dict:
        """حذف اطلاعات حساس از لاگ"""
        sensitive_fields = ['api_key', 'merchant_id', 'password', 'token']
        sanitized = data.copy()
        
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = '***'
                
        return sanitized


class PaymentGatewayError(Exception):
    """خطای درگاه پرداخت"""
    pass


class PaymentVerificationError(Exception):
    """خطای تایید پرداخت"""
    pass