"""
درگاه پرداخت آیدی‌پی
IDPay Payment Gateway
"""

import requests
from typing import Dict, Optional
from .base_gateway import BasePaymentGateway, PaymentGatewayError, PaymentVerificationError


class IDPayGateway(BasePaymentGateway):
    """درگاه پرداخت آیدی‌پی"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.api_key = config['api_key']
        self.base_url = config.get('base_url', 'https://api.idpay.ir/v1.1')
        self.callback_url = config.get('callback_url', '')
        self.sandbox = config.get('sandbox', False)
        
    def create_payment(
        self,
        amount: int,
        order_id: str,
        callback_url: str,
        description: str = "",
        mobile: Optional[str] = None,
        email: Optional[str] = None
    ) -> Dict:
        """ایجاد پرداخت در آیدی‌پی"""
        
        self.validate_amount(amount)
        
        # آماده‌سازی درخواست
        payload = {
            "order_id": order_id,
            "amount": amount,
            "callback": callback_url or self.callback_url,
            "desc": description or f"پرداخت سفارش {order_id}",
        }
        
        # اضافه کردن اطلاعات اختیاری
        if mobile:
            payload["phone"] = mobile
        if email:
            payload["mail"] = email
            
        headers = {
            'Content-Type': 'application/json',
            'X-API-KEY': self.api_key,
            'X-SANDBOX': '1' if self.sandbox else '0'
        }
        
        try:
            # ارسال درخواست
            response = requests.post(
                f"{self.base_url}/payment",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 201:
                result = response.json()
                
                self.log_request('create_payment', payload, result)
                
                return {
                    'success': True,
                    'payment_url': result['link'],
                    'reference': result['id'],
                    'gateway': 'idpay'
                }
            else:
                error_data = response.json() if response.content else {}
                error_message = self._get_error_message(
                    error_data.get('error_code', response.status_code)
                )
                raise PaymentGatewayError(f"خطا در ایجاد پرداخت: {error_message}")
                
        except requests.RequestException as e:
            self.logger.error(f"IDPay request error: {str(e)}")
            raise PaymentGatewayError(f"خطا در اتصال به آیدی‌پی: {str(e)}")
        except Exception as e:
            self.logger.error(f"IDPay create payment error: {str(e)}")
            raise PaymentGatewayError(f"خطا در ایجاد پرداخت آیدی‌پی: {str(e)}")
            
    def verify_payment(
        self,
        reference: str,
        amount: Optional[int] = None
    ) -> Dict:
        """تایید پرداخت آیدی‌پی"""
        
        # آماده‌سازی درخواست
        payload = {
            "id": reference,
            "order_id": reference  # در صورت نیاز به order_id
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-API-KEY': self.api_key,
            'X-SANDBOX': '1' if self.sandbox else '0'
        }
        
        try:
            # ارسال درخواست تایید
            response = requests.post(
                f"{self.base_url}/payment/verify",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                self.log_request('verify_payment', payload, result)
                
                return {
                    'success': True,
                    'amount': result['amount'],
                    'reference': result['id'],
                    'track_id': result['track_id'],
                    'order_id': result['order_id'],
                    'card_no': result.get('payment', {}).get('card_no', 'نامشخص'),
                    'hashed_card_no': result.get('payment', {}).get('hashed_card_no', ''),
                    'date': result.get('payment', {}).get('date'),
                    'gateway': 'idpay'
                }
            else:
                error_data = response.json() if response.content else {}
                error_message = self._get_error_message(
                    error_data.get('error_code', response.status_code)
                )
                raise PaymentVerificationError(error_message)
                
        except requests.RequestException as e:
            self.logger.error(f"IDPay verify error: {str(e)}")
            raise PaymentVerificationError(f"خطا در اتصال به آیدی‌پی: {str(e)}")
        except Exception as e:
            self.logger.error(f"IDPay verify payment error: {str(e)}")
            raise PaymentVerificationError(f"خطا در تایید پرداخت آیدی‌پی: {str(e)}")
            
    def refund_payment(
        self,
        reference: str,
        amount: Optional[int] = None
    ) -> Dict:
        """بازگشت وجه در آیدی‌پی"""
        
        # آیدی‌پی از بازگشت وجه پشتیبانی می‌کند
        # ولی نیاز به تنظیمات خاص دارد
        
        return {
            'success': False,
            'message': 'بازگشت وجه در آیدی‌پی نیاز به تنظیمات خاص دارد',
            'manual_refund_required': True,
            'gateway': 'idpay'
        }
    
    def _get_error_message(self, error_code) -> str:
        """دریافت پیام خطا بر اساس کد"""
        error_messages = {
            11: 'کاربر مسدود شده است',
            12: 'API Key یافت نشد',
            13: 'درخواست شما از {ip} ارسال شده است. این IP با IP های ثبت شده در وب سرویس همخوانی ندارد',
            14: 'وب سرویس تایید نشده است',
            21: 'حساب بانکی متصل به وب سرویس تایید نشده است',
            31: 'کد تراکنش order_id تکراری است',
            32: 'مبلغ کمتر از حداقل مجاز است',
            33: 'مبلغ بیشتر از حداکثر مجاز است',
            34: 'مبلغ بیشتر از سقف روزانه است',
            35: 'مبلغ بیشتر از سقف ماهانه است',
            41: 'فیلد order_id خالی است',
            42: 'فیلد amount خالی است',
            43: 'فیلد phone خالی است',
            44: 'فیلد callback خالی است',
            45: 'فیلد desc خالی است',
            51: 'تراکنش ایجاد نشد',
            52: 'استعلام ناموفق',
            53: 'تایید پرداخت ناموفق',
            54: 'مدت زمان تایید پرداخت سپری شده است',
            401: 'عدم دسترسی',
            403: 'دسترسی غیر مجاز',
            404: 'یافت نشد',
            500: 'خطای سرور'
        }
        
        return error_messages.get(error_code, f'خطای ناشناخته: {error_code}')