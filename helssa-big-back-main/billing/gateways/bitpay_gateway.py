"""
درگاه پرداخت BitPay.ir
BitPay.ir Payment Gateway
"""

import requests
from typing import Dict, Optional
from .base_gateway import BasePaymentGateway, PaymentGatewayError, PaymentVerificationError


class BitPayGateway(BasePaymentGateway):
    """درگاه پرداخت BitPay.ir"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.api_key = config['api_key']
        self.base_url = config.get('base_url', 'https://bitpay.ir/payment')
        self.callback_url = config.get('callback_url', '')
        
    def create_payment(
        self,
        amount: int,
        order_id: str,
        callback_url: str,
        description: str = "",
        mobile: Optional[str] = None,
        email: Optional[str] = None
    ) -> Dict:
        """ایجاد پرداخت در BitPay"""
        
        self.validate_amount(amount)
        
        # آماده‌سازی داده‌ها
        data = {
            'api': self.api_key,
            'amount': amount,
            'factorId': order_id,
            'redirect': callback_url or self.callback_url,
            'name': mobile or '',
            'email': email or '',
            'description': description or f'پرداخت سفارش {order_id}'
        }
        
        try:
            # ارسال درخواست
            response = requests.post(
                f"{self.base_url}/gateway-send",
                data=data,
                timeout=30
            )
            
            result = response.json()
            
            self.log_request('create_payment', data, result)
            
            # بررسی پاسخ
            if result.get('status') == -1:
                return {
                    'success': True,
                    'payment_url': f"{self.base_url}/gateway/{result['id_get']}",
                    'reference': result['id_get'],
                    'gateway': 'bitpay'
                }
            else:
                error_messages = {
                    -2: 'transId یافت نشد',
                    -3: 'api_key یافت نشد',
                    -4: 'amount نامعتبر',
                    -5: 'واحد پول نامعتبر',
                    -6: 'transId تکراری',
                    -7: 'api_key نامعتبر'
                }
                
                error_message = error_messages.get(
                    result.get('status'), 
                    'خطای ناشناخته'
                )
                
                raise PaymentGatewayError(error_message)
                
        except requests.RequestException as e:
            self.logger.error(f"BitPay request error: {str(e)}")
            raise PaymentGatewayError(f"خطا در اتصال به BitPay: {str(e)}")
        except Exception as e:
            self.logger.error(f"BitPay create payment error: {str(e)}")
            raise PaymentGatewayError(f"خطا در ایجاد پرداخت BitPay: {str(e)}")
            
    def verify_payment(
        self,
        reference: str,
        amount: Optional[int] = None
    ) -> Dict:
        """تایید پرداخت BitPay"""
        
        # آماده‌سازی داده‌ها
        data = {
            'api': self.api_key,
            'id_get': reference,
            'json': 1
        }
        
        try:
            # ارسال درخواست تایید
            response = requests.post(
                f"{self.base_url}/gateway-result-second",
                data=data,
                timeout=30
            )
            
            result = response.json()
            
            self.log_request('verify_payment', data, result)
            
            # بررسی نتیجه
            if result.get('status') == 1:
                return {
                    'success': True,
                    'amount': int(result['amount']),
                    'factor_id': result['factorId'],
                    'reference': result['id_get'],
                    'card_number': result.get('cardNumber', 'نامشخص'),
                    'date': result.get('date'),
                    'gateway': 'bitpay'
                }
            else:
                error_messages = {
                    -1: 'api_key نامعتبر',
                    -2: 'transId یافت نشد',
                    -3: 'تراکنش قبلاً تایید شده',
                    -4: 'amount نامطابق',
                    2: 'تراکنش یافت نشد',
                    3: 'توکن منقضی شده',
                    4: 'مبلغ نادرست',
                    7: 'انصراف از پرداخت'
                }
                
                error_message = error_messages.get(
                    result.get('status'), 
                    'خطای ناشناخته در تایید'
                )
                
                raise PaymentVerificationError(error_message)
                
        except requests.RequestException as e:
            self.logger.error(f"BitPay verify error: {str(e)}")
            raise PaymentVerificationError(f"خطا در اتصال به BitPay: {str(e)}")
        except Exception as e:
            self.logger.error(f"BitPay verify payment error: {str(e)}")
            raise PaymentVerificationError(f"خطا در تایید پرداخت BitPay: {str(e)}")
            
    def refund_payment(
        self,
        reference: str,
        amount: Optional[int] = None
    ) -> Dict:
        """بازگشت وجه در BitPay"""
        
        # BitPay.ir بازگشت خودکار ندارد
        # باید به صورت دستی انجام شود
        
        return {
            'success': False,
            'message': 'بازگشت وجه باید به صورت دستی انجام شود',
            'manual_refund_required': True,
            'gateway': 'bitpay'
        }